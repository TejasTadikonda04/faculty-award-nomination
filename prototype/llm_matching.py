import os
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

script_dir = Path(__file__).parent
project_root = script_dir.parent

# Read award text
award_file = project_root / "data" / "output" / "5.02_Research Excellence.txt"
with open(award_file, "r", encoding="utf-8") as f:
    award_text = f.read()

# Read CV text
cv_text_file = project_root / "data" / "output" / "cv_text.txt"
with open(cv_text_file, "r", encoding="utf-8") as f:
    cv_text = f.read()

# Read prompt template 
prompt_file = script_dir / "prompts" / "award_to_cvs_prompt.md"
with open(prompt_file, "r", encoding="utf-8") as f:
    prompt_template = f.read().strip()

# Replace variables in prompt template
prompt = prompt_template.replace("{AWARD_TEXT}", award_text).replace("{CV_TEXT}", cv_text)

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
