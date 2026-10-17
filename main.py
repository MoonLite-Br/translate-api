from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from deep_translator import GoogleTranslator

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

@app.post("/translate")
def translate(body: Body):
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(400, "text rỗng")
    direction = body.direction.strip().lower()
    if direction not in ("en-vi", "vi-en"):
        raise HTTPException(400, "direction phải là en-vi hoặc vi-en")
    try:
        if direction == "en-vi":
            result = GoogleTranslator(source="en", target="vi").translate(text)
        else:
            result = GoogleTranslator(source="vi", target="en").translate(text)
        return {"text": text, "direction": direction, "result": result, "engine": "google"}
    except Exception as e:
        raise HTTPException(500, f"Lỗi dịch: {e}")
