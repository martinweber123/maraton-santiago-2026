# 🏃 Maratón Santiago 2026 — App

App PWA para seguimiento del plan de entrenamiento Maratón Santiago 2026.
Coach con IA (Claude), registro de fuerza, datos Garmin y progreso semanal.

---

## 🚀 DEPLOY EN RAILWAY (paso a paso)

### Paso 1: Sube el código a GitHub

1. Ve a **github.com** → "New repository"
2. Nombre: `maraton-santiago-2026`
3. Privado ✓ → "Create repository"
4. En tu computador, descomprime el ZIP y abre una terminal en esa carpeta:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/maraton-santiago-2026.git
git push -u origin main
```

### Paso 2: Deploy en Railway

1. Ve a **railway.app** → "Start a New Project"
2. "Deploy from GitHub repo" → selecciona `maraton-santiago-2026`
3. Railway detecta automáticamente Python

### Paso 3: Variables de entorno

En Railway → tu proyecto → **Variables** → agrega:

| Variable | Valor |
|----------|-------|
| `ANTHROPIC_API_KEY` | tu key sk-ant-... |

### Paso 4: Obtener URL

Railway genera automáticamente una URL tipo:
`https://maraton-santiago-2026-production.up.railway.app`

### Paso 5: Instalar como app en tu teléfono

**iPhone (Safari):**
1. Abre la URL en Safari
2. Toca el ícono de compartir ↑
3. "Agregar a pantalla de inicio"
4. ¡Lista la app!

**Android (Chrome):**
1. Abre la URL en Chrome
2. Toca los 3 puntos ⋮
3. "Agregar a pantalla de inicio"
4. ¡Lista la app!

---

## 📱 Funcionalidades

- **Hoy**: Entrenamiento del día con instrucciones detalladas
- **Plan**: Las 8 semanas completas con todos los entrenamientos
- **Coach**: Chat con IA para preguntas, ajustes y motivación
- **Fuerza**: Registro de pesos y PRs para cada ejercicio
- **Garmin**: Ingreso manual de datos del reloj (HRV, VO2max, Zona 2, etc.)

---

## 🏗️ Arquitectura

- **Backend**: FastAPI (Python)
- **Frontend**: HTML/CSS/JS vanilla (PWA)
- **IA**: Claude claude-sonnet-4-20250514 via API
- **DB**: SQLite (persiste en Railway)
- **Deploy**: Railway (gratis en tier hobby)
