from pathlib import Path

from loguru import logger

import first_bot.config as cfg
from first_bot.models import COLUMNAS_ARCHIVO
from first_bot.processable_file import ProcessableInputFile
from first_bot.readers import reader_factory
from first_bot.services import classify, deduplicate, validate
from first_bot.submitter import WebSubmitter
from first_bot.tracker import get_unprocessed_files
from first_bot.reporter import (
    guardar_resultados,
    resumen_archivo,
    resumen_global,
    setup_logging,
)


class Orchestrator:
    def __init__(self):
        self.submitter = WebSubmitter(headless=cfg.HEADLESS)

    def run(self):
        setup_logging()

        pendientes = get_unprocessed_files()
        total_archivos = len(pendientes)

        if not pendientes:
            logger.info("No hay archivos pendientes por procesar.")
            resumen_global(0, 0, 0)
            return

        logger.info(f"Archivos pendientes: {total_archivos}")

        procesados = 0

        for archivo in pendientes:
            try:
                self._procesar_archivo(archivo)
                procesados += 1
            except Exception as e:
                logger.exception(f"Error crítico procesando {archivo.path_dir}: {e}")

        omitidos = total_archivos - procesados
        resumen_global(total_archivos, procesados, omitidos)

    def _procesar_archivo(self, archivo: ProcessableInputFile):
        logger.info(f"Procesando: {archivo.path_dir}")

        ext = archivo.full_path.suffix
        reader = reader_factory(ext)
        df = reader.read(archivo.full_path)

        for col in COLUMNAS_ARCHIVO:
            if col not in df.columns:
                logger.warning(f"Columna '{col}' no encontrada en {archivo.path_dir}")

        total_filas = len(df)

        validos, errores = validate(df)
        logger.info(f"  Validación: {len(validos)} válidos, {len(errores)} errores")

        for err in errores:
            logger.warning(f"  Fila {err['fila']}: {'; '.join(err['errores'])}")

        unicos, duplicados = deduplicate(validos)
        if duplicados:
            logger.info(f"  Duplicados detectados: {len(duplicados)}")
            for d in duplicados:
                logger.warning(
                    f"  Duplicado: {d['identificador']} — email: {d['email']}"
                )

        grupos = classify(unicos)
        logger.info(f"  Clasificación: {len(grupos)} tipo(s)")

        resultados_submit = self.submitter.submit(unicos)
        submit_ok = sum(1 for r in resultados_submit if r["error"] is None)
        submit_fail = len(resultados_submit) - submit_ok
        logger.info(f"  Envíos: {submit_ok} OK, {submit_fail} fallidos")

        guardar_resultados(archivo, unicos, duplicados, errores, resultados_submit)

        resumen_archivo(
            filename=archivo.path_dir,
            total_filas=total_filas,
            validos=len(validos),
            duplicados=len(duplicados),
            errores=len(errores),
            submit_ok=submit_ok,
            submit_fail=submit_fail,
        )
