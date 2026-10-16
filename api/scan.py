from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import base64
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/scan")
async def scan_ticket(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        encoded_string = base64.b64encode(contents).decode('utf-8')
        
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="API Key no configurada")

        prompt = """
        Eres un asistente experto en OCR y extracción de datos de tickets de supermercado.
        Tu tarea es analizar la imagen y devolver un objeto JSON estrictamente estructurado.
        El JSON debe tener exactamente estas claves:
        - "establecimiento": (string o null)
        - "fecha": (string o null) Formato YYYY-MM-DD
        - "total": (number o null)
        - "productos": (array de objetos) Cada objeto con "nombre" (string) y "precio" (number).
        Reglas: NO INVENTES DATOS. Si no es visible, null. Devuelve SOLO el JSON.
        """
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": encoded_string}}
                ]
            }]
        }
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            texto = result['candidates'][0]['content']['parts'][0]['text']
            texto = texto.strip()
            if texto.startswith("```json"):
                texto = texto[7:-3].strip()
            elif texto.startswith("```"):
                texto = texto[3:-3].strip()
            return json.loads(texto)
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))