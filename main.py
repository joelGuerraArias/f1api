from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import random
import asyncio
import time
import logging
from datetime import datetime
from typing import List

# Configuración inicial
app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("F1-API")

# Datos de pilotos 2025
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

# Helpers
def handle_safety_car(current_status: bool, events: List[str]) -> bool:
    """Gestiona la lógica del Safety Car"""
    if current_status:
        if random.random() < 0.3:  # 30% de probabilidad de retirarlo
            events.append("Safety Car entra a boxes")
            return False
    else:
        if random.random() < 0.15:  # 15% de probabilidad de activarlo
            events.append("Safety Car despliega")
            return True
    return current_status

def process_pit_stops(standings: List[str], events: List[str], safety_car_active: bool):
    """Maneja las entradas a pits"""
    if not safety_car_active:
        for i in range(len(standings)):
            if random.random() < 0.1:  # 10% por piloto
                driver = standings[i]
                new_pos = random.randint(5, len(standings)-1)
                standings.insert(new_pos, standings.pop(i))
                events.append(f"{driver} entra a pits (P{i+1} → P{new_pos+1})")

@app.get("/drivers")
def get_drivers():
    """Obtener lista completa de pilotos"""
    return {"drivers": PILOTS}

@app.post("/set_weather")
def set_weather(raining: bool = Query(...)):
    """Configurar clima manualmente"""
    weather["raining"] = raining
    return {"message": f"Weather set to {'rain' if raining else 'dry'}"}

@app.get("/simulate_race")
async def full_race_simulation():
    """Simulación completa con streaming en tiempo real"""
    async def race_generator():
        try:
            standings = PILOTS.copy()
            random.shuffle(standings)
            local_weather = weather["raining"]
            safety_car = safety_car_status["active"]
            
            for lap in range(1, 11):
                lap_start = time.time()
                events = []
                
                # Cambio de clima
                if random.random() < 0.2:
                    local_weather = not local_weather
                    events.append(f"Cambio de clima a {'lluvia' if local_weather else 'seco'}")
                
                # Safety Car
                safety_car = handle_safety_car(safety_car, events)
                
                # Cambios de posición
                if not safety_car and random.random() < 0.3:
                    pos1, pos2 = random.sample(range(10), 2)
                    standings[pos1], standings[pos2] = standings[pos2], standings[pos1]
                    events.append(f"Cambio de posición: P{pos1+1} ↔ P{pos2+1}")
                
                # Entradas a pits
                process_pit_stops(standings, events, safety_car)
                
                # Construir payload
                payload = {
                    "lap": lap,
                    "standings": standings[:10],
                    "raining": local_weather,
                    "safety_car": safety_car,
                    "events": events,
                    "next_update": f"{60 - (time.time() - lap_start):.1f}s",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                
                # Formato SSE correcto
                yield f"data: {json.dumps(payload)}\n\n"
                
                # Espera precisa
                elapsed = time.time() - lap_start
                await asyncio.sleep(max(60 - elapsed, 0))
                
        except Exception as e:
            logger.error(f"Error en generador: {str(e)}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
            
        finally:
            logger.info("Simulación completada")

    return StreamingResponse(
        race_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/simulate_live")
async def live_race_preview():
    """Versión rápida para pruebas (1 vuelta/segundo)"""
    async def quick_generator():
        standings = PILOTS.copy()
        random.shuffle(standings)
        
        for lap in range(1, 11):
            # Lógica simplificada
            events = []
            if random.random() < 0.2:
                events.append("Evento rápido de prueba")
                
            yield {
                "lap": lap,
                "standings": standings[:10],
                "events": events,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            await asyncio.sleep(1)
            
    return StreamingResponse(
        quick_generator(),
        media_type="application/x-ndjson"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        timeout_keep_alive=300
    )
