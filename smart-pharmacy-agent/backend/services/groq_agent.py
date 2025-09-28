import os
from typing import List
from dotenv import load_dotenv

try:
    # Optional: load .env if present
    load_dotenv()
except Exception:
    pass

# Lazy import (so app still runs if key missing until used)
# def _client():
#     from groq import Groq  # imported here to avoid hard dependency on import time
#     api_key = os.getenv("GROQ_API_KEY")
#     if not api_key:
#         raise RuntimeError("GROQ_API_KEY is not set. Export it or create a .env file.")
#     return Groq(api_key=api_key)

def _client():
    from groq import Groq
    # Just instantiate without passing api_key — the SDK will pick it up
    # from the GROQ_API_KEY environment variable
    return Groq()

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

SYSTEM_PROMPT = "You are a pharmacy demand forecasting assistant. Respond tersely and ONLY with requested data format."

def ask_groq(prompt: str, model: str = DEFAULT_MODEL) -> str:
    client = _client()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    # groq sdk returns pydantic-like object; access .choices[0].message.content
    return resp.choices[0].message.content

def forecast_with_groq(history: list, horizon: int = 7, drug: str = "Unknown") -> List[float]:
    # Keep last 30 points for compact prompt
    hist = history[-30:]
    prompt = f"""
    Demand history (most recent last) for {drug}: {hist}
    Forecast the next {horizon} daily quantities as a comma-separated list of numbers (no text).
    Example: 12, 13, 11, 10, 12, 9, 8
    Only return the list.
    """
    reply = ask_groq(prompt)
    try:
        values = [float(x.strip()) for x in reply.split(",")]
        if len(values) < horizon:
            # pad if model returned fewer values
            values = values + [values[-1] if values else 0.0] * (horizon - len(values))
        return values[:horizon]
    except Exception:
        return [0.0] * horizon

def explain_reorder(center_id: str, drug: str, stock: float, reorder_point: float) -> str:
    prompt = f"""
    Center {center_id}, Drug {drug}
    Current stock: {stock}, Reorder point: {reorder_point:.2f}
    In 2 sentences, explain if a reorder is needed and why. Avoid jargon.
    """
    return ask_groq(prompt)


def chat_with_groq(query: str, context: str = "") -> str:
    """
    General chat with pharmacy assistant.
    context: Optional summary of inventory/forecasts to include.
    """
    system_prompt = """You are a helpful Smart Pharmacy Inventory Agent assistant. 
    You can answer questions about inventory levels, demand forecasts, reorder suggestions, redistribution, and route optimization.
    Be concise, professional, and use simple language. If data is provided in context, reference it accurately.
    If you don't know something, say so."""
    
    full_prompt = f"{context}\n\nUser: {query}"
    
    client = _client()
    resp = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content
