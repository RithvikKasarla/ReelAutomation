from dotenv import load_dotenv
import os
from openai import OpenAI
import requests
from PIL import Image, ImageDraw
import numpy as np

load_dotenv()

client = OpenAI()

client.api_key = os.getenv("OPENAI_API_KEY")

def create_rounded_corner_mask(size, radius):
    """
    Creates a rounded rectangle mask for an image.

    Args:
        size (tuple): The size of the mask (width, height).
        radius (int): The radius of the rounded corners.

    Returns:
        np.array: A mask array with rounded corners.
    """
    width, height = size
    mask = Image.new("L", (width, height), 0)  # Black background
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)  # White rounded rectangle
    return np.array(mask) / 255.0

def generate_image(prompt, output_path, size="1024x1024", quality="standard"):
    """
    Generates an image using DALL·E 3, saves it to the specified path, and returns the path.
    
    Args:
        prompt (str): The text prompt for DALL·E.
        output_path (str): Path to save the generated image.
        size (str): The size of the image (e.g., "1024x1024").
        quality (str): The quality of the image ("standard" or "hd").
    
    Returns:
        str: The saved file path or None if an error occurred.
    """
    try:
        # Generate the image using the OpenAI API
        response = client.images.generate(
            model="dall-e-2",
            prompt=prompt,
            size=size,
            quality=quality,
            n=1  # Generate 1 image
        )
        image_url = response.data[0].url
        
        # Download the image from the returned URL
        image_data = requests.get(image_url).content
        
        # Save the image to the specified output path
        with open(output_path, "wb") as f:
            f.write(image_data)
        print(f"Image saved to {output_path}")
        return output_path
    except Exception as e:
        print(f"Error generating or saving image: {e}")
        return None

if __name__ == "__main__":
    prompt = "A surreal landscape with floating islands and a pink sky."
    output_path = "generated_image.png"
    generate_image(prompt, output_path)