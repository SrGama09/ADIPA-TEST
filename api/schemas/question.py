from pydantic import BaseModel
from typing import Optional


class Alternativa(BaseModel):
    """
    Description: Single answer alternative for a question.

    Args:
        letra: Letter label (A, B, C, etc.)
        texto: Alternative text content

    Returns:
    """

    letra: str
    texto: str


class Pregunta(BaseModel):
    """
    Description: Single detected question with its alternatives.

    Args:
        numero: Sequential question number
        enunciado: Question statement text
        tipo: Question type — seleccion_multiple | verdadero_falso | desarrollo | emparejamiento
        alternativas: List of answer alternatives (empty for verdadero_falso and desarrollo)
        respuesta_correcta: Correct answer if present in the document, None otherwise

    Returns:
    """

    numero: int
    enunciado: str
    tipo: str
    alternativas: list[Alternativa]
    respuesta_correcta: Optional[str]


class ExtractionResult(BaseModel):
    """
    Description: Full extraction result containing all detected questions.

    Args:
        total_preguntas: Total number of questions detected
        preguntas: List of detected questions

    Returns:
    """

    total_preguntas: int
    preguntas: list[Pregunta]
