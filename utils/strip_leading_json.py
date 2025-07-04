import re

def strip_leading_json(text):
    # Remove leading JSON object if present
    match = re.match(r'^\s*\{.*?\}\s*', text)
    if match:
        return text[match.end():].lstrip()
    return text