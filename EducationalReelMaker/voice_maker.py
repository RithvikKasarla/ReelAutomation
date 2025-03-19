import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

def get_ttl(text, voice_id, model="ar-diff-50k"):
    print("Generating text-to-speech audio file...")
    response = requests.request(
    method="POST",
    url="https://api.neets.ai/v1/tts",
    headers={
        "Content-Type": "application/json",
        "X-API-Key": os.getenv("NEETS_API_KEY")
    },
    json={
        "text": text, 
        "voice_id": voice_id,
        "params": {
        "model": model
        }
    }
    )

    return response.content
