from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI(title="MLOps")

# 1. Define how a 'Question' looks (The Schema)
class Question(BaseModel):
    prompt: str
    max_tokens: int = 128

# 2. This is the address for the 'Model' lead's container
# We use 'model-service' because that's what we'll name the container later
MODEL_SERVER_URL = "http://ai-model:8080/completion"

@app.get("/")
def health_check():
    """Tells you if the backend is alive."""
    return {"status": "Backend is running", "target": "Qwen-5.0"}

@app.post("/ask")
async def ask_ai(user_query: Question):
    """
    Receives a prompt and forwards it to the llama.cpp server.
    """
    # The payload format required by llama.cpp
    payload = {
        "prompt": user_query.prompt,
        "n_predict": user_query.max_tokens
    }

    try:
        # Async client sends the request without blocking your app
        async with httpx.AsyncClient() as client:
            response = await client.post(MODEL_SERVER_URL, json=payload, timeout=60.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        # If the other container isn't running yet, this will catch it
        raise HTTPException(
            status_code=503, 
            detail=f"Model server unreachable. Is the other container running? Error: {str(e)}"
        )