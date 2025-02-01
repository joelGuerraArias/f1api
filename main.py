from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import random
import asyncio
import time
from datetime import datetime

app = FastAPI()

# Configurar CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lista de pilotos 2025
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

# Variable global para clima
is_raining = False

@app.get("/")
async def root():
    return {"message": "Bienvenido al simulador F1 2025! Use /docs para la documentación"}

@app.get("/drivers")
def get_drivers():
    """Lista completa de pilotos"""
    return {"drivers": pilots}

@app.post("/set_weather")
def set_weather(raining: bool = Query(..., description="True = lluvia, False = seco")):
    global is_raining
    is_raining = raining
    return {"message": f"Clima actualizado a {'lluvia' if raining else 'seco'}", "raining": is_raining}

@app.get("/simulate_race")
def simulate_race():
    """Simulación rápida de 10 vueltas (para testing)"""
    global is_raining
    standings = pilots.copy()
    random.shuffle(standings)
    race_results = []
    
    for lap in range(1, 11):
        events = []
        
        # Eventos de pits
        for pilot in standings:
            if random.random() < 0.1:
                events.append(f"{pilot} entró a pits")
        
        # Cambios de posición
        if random.random() < 0.3:
            pos1, pos2 = random.sample(range(len(standings)), 2)
            standings[pos1], standings[pos2] = standings[pos2], standings[pos1]
            events.append(f"Cambio entre {standings[pos1]} y {standings[pos2]}")
        
        # Cambio de clima
        if random.random() < 0.2:
            is_raining = not is_raining
        
        race_results.append({
            "lap": lap,
            "standings": standings.copy(),
            "events": events,
            "raining": is_raining,
            "timestamp": datetime.now().isoformat()
        })
    
    return {"race": race_results, "winner": standings[0]}

@app.get("/simulate_live")
async def live_race_simulation():
    """Simulación en tiempo real con duración real (1 minuto/vuelta)"""
    async def generate_race_updates():
        standings = pilots.copy()
        random.shuffle(standings)
        local_raining = is_raining
        
        for lap in range(1, 11):
            lap_start = time.time()
            events = []
            
            # Simular pits
            for pilot in standings:
                if random.random() < 0.1:
                    events.append(f"{pilot} entró a pits en vuelta {lap}")
            
            # Cambios de posición
            if random.random() < 0.3:
                pos1, pos2 = random.sample(range(len(standings)), 2)
                standings[pos1], standings[pos2] = standings[pos2], standings[pos1]
                events.append(f"Posiciones cambiadas: {standings[pos1]} ↔ {standings[pos2]}")
            
            # Cambio de clima
            if random.random() < 0.2:
                local_raining = not local_raining
                events.append(f"Clima cambiado a {'lluvia' if local_raining else 'seco'}")
            
            # Esperar para mantener 1 minuto por vuelta
            elapsed = time.time() - lap_start
            await asyncio.sleep(max(60 - elapsed, 0))
            
            yield {
                "lap": lap,
                "standings": standings.copy(),
                "events": events,
                "raining": local_raining,
                "timestamp": datetime.now().isoformat()
            }
        
        yield {"event": "FINISH", "winner": standings[0]}
    
    return StreamingResponse(generate_race_updates(), media_type="application/json+stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
