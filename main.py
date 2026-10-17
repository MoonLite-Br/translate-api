import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import MarianMTModel, MarianTokenizer
import torch

app = FastAPI(title="EN-VI Translate API (CPU)")

_models = {}

def get_model(direction: str):
    if direction not in _models:
        name = "Helsinki-NLP/opus-mt-en-vi" if direction == "en-vi" else "Helsinki-NLP/opus-mt-vi-en"
        tok = MarianTokenizer.from_pretrained(name)
        model = MarianMTModel.from_pretrained(name)
        model.eval()
        _models[direction] = (tok, model)
    return _models[direction]

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
        tok, model = get_model(direction)
        inputs = tok(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            out = model.generate(**inputs, max_length=512, num_beams=2)
        result = tok.decode(out[0], skip_special_tokens=True)
        return {"text": text, "direction": direction, "result": result}
    except Exception as e:
        raise HTTPException(500, f"Lỗi dịch: {e}")
