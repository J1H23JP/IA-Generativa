import re

def clean(text: str) -> str:
    text = text.replace("\x00", "").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    # PROTEGER LAS TABLAS MARKDOWN DE AZURE
    # text = re.sub(r"^[-=_*]{3,}\s*$", "", text, flags=re.MULTILINE)
    
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(lines).strip()

def clean_pages(pages: list[dict]) -> list[dict]:
    cleaned = []
    for page in pages:
        clean_text = clean(page["text"])
        if len(clean_text) > 50:
            cleaned.append({**page, "text": clean_text})
    return cleaned