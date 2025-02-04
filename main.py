import os
import openai
import wikipediaapi
import random
import asyncio
import time
import logging
import json
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ ERROR: No se encontró la clave de OpenAI. Verifica las variables de entorno en Railway.")

openai.api_key = OPENAI_API_KEY

# Configuración inicial
app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("F1-API")

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔹 Cambia "*" por ["https://tu-dominio.com"] en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lista de pilotos 2025
PILOTS = [
    "George Russell (Mercedes)",
    "Andrea Kimi Antonelli (Mercedes)",
    "Max Verstappen (Red Bull)",
    "Liam Lawson (Red Bull)",
    "Lando Norris (McLaren)",
    "Oscar Piastri (McLaren)",
    "Fernando Alonso (Aston Martin)",
    "Lance Stroll (Aston Martin)",
    "Pierre Gasly (Alpine)",
    "Jack Doohan (Alpine)",
    "Charles Leclerc (Ferrari)",
    "Lewis Hamilton (Ferrari)",
    "Yuki Tsunoda (Racing Bulls)",
    "Isack Hadjar (Racing Bulls)",
    "Nico Hülkenberg (Sauber)",
    "Gabriel Bortoleto (Sauber)",
    "Oliver Bearman (Haas)",
    "Esteban Ocon (Haas)",
    "Alex Albon (Williams)",
    "Carlos Sainz (Williams)"
]

# Estado global
weather = {"raining": False}
safety_car_status = {"active": False}

def handle_safety_car(current_status, events):
    """Gestiona la lógica del Safety Car"""
    if current_status:
        if random.random() < 0.3:  # 30% de probabilidad de retirarlo
            events.append("🚨 Safety Car entra a boxes")
            return False
    else:
        if random.random() < 0.15:  # 15% de probabilidad de activarlo
            events.append("🚨 Safety Car despliega en la pista")
            return True
    return current_status

def process_pit_stops(standings, events):
    """Maneja las entradas a pits"""
    for i in range(len(standings)):
        if random.random() < 0.1:  # 10% de probabilidad por piloto
            driver = standings[i]
            new_pos = random.randint(5, len(standings)-1)
            standings.insert(new_pos, standings.pop(i))
            events.append(f"🛠️ {driver} entra a pits (P{i+1} → P{new_pos+1})")

def fetch_pilot_info(pilot_name):
    """Obtiene un dato curioso de Wikipedia sobre el piloto"""
    wiki_wiki = wikipediaapi.Wikipedia('es')  # Wikipedia en español
    page = wiki_wiki.page(pilot_name.split(" ")[0])  # Buscar solo el primer nombre del piloto
    if page.exists():
        summary = page.summary.split(".")[0] + "."  # Solo la primera oración
        return summary
    return f"No se encontró información sobre {pilot_name} en Wikipedia."

async def generate_comment(previous_standings, new_standings):
    """Genera un comentario usando OpenAI basado en los cambios de carrera"""
    prompt = f"""Basado en la Fórmula 1, genera un comentario sobre la carrera.
    La vuelta anterior tenía este Top 3: {previous_standings}
    Ahora el Top 3 es: {new_standings}.
    Analiza los cambios y genera un comentario en español:
    """
    
    response = openai.Completion.create(
        model="gpt-3.5-turbo",
        prompt=prompt,
        max_tokens=50
    )
    
    return response["choices"][0]["text"].strip()

@app.get("/simulate_race")
async def full_race_simulation():
    """Simulación de carrera con 5 vueltas y cambios en las primeras 3 posiciones"""
    async def race_generator():
        try:
            standings = PILOTS.copy()
            random.shuffle(standings)
            local_weather = weather["raining"]
            safety_car = safety_car_status["active"]
            start_time = time.time()
            previous_standings = []

            for lap in range(1, 6):  # 5 vueltas
                lap_start = time.time()
                events = []

                # Cambio de clima con 20% de probabilidad
                if random.random() < 0.2:
                    local_weather = not local_weather
                    events.append(f"🌦️ Cambio de clima a {'lluvia' if local_weather else 'seco'}")

                # Manejo del Safety Car
                safety_car = handle_safety_car(safety_car, events)

                # Solo cambiar las primeras 3 posiciones
                previous_standings = standings[:3]  # Guardar la vuelta anterior
                if not safety_car:
                    positions = [0, 1, 2]  # Solo los primeros 3
                    random.shuffle(positions)
                    standings[positions[0]], standings[positions[1]] = standings[positions[1]], standings[positions[0]]
                    events.append(f"🔄 Cambio en el top 3: {standings[0]} ahora lidera la carrera")

                # Manejo de pits
                process_pit_stops(standings, events)

                # Obtener comentario generado por OpenAI
                comment = await generate_comment(previous_standings, standings[:3])

                # Obtener dato curioso de Wikipedia sobre el líder
                pilot_info = fetch_pilot_info(standings[0])

                # Construcción del mensaje de salida
                formatted_output = (
                    f"\n=== Vuelta {lap} ===\n"
                    f"⏱️  Tiempo desde inicio: {time.time() - start_time:.1f}s\n"
                    f"🌦️  Clima: {'Lluvia' if local_weather else 'Seco'}\n"
                    f"🚨 Safety Car: {'ACTIVO' if safety_car else 'INACTIVO'}\n\n"
                    f"Top 3:\n"
                )

                for i, driver in enumerate(standings[:3], 1):
                    team = driver.split('(')[1].replace(')', '')
                    formatted_output += f"P{i}: {driver.split('(')[0].strip()} ({team})\n"

                # Comentario generado por OpenAI
                formatted_output += f"\n🗣️ Comentario: {comment}\n"

                # Dato curioso de Wikipedia
                formatted_output += f"\n📌 Dato Curioso: {pilot_info}\n"

                # Enviar la respuesta formateada como un evento SSE
                yield f"data: {json.dumps({'message': formatted_output})}\n\n"

                # Contador regresivo (una sola línea actualizando)
                for i in range(60, 0, -1):
                    yield f"data: {json.dumps({'message': f'⏳ Próxima vuelta en {i} segundos'})}\n\n"
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error en generador: {str(e)}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(race_generator(), media_type="text/event-stream")
