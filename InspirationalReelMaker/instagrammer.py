import time
import requests
import hmac
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET")
IG_USER_ID = os.getenv("INSTAGRAM_USER_ID")

# Generate App Secret Proof
def generate_app_secret_proof(access_token, app_secret):
    return hmac.new(
        app_secret.encode("utf-8"),
        msg=access_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


# Generate app secret proof
app_secret_proof = generate_app_secret_proof(ACCESS_TOKEN, APP_SECRET)

# Step 1: Create Media Container
def create_media_container(VIDEO_URL, CAPTION):
    url = f"https://graph.instagram.com/v21.0/{IG_USER_ID}/media"
    payload = {
        "media_type": "REELS",
        "video_url": VIDEO_URL,
        "caption": CAPTION,
        "access_token": ACCESS_TOKEN,
        "appsecret_proof": app_secret_proof,
    }
    response = requests.post(url, data=payload)
    return response.json()

# Step 2: Check Media Status
def check_media_status(container_id):
    url = f"https://graph.instagram.com/v21.0/{container_id}?fields=status_code&access_token={ACCESS_TOKEN}&appsecret_proof={app_secret_proof}"
    response = requests.get(url)
    return response.json()

# Step 3: Publish Media Container
def publish_media_container(container_id):
    url = f"https://graph.instagram.com/v21.0/{IG_USER_ID}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": ACCESS_TOKEN,
        "appsecret_proof": app_secret_proof,
    }
    response = requests.post(url, data=payload)
    return response.json()

def post_reel(VIDEO_URL, CAPTION):
    # Step 1: Create Media Container
    print("Creating media container...")
    container_response = create_media_container(VIDEO_URL=VIDEO_URL, CAPTION=CAPTION)
    if "id" in container_response:
        container_id = container_response["id"]
        print(f"Media container created successfully! Container ID: {container_id}")

        # Step 2: Wait for Media Processing
        print("Waiting for media processing...")
        for _ in range(10):  # Poll for up to 5 minutes
            status_response = check_media_status(container_id)
            if status_response.get("status_code") == "FINISHED":
                print("Media is ready for publishing!")
                break
            elif status_response.get("status_code") == "ERROR":
                print("Error in media processing:", status_response)
                exit()
            else:
                print("Media is still processing. Retrying in 30 seconds...")
                time.sleep(30)
        else:
            print("Media processing timed out.")
            exit()

        # Step 3: Publish the Reel
        print("Publishing the Reel...")
        publish_response = publish_media_container(container_id)
        if "id" in publish_response:
            print(f"Reel published successfully! Reel ID: {publish_response['id']}")
        else:
            print("Failed to publish Reel:", publish_response)
    else:
        print("Failed to create media container:", container_response)
