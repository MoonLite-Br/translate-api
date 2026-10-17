import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from deep_translator import GoogleTranslator, MyMemoryTranslator

app = FastAPI(title="EN-VI Translate API")

class Body(BaseModel):
    text: str
    direction: str = "en-vi"  # en-vi | vi-en

@app.get("/")
def root():
    return {"ok": True, "docs": "/docs", "endpoints": ["/translate", "/health"]}

@app.get("/health")
def health():
    return {"status": "ok"}

def _langs(direction: str):
    if direction == "en-vi":
        return "en", "vi"
    return "vi", "en"

def translate_with_fallback(text: str, src: str, tgt: str):
    errors = []

    # 1) Google (retry nhẹ)
    for attempt in range(3):
        try:
            result = GoogleTranslator(source=src, target=tgt).translate(text)
            if result:
                return result, "google"
        except Exception as e:
            errors.append(f"google[{attempt}]: {e}")
            time.sleep(1.2 * (attempt + 1))

    # 2) MyMemory fallback
    try:
        result = MyMemoryTranslator(source=src, target=tgt).translate(text)
        if result:
            return result, "mymemory"
    except Exception as e:
        errors.append(f"mymemory: {e}")

    raise RuntimeError(" | ".join(errors[-3:]))

@app.post("/translate")
def translate(body: Body):
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(400, "text rỗng")

    direction = body.direction.strip().lower()
    if direction not in ("en-vi", "vi-en"):
        raise HTTPException(400, "direction phải là en-vi hoặc vi-en")

    # tránh spam quá nhanh từ cùng instance
    time.sleep(0.4)

    src, tgt = _langs(direction)
    try:
        result, engine = translate_with_fallback(text, src, tgt)
        return {
            "text": text,
            "direction": direction,
            "result": result,
            "engine": engine,
        }
    except Exception as e:
        raise HTTPException(503, f"Lỗi dịch (thử lại sau vài giây): {e}")
