# main.py
from __future__ import annotations
from contextlib import asynccontextmanager
from typing import Optional, List
import os

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field, EmailStr, PositiveInt
from datetime import date, datetime

from models import Miembro, Evento

# ── Conexión ────────────────────────────────────────────────
def get_conn():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "sigma_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )
    conn.autocommit = False
    try:
        yield conn
    finally:
        conn.close()

app = FastAPI(title="Sigma Data Club API", version="1.0.0")

# ════════════════════════════════════════════════════════════
#  MIEMBRO
# ════════════════════════════════════════════════════════════

# Schemas de entrada/salida (separados del modelo de validación)
class MiembroIn(BaseModel):
    dni: str
    nombre: str
    apellidos: str
    correo: EmailStr
    carrera: Optional[str] = None
    curso: Optional[str] = None
    tlf: Optional[str] = None
    cargo: Optional[str] = "Socio"

class MiembroOut(MiembroIn):
    pass


@app.get("/miembros", response_model=List[MiembroOut], tags=["Miembros"])
def list_miembros(conn=Depends(get_conn)):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM miembro ORDER BY apellidos")
        return cur.fetchall()


@app.get("/miembros/{dni}", response_model=MiembroOut, tags=["Miembros"])
def get_miembro(dni: str, conn=Depends(get_conn)):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM miembro WHERE dni = %s", (dni.upper(),))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    return row


@app.post("/miembros", response_model=MiembroOut, status_code=201, tags=["Miembros"])
def create_miembro(data: MiembroIn, conn=Depends(get_conn)):
    # Validamos con el modelo Pydantic existente
    validated = Miembro.model_validate(data.model_dump())
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO miembro
                   (dni, nombre, apellidos, correo, carrera, curso, tlf, cargo)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING *""",
                (validated.dni, validated.nombre, validated.apellidos,
                 validated.correo, validated.carrera,
                 validated.curso.value if validated.curso else None,
                 validated.tlf, data.cargo or "Socio")
            )
            row = cur.fetchone()
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return row


@app.put("/miembros/{dni}", response_model=MiembroOut, tags=["Miembros"])
def update_miembro(dni: str, data: MiembroIn, conn=Depends(get_conn)):
    validated = Miembro.model_validate(data.model_dump())
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """UPDATE miembro SET
                   nombre=%s, apellidos=%s, correo=%s,
                   carrera=%s, curso=%s, tlf=%s, cargo=%s
                   WHERE dni=%s RETURNING *""",
                (validated.nombre, validated.apellidos, validated.correo,
                 validated.carrera,
                 validated.curso.value if validated.curso else None,
                 validated.tlf, data.cargo or "Socio",
                 dni.upper())
            )
            row = cur.fetchone()
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    if not row:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    return row


@app.delete("/miembros/{dni}", status_code=204, tags=["Miembros"])
def delete_miembro(dni: str, conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM miembro WHERE dni = %s", (dni.upper(),))
        if cur.rowcount == 0:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Miembro no encontrado")
        conn.commit()


# ════════════════════════════════════════════════════════════
#  EVENTO
# ════════════════════════════════════════════════════════════

class EventoIn(BaseModel):
    nombre: str
    fecha_evento: date
    aula: Optional[str] = None
    categoria: Optional[str] = None
    aforo: PositiveInt
    premio: Optional[str] = None
    catering: Optional[bool] = False
    fecha_hora_pub: datetime
    fecha_hora_sold_out: Optional[datetime] = None

class EventoOut(EventoIn):
    id_evento: int


@app.get("/eventos", response_model=List[EventoOut], tags=["Eventos"])
def list_eventos(conn=Depends(get_conn)):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM evento ORDER BY fecha_evento DESC")
        return cur.fetchall()


@app.get("/eventos/{id_evento}", response_model=EventoOut, tags=["Eventos"])
def get_evento(id_evento: int, conn=Depends(get_conn)):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM evento WHERE id_evento = %s", (id_evento,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return row


@app.post("/eventos", response_model=EventoOut, status_code=201, tags=["Eventos"])
def create_evento(data: EventoIn, conn=Depends(get_conn)):
    # Reutilizamos la validación Pydantic (check sold_out > pub)
    validated = Evento.model_validate({**data.model_dump(), "id_evento": 1})
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO evento
                   (nombre, fecha_evento, aula, categoria, aforo, premio,
                    catering, fecha_hora_pub, fecha_hora_sold_out)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING *""",
                (validated.nombre, validated.fecha_evento,
                 validated.aula, validated.categoria, validated.aforo,
                 validated.premio, validated.catering,
                 validated.fecha_hora_pub, validated.fecha_hora_sold_out)
            )
            row = cur.fetchone()
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return row


@app.put("/eventos/{id_evento}", response_model=EventoOut, tags=["Eventos"])
def update_evento(id_evento: int, data: EventoIn, conn=Depends(get_conn)):
    validated = Evento.model_validate({**data.model_dump(), "id_evento": id_evento})
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """UPDATE evento SET
                   nombre=%s, fecha_evento=%s, aula=%s, categoria=%s,
                   aforo=%s, premio=%s, catering=%s,
                   fecha_hora_pub=%s, fecha_hora_sold_out=%s
                   WHERE id_evento=%s RETURNING *""",
                (validated.nombre, validated.fecha_evento,
                 validated.aula, validated.categoria, validated.aforo,
                 validated.premio, validated.catering,
                 validated.fecha_hora_pub, validated.fecha_hora_sold_out,
                 id_evento)
            )
            row = cur.fetchone()
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    if not row:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return row


@app.delete("/eventos/{id_evento}", status_code=204, tags=["Eventos"])
def delete_evento(id_evento: int, conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM evento WHERE id_evento = %s", (id_evento,))
        if cur.rowcount == 0:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Evento no encontrado")
        conn.commit()
