from brain import topic_identifier, refine_description, determine_voice, make_caption
from voice_maker import get_ttl
from video_compiler import get_random_video_segment, overlay_text_with_groq, overlay_images_and_text_with_chunks, crop_to_aspect_ratio
from pydub import AudioSegment
from aws import upload_to_s3
from instagrammer import post_reel
import time
import os
import schedule

S3_BUCKET_NAME = "educationalreeltempstorage"
S3_REGION = "us-east-1"

output_video_file = "output_video.mp4"

def get_audio_length(audio_file):
    audio = AudioSegment.from_file(audio_file)
    return len(audio) / 1000

def main():
    topic = topic_identifier()
    # topic = "The surprising science behind why your favorite songs get stuck in your head (earworms)."
    print("TOPIC: ", topic)

    voice_id = determine_voice()
    description = refine_description(topic, voice_id)
    print("voice id: ", voice_id)

    audio_data = get_ttl(description, voice_id)
    print("AUDEO MADE")

    with open("output.mp3", "wb") as file:
        file.write(audio_data)
    
    
    video_segment = get_random_video_segment(get_audio_length("output.mp3"), videos_folder="backgrounds")
    output_video_file = "output_video_uncropped.mp4"
    video_segment.write_videofile(output_video_file)

    crop_to_aspect_ratio(output_video_file, 'output_video.mp4')
    overlay_images_and_text_with_chunks('output_video.mp4', "output.mp3", "final_video.mp4")
    # overlay_text_with_groq('output_video.mp4', "output.mp3", "final_video.mp4")
    
    video_url = upload_to_s3("final_video.mp4", S3_BUCKET_NAME, S3_REGION)
    caption = make_caption(topic, description)
    post_reel(video_url, caption)
    
def cleanup_files(files_to_delete): 
    """
    Deletes specific files if they exist.

    Args:
        files_to_delete (list): List of file paths to delete.
    """
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
        else:
            print(f"File not found, skipping: {file_path}")
          
def run_main():
    files_to_delete = [
        "final_video.mp4",
        "output_video_uncropped.mp4",
        "output_video.mp4",
        "output.mp3",
    ]
    try:
        cleanup_files(files_to_delete)
        main()
    except Exception as e:
        print(f"Error: {e}")
        cleanup_files(files_to_delete)

schedule.every(2).hours.do(run_main)

if __name__ == "__main__":
    print("Scheduler is running. The script will execute once per hour.")
    run_main()  # Run immediately at the start
    while True:
        schedule.run_pending()
        time.sleep(1) 
    
