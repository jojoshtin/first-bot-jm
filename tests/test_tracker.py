"""Tests exhaustivos para el tracker con estructura de fechas YYYY/MM/DD/ y
diferencia de conjuntos.

Verifica:
1. Caso base: directorio vacío → []
2. Inputs pendientes sin ningún archivo en output → todos devueltos como ProcessableInputFile
3. Archivo ya procesado (existe en output con la misma ruta relativa) → omitido
4. Extensiones soportadas (.csv, .xlsx, mayúsculas .CSV, .XLSX)
5. Extensiones ignoradas (.txt, .png, .pdf, .xls, .json)
6. Archivos huérfanos en output (no están en input) no rompen la lógica
7. Directorio base no existente manejado de forma segura
8. Múltiples fechas ordenadas cronológicamente y luego alfabéticamente
9. Archivos fuera de la estructura de fechas ignorados con advertencia
10. Verificación estricta del ejemplo dado en Asignacion.md
"""

import tempfile
from pathlib import Path

import pytest

from first_bot.tracker import get_unprocessed_files
from first_bot.processable_file import ProcessableInputFile


@pytest.fixture
def tracker_env():
    """Crea directorios temporales input/output y los inyecta en config."""
    with tempfile.TemporaryDirectory() as input_dir, \
         tempfile.TemporaryDirectory() as output_dir:
        import first_bot.config as cfg
        old_input, old_output = cfg.INPUT_PATH, cfg.OUTPUT_PATH
        cfg.INPUT_PATH = Path(input_dir)
        cfg.OUTPUT_PATH = Path(output_dir)
        yield Path(input_dir), Path(output_dir)
        cfg.INPUT_PATH = old_input
        cfg.OUTPUT_PATH = old_output


def _crear_archivo(base: Path, rel_path: str) -> Path:
    """Helper: crea un archivo vacío con la ruta relativa dada."""
    full = base / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.touch()
    return full


# ==============================================================================
# Tests Principales
# ==============================================================================

def test_sin_archivos_input(tracker_env):
    pendientes = get_unprocessed_files()
    assert pendientes == []


def test_archivos_pendientes_sin_output(tracker_env):
    input_dir, _ = tracker_env
    _crear_archivo(input_dir, "2028/01/15/a.csv")
    _crear_archivo(input_dir, "2028/01/15/b.xlsx")

    pendientes = get_unprocessed_files()
    assert len(pendientes) == 2
    assert all(isinstance(p, ProcessableInputFile) for p in pendientes)
    assert {p.path_dir for p in pendientes} == {
        "2028/01/15/a.csv",
        "2028/01/15/b.xlsx",
    }


def test_archivo_ya_procesado_se_omite(tracker_env):
    input_dir, output_dir = tracker_env
    _crear_archivo(input_dir, "2028/01/15/data.csv")
    _crear_archivo(input_dir, "2028/01/15/other.xlsx")
    # El output tiene la MISMA ruta relativa que el input
    _crear_archivo(output_dir, "2028/01/15/data.csv")

    pendientes = get_unprocessed_files()
    assert len(pendientes) == 1
    assert pendientes[0].path_dir == "2028/01/15/other.xlsx"
    assert isinstance(pendientes[0], ProcessableInputFile)


def test_ejemplo_consigna_completo(tracker_env):
    """Prueba la estructura exacta descrita en Asignacion.md:
    data/input/
      2028/01/15/
        solicitudes_a.csv
        pedidos_b.xlsx
      2028/01/16/
        reclamos_c.csv

    data/output/
      2028/01/15/
        solicitudes_a.csv
        pedidos_b.xlsx
      2028/01/16/
        (vacío → reclamos_c.csv está pendiente)
    """
    input_dir, output_dir = tracker_env

    _crear_archivo(input_dir, "2028/01/15/solicitudes_a.csv")
    _crear_archivo(input_dir, "2028/01/15/pedidos_b.xlsx")
    _crear_archivo(input_dir, "2028/01/16/reclamos_c.csv")

    _crear_archivo(output_dir, "2028/01/15/solicitudes_a.csv")
    _crear_archivo(output_dir, "2028/01/15/pedidos_b.xlsx")

    pendientes = get_unprocessed_files()
    assert len(pendientes) == 1
    assert pendientes[0].path_dir == "2028/01/16/reclamos_c.csv"
    assert pendientes[0].year == 2028
    assert pendientes[0].month == 1
    assert pendientes[0].day == 16


def test_ignora_extensiones_no_soportadas(tracker_env):
    """Solo debe considerar .csv y .xlsx (no .txt, .png, .pdf, .xls, .json)."""
    input_dir, _ = tracker_env
    _crear_archivo(input_dir, "2028/01/15/nota.txt")
    _crear_archivo(input_dir, "2028/01/15/imagen.png")
    _crear_archivo(input_dir, "2028/01/15/doc.pdf")
    _crear_archivo(input_dir, "2028/01/15/old.xls")
    _crear_archivo(input_dir, "2028/01/15/data.json")
    _crear_archivo(input_dir, "2028/01/15/valido.csv")
    _crear_archivo(input_dir, "2028/01/15/valido.xlsx")

    pendientes = get_unprocessed_files()
    assert len(pendientes) == 2
    paths = {p.path_dir for p in pendientes}
    assert paths == {"2028/01/15/valido.csv", "2028/01/15/valido.xlsx"}


def test_extensiones_mayusculas(tracker_env):
    """Debe reconocer .CSV y .XLSX en mayúsculas."""
    input_dir, _ = tracker_env
    _crear_archivo(input_dir, "2028/01/15/datos.CSV")
    _crear_archivo(input_dir, "2028/01/15/planilla.XLSX")

    pendientes = get_unprocessed_files()
    assert len(pendientes) == 2


def test_archivos_huerfanos_en_output(tracker_env):
    """Archivos en output que no existen en input no alteran el resultado."""
    input_dir, output_dir = tracker_env
    _crear_archivo(input_dir, "2028/01/15/a.csv")
    _crear_archivo(output_dir, "2028/01/15/fantasma.csv")

    pendientes = get_unprocessed_files()
    assert len(pendientes) == 1
    assert pendientes[0].path_dir == "2028/01/15/a.csv"


def test_todos_procesados(tracker_env):
    input_dir, output_dir = tracker_env
    _crear_archivo(input_dir, "2028/01/15/a.csv")
    _crear_archivo(output_dir, "2028/01/15/a.csv")

    pendientes = get_unprocessed_files()
    assert pendientes == []


def test_ordenamiento_cronologico_y_alfabetico(tracker_env):
    input_dir, _ = tracker_env
    _crear_archivo(input_dir, "2028/03/01/a.csv")
    _crear_archivo(input_dir, "2028/01/15/z.csv")
    _crear_archivo(input_dir, "2028/01/15/a.csv")
    _crear_archivo(input_dir, "2028/02/10/m.xlsx")

    pendientes = get_unprocessed_files()
    paths = [p.path_dir for p in pendientes]
    assert paths == [
        "2028/01/15/a.csv",
        "2028/01/15/z.csv",
        "2028/02/10/m.xlsx",
        "2028/03/01/a.csv",
    ]


def test_directorio_output_no_existe(tracker_env):
    """Si output_dir no existe físicamente en el disco, devuelve todos los inputs."""
    input_dir, output_dir = tracker_env
    # Eliminar directorio output
    import shutil
    shutil.rmtree(output_dir)

    _crear_archivo(input_dir, "2028/01/15/a.csv")

    pendientes = get_unprocessed_files()
    assert len(pendientes) == 1
    assert pendientes[0].path_dir == "2028/01/15/a.csv"


def test_directorio_input_no_existe(tracker_env):
    """Si input_dir no existe físicamente, devuelve lista vacía sin error."""
    input_dir, _ = tracker_env
    import shutil
    shutil.rmtree(input_dir)

    pendientes = get_unprocessed_files()
    assert pendientes == []


def test_ignora_archivos_fuera_de_estructura_fecha(tracker_env):
    input_dir, _ = tracker_env
    _crear_archivo(input_dir, "solicitudes_raiz.csv")
    _crear_archivo(input_dir, "2028/incompleto.csv")
    _crear_archivo(input_dir, "2028/01/15/correcto.csv")

    pendientes = get_unprocessed_files()
    assert len(pendientes) == 1
    assert pendientes[0].path_dir == "2028/01/15/correcto.csv"
