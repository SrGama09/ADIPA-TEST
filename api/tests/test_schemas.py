from schemas.question import Alternativa, ExtractionResult, Pregunta


def test_alternativa():
    a = Alternativa(letra="A", texto="Opción A")
    assert a.letra == "A"
    assert a.texto == "Opción A"


def test_pregunta_seleccion_multiple():
    p = Pregunta(
        numero=1,
        enunciado="¿Cuál es?",
        tipo="seleccion_multiple",
        alternativas=[Alternativa(letra="A", texto="Opción A")],
        respuesta_correcta="A",
    )
    assert p.numero == 1
    assert p.respuesta_correcta == "A"


def test_pregunta_sin_respuesta_correcta():
    p = Pregunta(
        numero=2,
        enunciado="Verdadero o falso",
        tipo="verdadero_falso",
        alternativas=[],
        respuesta_correcta=None,
    )
    assert p.respuesta_correcta is None


def test_extraction_result():
    result = ExtractionResult(
        total_preguntas=1,
        preguntas=[
            Pregunta(
                numero=1,
                enunciado="¿Cuál es?",
                tipo="seleccion_multiple",
                alternativas=[Alternativa(letra="A", texto="Opción A")],
                respuesta_correcta="A",
            )
        ],
    )
    assert result.total_preguntas == 1
    assert len(result.preguntas) == 1
