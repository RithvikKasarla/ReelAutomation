from brain import GetPhilosopher, quote_generator, make_caption, situation_maker, play_situation_maker
from voice_maker import get_ttl
from video_compiler import create_background, overlay_text, crop_to_aspect_ratio, create_introspective_video_type, get_random_video_segment
from pydub import AudioSegment
from aws import upload_to_s3
from instagrammer import post_reel
import time
import os
import schedule
import random

S3_BUCKET_NAME = "educationalreeltempstorage"
S3_REGION = "us-east-1"

output_video_file = "output_video.mp4"

def get_audio_length(audio_file):
    audio = AudioSegment.from_file(audio_file)
    return len(audio) / 1000

def main():
    random_number = random.randint(0, 10)
    philosopher = GetPhilosopher()
    print("Philosopher: ", philosopher)
    quote = quote_generator(philosopher)
    print("QUOTE: ", quote)
    caption = make_caption(philosopher, quote)

    if random_number <= 9: # Introspective video
        random_number = random.randint(0, 1)
        # random_number = 1 # For testing 
        play = False
        if random_number == 0:
            situation = situation_maker(quote)
            play = False
        else:        
            situation = play_situation_maker(quote)
            play = True
        # situation_maker(quote)
        print("SITUATION: ", situation)
        background = get_random_video_segment()
        print("BACKGROUND: ", background)
        create_introspective_video_type(background, situation, play, "final_video.mp4")
    else: # Regular video
        print("DESCRIPTION: ", caption)    
        audio_data = get_ttl(f"{philosopher}. {quote}", "output.mp3")
        print("AUDIO MADE")     
        create_background(get_audio_length("output.mp3"), philosopher)
        crop_to_aspect_ratio("output_video_uncropped.mp4", 'output_video.mp4')
        overlay_text("output_video.mp4", "output.mp3", quote, philosopher, "final_video.mp4")
    video_url = upload_to_s3("final_video.mp4", S3_BUCKET_NAME, S3_REGION)
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
    
    cleanup_files(files_to_delete)
    main()

schedule.every(2).hours.do(run_main)

if __name__ == "__main__":
    # print("Scheduler is running. The script will execute once per hour.")
    run_main()  # Run immediately at the start
    while True:
        schedule.run_pending()
        time.sleep(1) 
