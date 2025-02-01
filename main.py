from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import random
import asyncio
import time
from datetime import datetime

app = FastAPI()

# Lista completa de pilotos 2025
pilots = [
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

@app.get("/simulate_race")
async def race_simulation():
    """Simulación de carrera con actualizaciones cada 1 minuto por vuelta"""
    async def race_generator():
        standings = pilots.copy()
        random.shuffle(standings)
        is_raining = False
        safety_car = False
        lap_count = 0
        
        while lap_count < 10:
            start_time = time.time()
            events = []
            lap_count += 1

            # Cambios de clima (20% probabilidad)
            if random.random() < 0.2:
                is_raining = not is_raining
                events.append(f"Cambio de clima: {'Lluvia' if is_raining else 'Seco'}")

            # Safety Car (15% probabilidad de salir, 30% de retirarse si está activo)
            if safety_car:
                if random.random() < 0.3:
                    safety_car = False
                    events.append("Safety Car entra a boxes")
            else:
                if random.random() < 0.15:
                    safety_car = True
                    events.append("Safety Car despliega")

            # Cambios de posición (30% probabilidad)
            if random.random() < 0.3 and not safety_car:
                pos1, pos2 = random.sample(range(10), 2)
                standings[pos1], standings[pos2] = standings[pos2], standings[pos1]
                events.append(f"Cambio de posición: P{pos1+1} ↔ P{pos2+1}")

            # Entradas a pits (10% por piloto)
            for i in range(10):
                if random.random() < 0.1 and not safety_car:
                    events.append(f"{standings[i]} entra a pits")
                    new_pos = random.randint(5, 19)
                    standings.insert(new_pos, standings.pop(i))

            # Esperar 1 minuto real
            elapsed = time.time() - start_time
            await asyncio.sleep(max(60 - elapsed, 0))

            yield {
                "lap": lap_count,
                "standings": standings[:10],  # Solo top 10
                "raining": is_raining,
                "safety_car": safety_car,
                "events": events,
                "next_update": f"{(60 - elapsed):.1f}s" if elapsed < 60 else "0s",
                "timestamp": datetime.now().isoformat()
            }

    return StreamingResponse(race_generator(), media_type="application/json")

@app.get("/drivers")
def get_all_drivers():
    """Obtener lista completa de pilotos"""
    return {"drivers": pilots}
