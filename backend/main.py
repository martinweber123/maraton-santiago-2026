from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from anthropic import Anthropic
import os, json, sqlite3
from pathlib import Path

app = FastAPI()
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

DB_PATH = os.environ.get("DB_PATH", "/tmp/maraton.db")
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend" / "public"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY, data TEXT
    )""")
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

SYSTEM_PROMPT = """Eres el coach personal de Martín para el Maratón de Santiago 2026 (26 de abril).
Sigues la metodología de Peter Attia: zona 2 cardio, VO2max, fuerza funcional y estabilidad.
El plan es de 8 semanas, comenzando el 2 de marzo 2026. Meta: 2:00-2:15 hrs (ritmo 6:01/km).

Plan de entrenamiento:
- Semana 1-2 (Base Aeróbica): 4 días/semana, 35-45 km total, zona 2 principalmente
- Semana 3-4 (Volumen): 5 días/semana, 45-55 km, incorporar tempo runs
- Semana 5-6 (Específico): 5 días/semana, 55-65 km, intervalos y long runs
- Semana 7 (Peak): 5 días/semana, 60-70 km, máxima carga
- Semana 8 (Taper): 3-4 días/semana, reducir 40%, preparación final

Ejercicios de fuerza: sentadillas búlgaras, peso muerto rumano, elevaciones de pantorrilla, planchas, hip thrust, chin-ups.

Responde siempre en español, con motivación pero siendo directo y técnico cuando sea necesario.
Si el usuario pregunta por cambios de ejercicios o rutinas, adáptalos manteniendo el objetivo principal.
Usa datos de Garmin cuando los proporcione (VO2max, zonas FC, HRV, Body Battery)."""

@app.post("/api/chat")
async def chat(msg: ChatMsg):
    try:
        messages = msg.history + [{"role": "user", "content": msg.message}]
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=messages
        )
        return {"reply": response.content[0].text}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/workout/update")
async def update_workout(wu: WorkoutUpdate):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT OR REPLACE INTO workouts VALUES (?,?,?,?,?,?)""",
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

# Serve frontend static files LAST
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
