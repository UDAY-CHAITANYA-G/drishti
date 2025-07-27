
import time
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

genai.configure(api_key="AIzaSyBGNE0niio33f45McUjniJqmrOmqJhpYVQ")
model = genai.GenerativeModel("gemini-1.5-pro-latest")

def analyze_crowd_behavior(prompt: str, retries=3, delay=30) -> str:
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except ResourceExhausted as e:
            print(f"[Retry {attempt+1}] Quota error: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise
