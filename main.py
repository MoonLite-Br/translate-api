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

def translate_with_fallback(text: str, direction: str):
    errors = []

    if direction == "en-vi":
        g_src, g_tgt = "en", "vi"
        m_src, m_tgt = "en-GB", "vi-VN"
    else:
        g_src, g_tgt = "vi", "en"
        m_src, m_tgt = "vi-VN", "en-GB"

    # 1) MyMemory trước (ít bị chặn hơn từ datacenter)
    try:
        result = MyMemoryTranslator(source=m_src, target=m_tgt).translate(text)
        if result and result.strip():
            return result, "mymemory"
    except Exception as e:
        errors.append(f"mymemory: {e}")

    # 2) Google (retry)
    for attempt in range(3):
        try:
            time.sleep(1.5 * (attempt + 1))
            result = GoogleTranslator(source=g_src, target=g_tgt).translate(text)
            if result and result.strip():
                return result, "google"
        except Exception as e:
            errors.append(f"google[{attempt}]: {e}")

    raise RuntimeError(" | ".join(str(x)[:120] for x in errors[-3:]))

@app.post("/translate")
def translate(body: Body):
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(400, "text rỗng")

    direction = body.direction.strip().lower()
    if direction not in ("en-vi", "vi-en"):
        raise HTTPException(400, "direction phải là en-vi hoặc vi-en")

    try:
        result, engine = translate_with_fallback(text, direction)
        return {
            "text": text,
            "direction": direction,
            "result": result,
            "engine": engine,
        }
    except Exception as e:
        raise HTTPException(503, f"Lỗi dịch (đợi 30-60s rồi thử lại): {e}")
