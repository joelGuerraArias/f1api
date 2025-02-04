from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import random
import asyncio
import time
import logging
import json
import openai
import wikipediaapi  # 📌 API de Wikipedia en español

# Configuración inicial
app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("F1-API")

# 🔹 Cargar API Key de OpenAI desde las variables de entorno en Railway
openai.api_key = os.getenv("OPENAI_API_KEY")

# Verificar que la clave se haya cargado correctamente
if not openai.api_key:
    raise ValueError("❌ ERROR: No se encontró la clave de OpenAI. Verifica las variables de entorno en Railway.")

# Configurar Wikipedia en Español
wiki_api = wikipediaapi.Wikipedia('es')

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lista de pilotos 2025
PILOTS = [
    "George Russell (Mercedes)", "Andrea Kimi Antonelli (Mercedes)",
    "Max Verstappen (Red Bull)", "Liam Lawson (Red Bull)",
    "Lando Norris (McLaren)", "Oscar Piastri (McLaren)",
    "Fernando Alonso (Aston Martin)", "Lance Stroll (Aston Martin)",
    "Pierre Gasly (Alpine)", "Jack Doohan (Alpine)",
    "Charles Leclerc (Ferrari)", "Lewis Hamilton (Ferrari)",
    "Yuki Tsunoda (Racing Bulls)", "Isack Hadjar (Racing Bulls)",
    "Nico Hülkenberg (Sauber)", "Gabriel Bortoleto (Sauber)",
    "Oliver Bearman (Haas)", "Esteban Ocon (Haas)",
    "Alex Albon (Williams)", "Carlos Sainz (Williams)"
]

# Estado global
weather = {"raining": False}
safety_car_status = {"active": False}
previous_lap = None

def handle_safety_car(current_status, events):
    """Gestiona la lógica del Safety Car"""
    if current_status:
        if random.random() < 0.3:
            events.append("🚨 Safety Car entra a boxes")
            return False
    else:
        if random.random() < 0.15:
            events.append("🚨 Safety Car despliega en la pista")
            return True
    return current_status

def process_pit_stops(standings, events):
    """Maneja las entradas a pits"""
    for i in range(len(standings)):
        if random.random() < 0.1:
            driver = standings[i]
            new_pos = random.randint(5, len(standings)-1)
            standings.insert(new_pos, standings.pop(i))
            events.append(f"🛠️ {driver} entra a pits (P{i+1} → P{new_pos+1})")

def get_wikipedia_summary(driver_name):
    """Obtiene un dato interesante de Wikipedia sobre el piloto en español"""
    page = wiki_api.page(driver_name)
    if page.exists():
        summary = page.summary.split('. ')[0] + '.'  # 📌 Solo la primera oración
        return f"📌 Dato curioso: {summary}"
    return "📌 No se encontraron datos curiosos sobre este piloto."

async def generate_commentary(lap, previous_lap, standings, weather, safety_car, events):
    """Genera un comentario en español con OpenAI comparando la vuelta actual con la anterior"""
    if previous_lap:
        prev_top3 = previous_lap["standings"][:3]
        curr_top3 = standings[:3]
        top3_changes = [f"{prev} → {curr}" for prev, curr in zip(prev_top3, curr_top3) if prev != curr]
        change_summary = "Cambios en el top 3: " + ", ".join(top3_changes) if top3_changes else "No hubo cambios en los tres primeros puestos."
        
        prev_weather = "Lluvia" if previous_lap["weather"] else "Seco"
        curr_weather = "Lluvia" if weather else "Seco"
        weather_summary = f"🌦️ Cambio de clima de {prev_weather} a {curr_weather}." if prev_weather != curr_weather else f"🌦️ Clima sigue siendo {curr_weather}."

        prev_safety = "ACTIVO" if previous_lap["safety_car"] else "INACTIVO"
        curr_safety = "ACTIVO" if safety_car else "INACTIVO"
        safety_summary = f"🚨 Safety Car {'se mantiene' if prev_safety == curr_safety else 'ha cambiado su estado'}."

        comparison_summary = f"{change_summary} {weather_summary} {safety_summary}"
    else:
        comparison_summary = "Esta es la primera vuelta de la carrera."

    # Obtener un solo dato curioso de Wikipedia
    driver_name = standings[random.randint(0, 2)].split('(')[0].strip()  # 🔹 Un piloto del Top 3 aleatorio
    wiki_summary = get_wikipedia_summary(driver_name)

    prompt = f"""
    Simula ser un comentarista de Fórmula 1 y describe la vuelta {lap} en español. 
    La carrera está en clima {'lluvioso' if weather else 'seco'}. 
    El Safety Car está {'activo' if safety_car else 'inactivo'}. 
    Los tres primeros lugares son: {standings[0]}, {standings[1]}, {standings[2]}. 
    Los eventos importantes en esta vuelta son: {', '.join(events) if events else 'sin eventos destacados'}.
    
    Comparando con la vuelta anterior: {comparison_summary}

    Datos adicionales sobre los pilotos:
    {wiki_summary}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "Eres un comentarista deportivo en español."},
                      {"role": "user", "content": prompt}],
            max_tokens=200
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Error generando comentario: {str(e)}")
        return "🎙️ Error generando comentario."

@app.get("/simulate_race")
async def full_race_simulation():
    """Simulación de carrera con comentarios en español y datos de Wikipedia"""
    async def race_generator():
        global previous_lap
        try:
            standings = PILOTS.copy()
            random.shuffle(standings)
            local_weather = weather["raining"]
            safety_car = safety_car_status["active"]
            start_time = time.time()

            for lap in range(1, 6):
                lap_start = time.time()
                events = []

                if random.random() < 0.2:
                    local_weather = not local_weather
                    events.append(f"🌦️ Cambio de clima a {'lluvia' if local_weather else 'seco'}")

                safety_car = handle_safety_car(safety_car, events)
                if not safety_car:
                    random.shuffle(standings[:3])
                    events.append(f"🔄 Cambio en el top 3: {standings[0]} ahora lidera la carrera")

                process_pit_stops(standings, events)

                commentary = await generate_commentary(lap, previous_lap, standings, local_weather, safety_car, events)

                previous_lap = {
                    "standings": standings.copy(),
                    "weather": local_weather,
                    "safety_car": safety_car
                }

                yield f"data: {json.dumps({'message': commentary})}\n\n"
                await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"Error en generador: {str(e)}")

    return StreamingResponse(race_generator(), media_type="text/event-stream")



