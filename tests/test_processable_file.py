"""Tests exhaustivos para las clases ProcessableInputFile, ProcessableOutputFile y
ProcessableFileFactory.

Cubre minuciosamente la consigna de Asignacion.md:
- Atributos requeridos y sus tipos exactos (year: int, month: int, day: int, date: date, path_dir: str, full_path: Path)
- Inmutabilidad estricta (frozen dataclass)
- Igualdad cross-type (un input es igual a un output si comparten path_dir)
- Hash cross-type (mismo hash si comparten path_dir)
- Comparación contra otros tipos (str, int, None) devuelve False
- Operaciones de conjuntos (diferencia, intersección, pertenencia)
- Validación de rutas (fechas inválidas, formatos incorrectos, nombres complejos)
- Instanciación directa vs vía Factory
"""

import tempfile
from datetime import date
from pathlib import Path

import pytest

from first_bot.processable_file import (
    ProcessableFileFactory,
    ProcessableInputFile,
    ProcessableOutputFile,
    _ProcessableFile,
)


@pytest.fixture
def temp_dirs():
    """Crea directorios temporales input/output con estructura de fechas."""
    with tempfile.TemporaryDirectory() as base:
        input_dir = Path(base) / "input"
        output_dir = Path(base) / "output"

        (input_dir / "2028" / "01" / "15").mkdir(parents=True)
        (input_dir / "2028" / "01" / "16").mkdir(parents=True)
        (output_dir / "2028" / "01" / "15").mkdir(parents=True)
        (output_dir / "2028" / "01" / "16").mkdir(parents=True)

        yield input_dir, output_dir


# ==============================================================================
# 1. Verificación de atributos, tipos y comportamiento de Dataclass
# ==============================================================================

class TestAttributesAndTypes:
    def test_atributos_y_tipos_exactos(self, temp_dirs):
        input_dir, _ = temp_dirs
        archivo = input_dir / "2028" / "01" / "15" / "solicitudes_a.csv"
        archivo.touch()

        pf = ProcessableFileFactory.create_input(archivo, input_dir)

        # Verificar tipos exactos según la tabla de la consigna
        assert type(pf.year) is int
        assert pf.year == 2028

        assert type(pf.month) is int
        assert pf.month == 1  # 01 convertido a int 1

        assert type(pf.day) is int
        assert pf.day == 15

        assert type(pf.date) is date
        assert pf.date == date(2028, 1, 15)

        assert type(pf.path_dir) is str
        assert pf.path_dir == "2028/01/15/solicitudes_a.csv"

        assert isinstance(pf.full_path, Path)
        assert pf.full_path == archivo.resolve()

    def test_instanciacion_directa(self):
        """Verifica que se pueden instanciar directamente con los argumentos del constructor."""
        pf_in = ProcessableInputFile(
            year=2028,
            month=1,
            day=15,
            date=date(2028, 1, 15),
            path_dir="2028/01/15/pedidos.xlsx",
            full_path=Path("/abs/data/input/2028/01/15/pedidos.xlsx"),
        )
        pf_out = ProcessableOutputFile(
            year=2028,
            month=1,
            day=15,
            date=date(2028, 1, 15),
            path_dir="2028/01/15/pedidos.xlsx",
            full_path=Path("/abs/data/output/2028/01/15/pedidos.xlsx"),
        )

        assert pf_in.year == 2028
        assert pf_in.month == 1
        assert pf_in.day == 15
        assert pf_in.date == date(2028, 1, 15)
        assert pf_in.path_dir == "2028/01/15/pedidos.xlsx"
        assert pf_in == pf_out

    def test_inmutabilidad_frozen_dataclass(self, temp_dirs):
        input_dir, _ = temp_dirs
        archivo = input_dir / "2028" / "01" / "15" / "test.csv"
        archivo.touch()

        pf = ProcessableFileFactory.create_input(archivo, input_dir)

        with pytest.raises(AttributeError):
            pf.year = 2029
        with pytest.raises(AttributeError):
            pf.month = 2
        with pytest.raises(AttributeError):
            pf.day = 20
        with pytest.raises(AttributeError):
            pf.date = date(2029, 2, 20)
        with pytest.raises(AttributeError):
            pf.path_dir = "otra/ruta.csv"
        with pytest.raises(AttributeError):
            pf.full_path = Path("/otro/path")


# ==============================================================================
# 2. Igualdad y Hash Cross-Type (Requisito clave de la consigna)
# ==============================================================================

class TestCrossTypeEqualityAndHash:
    def test_input_igual_a_output_con_mismo_path_dir(self, temp_dirs):
        input_dir, output_dir = temp_dirs
        in_file = input_dir / "2028" / "01" / "15" / "solicitudes_a.csv"
        out_file = output_dir / "2028" / "01" / "15" / "solicitudes_a.csv"
        in_file.touch()
        out_file.touch()

        pf_in = ProcessableFileFactory.create_input(in_file, input_dir)
        pf_out = ProcessableFileFactory.create_output(out_file, output_dir)

        # Igualdad simétrica
        assert pf_in == pf_out
        assert pf_out == pf_in

        # Mismo hash
        assert hash(pf_in) == hash(pf_out)

    def test_input_desigual_si_difiere_path_dir(self, temp_dirs):
        input_dir, output_dir = temp_dirs
        in_file = input_dir / "2028" / "01" / "15" / "solicitudes_a.csv"
        out_file = output_dir / "2028" / "01" / "16" / "solicitudes_a.csv"
        in_file.touch()
        out_file.touch()

        pf_in = ProcessableFileFactory.create_input(in_file, input_dir)
        pf_out = ProcessableFileFactory.create_output(out_file, output_dir)

        assert pf_in != pf_out
        assert pf_out != pf_in

    def test_comparacion_con_otros_tipos_retorna_false(self, temp_dirs):
        input_dir, _ = temp_dirs
        archivo = input_dir / "2028" / "01" / "15" / "solicitudes_a.csv"
        archivo.touch()

        pf = ProcessableFileFactory.create_input(archivo, input_dir)

        assert pf != "2028/01/15/solicitudes_a.csv"
        assert pf != 2028
        assert pf is not None
        assert (pf == None) is False  # noqa: E711
        assert (pf == 123) is False

    def test_uso_como_clave_de_diccionario(self, temp_dirs):
        input_dir, output_dir = temp_dirs
        in_file = input_dir / "2028" / "01" / "15" / "solicitudes_a.csv"
        out_file = output_dir / "2028" / "01" / "15" / "solicitudes_a.csv"
        in_file.touch()
        out_file.touch()

        pf_in = ProcessableFileFactory.create_input(in_file, input_dir)
        pf_out = ProcessableFileFactory.create_output(out_file, output_dir)

        tabla = {pf_in: "estado_procesado"}
        # Se puede acceder usando el objeto output equivalente
        assert tabla[pf_out] == "estado_procesado"


# ==============================================================================
# 3. Operaciones de Conjuntos (Set Difference / Intersection)
# ==============================================================================

class TestSetOperations:
    def test_diferencia_de_conjuntos_ejemplo_consigna(self, temp_dirs):
        """Verifica exactamente el ejemplo de la consigna:
        Input:
          2028/01/15/solicitudes_a.csv
          2028/01/15/pedidos_b.xlsx
          2028/01/16/reclamos_c.csv
        Output:
          2028/01/15/solicitudes_a.csv
          2028/01/15/pedidos_b.xlsx
        Pendientes (inputs - outputs):
          2028/01/16/reclamos_c.csv
        """
        input_dir, output_dir = temp_dirs

        (input_dir / "2028" / "01" / "15" / "solicitudes_a.csv").touch()
        (input_dir / "2028" / "01" / "15" / "pedidos_b.xlsx").touch()
        (input_dir / "2028" / "01" / "16" / "reclamos_c.csv").touch()

        (output_dir / "2028" / "01" / "15" / "solicitudes_a.csv").touch()
        (output_dir / "2028" / "01" / "15" / "pedidos_b.xlsx").touch()

        in1 = ProcessableFileFactory.create_input(input_dir / "2028" / "01" / "15" / "solicitudes_a.csv", input_dir)
        in2 = ProcessableFileFactory.create_input(input_dir / "2028" / "01" / "15" / "pedidos_b.xlsx", input_dir)
        in3 = ProcessableFileFactory.create_input(input_dir / "2028" / "01" / "16" / "reclamos_c.csv", input_dir)

        out1 = ProcessableFileFactory.create_output(output_dir / "2028" / "01" / "15" / "solicitudes_a.csv", output_dir)
        out2 = ProcessableFileFactory.create_output(output_dir / "2028" / "01" / "15" / "pedidos_b.xlsx", output_dir)

        inputs = {in1, in2, in3}
        outputs = {out1, out2}

        pendientes = inputs - outputs

        assert len(pendientes) == 1
        elemento = pendientes.pop()
        assert elemento == in3
        assert isinstance(elemento, ProcessableInputFile)
        assert elemento.path_dir == "2028/01/16/reclamos_c.csv"

    def test_interseccion_de_conjuntos(self, temp_dirs):
        input_dir, output_dir = temp_dirs
        (input_dir / "2028" / "01" / "15" / "a.csv").touch()
        (output_dir / "2028" / "01" / "15" / "a.csv").touch()

        in1 = ProcessableFileFactory.create_input(input_dir / "2028" / "01" / "15" / "a.csv", input_dir)
        out1 = ProcessableFileFactory.create_output(output_dir / "2028" / "01" / "15" / "a.csv", output_dir)

        interseccion = {in1} & {out1}
        assert len(interseccion) == 1


# ==============================================================================
# 4. Validación de Rutas y Fechas
# ==============================================================================

class TestRouteAndDateParsing:
    def test_soporte_un_digito_mes_dia(self, temp_dirs):
        input_dir, _ = temp_dirs
        dir_path = input_dir / "2028" / "1" / "5"
        dir_path.mkdir(parents=True, exist_ok=True)
        archivo = dir_path / "datos.csv"
        archivo.touch()

        pf = ProcessableFileFactory.create_input(archivo, input_dir)
        assert pf.year == 2028
        assert pf.month == 1
        assert pf.day == 5
        assert pf.date == date(2028, 1, 5)

    def test_rechaza_fecha_calendario_invalida(self, temp_dirs):
        input_dir, _ = temp_dirs
        # 30 de febrero no existe
        dir_path = input_dir / "2028" / "02" / "30"
        dir_path.mkdir(parents=True, exist_ok=True)
        archivo = dir_path / "datos.csv"
        archivo.touch()

        with pytest.raises(ValueError, match="Fecha inválida"):
            ProcessableFileFactory.create_input(archivo, input_dir)

    def test_rechaza_mes_fuera_de_rango(self, temp_dirs):
        input_dir, _ = temp_dirs
        dir_path = input_dir / "2028" / "13" / "01"
        dir_path.mkdir(parents=True, exist_ok=True)
        archivo = dir_path / "datos.csv"
        archivo.touch()

        with pytest.raises(ValueError, match="Fecha inválida"):
            ProcessableFileFactory.create_input(archivo, input_dir)

    def test_nombre_con_multiples_puntos(self, temp_dirs):
        input_dir, _ = temp_dirs
        archivo = input_dir / "2028" / "01" / "15" / "solicitudes.v2.backup.final.csv"
        archivo.touch()

        pf = ProcessableFileFactory.create_input(archivo, input_dir)
        assert pf.path_dir == "2028/01/15/solicitudes.v2.backup.final.csv"
        assert pf.year == 2028
        assert pf.month == 1
        assert pf.day == 15
