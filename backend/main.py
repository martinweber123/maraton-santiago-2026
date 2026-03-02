from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from anthropic import Anthropic
import os, json, sqlite3
from pathlib import Path
from datetime import date, datetime

app = FastAPI()
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

DB_PATH = os.environ.get("DB_PATH", "/tmp/maraton.db")
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend" / "public"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS workouts (
        id TEXT PRIMARY KEY, week INTEGER, day TEXT,
        completed INTEGER, metrics TEXT, notes TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS strength_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise TEXT, sets INTEGER, reps INTEGER,
        weight REAL, date TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

def get_current_week():
    start = date(2026, 3, 2)
    today = date.today()
    diff = (today - start).days
    if diff < 0:
        return 1, 0
    week = min(diff // 7 + 1, 8)
    day_idx = diff % 7
    return week, day_idx

def get_completed_count():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM workouts WHERE completed=1")
        count = c.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

PLAN_NAMES = [
    ["Carrera Z2 + Activación","Fuerza Tren Inferior","Descanso activo","Carrera Z2 moderada","Fuerza Core + Upper","Long run 16km","Recuperación"],
    ["Carrera Z2 + Strides","Fuerza Tren Inferior","Carrera Z2 corta","Tempo run 20min","Fuerza Full Body","Long run 18km","Recuperación"],
    ["Carrera Z2","Intervalos 4x1km","Fuerza + Movilidad","Carrera Z2 + Tempo","Fuerza Tren Inferior","Long run 20km","Rodaje suave"],
    ["Carrera Z2","Fuerza Upper + Core","Intervalos 6x800m","Maratón pace","Fuerza Tren Inferior","Long run 22km","Recuperación activa"],
    ["Carrera Z2","Fuerza completa","Intervals 3x2km","Tempo run 35min","Fuerza + Movilidad","Long run 24km","Rodaje corto"],
    ["Carrera Z2 larga","Fuerza tren inferior","Intervalos 5x1mile","Maratón pace largo","Fuerza Upper + Core","Long run 26km","Recuperación"],
    ["Carrera Z2","Fuerza Peak","Intervalos 8x600m","Tempo run 40min","Fuerza ligera","Long run 28km","Rodaje recuperación"],
    ["Carrera Z2 corta","Fuerza muy ligera","Intervalos cortos","Maratón pace corto","Trote suave","Activación pre-carrera","🏆 MARATÓN SANTIAGO"],
]
DAY_NAMES = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]

class ChatMsg(BaseModel):
    message: str
    history: list = []

class WorkoutUpdate(BaseModel):
    id: str
    week: int
    day: str
    completed: bool
    metrics: dict = {}
    notes: str = ""

class StrengthLog(BaseModel):
    exercise: str
    sets: int
    reps: int
    weight: float
    date: str

@app.post("/api/chat")
async def chat(msg: ChatMsg):
    try:
        week, day_idx = get_current_week()
        completed = get_completed_count()
        today_name = PLAN_NAMES[week-1][day_idx]
        today_day = DAY_NAMES[day_idx]
        today_date = datetime.now().strftime("%d/%m/%Y")

        system = f"""Eres el coach personal de Martín para el Maratón de Santiago 2026 (26 de abril).
Sigues la metodología de Peter Attia: zona 2 cardio, VO2max, fuerza funcional y estabilidad.
El plan es de 8 semanas, comenzando el 2 de marzo 2026. Meta: 2:00-2:15 hrs (ritmo 6:01/km).
Martín tiene 26 años, entrena 5-6 días/semana combinando running, spinning, HIIT y fútbol semanal.
Practica ayuno intermitente y dieta alta en proteínas.

ESTADO ACTUAL DEL PLAN:
- Fecha de hoy: {today_date} ({today_day})
- Semana actual: {week} de 8
- Entrenamiento de hoy: {today_name}
- Entrenamientos completados hasta ahora: {completed}
- Días para el maratón: {(date(2026,4,26) - date.today()).days}

Fases del plan:
- Semana 1-2: Base Aeróbica (35-45 km/semana)
- Semana 3-4: Volumen (45-55 km/semana)
- Semana 5-6: Específico (55-65 km/semana)
- Semana 7: Peak (65-70 km/semana)
- Semana 8: Taper (30-35 km/semana)

Responde siempre en español, con motivación pero directo y técnico.
Si el usuario pregunta por cambios de ejercicios o rutinas, adáptalos manteniendo el objetivo.
Usa datos de Garmin cuando los proporcione (VO2max, zonas FC, HRV, Body Battery).
Cuando el usuario pregunte por el entrenamiento de hoy, usa el estado actual del plan."""

        messages = msg.history + [{"role": "user", "content": msg.message}]
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system,
            messages=messages
        )
        return {"reply": response.content[0].text}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/workout/update")
async def update_workout(wu: WorkoutUpdate):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO workouts VALUES (?,?,?,?,?,?)",
              (wu.id, wu.week, wu.day, int(wu.completed),
               json.dumps(wu.metrics), wu.notes))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/api/workout/all")
async def get_workouts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM workouts")
    rows = c.fetchall()
    conn.close()
    result = {}
    for r in rows:
        result[r[0]] = {
            "week": r[1], "day": r[2], "completed": bool(r[3]),
            "metrics": json.loads(r[4]) if r[4] else {},
            "notes": r[5]
        }
    return result

@app.post("/api/strength/log")
async def log_strength(log: StrengthLog):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO strength_logs (exercise,sets,reps,weight,date) VALUES (?,?,?,?,?)",
              (log.exercise, log.sets, log.reps, log.weight, log.date))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/api/strength/history")
async def get_strength_history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM strength_logs ORDER BY date DESC LIMIT 100")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "exercise": r[1], "sets": r[2], "reps": r[3],
             "weight": r[4], "date": r[5]} for r in rows]

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
