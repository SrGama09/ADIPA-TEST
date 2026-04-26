from unittest.mock import patch

import fitz
from fastapi.testclient import TestClient

from main import app
from schemas.question import Alternativa, ExtractionResult, Pregunta
from services.groq_service import GroqConfigError

client = TestClient(app)


def _make_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    return doc.tobytes()


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_extract_success():
    mock_result = ExtractionResult(
        total_preguntas=1,
        preguntas=[
            Pregunta(
                numero=1,
                enunciado="¿Pregunta de prueba?",
                tipo="seleccion_multiple",
                alternativas=[Alternativa(letra="A", texto="Opción A")],
                respuesta_correcta="A",
            )
        ],
    )
    pdf_bytes = _make_pdf_bytes("¿Pregunta de prueba? A) Opción A")

    with patch("main.extract_questions", return_value=mock_result):
        response = client.post(
            "/api/extract",
            files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["total_preguntas"] == 1
    assert body["preguntas"][0]["enunciado"] == "¿Pregunta de prueba?"


def test_extract_unsupported_format():
    response = client.post(
        "/api/extract",
        files={"file": ("test.txt", b"data", "text/plain")},
    )
    assert response.status_code == 422
    assert "Formato no soportado" in response.json()["detail"]


def test_extract_no_questions_detected():
    pdf_bytes = _make_pdf_bytes("Texto sin preguntas")
    empty_result = ExtractionResult(total_preguntas=0, preguntas=[])

    with patch("main.extract_questions", return_value=empty_result):
        response = client.post(
            "/api/extract",
            files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        )

    assert response.status_code == 400
    assert "No se detectaron preguntas" in response.json()["detail"]


def test_extract_empty_file():
    response = client.post(
        "/api/extract",
        files={"file": ("test.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
    assert "vacío" in response.json()["detail"]


def test_extract_oversized_file():
    big = b"\x00" * (10 * 1024 * 1024 + 1)
    response = client.post(
        "/api/extract",
        files={"file": ("test.pdf", big, "application/pdf")},
    )
    assert response.status_code == 413


def test_extract_missing_api_key_returns_503():
    pdf_bytes = _make_pdf_bytes("¿Pregunta?")
    with patch("main.extract_questions", side_effect=GroqConfigError("GROQ_API_KEY no está configurada en el servidor")):
        response = client.post(
            "/api/extract",
            files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        )
    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json()["detail"]


def test_extract_model_failure_returns_502():
    pdf_bytes = _make_pdf_bytes("¿Pregunta?")
    with patch("main.extract_questions", side_effect=ValueError("bad json")):
        response = client.post(
            "/api/extract",
            files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        )
    assert response.status_code == 502
