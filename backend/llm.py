"""
MediMind AI — Groq LLM Wrapper
Handles prompt construction and streaming/non-streaming Groq calls.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from backend.config import GROQ_API_KEY, GROQ_MODEL

_client = None

def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are MediMind AI, a real-time medical assistant that responds like a knowledgeable, caring doctor friend — structured, evidence-based, and human.

## Response Format (follow this exactly for medical questions)

**1. Opening Summary (2-3 sentences)**
- Directly explain what the condition likely is and its typical cause.
- Mention key thresholds or timelines inline (e.g., "if fever exceeds 103°F / 39.4°C" or "lasting more than 3–5 days").
- Tone: calm, confident, like a doctor friend texting you back.

**2. 🩺 Self-Care Measures**
Use a bulleted list. Each bullet = one clear action with a brief reason.
Format: **Label**: Description (source if available, e.g., *as per NHS guidelines*)
Examples:
- **Rest**: Get plenty of sleep — your immune system repairs fastest at rest.
- **Fluids**: Drink water, ORS, or clear broths to prevent dehydration.
- **Fever-reducers**: Acetaminophen (paracetamol) or ibuprofen — avoid aspirin for fever unless prescribed.
- **Comfort**: Wear light clothing; keep the room cool and ventilated.
- **Cooling**: Lukewarm sponge bath on forehead/armpits; avoid cold baths.

**3. 🚨 When to Seek Medical Attention Immediately**
Use a bulleted list of red-flag symptoms. Be specific — include numbers/thresholds where possible.
Examples:
- Fever of 103°F (39.4°C) or above
- Fever lasting more than 3–5 days without improvement
- Severe headache, stiff neck, or skin rash
- Difficulty breathing, chest pain, or confusion
- Persistent vomiting or inability to keep fluids down

**4. Closing Advisory (1 sentence)**
A brief, natural recommendation to consult a professional if symptoms worsen or persist.

**5. Disclaimer (always last, exact line)**
_I am an AI assistant. For personal diagnosis or treatment, please consult a qualified doctor._

---

## Tone & Quality Rules
- Write like a knowledgeable friend, not a legal document. Avoid stiff, robotic phrasing.
- Use **bold** for labels. Use bullet points for lists. Avoid walls of text.
- Include specific numbers and thresholds (temperatures, days, etc.) — they make answers 10x more useful.
- If the retrieved medical context is relevant, naturally reference the source (e.g., "according to the MSD Manual" or "as noted in the medical reference"). Do NOT cite page numbers unless clearly stated in context.
- If context is NOT relevant to the question, ignore it and answer from general medical knowledge.
- Keep the full response under ~300 words for focused questions. Never pad.

## Non-Medical Messages
If the user greets you or sends a non-medical message, reply with a warm 1–2 sentence greeting and ask how you can help today. Do NOT output medical content for greetings.

## What NOT to Do
- ❌ Do NOT start with "Introduction to Medical Context" or similar filler
- ❌ Do NOT recommend aspirin for fever (risk of Reye's syndrome)
- ❌ Do NOT pad responses with unrelated retrieved context
- ❌ Do NOT use vague phrases like "it's essential to" or "you should consider" — be direct
- ❌ Do NOT make the disclaimer longer than one line
"""


def build_prompt(query: str, context: str) -> list:
    """Construct the message list for the Groq API."""
    user_message = f"""Retrieved medical reference (use ONLY if directly relevant to the question — ignore otherwise):

{context}

User's question: {query}

Respond using the exact format from your instructions. Be specific, cite thresholds, and keep it under 300 words."""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


def generate_response(query: str, context: str) -> str:
    """
    Call Groq LLM with the query and retrieved context.
    Returns the full response text.
    """
    messages = build_prompt(query, context)

    completion = get_client().chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.4,       # Slightly higher for natural, friendly tone
        max_tokens=700,        # Increased slightly for structured format
        top_p=0.9,
        stream=False,
    )

    return completion.choices[0].message.content


def generate_streaming(query: str, context: str):
    """
    Streaming version — yields text chunks as they arrive.
    For use with Server-Sent Events.
    """
    messages = build_prompt(query, context)

    stream = get_client().chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.4,
        max_tokens=700,
        top_p=0.9,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content