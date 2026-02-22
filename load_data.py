# load_data.py
import os
import csv
import psycopg2
from datetime import datetime, date
from models import (
    Miembro, Evento, EmpresentaPonente, Proyecto,
    Publicacion, MetricasRRSS,
    InscripcionEvento, ParticipacionProyecto, EventoPonente
)
from pydantic import ValidationError

# --- Conexión ---
conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", 5432),
    dbname=os.getenv("DB_NAME", "sigma_db"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "postgres"),
)
cur = conn.cursor()

# --- Helper genérico ---
def load_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def none_if_empty(d: dict) -> dict:
    """Convierte strings vacíos a None para campos opcionales."""
    return {k: (None if v == "" else v) for k, v in d.items()}

# ============================================================
# 1. MIEMBRO (sin FK)
# ============================================================
print("▶ Insertando miembros...")
for row in load_csv("data/miembros.csv"):
    try:
        m = Miembro.model_validate(none_if_empty(row))
        cur.execute(
            """INSERT INTO miembro (dni, nombre, apellidos, correo, carrera, curso, tlf, cargo)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (dni) DO NOTHING""",
            (m.dni, m.nombre, m.apellidos, m.correo,
             m.carrera, m.curso.value if m.curso else None,
             m.tlf, row.get("cargo") or "Socio")
        )
    except ValidationError as e:
        print(f"  ❌ Miembro inválido ({row}): {e}")
conn.commit()
print("  ✅ Miembros OK")

# ============================================================
# 2. EVENTO (sin FK)
# ============================================================
print("▶ Insertando eventos...")
for row in load_csv("data/eventos.csv"):
    try:
        row = none_if_empty(row)
        row.pop("id_evento", None)          # SERIAL, no lo insertamos
        e = Evento.model_validate(row)
        cur.execute(
            """INSERT INTO evento
               (nombre, fecha_evento, aula, categoria, aforo, premio,
                catering, fecha_hora_pub, fecha_hora_sold_out)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id_evento""",
            (e.nombre, e.fecha_evento, e.aula, e.categoria,
             e.aforo, e.premio, e.catering,
             e.fecha_hora_pub, e.fecha_hora_sold_out)
        )
        id_evento = cur.fetchone()[0]
        print(f"  ✅ Evento '{e.nombre}' → id_evento={id_evento}")
    except ValidationError as e:
        print(f"  ❌ Evento inválido ({row}): {e}")
conn.commit()

# ============================================================
# 3. EMPRESAS_PONENTES (sin FK)
# ============================================================
print("▶ Insertando ponentes...")
for row in load_csv("data/ponentes.csv"):
    r = none_if_empty(row)
    cur.execute(
        """INSERT INTO empresas_ponentes (nombre_ponente, empresa, cargo)
           VALUES (%s, %s, %s) ON CONFLICT DO NOTHING""",
        (r["nombre_ponente"], r["empresa"], r.get("cargo"))
    )
conn.commit()
print("  ✅ Ponentes OK")

# ============================================================
# 4. PROYECTO (sin FK)
# ============================================================
print("▶ Insertando proyectos...")
for row in load_csv("data/proyectos.csv"):
    r = none_if_empty(row)
    cur.execute(
        """INSERT INTO proyecto (nombre_proy, descripcion, fecha_inicio, estado)
           VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING""",
        (r["nombre_proy"], r.get("descripcion"),
         r.get("fecha_inicio"), r["estado"])
    )
conn.commit()
print("  ✅ Proyectos OK")

# ============================================================
# 5. TABLAS INTERMEDIAS (dependen de las anteriores)
# ============================================================
print("▶ Insertando evento_ponente...")
for row in load_csv("data/evento_ponente.csv"):
    r = none_if_empty(row)
    cur.execute(
        """INSERT INTO evento_ponente (id_evento, id_ponente)
           VALUES (%s, %s) ON CONFLICT DO NOTHING""",
        (r["id_evento"], r["id_ponente"])
    )
conn.commit()

print("▶ Insertando inscripciones_eventos...")
for row in load_csv("data/inscripciones_eventos.csv"):
    r = none_if_empty(row)
    cur.execute(
        """INSERT INTO inscripciones_eventos
           (id_miembro, id_evento, fecha_inscripcion, asistencia)
           VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING""",
        (r["id_miembro"], r["id_evento"],
         r.get("fecha_inscripcion") or datetime.now(),
         r.get("asistencia", "false").lower() == "true")
    )
conn.commit()

print("▶ Insertando participacion_proyectos...")
for row in load_csv("data/participacion_proyectos.csv"):
    r = none_if_empty(row)
    cur.execute(
        """INSERT INTO participacion_proyectos (id_miembro, id_proyecto, rol)
           VALUES (%s, %s, %s) ON CONFLICT DO NOTHING""",
        (r["id_miembro"], r["id_proyecto"], r.get("rol"))
    )
conn.commit()

# ============================================================
# 6. PUBLICACION (FK → miembro + evento)
# ============================================================
print("▶ Insertando publicaciones...")
for row in load_csv("data/publicaciones.csv"):
    try:
        p = Publicacion.model_validate(none_if_empty(row))
        cur.execute(
            """INSERT INTO publicacion
               (url_post, plataforma, fecha_post, id_evento, miembro_que_publico)
               VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
            (str(p.url_post), p.plataforma.value, p.fecha_post,
             p.id_evento, p.miembro_que_publico)
        )
    except ValidationError as e:
        print(f"  ❌ Publicacion inválida: {e}")
conn.commit()
print("  ✅ Publicaciones OK")

# ============================================================
# 7. METRICAS_RRSS (FK → publicacion)
# ============================================================
print("▶ Insertando métricas RRSS...")
for row in load_csv("data/metricas_rrss.csv"):
    r = none_if_empty(row)
    cur.execute(
        """INSERT INTO metricas_rrss
           (url_post, fecha_medicion, likes, reposts, comentarios, guardados)
           VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
        (r["url_post"],
         r.get("fecha_medicion") or datetime.now(),
         int(r.get("likes") or 0),
         int(r.get("reposts") or 0),
         int(r.get("comentarios") or 0),
         int(r.get("guardados") or 0))
    )
conn.commit()
print("  ✅ Métricas RRSS OK")

cur.close()
conn.close()
print("\n🎉 Ingesta completada sin errores.")
