"""Modelos de archivos procesables con tracking por fechas.

Patrones de diseño aplicados:
- Value Object: dataclasses frozen inmutables, igualdad por path_dir.
- Template Method: la clase base _ProcessableFile define la lógica de
  parsing de ruta y comparación; las subclases solo aportan identidad de tipo.
- Factory Method: ProcessableFileFactory centraliza la creación validada
  de ProcessableInputFile y ProcessableOutputFile.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────────────
# Patrón: regex reutilizable para extraer YYYY/MM/DD de una ruta relativa
# ──────────────────────────────────────────────────────────────────────
_DATE_PATH_RE = re.compile(r"^(\d{4})[/\\](\d{1,2})[/\\](\d{1,2})[/\\]")


# ──────────────────────────────────────────────────────────────────────
# Template Method  – clase base con lógica compartida
# ──────────────────────────────────────────────────────────────────────
@dataclass(frozen=True, eq=False)
class _ProcessableFile:
    """Clase base inmutable para archivos procesables.

    La igualdad y el hash se definen exclusivamente por ``path_dir``,
    lo que permite comparar un input con un output directamente y usar
    diferencia de conjuntos (``inputs - outputs``).

    Se usa ``eq=False`` en el decorador ``@dataclass`` para que el
    ``__eq__`` y ``__hash__`` personalizados no sean sobreescritos
    por los auto-generados (que comparan todos los campos y el tipo).
    """

    year: int
    month: int
    day: int
    date: date
    path_dir: str
    full_path: Path

    # ── Value Object: __eq__ y __hash__ por path_dir ──────────────────

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _ProcessableFile):
            return NotImplemented
        return self.path_dir == other.path_dir

    def __hash__(self) -> int:
        return hash(self.path_dir)

    # ── Template Method: construcción desde ruta ──────────────────────

    @classmethod
    def _from_path(cls, path: Path, base_dir: Path) -> "_ProcessableFile":
        """Construye la instancia a partir de una ruta absoluta y su base.

        Extrae year/month/day de la estructura ``YYYY/MM/DD/archivo.ext``
        dentro de ``base_dir``.
        """
        rel = path.relative_to(base_dir).as_posix()  # siempre con /
        match = _DATE_PATH_RE.match(rel)
        if match is None:
            raise ValueError(
                f"La ruta '{rel}' no cumple el formato YYYY/MM/DD/archivo: "
                f"(base={base_dir})"
            )
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        try:
            parsed_date = date(year, month, day)
        except ValueError as e:
            raise ValueError(f"Fecha inválida en la ruta '{rel}': {e}") from e

        return cls(
            year=year,
            month=month,
            day=day,
            date=parsed_date,
            path_dir=rel,
            full_path=path.resolve(),
        )


# ──────────────────────────────────────────────────────────────────────
# Subclases concretas (solo identidad de tipo)
# ──────────────────────────────────────────────────────────────────────
@dataclass(frozen=True, eq=False)
class ProcessableInputFile(_ProcessableFile):
    """Archivo de entrada ubicado en ``data/input/YYYY/MM/DD/``."""
    pass


@dataclass(frozen=True, eq=False)
class ProcessableOutputFile(_ProcessableFile):
    """Archivo de salida ubicado en ``data/output/YYYY/MM/DD/``."""
    pass


# ──────────────────────────────────────────────────────────────────────
# Factory Method  – creación validada
# ──────────────────────────────────────────────────────────────────────
class ProcessableFileFactory:
    """Fábrica que crea objetos ProcessableInputFile / ProcessableOutputFile.

    Centraliza la validación de la estructura de directorios y el parsing
    de la fecha embebida en la ruta.
    """

    @staticmethod
    def create_input(path: Path, base_dir: Path) -> ProcessableInputFile:
        """Crea un ``ProcessableInputFile`` a partir de la ruta absoluta."""
        return ProcessableInputFile._from_path(path, base_dir)

    @staticmethod
    def create_output(path: Path, base_dir: Path) -> ProcessableOutputFile:
        """Crea un ``ProcessableOutputFile`` a partir de la ruta absoluta."""
        return ProcessableOutputFile._from_path(path, base_dir)
