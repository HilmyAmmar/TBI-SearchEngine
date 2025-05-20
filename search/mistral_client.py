import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()
client = InferenceClient(
    provider="hf-inference",
    api_key=(os.getenv("API_KEY")),
)
