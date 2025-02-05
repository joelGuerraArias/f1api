from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import wikipediaapi
import random
import asyncio
import time
import os
import json
from dotenv import load_dotenv
from openai import AsyncOpenAI

# 🔹 Cargar variables de entorno
load_dotenv()

# 🔹 Obtener clave de OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ ERROR: No se encontró la clave de OpenAI. Verifica las variables de entorno.")

# 🔹 Inicializar el cliente asíncrono de OpenAI (nueva versión)
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# 🔹 Inicialización de la API FastAPI
app = FastAPI()

# 🔹 Configurar CORS (ajusta para producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia "*" por tu dominio en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Lista de pilotos 2025
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

# 🔹 Estado global
weather = {"raining": False}
safety_car_status = {"active": False}

# 🔹 Función para manejar el Safety Car
def handle_safety_car(current_status, events):
    if current_status:
        if random.random() < 0.3:
            events.append("🚨 Safety Car entra a boxes")
            return False
    else:
        if random.random() < 0.15:
            events.append("🚨 Safety Car despliega en la pista")
            return True
    return current_status

# 🔹 Función para manejar pits
def process_pit_stops(standings, events):
    for i in range(len(standings)):
        if random.random() < 0.1:
            driver = standings[i]
            new_pos = random.randint(5, len(standings) - 1)
            standings.insert(new_pos, standings.pop(i))
            events.append(f"🛠️ {driver} entra a pits (P{i+1} → P{new_pos+1})")

# 🔹 Función asíncrona para generar un comentario con OpenAI
async def generate_commentary(lap, top_3, raining):
    prompt = f"""
Genera un comentario en español sobre la vuelta {lap} en una carrera de F1.
El clima es {'lluvia' if raining else 'seco'}.
Los tres primeros lugares son:
1. {top_3[0]}
2. {top_3[1]}
3. {top_3[2]}
Menciona un dato interesante sobre la carrera sin repetir información básica.
    """
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        # Imprime el error para facilitar la depuración
        print("Error generando comentario:", e)
        return "No se pudo generar un comentario para esta vuelta."

# 🔹 Función para obtener un dato curioso de Wikipedia
def get_pilot_fact(driver):
    wiki = wikipediaapi.Wikipedia(language="es", user_agent="F1RaceSim/1.0 (autosemana@gmail.com)")
    pilot_name = driver.split("(")[0].strip()
    page = wiki.page(pilot_name)
    if page.exists():
        # Verifica si el resumen sugiere una página de desambiguación
        if "puede referirse a" in page.summary:
            return f"📌 No se encontró un dato específico para {pilot_name}. La página parece ser de desambiguación."
        else:
            summary = page.summary
            if len(summary) > 500:
                summary = summary[:500] + "..."
            return f"📌 Dato curioso: {summary}"
    return f"📌 No se encontró información para {pilot_name} en Wikipedia."

@app.get("/simulate_race")
async def full_race_simulation():
    """Simulación de carrera con comentarios AI y datos curiosos"""
    async def race_generator():
        try:
            standings = PILOTS.copy()
            random.shuffle(standings)
            local_weather = weather["raining"]
            safety_car = safety_car_status["active"]
            start_time = time.time()

            for lap in range(1, 6):  # Simula 5 vueltas
                events = []

                # Cambio de clima con 20% de probabilidad
                if random.random() < 0.2:
                    local_weather = not local_weather
                    events.append(f"🌦️ Cambio de clima a {'lluvia' if local_weather else 'seco'}")

                # Manejo del Safety Car
                safety_car = handle_safety_car(safety_car, events)

                # Cambiar posiciones en el top 3 solo si no hay Safety Car
                if not safety_car:
                    positions = [0, 1, 2]
                    random.shuffle(positions)
                    standings[positions[0]], standings[positions[1]] = standings[positions[1]], standings[positions[0]]
                    events.append(f"🔄 Cambio en el top 3: {standings[0]} ahora lidera la carrera")

                # Manejo de pits
                process_pit_stops(standings, events)

                # Generar comentario AI y obtener dato curioso de Wikipedia
                commentary = await generate_commentary(lap, standings[:3], local_weather)
                fact = get_pilot_fact(standings[0])

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

                if events:
                    formatted_output += "\nEventos:\n" + "\n".join(f"• {event}" for event in events)
                else:
                    formatted_output += "\nSin eventos destacados\n"

                formatted_output += f"\n📢 {commentary}\n{fact}\n"
                formatted_output += f"\nPróxima actualización en: 60.0s\n" + "-" * 50

                yield f"data: {json.dumps({'message': formatted_output})}\n\n"

                # Contador regresivo: envía un mensaje cada segundo
                for i in range(60, 0, -1):
                    countdown_message = f"data: {json.dumps({'message': f'⏳ Próxima vuelta en {i} segundos'})}\n\n"
                    yield countdown_message
                    await asyncio.sleep(1)

        except Exception as e:
            print("Error en la simulación de la carrera:", e)
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(race_generator(), media_type="text/event-stream")
