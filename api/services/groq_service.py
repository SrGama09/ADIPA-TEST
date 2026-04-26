import json
import os
import re

from openai import OpenAI

from schemas.question import ExtractionResult

_SYSTEM_PROMPT = (
    "Eres un extractor de preguntas académicas. Analiza el texto proporcionado "
    "y devuelve ÚNICAMENTE un JSON válido con este esquema exacto:\n"
    '{"total_preguntas": N, "preguntas": [{"numero": int, "enunciado": str, '
    '"tipo": "seleccion_multiple" | "verdadero_falso" | "desarrollo" | "emparejamiento", '
    '"alternativas": [{"letra": str, "texto": str}], "respuesta_correcta": str | null}]}\n'
    "No incluyas texto adicional, markdown ni bloques de código. "
    'Si no hay preguntas, devuelve: {"total_preguntas": 0, "preguntas": []}.'
)

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqConfigError(RuntimeError):
    """Raised when the required Groq configuration is missing or invalid."""


def extract_questions(text: str) -> ExtractionResult:
    """
    Description: Send extracted document text to Groq and return structured questions.

    Args:
        text: Plain text extracted from the uploaded document

    Returns:
        ExtractionResult with all detected questions and their alternatives
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise GroqConfigError("GROQ_API_KEY no está configurada en el servidor")

    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    client = OpenAI(api_key=api_key, base_url=_GROQ_BASE_URL)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    json_str = _parse_json(raw)
    data = json.loads(json_str)
    return ExtractionResult(**data)


def _parse_json(text: str) -> str:
    """
    Description: Extract a JSON object from a string that may contain surrounding text or fences.

    Args:
        text: Raw string from Groq that may include extra prose or ```json fences

    Returns:
        JSON string ready for json.loads()
    """
    if text is None:
        raise ValueError("Empty response from Groq")

    fence = _FENCE_RE.search(text)
    candidate = fence.group(1) if fence else text

    match = _OBJECT_RE.search(candidate)
    if not match:
        raise ValueError("No JSON object found in Groq response")
    return match.group()