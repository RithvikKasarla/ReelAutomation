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
from moviepy.video.fx import CrossFadeIn, CrossFadeOut, MultiplySpeed
from moviepy import *
import ffmpeg
import math
import requests
from image_generator import generate_image, create_rounded_corner_mask

load_dotenv()

def get_random_video_segment():
    folder_path = "Backgrounds"
    try:
        video_files = [file for file in os.listdir(folder_path) if file.endswith(('.mp4', '.avi', '.mov', '.mkv'))]
    except FileNotFoundError:
        raise FileNotFoundError(f"The folder '{folder_path}' does not exist.")
    if not video_files:
        raise FileNotFoundError(f"No video files found in the folder '{folder_path}'.")
    random_video = random.choice(video_files)
    return os.path.join(folder_path, random_video)

def create_introspective_video_type(input_video, situation, is_play_style, output_file):
    # duration = 15
    cropped_video = "cropped_video.mp4"
    crop_to_aspect_ratio(input_video, cropped_video)
    background_clip = VideoFileClip(cropped_video)
    duration = background_clip.duration
    # slowed_background_clip = MultiplySpeed(final_duration=duration).apply(background_clip)
    video_width, video_height = background_clip.size
    if is_play_style:
        white_bar_height = int(video_height * 0.4)
    else:
        white_bar_height = int(video_height * 0.3)
        
    total_height = video_height + white_bar_height
    white_bar = (
        ColorClip(size=(video_width, white_bar_height), color=(255, 255, 255))
        .with_duration(duration)
        .with_position(("center", "top"))
    )

    # Step 8: Create a TextClip for the situation
    situation_clip = (
        TextClip(
            text=situation,
            font="./Fonts/Arial.ttf",
            font_size=40,
            color="black",
            size=(video_width, white_bar_height),
            method="caption",
        )
        .with_duration(duration)
        .with_position(("center", "top"))
    )
    audio_clip = AudioFileClip(get_random_audio_track()).subclipped(0, duration)

    positioned_background_clip = background_clip.with_position(("center", white_bar_height))
    final_clip = CompositeVideoClip([white_bar, positioned_background_clip, situation_clip], size=(video_width, total_height))
    final_clip = final_clip.with_audio(audio_clip)
    final_clip.write_videofile(output_file) 

def get_random_audio_track():
    folder_path = "Music"
    try:
        audio_files = [file for file in os.listdir(folder_path) if file.endswith(('.mp3', '.wav'))]
    except FileNotFoundError:
        raise FileNotFoundError(f"The folder '{folder_path}' does not exist.")
    if not audio_files:
        raise FileNotFoundError(f"No audio files found in the folder '{folder_path}'.")
    random_audio = random.choice(audio_files)
    return os.path.join(folder_path, random_audio)

# def mask_opacity(t, total_duration, fade_duration):
#     if t < fade_duration:  # Fade-in
#         return t / fade_duration
#     elif t > (total_duration - fade_duration):  # Fade-out
#         return (total_duration - t) / fade_duration
#     else:  # Fully visible
#         return 1 

def create_background(audio_length, philosopher, output_file = "output_video_uncropped.mp4"):
    generate_image( f"generate me an image of a stone masshead of the philosopher {philosopher}, make it black and white. Behind it should be some kind of stoneish wall", "philosopher_image.png")
    
    final_clip = ImageClip("philosopher_image.png").with_duration(audio_length)
    final_clip.write_videofile(output_file, fps=24)
    
    
def crop_to_aspect_ratio(input_video, output_video):
    # Probe video to get original dimensions
    probe = ffmpeg.probe(input_video)
    video_stream = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
    width = int(video_stream['width'])
    height = int(video_stream['height'])

    target_width = height * 3 // 4
    crop_x = (width - target_width) // 2 

    ffmpeg.input(input_video).crop(x=crop_x, y=0, width=target_width, height=height).output(output_video).overwrite_output().run()


def overlay_text(video_file, audio_file, text, philosopher, output_file):
    """
    Overlays text on the center of the video and adds background audio.
    
    Parameters:
        video_file (str): Path to the input video file.
        audio_file (str): Path to the background audio file.
        text (str): Text to overlay on the video.
        output_file (str): Path to save the output video file.
    """
    # Load the video and audio clips
    video = VideoFileClip(video_file)
    audio = AudioFileClip(audio_file)

    # Create a TextClip for overlaying text
    main_text_clip = (
        TextClip(
            font="./Fonts/Arial.ttf",
            text=text,
            font_size=35,
            color="white",
            stroke_color="black",
            stroke_width=2,
            method="caption",
            size=(video.size[0], None)
        )
        .with_position("center", video.size[1] // 2 - 150)
        .with_duration(video.duration)
    )
    
    philosopher_clip = (
        TextClip(
            font="./Fonts/Arial.ttf",
            text=philosopher,
            font_size=40,
            color="white",
            stroke_color="black",
            stroke_width=2,
            method="caption",
            size=(video.size[0], None)
        )
        .with_position(("center", video.size[1] // 2 + 100))  # Adjust y-offset
        .with_duration(video.duration)
    )

    like_follow_clip = (
        TextClip(
            font="./Fonts/Arial.ttf",
            text= "Like & Follow",
            font_size=35,
            color="white",
            stroke_color="black",
            stroke_width=2,
            method="caption",
            size=(video.size[0], None)
        )
        .with_position(("center", video.size[1] // 2 + 200))  # Adjust y-offset further
        .with_duration(video.duration)
    )


    final_video = CompositeVideoClip([video, main_text_clip, philosopher_clip, like_follow_clip])
    final_video.audio = CompositeAudioClip([audio])
    final_video.write_videofile(output_file)

if __name__ == "__main__":
    video_file = "output_video.mp4"
    audio_file = "output.mp3"
    output_file = "final_video.mp4"
    # input_video = "input.mp4"
    output_video_crop = "output_cropped.mp4"
    add_wave_and_mist_with_opencv("philosopher_image.png", 10, "philosopher_effects.mp4")
    # get_random_video_segment(10, "Aristotle")
    # # Crop the video
    # crop_to_aspect_ratio(video_file, output_video_crop)

    # overlay_text_with_groq(video_file, audio_file, output_file)
