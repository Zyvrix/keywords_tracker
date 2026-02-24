from config.settings import BRAND_NAME, BRAND_VARIANTS

def is_brand_mentioned(text, brand=BRAND_NAME):
    if not text:
        return False
    text = text.lower()
    return any(v in text for v in BRAND_VARIANTS)
