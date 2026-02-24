
import anthropic, os
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def scan_claude(keyword):
    msg = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=500,
        messages=[{"role":"user","content":keyword}]
    )
    return {"text": msg.content[0].text}
