import os
import random
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import ImageClip
from dotenv import load_dotenv
from groq import Groq
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing import CompositeVideoClip
from moviepy.video.fx.FadeIn import FadeIn
from moviepy.video.fx.FadeOut import FadeOut
from moviepy.video.fx import CrossFadeIn, CrossFadeOut
from moviepy import *
import ffmpeg
import math
import requests
from image_generator import generate_image, create_rounded_corner_mask

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def mask_opacity(t, total_duration, fade_duration):
    if t < fade_duration:  # Fade-in
        return t / fade_duration
    elif t > (total_duration - fade_duration):  # Fade-out
        return (total_duration - t) / fade_duration
    else:  # Fully visible
        return 1

def overlay_images_and_text_with_chunks(video_file, audio_file, output_file):
    """
    Overlays DALL-E-generated images and transcribed 3-word chunks on a video.
    Args:
        video_file (str): Path to the input video file.
        audio_file (str): Path to the input audio file.
        output_file (str): Path to the output video file.
    """
    # Transcribe audio into broader segments
    segments = transcribe_audio_with_groq(audio_file)  # Original segments (unsplit)

    video = VideoFileClip(video_file)
    audio = AudioFileClip(audio_file)
    video = video.with_audio(audio)

    video_width, video_height = video.size

    # Define a maximum size for the image
    max_image_width = video_width * 0.5  # Half the video width
    max_image_height = video_height * 0.4  # 40% of the video height
    
    text_clips = []
    image_clips = []
    rounded_mask = create_rounded_corner_mask(
        (int(max_image_width), int(max_image_height)),  # Size matches resized image
        radius=20  # Adjust radius for corner rounding
    )
    for i, seg in enumerate(segments):
        start_time = seg["start"]
        end_time = seg["end"]
        text_content = seg["text"]

        # Generate an image for the topic of this segment
        prompt = text_content  # Use the segment text as a broad DALL-E prompt
#        image_path = f"segment_topic_image_{i}.png"
#        generate_image(prompt, image_path)

        # Create an ImageClip for the generated image
#        total_duration = end_time - start_time
#        try:
#            img_clip = (
#                ImageClip(image_path)
#                .resized(height=max_image_height)
#                .with_duration(total_duration)  # Match image duration to segment duration
#                .with_start(start_time)  # Start at the segment's start time
#                .with_position(("center", 50))  # Position at the top
#            )
#            fade_duration = 0.5  # 1-second fade
#            img_clip = CrossFadeIn(fade_duration).apply(img_clip)
#            img_clip = CrossFadeOut(fade_duration).apply(img_clip)
            # img_clip = add_fade_effects(img_clip, fade_duration) # Add fade-in and fade-out effects
#            image_clips.append(img_clip)
#        except Exception as e:
#            print(f"Error creating image clip for segment {i}: {e}")
            
        # Split text into 3-word chunks and create TextClips for each
        three_word_segments = split_segments([seg], words_per_chunk=3)  # Split this segment only
        bottom_padding = 75
        for chunk in three_word_segments:
            chunk_start = chunk["start"]
            chunk_end = chunk["end"]
            chunk_text = chunk["text"]

            txt_clip = (
                TextClip(
                    font="./Fonts/Arial.ttf",
                    text=chunk_text,
                    font_size=28,
                    color="black",
                    stroke_color="white",
                    stroke_width=2,
                    method="caption",
                    size=(video.size[0], None)
                )
                .with_position(("center", video_height/2 + bottom_padding))  # Text at the bottom center
                .with_start(chunk_start)
                .with_end(chunk_end)
            )
            text_clips.append(txt_clip)
    #final_video = CompositeVideoClip([video] + image_clips + text_clips)
    final_video = CompositeVideoClip([video] + text_clips)
    final_video.audio = CompositeAudioClip([audio])    
    final_video.write_videofile(output_file)

def get_random_video_segment(audio_length, videos_folder="backgrounds"):
    video_files = [f for f in os.listdir(videos_folder) if f.endswith((".mp4", ".mov", ".avi", ".mkv"))]
    if not video_files:
        raise FileNotFoundError("No video files found in the backgrounds folder.")

    selected_video = random.choice(video_files)
    video_path = os.path.join(videos_folder, selected_video)

    video_clip = VideoFileClip(video_path)
    video_duration = video_clip.duration

    if video_duration < audio_length:
        raise ValueError(f"The video {selected_video} is too short for the audio length ({audio_length} seconds).")

    start_time = random.uniform(0, video_duration - audio_length)
    end_time = start_time + audio_length

    video_segment = video_clip.subclipped(start_time, end_time)

    video_segment = video_segment.without_audio()
    return video_segment

def crop_to_aspect_ratio(input_video, output_video):
    # Probe video to get original dimensions
    probe = ffmpeg.probe(input_video)
    video_stream = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
    width = int(video_stream['width'])
    height = int(video_stream['height'])

    target_width = height * 3 // 4
    crop_x = (width - target_width) // 2 

    ffmpeg.input(input_video).crop(x=crop_x, y=0, width=target_width, height=height).output(output_video).overwrite_output().run()

def split_segments(segments, words_per_chunk=3):
    """
    Takes the transcribed segments (each having a start, end, text)
    and returns a new list of segments, each with up to `words_per_chunk` words.
    The total segment duration is evenly distributed among the smaller chunks.
    """
    new_segments = []
    for seg in segments:
        original_start = seg["start"]
        original_end   = seg["end"]
        text          = seg["text"].strip()

        # Split the text into words
        words = text.split()
        if not words:
            continue

        total_words = len(words)
        segment_duration = original_end - original_start

        # Number of sub-segments needed
        num_chunks = math.ceil(total_words / words_per_chunk)
        # Each chunk gets an equal share of the original duration
        chunk_duration = segment_duration / num_chunks

        for i in range(num_chunks):
            chunk_start = original_start + i * chunk_duration
            chunk_end   = original_start + (i + 1) * chunk_duration

            # Slice out up to `words_per_chunk` words for this chunk
            chunk_words = words[i * words_per_chunk : (i + 1) * words_per_chunk]
            chunk_text  = " ".join(chunk_words)

            new_segments.append({
                "start": chunk_start,
                "end":   chunk_end,
                "text":  chunk_text
            })

    return new_segments

def transcribe_audio_with_groq(audio_file):
    """
    Transcribes audio using the Groq API and returns segments with timestamps.
    """
    with open(audio_file, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(audio_file, file.read()),
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
            language="en",
        )
    # print(transcription)
    return transcription.segments

def overlay_text_with_groq(video_file, audio_file, output_file):
    """
    Overlays transcribed text on a given video, synchronized with the voice
    segments provided by Groq’s transcription.
    """
    # print("Transcribing audio...")
    segments = transcribe_audio_with_groq(audio_file)
    segments = split_segments(segments, words_per_chunk=3)

    video = VideoFileClip(video_file)
    audio = AudioFileClip(audio_file)

    video = video.with_audio(audio)

    text_clips = []
    for seg in segments:
        start_time = seg["start"]
        end_time = seg["end"]
        text_content = seg["text"]

        txt_clip = (
            TextClip(
                font="./Fonts/Arial.ttf",
                text=text_content,
                font_size=28,
                color="black",
                stroke_color="white",
                stroke_width=2,
                method="caption",
                size=(video.size[0], None)
            )
            .with_position(("center"))
            .with_start(start_time)
            .with_end(end_time)
        )

        text_clips.append(txt_clip)

    final_video = CompositeVideoClip([video] + text_clips)


    new_audioclip = CompositeAudioClip([audio])
    final_video.audio = new_audioclip
    final_video.write_videofile(output_file)

if __name__ == "__main__":
    video_file = "output_video.mp4"
    audio_file = "output.mp3"
    output_file = "final_video.mp4"
    # input_video = "input.mp4"
    output_video_crop = "output_cropped.mp4"

    # Crop the video
    crop_to_aspect_ratio(video_file, output_video_crop)

    # overlay_text_with_groq(video_file, audio_file, output_file)
