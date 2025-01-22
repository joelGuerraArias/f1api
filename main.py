from fastapi import FastAPI, Query
import random
import time
from datetime import datetime

app = FastAPI()

# Lista de pilotos y equipos para la temporada 2025
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

# Variable global para la condición climática
is_raining = False

@app.get("/drivers")
def get_drivers():
    """Listar todos los pilotos disponibles."""
    print("GET /drivers llamado")
    return {"drivers": pilots}

@app.post("/set_weather")
def set_weather(raining: bool = Query(..., description="Indica si está lloviendo (true) o no (false).")):
    """Configurar manualmente la condición climática."""
    global is_raining
    is_raining = raining
    print(f"POST /set_weather llamado - Raining: {is_raining}")
    return {"message": "Condición climática actualizada.", "raining": is_raining}

@app.get("/simulate_race")
def simulate_race():
    """Simular una carrera completa de 10 vueltas con contador de tiempo."""
    global is_raining

    # Orden inicial de los pilotos
    standings = pilots.copy()
    random.shuffle(standings)

    # Resultados por vuelta
    race_results = []

    for lap in range(1, 11):
        start_time = datetime.now()
        events = []

        # Log para la vuelta actual
        print(f"\n--- Iniciando vuelta {lap} ---")

        # Mostrar las 5 primeras posiciones y el estado del clima
        top_5 = standings[:5]
        print(f"Vuelta {lap}: Top 5 posiciones: {top_5}")
        print(f"Clima: {'Lluvia' if is_raining else 'Seco'}")

        # Simular entradas a pits (10% de probabilidad por piloto)
        for i, pilot in enumerate(standings):
            if random.random() < 0.1:
                event = f"{pilot} entra a pits en la vuelta {lap}."
                events.append(event)
                print(event)

        # Cambios de posición aleatorios
        if random.random() < 0.3:  # 30% de probabilidad de cambio de posiciones
            pos1, pos2 = random.sample(range(len(standings)), 2)
            standings[pos1], standings[pos2] = standings[pos2], standings[pos1]
            event = f"{standings[pos2]} intercambia posición con {standings[pos1]}."
            events.append(event)
            print(event)

        # Simular distancia entre pilotos
        distances = {pilot: round(random.uniform(0.5, 5.0), 2) for pilot in standings}
        print(f"Distancias entre pilotos: {distances}")

        # Cambiar la condición climática (20% de probabilidad por vuelta)
        if random.random() < 0.2:
            is_raining = not is_raining
            print(f"Cambio de clima: {'Lluvia' if is_raining else 'Seco'}")

        # Duración de la vuelta
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Guardar los resultados de la vuelta
        race_results.append({
            "lap": lap,
            "raining": is_raining,
            "standings": standings.copy(),
            "events": events,
            "distances": distances,
            "lap_duration_seconds": duration
        })

    # Log para resultados finales
    print("\n--- Fin de la carrera ---")
    print(f"Ganador: {standings[0]}")
    return {
        "race_results": race_results,
        "winner": standings[0]
    }
