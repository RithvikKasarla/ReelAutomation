import boto3
from botocore.exceptions import NoCredentialsError
import os
from datetime import datetime

S3_BUCKET_NAME = "educationalreeltempstorage"
S3_REGION = "us-east-1"
LOCAL_VIDEO_PATH = "final_video.mp4"

def upload_to_s3(local_file_path, bucket_name, region):
    try:
        # Initialize S3 client
        s3 = boto3.client("s3", region_name=region)
        
        # Generate a unique S3 object key with a timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        s3_file_key = f"videos/{timestamp}_{os.path.basename(local_file_path)}"
        
        # Upload file to S3
        s3.upload_file(local_file_path, bucket_name, s3_file_key)
        print(f"File uploaded successfully to {bucket_name}/{s3_file_key}")
        
        # Generate a public URL
        public_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_file_key}"
        return public_url
    except FileNotFoundError:
        print("Error: The file was not found.")
        return None
    except NoCredentialsError:
        print("Error: AWS credentials not available.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    video_url = upload_to_s3(LOCAL_VIDEO_PATH, S3_BUCKET_NAME, S3_REGION)
    if video_url:
        print("Public URL:", video_url)
    else:
        print("Failed to upload video to S3.")
