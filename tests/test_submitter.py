import tempfile
from datetime import date
from pathlib import Path

import pytest

from first_bot.submitter import WebSubmitter
from first_bot.models import Persona, Solicitud


@pytest.fixture
def solicitudes():
    p = Persona(
        first_name="Test", last_name="User",
        company_name="Corp", role_in_company="Dev",
        address="St 1", email="test@example.com",
        phone_number="+1-555-0000",
    )
    return [
        Solicitud(
            persona=p,
            tipo_solicitud="soporte",
            fecha=date(2024, 1, 1),
            prioridad="alta",
            identificador="SOL-001",
            descripcion="Test",
            estado="pendiente",
        ),
        Solicitud(
            persona=p,
            tipo_solicitud="consulta",
            fecha=date(2024, 2, 1),
            prioridad="media",
            identificador="SOL-002",
            descripcion="Test 2",
            estado="pendiente",
        ),
    ]


def test_submitter_stub_retorna_resultados(solicitudes):
    submitter = WebSubmitter()
    resultados = submitter.submit(solicitudes)
    assert len(resultados) == 2
    assert all(r["resultado"] == "registrado" for r in resultados)
    assert all(r["error"] is None for r in resultados)
    assert resultados[0]["identificador"] == "SOL-001"


def test_submitter_acepta_lista_vacia():
    submitter = WebSubmitter()
    resultados = submitter.submit([])
    assert resultados == []


def test_submitter_custom_url():
    submitter = WebSubmitter(form_url="http://custom.local/form")
    assert submitter.form_url == "http://custom.local/form"
