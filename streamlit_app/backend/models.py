# models.py
import requests
import base64
from PIL import Image
import io

# ========================
# CONFIGURATION
# ========================
LLAMA_API_KEY = "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"
MISTRAL_API_KEY = "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"

LLAMA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MISTRAL_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# ========================
# 1. LLaMA 3.3 - Chat Only
# ========================
def chat_with_llama(prompt: str, history=None, stream=False):
    """
    Sends a text-only prompt to LLaMA 3.3 (70B) and returns response.
    """
    messages = []
    if history:
        for user_msg, assistant_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})
    
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {LLAMA_API_KEY}",
        "Accept": "text/event-stream" if stream else "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta/llama-3.3-70b-instruct",
        "messages": messages,
        "temperature": 0.2,
        "top_p": 0.7,
        "max_tokens": 1024,
        "stream": stream
    }

    response = requests.post(LLAMA_URL, headers=headers, json=payload)

    if stream:
        def stream_generator():
            for line in response.iter_lines():
                if line and line.decode("utf-8").startswith("data: "):
                    yield line.decode("utf-8")[6:]
        return stream_generator()

    return response.json()["choices"][0]["message"]["content"]

# ========================
# 2. Mistral - Image + Text
# ========================
def encode_image_to_base64(image: Image.Image) -> str:
    """
    Converts a PIL Image to a base64-encoded string.
    """
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def image_to_text_mistral(image: Image.Image, prompt: str = "Describe this image.", stream=False):
    """
    Sends an image and a prompt to Mistral Medium 3 Instruct via NIM API and returns caption/reasoning.
    """
    base64_image = encode_image_to_base64(image)

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Accept": "text/event-stream" if stream else "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/mistral-medium-3-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }
        ],
        "temperature": 0.7,
        "top_p": 1.0,
        "max_tokens": 512,
        "stream": stream
    }

    response = requests.post(MISTRAL_URL, headers=headers, json=payload)

    if stream:
        def stream_generator():
            for line in response.iter_lines():
                if line and line.decode("utf-8").startswith("data: "):
                    yield line.decode("utf-8")[6:]
        return stream_generator()

    return response.json()["choices"][0]["message"]["content"]
