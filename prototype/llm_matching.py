import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

with open(os.path.join(os.path.dirname(__file__), "prompts"), "r") as f:
    prompt = f.read()

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "model": "qwen/qwen3-coder:free",
        "messages": [{"role": "user", "content": prompt}]
    }
)

data = response.json()
if "choices" in data:
    print(data["choices"][0]["message"]["content"])
else:
    print("Error:", data)
