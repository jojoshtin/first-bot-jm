import tempfile
from pathlib import Path

import pandas as pd
import pytest

from first_bot.orchestrator import Orchestrator


@pytest.fixture
def orch_env():
    with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
        import first_bot.config as cfg
        old_input, old_output = cfg.INPUT_PATH, cfg.OUTPUT_PATH
        cfg.INPUT_PATH = Path(input_dir)
        cfg.OUTPUT_PATH = Path(output_dir)
        yield Path(input_dir), Path(output_dir)
        cfg.INPUT_PATH = old_input
        cfg.OUTPUT_PATH = old_output


def _crear_csv_valido(directorio: Path, nombre: str = "valido.csv") -> Path:
    directorio.mkdir(parents=True, exist_ok=True)
    path = directorio / nombre
    df = pd.DataFrame(
        [
            {
                "First Name": "Juan",
                "Last Name": "Pérez",
                "Company Name": "TechCorp",
                "Role in Company": "Developer",
                "Address": "Calle 123",
                "Email": "juan@example.com",
                "Phone Number": "+1-555-1234",
                "tipo_solicitud": "soporte",
                "fecha": "2024-06-15",
                "prioridad": "alta",
                "identificador": "SOL-001",
                "descripcion": "Problema con el sistema",
                "estado": "pendiente",
            }
        ]
    )
    df.to_csv(path, index=False)
    return path


def test_orchestrator_sin_archivos(orch_env):
    orch = Orchestrator()
    orch.run()


def test_orchestrator_procesa_csv_valido(orch_env):
    input_dir, output_dir = orch_env
    _crear_csv_valido(input_dir / "2028" / "01" / "15")

    orch = Orchestrator()
    orch.run()

    output_file = output_dir / "2028" / "01" / "15" / "valido.csv"
    assert output_file.exists()


def test_orchestrator_no_reprocesa(orch_env):
    input_dir, output_dir = orch_env
    _crear_csv_valido(input_dir / "2028" / "01" / "15")

    orch = Orchestrator()
    orch.run()

    output_file = output_dir / "2028" / "01" / "15" / "valido.csv"
    assert output_file.exists()
    mtime_before = output_file.stat().st_mtime

    # Segunda corrida: ya existe en output con la misma ruta relativa, no reprocesar
    orch.run()

    mtime_after = output_file.stat().st_mtime
    assert mtime_after == mtime_before
