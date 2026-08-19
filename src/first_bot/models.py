import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from first_bot.processable_file import (
    ProcessableFileFactory,
    ProcessableInputFile,
    ProcessableOutputFile,
)


class Persona(BaseModel):
    """Datos personales mapeables al formulario web."""
    first_name: str
    last_name: str
    company_name: str
    role_in_company: str
    address: str
    email: EmailStr
    phone_number: str

    @field_validator("first_name", "last_name", "company_name", "role_in_company", "address", "phone_number")
    @classmethod
    def not_empty(cls, v: str) -> str:
        stripped = v.strip() if isinstance(v, str) else v
        if not stripped:
            raise ValueError("campo obligatorio vacío")
        return stripped


class Solicitud(BaseModel):
    """Solicitud completa: persona + datos de negocio."""
    persona: Persona
    tipo_solicitud: str
    fecha: date
    prioridad: Literal["alta", "media", "baja"]
    identificador: str
    descripcion: str
    estado: Literal["pendiente", "en_proceso", "completada"]

    @field_validator("tipo_solicitud", "identificador", "descripcion")
    @classmethod
    def not_empty_str(cls, v: str) -> str:
        stripped = v.strip() if isinstance(v, str) else v
        if not stripped:
            raise ValueError("campo obligatorio vacío")
        return stripped

    @field_validator("fecha", mode="before")
    @classmethod
    def parse_fecha(cls, v: object) -> date:
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
                try:
                    from datetime import datetime
                    return datetime.strptime(v.strip(), fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"formato de fecha no reconocido: {v}")
        if hasattr(v, "date"):
            return v.date()
        raise ValueError(f"tipo de fecha no soportado: {type(v)}")


COLUMNAS_ARCHIVO = [
    "First Name", "Last Name", "Company Name", "Role in Company",
    "Address", "Email", "Phone Number",
    "tipo_solicitud", "fecha", "prioridad",
    "identificador", "descripcion", "estado",
]


def row_to_solicitud(row: dict) -> Solicitud:
    persona = Persona(
        first_name=str(row.get("First Name", "")),
        last_name=str(row.get("Last Name", "")),
        company_name=str(row.get("Company Name", "")),
        role_in_company=str(row.get("Role in Company", "")),
        address=str(row.get("Address", "")),
        email=str(row.get("Email", "")),
        phone_number=str(row.get("Phone Number", "")),
    )
    return Solicitud(
        persona=persona,
        tipo_solicitud=str(row.get("tipo_solicitud", "")),
        fecha=row.get("fecha", ""),
        prioridad=str(row.get("prioridad", "")),
        identificador=str(row.get("identificador", "")),
        descripcion=str(row.get("descripcion", "")),
        estado=str(row.get("estado", "")),
    )
