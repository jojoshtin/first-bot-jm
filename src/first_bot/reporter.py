from pathlib import Path
from datetime import datetime
from typing import Union

import pandas as pd
from loguru import logger

import first_bot.config as cfg
from first_bot.models import Solicitud
from first_bot.processable_file import ProcessableInputFile
from first_bot.utils import output_filename


def setup_logging():
    cfg.LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = cfg.LOG_DIR / f"bot_{timestamp}.log"
    logger.add(
        log_file,
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    )


def guardar_resultados(
    input_path: Union[Path, ProcessableInputFile],
    unicos: list[Solicitud],
    duplicados: list[dict],
    errores: list[dict],
    resultados_submit: list[dict],
):
    output = output_filename(input_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    filas: list[dict] = []

    for s in unicos:
        submit_result = next(
            (r for r in resultados_submit if r["identificador"] == s.identificador),
            {"resultado": "pendiente", "error": None},
        )
        filas.append({
            "first_name": s.persona.first_name,
            "last_name": s.persona.last_name,
            "email": s.persona.email,
            "tipo_solicitud": s.tipo_solicitud,
            "fecha": s.fecha,
            "prioridad": s.prioridad,
            "identificador": s.identificador,
            "estado": s.estado,
            "resultado": submit_result["resultado"],
            "error": submit_result.get("error"),
        })

    for d in duplicados:
        filas.append({
            "first_name": "",
            "last_name": "",
            "email": d.get("email", ""),
            "tipo_solicitud": "",
            "fecha": None,
            "prioridad": "",
            "identificador": d.get("identificador", ""),
            "estado": "",
            "resultado": "duplicado",
            "error": f"Email duplicado: {d.get('email', '')}",
        })

    for e in errores:
        filas.append({
            "first_name": "",
            "last_name": "",
            "email": "",
            "tipo_solicitud": "",
            "fecha": None,
            "prioridad": "",
            "identificador": f"fila_{e['fila']}",
            "estado": "",
            "resultado": "error_validacion",
            "error": "; ".join(e["errores"]),
        })

    df_out = pd.DataFrame(filas)
    df_out.to_csv(output, index=False)
    logger.info(f"Resultados guardados en: {output}")


def resumen_archivo(
    filename: str,
    total_filas: int,
    validos: int,
    duplicados: int,
    errores: int,
    submit_ok: int,
    submit_fail: int,
):
    logger.info("=" * 50)
    logger.info(f"RESUMEN: {filename}")
    logger.info(f"  Total filas leídas:    {total_filas}")
    logger.info(f"  Válidas:               {validos}")
    logger.info(f"  Duplicados:            {duplicados}")
    logger.info(f"  Errores validación:    {errores}")
    logger.info(f"  Envíos exitosos:       {submit_ok}")
    logger.info(f"  Envíos fallidos:       {submit_fail}")
    logger.info("=" * 50)


def resumen_global(total_archivos: int, procesados: int, omitidos: int):
    logger.info("=" * 50)
    logger.info("RESUMEN GLOBAL DE EJECUCIÓN")
    logger.info(f"  Archivos totales:      {total_archivos}")
    logger.info(f"  Archivos procesados:   {procesados}")
    logger.info(f"  Archivos omitidos:     {omitidos}")
    logger.info("=" * 50)
