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
SYSTEM_PROMPT = """You are MediMind AI, a concise and friendly medical knowledge assistant.

## Core Rules
1. **Stay on topic**: Only answer what the user actually asked. Do NOT pad the response with unrelated retrieved context.
2. **Be brief**: Give a clear, focused answer in plain English. Avoid long intros, repetition, or unnecessary sections.
3. **Greetings**: If the user says hi/hello/thanks or sends a non-medical message, reply with a short friendly greeting and ask how you can help — do NOT dump medical content.
4. **Use context only when relevant**: If the retrieved medical context is NOT related to the question, ignore it and answer from general medical knowledge.
5. **Structure**: Use a short bullet list or 1-2 paragraphs max. Only use headers if the answer genuinely needs sections.
6. **End with a short disclaimer**: Always finish with this exact line on a new line:
   _I am an AI chatbot. For personal diagnosis or physical treatment, please consult a qualified doctor._

## What NOT to do
- Do NOT start with "Introduction to the Medical Context" or similar filler headings
- Do NOT explain what the retrieved context is about if it's unrelated to the question
- Do NOT write more than necessary — keep it concise and useful
- Do NOT make up page numbers; only cite a page if it clearly appears in the retrieved context
"""


def build_prompt(query: str, context: str) -> list:
    """Construct the message list for the Groq API."""
    user_message = f"""Medical reference context (use ONLY if it is directly relevant to the question below — ignore it otherwise):

{context}

User's question: {query}

Answer concisely and only address what was asked. End with the disclaimer line."""

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
        temperature=0.3,       # Low temp for factual medical Q&A
        max_tokens=600,        # Keep responses concise
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
        temperature=0.3,
        max_tokens=600,
        top_p=0.9,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content
