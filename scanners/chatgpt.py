import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def scan_chatgpt(keyword):
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": keyword}]
    )
    return {"text": resp.choices[0].message.content}

