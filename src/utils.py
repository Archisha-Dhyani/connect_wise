# src/utils.py
import re

def clean_text(s: str) -> str:
    if s is None:
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s,]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def text_to_tokens(s: str):
    s = clean_text(s)
    # simple tokenization — split on whitespace and commas
    tokens = []
    for part in s.split(","):
        part = part.strip()
        if part:
            tokens.extend(part.split())
    return tokens
