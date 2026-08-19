"""Tracking de archivos pendientes por diferencia de conjuntos.

Recorre recursivamente ``data/input/`` y ``data/output/`` con estructura
``YYYY/MM/DD/archivo.ext`` y devuelve los archivos aún no procesados
aplicando ``inputs − outputs``.
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

import first_bot.config as cfg
from first_bot.processable_file import (
    ProcessableFileFactory,
    ProcessableInputFile,
    ProcessableOutputFile,
)

EXTENSIONES = {".csv", ".xlsx"}


def get_unprocessed_files() -> list[ProcessableInputFile]:
    """Devuelve los archivos de entrada pendientes de procesar.

    1. Recorre recursivamente ``INPUT_PATH`` → ``set[ProcessableInputFile]``
    2. Recorre recursivamente ``OUTPUT_PATH`` → ``set[ProcessableOutputFile]``
    3. Calcula ``pendientes = inputs − outputs`` (diferencia de conjuntos)
    4. Solo considera extensiones ``.csv`` y ``.xlsx``
    """
    inputs = _scan_inputs(cfg.INPUT_PATH)
    outputs = _scan_outputs(cfg.OUTPUT_PATH)

    pendientes = inputs - outputs

    logger.debug(
        f"Tracking: {len(inputs)} inputs, {len(outputs)} outputs, "
        f"{len(pendientes)} pendientes"
    )

    return sorted(pendientes, key=lambda f: (f.date, f.path_dir))


def _scan_inputs(base_dir: Path) -> set[ProcessableInputFile]:
    """Recorre recursivamente el directorio de entrada."""
    result: set[ProcessableInputFile] = set()
    if not base_dir.exists():
        return result

    for path in base_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in EXTENSIONES:
            try:
                result.add(ProcessableFileFactory.create_input(path, base_dir))
            except ValueError as e:
                logger.warning(f"Archivo ignorado (ruta inválida): {path} — {e}")
    return result


def _scan_outputs(base_dir: Path) -> set[ProcessableOutputFile]:
    """Recorre recursivamente el directorio de salida."""
    result: set[ProcessableOutputFile] = set()
    if not base_dir.exists():
        return result

    for path in base_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in EXTENSIONES:
            try:
                result.add(ProcessableFileFactory.create_output(path, base_dir))
            except ValueError as e:
                logger.warning(f"Archivo ignorado (ruta inválida): {path} — {e}")
    return result
