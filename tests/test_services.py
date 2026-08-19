import pandas as pd

from first_bot.services import classify, deduplicate, validate
from first_bot.models import Persona, Solicitud


def df_valido():
    return pd.DataFrame([{
        "First Name": "Juan", "Last Name": "Pérez",
        "Company Name": "Tech", "Role in Company": "Dev",
        "Address": "Calle 1", "Email": "juan@test.com",
        "Phone Number": "555", "tipo_solicitud": "soporte",
        "fecha": "2024-06-15", "prioridad": "alta",
        "identificador": "SOL-1", "descripcion": "X",
        "estado": "pendiente",
    }])


class TestValidate:
    def test_todas_validas(self):
        validos, errores = validate(df_valido())
        assert len(validos) == 1
        assert len(errores) == 0

    def test_detecta_errores(self, csv_con_errores):
        from first_bot.readers import CsvReader
        df = CsvReader().read(csv_con_errores)
        validos, errores = validate(df)
        assert len(validos) == 1
        assert len(errores) == 1

    def test_errores_contienen_fila(self, csv_con_errores):
        from first_bot.readers import CsvReader
        df = CsvReader().read(csv_con_errores)
        _, errores = validate(df)
        assert "fila" in errores[0]
        assert "errores" in errores[0]


class TestDeduplicate:
    def test_sin_duplicados(self):
        from datetime import date
        p1 = Persona(first_name="A", last_name="B", company_name="C",
                     role_in_company="D", address="E", email="a@t.com",
                     phone_number="1")
        p2 = Persona(first_name="X", last_name="Y", company_name="Z",
                     role_in_company="W", address="Q", email="b@t.com",
                     phone_number="2")
        s1 = Solicitud(persona=p1, tipo_solicitud="soporte",
                       fecha=date(2024, 1, 1), prioridad="alta",
                       identificador="ID1", descripcion="d", estado="pendiente")
        s2 = Solicitud(persona=p2, tipo_solicitud="soporte",
                       fecha=date(2024, 1, 1), prioridad="alta",
                       identificador="ID2", descripcion="d", estado="pendiente")

        unicos, dups = deduplicate([s1, s2])
        assert len(unicos) == 2
        assert len(dups) == 0

    def test_con_duplicados(self):
        from datetime import date
        p = Persona(first_name="A", last_name="B", company_name="C",
                     role_in_company="D", address="E", email="dup@t.com",
                     phone_number="1")
        s1 = Solicitud(persona=p, tipo_solicitud="soporte",
                       fecha=date(2024, 1, 1), prioridad="alta",
                       identificador="ID1", descripcion="d", estado="pendiente")
        s2 = Solicitud(persona=p, tipo_solicitud="soporte",
                       fecha=date(2024, 1, 1), prioridad="alta",
                       identificador="ID2", descripcion="d", estado="pendiente")

        unicos, dups = deduplicate([s1, s2])
        assert len(unicos) == 1
        assert len(dups) == 1
        assert dups[0]["email"] == "dup@t.com"


class TestClassify:
    def test_agrupa_por_tipo(self):
        from datetime import date
        p1 = Persona(first_name="A", last_name="B", company_name="C",
                     role_in_company="D", address="E", email="a@t.com",
                     phone_number="1")
        p2 = Persona(first_name="X", last_name="Y", company_name="Z",
                     role_in_company="W", address="Q", email="b@t.com",
                     phone_number="2")
        s1 = Solicitud(persona=p1, tipo_solicitud="soporte",
                       fecha=date(2024, 1, 1), prioridad="alta",
                       identificador="ID1", descripcion="d", estado="pendiente")
        s2 = Solicitud(persona=p1, tipo_solicitud="soporte",
                       fecha=date(2024, 2, 2), prioridad="media",
                       identificador="ID3", descripcion="d", estado="pendiente")
        s3 = Solicitud(persona=p2, tipo_solicitud="reclamo",
                       fecha=date(2024, 1, 1), prioridad="alta",
                       identificador="ID2", descripcion="d", estado="pendiente")

        grupos = classify([s1, s2, s3])
        assert len(grupos) == 2
        assert len(grupos["soporte"]) == 2
        assert len(grupos["reclamo"]) == 1

    def test_unico_tipo(self):
        from datetime import date
        p = Persona(first_name="A", last_name="B", company_name="C",
                     role_in_company="D", address="E", email="a@t.com",
                     phone_number="1")
        s = Solicitud(persona=p, tipo_solicitud="consulta",
                       fecha=date(2024, 1, 1), prioridad="alta",
                       identificador="ID1", descripcion="d", estado="pendiente")

        grupos = classify([s])
        assert len(grupos) == 1
        assert "consulta" in grupos
