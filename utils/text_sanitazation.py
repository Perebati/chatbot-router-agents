import re

SCRIPT_TAG = re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.I | re.S)
STYLE_TAG = re.compile(r"<\s*style[^>]*>.*?<\s*/\s*style\s*>", re.I | re.S)
HTML_TAG = re.compile(r"<[^>]+>")
DANGEROUS_PATTERNS = [
    re.compile(r"(?i)ignore previous instructions"),
    re.compile(r"(?i)system prompt"),
    re.compile(r"(?i)jailbreak"),
]

def sanitize_text(text: str, max_len: int = 4000) -> str:
    text = text[:max_len]
    text = SCRIPT_TAG.sub("", text)
    text = STYLE_TAG.sub("", text)
    text = HTML_TAG.sub("", text)
    for pat in DANGEROUS_PATTERNS:
        text = pat.sub("[blocked]", text)
    return text.strip()