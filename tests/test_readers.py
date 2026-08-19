from pathlib import Path

import pytest

from first_bot.exceptions import FileReadError
from first_bot.readers import CsvReader, XlsxReader, reader_factory


def test_factory_retorna_csv_reader():
    reader = reader_factory(".csv")
    assert isinstance(reader, CsvReader)


def test_factory_retorna_xlsx_reader():
    reader = reader_factory(".xlsx")
    assert isinstance(reader, XlsxReader)


def test_factory_retorna_xls_reader():
    reader = reader_factory(".xls")
    assert isinstance(reader, XlsxReader)


def test_factory_ext_sin_punto():
    reader = reader_factory("csv")
    assert isinstance(reader, CsvReader)


def test_factory_mayusculas():
    reader = reader_factory("CSV")
    assert isinstance(reader, CsvReader)


def test_factory_extension_invalida():
    with pytest.raises(FileReadError, match="Extensión no soportada"):
        reader_factory(".json")


def test_csv_reader_lee(csv_valido):
    reader = CsvReader()
    df = reader.read(csv_valido)
    assert len(df) == 1
    assert df.iloc[0]["First Name"] == "Juan"


def test_xlsx_reader_lee(xlsx_valido):
    reader = XlsxReader()
    df = reader.read(xlsx_valido)
    assert len(df) == 1
    assert df.iloc[0]["First Name"] == "María"


def test_csv_reader_archivo_no_existe():
    reader = CsvReader()
    with pytest.raises(FileReadError):
        reader.read(Path("/no/existe.csv"))


def test_xlsx_reader_archivo_no_existe():
    reader = XlsxReader()
    with pytest.raises(FileReadError):
        reader.read(Path("/no/existe.xlsx"))
