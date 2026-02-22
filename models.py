from __future__ import annotations

import re
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    PositiveInt,
    EmailStr,
    field_validator,
    model_validator,
)

class CursoEnum(str, Enum):
    _1 = "1"
    _2 = "2"
    _3 = "3"
    _4 = "4"
    _5 = "5"

class EstadoProyectoEnum(str, Enum):
    pendiente = "pendiente"
    en_proceso = "en proceso"
    finalizado = "finalizado"

class PlataformaEnum(str, Enum):
    instagram = "instagram"
    linkedin = "linkedin"
    twitter = "twitter"
    x = "x"
    tiktok = "tiktok"
    youtube = "youtube"
    web = "web"
    otra = "otra"

class SigmaBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class Miembro(SigmaBaseModel):
    # DNI clásico: 8 dígitos + 1 letra
    dni: str = Field(..., min_length=9, max_length=9)
    nombre: str = Field(..., min_length=1, max_length=100)
    apellidos: str = Field(..., min_length=1, max_length=100)
    correo: EmailStr
    carrera: Optional[str] = Field(None, max_length=50)
    curso: Optional[CursoEnum] = None

    # ❗️Sin max_length aquí para permitir input sucio y limpiar antes
    tlf: Optional[str] = None

    @field_validator("dni")
    @classmethod
    def normalize_dni(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) != 9:
            raise ValueError("dni debe tener exactamente 9 caracteres")
        if not re.fullmatch(r"\d{8}[A-Z]", v):
            raise ValueError("dni debe tener formato 8 números + 1 letra")
        return v

    @field_validator("correo")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()

    @field_validator("tlf")
    @classmethod
    def normalize_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        vv = "".join(ch for ch in v.strip() if ch.isdigit() or ch == "+")
        if not vv:
            raise ValueError("tlf inválido")
        if len(vv) > 15:
            raise ValueError("tlf excede 15 caracteres (limpio)")
        return vv

class Evento(SigmaBaseModel):
    id_evento: PositiveInt
    nombre: str = Field(..., min_length=1, max_length=100)
    fecha_evento: date
    aula: Optional[str] = Field(None, max_length=30)
    categoria: Optional[str] = Field(None, max_length=50)
    aforo: PositiveInt
    premio: Optional[str] = Field(None, max_length=100)
    catering: Optional[bool] = None
    fecha_hora_pub: datetime
    fecha_hora_sold_out: Optional[datetime] = None

    @model_validator(mode="after")
    def check_sold_out_after_pub(self) -> "Evento":
        if self.fecha_hora_sold_out is not None and self.fecha_hora_sold_out <= self.fecha_hora_pub:
            raise ValueError("fecha_hora_sold_out debe ser posterior a fecha_hora_pub")
        return self

class Publicacion(SigmaBaseModel):
    url_post: HttpUrl
    plataforma: PlataformaEnum
    fecha_post: datetime
    id_evento: Optional[PositiveInt] = None

    # si esto es DNI, también 9
    miembro_que_publico: str = Field(..., min_length=9, max_length=9)

    @field_validator("miembro_que_publico")
    @classmethod
    def normalize_miembro(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) != 9:
            raise ValueError("miembro_que_publico debe tener exactamente 9 caracteres")
        if not re.fullmatch(r"\d{8}[A-Z]", v):
            raise ValueError("miembro_que_publico debe tener formato 8 números + 1 letra")
        return v