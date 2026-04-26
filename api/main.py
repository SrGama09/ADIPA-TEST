import logging
import os

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from schemas.question import ExtractionResult
from services.extractor import UnsupportedFormatError, extract_text
from services.groq_service import GroqConfigError, extract_questions

MAX_UPLOAD_BYTES = 10 * 1024 * 1024

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("adipa.api")

app = FastAPI(title="Adipa Question Extractor", version="1.0.0")

_raw_origins = os.getenv("CORS_ORIGINS", "*").strip()
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    """
    Description: Liveness probe for orchestrators and uptime checks.

    Returns:
        Static JSON payload indicating the service is reachable.
    """
    return {"status": "ok"}


@app.post("/api/extract", response_model=ExtractionResult)
async def extract(file: UploadFile = File(...)) -> ExtractionResult:
    """
    Description: Receive a document, extract its text, and return detected questions.

    Args:
        file: Uploaded file (PDF, DOCX, or XLSX)

    Returns:
        ExtractionResult with all detected questions and their alternatives
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo sin nombre")

    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="El archivo está vacío")

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el máximo de {MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
        )

    try:
        text = extract_text(content, file.filename)
    except UnsupportedFormatError:
        raise HTTPException(
            status_code=422,
            detail="Formato no soportado. Use PDF, DOCX o XLSX",
        )
    except Exception as exc:
        logger.exception("Error extrayendo texto del archivo %s", file.filename)
        raise HTTPException(
            status_code=422,
            detail=f"No se pudo leer el archivo: {exc}",
        )

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="No se pudo extraer texto del documento",
        )

    try:
        result = extract_questions(text)
    except GroqConfigError as exc:
        logger.error("Configuración inválida de Groq: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.exception("Error procesando respuesta de Groq")
        raise HTTPException(
            status_code=502,
            detail=f"Error procesando respuesta del modelo: {exc}",
        )

    if result.total_preguntas == 0:
        raise HTTPException(
            status_code=400,
            detail="No se detectaron preguntas en el documento",
        )

    return result
