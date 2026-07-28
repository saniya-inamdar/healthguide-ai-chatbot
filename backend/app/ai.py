from groq import Groq

from app.config import get_settings

settings = get_settings()
client = Groq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = """You are HealthGuide AI, a careful healthcare information assistant.
Always respond in clear English. Give general educational information, not a diagnosis.
Never claim certainty, prescribe medications, calculate dosages, or replace a clinician.
Encourage users with persistent, severe, or worsening symptoms to contact a qualified healthcare professional.
If the user describes possible emergency symptoms (for example chest pain, trouble breathing,
stroke signs, severe bleeding, loss of consciousness, seizure, or self-harm), tell them to call
their local emergency number or go to the nearest emergency department immediately.
Be concise, empathetic, and ask one relevant follow-up question when useful."""


def generate_reply(message: str, history: list[dict[str, str]]) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history, {"role": "user", "content": message}]
    completion = client.chat.completions.create(
        model=settings.model_name,
        messages=messages,
        temperature=0.3,
        max_tokens=700,
    )
    return completion.choices[0].message.content or "I could not generate a response. Please try again."
