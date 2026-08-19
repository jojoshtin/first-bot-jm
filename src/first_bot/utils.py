from pathlib import Path
from typing import Union

import first_bot.config as cfg
from first_bot.processable_file import ProcessableInputFile


def output_filename(input_source: Union[str, Path, ProcessableInputFile]) -> Path:
    """Construye la ruta del archivo de salida correspondiente al input.

    Con el nuevo sistema de tracking por fechas, el archivo de salida
    mantiene la **misma ruta relativa** que el de entrada:

        input:  data/input/2028/01/15/solicitudes.csv
        output: data/output/2028/01/15/solicitudes.csv

    Para compatibilidad retroactiva, si se recibe un ``Path`` o ``str``
    plano se usa el esquema legacy ``resultado_<stem>.csv``.
    """
    if isinstance(input_source, ProcessableInputFile):
        return cfg.OUTPUT_PATH / input_source.path_dir

    # Legacy fallback
    path = Path(input_source)
    return cfg.OUTPUT_PATH / f"resultado_{path.stem}.csv"
