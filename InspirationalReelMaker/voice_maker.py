from elevenlabs import ElevenLabs, save
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

VOICE_ID = "7gTjb6IKV9vMxWqcKfRW"

def get_ttl(text,output_file, voice_id=VOICE_ID):
    client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    
    audio = client.text_to_speech.convert(
        voice_id=VOICE_ID,
        output_format="mp3_44100_128",
        text=text,
        model_id="eleven_multilingual_v2",
    )
    save(audio, output_file)
    # with open(output_file, "wb") as f:
    #     f.write(response)
    #     print(f"Audio saved as {output_file}")
