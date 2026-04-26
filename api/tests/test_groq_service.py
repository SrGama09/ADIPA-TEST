import json
from unittest.mock import MagicMock, patch

import pytest

from services.groq_service import (
    GroqConfigError,
    _parse_json,
    extract_questions,
)


def test_parse_json_clean():
    raw = '{"total_preguntas": 1, "preguntas": []}'
    assert json.loads(_parse_json(raw)) == {"total_preguntas": 1, "preguntas": []}


def test_parse_json_with_extra_text():
    raw = 'Aquí está el resultado:\n{"total_preguntas": 0, "preguntas": []}\nListo.'
    result = json.loads(_parse_json(raw))
    assert result["total_preguntas"] == 0


def test_parse_json_with_markdown_fence():
    raw = '```json\n{"total_preguntas": 2, "preguntas": []}\n```'
    result = json.loads(_parse_json(raw))
    assert result["total_preguntas"] == 2


def test_parse_json_with_plain_fence():
    raw = '```\n{"total_preguntas": 3, "preguntas": []}\n```'
    result = json.loads(_parse_json(raw))
    assert result["total_preguntas"] == 3


def test_parse_json_no_object_raises():
    with pytest.raises(ValueError):
        _parse_json("Sin JSON aquí")


def test_extract_questions_returns_extraction_result(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    groq_response = json.dumps({
        "total_preguntas": 1,
        "preguntas": [
            {
                "numero": 1,
                "enunciado": "¿Cuál es la capital?",
                "tipo": "seleccion_multiple",
                "alternativas": [
                    {"letra": "A", "texto": "Madrid"},
                    {"letra": "B", "texto": "Barcelona"},
                ],
                "respuesta_correcta": "A",
            }
        ],
    })

    mock_message = MagicMock()
    mock_message.content = groq_response
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_completion

    with patch("services.groq_service.OpenAI", return_value=mock_client):
        result = extract_questions("texto de prueba")

    assert result.total_preguntas == 1
    assert result.preguntas[0].enunciado == "¿Cuál es la capital?"
    assert result.preguntas[0].alternativas[0].letra == "A"


def test_extract_questions_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(GroqConfigError):
        extract_questions("cualquier texto")


def test_extract_questions_blank_api_key_raises(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "   ")
    with pytest.raises(GroqConfigError):
        extract_questions("cualquier texto")