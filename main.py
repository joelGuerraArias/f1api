from fastapi import FastAPI, Query
import random

app = FastAPI()

# Lista de pilotos de ejemplo (actualízala con los de 2025)
pilots = [
    "Max Verstappen",
    "Charles Leclerc",
    "Lewis Hamilton",
    "Fernando Alonso",
    "Lando Norris",
    "Sergio Pérez",
    "Carlos Sainz",
    "George Russell",
    "Oscar Piastri",
    "Esteban Ocon",
    "Pierre Gasly",
    "Yuki Tsunoda",
    "Daniel Ricciardo",
    "Kevin Magnussen",
    "Nico Hülkenberg",
    "Valtteri Bottas",
    "Zhou Guanyu",
    "Alexander Albon",
    "Logan Sargeant",
    "Liam Lawson"
]

# Variable global para la condición climática
is_raining = False

@app.get("/drivers")
def get_drivers():
    """Listar todos los pilotos disponibles."""
    return {"drivers": pilots}

@app.post("/set_weather")
def set_weather(raining: bool = Query(..., description="Indica si está lloviendo (true) o no (false).")):
    """Configurar manualmente la condición climática."""
    global is_raining
    is_raining = raining
    return {"message": "Condición climática actualizada.", "raining": is_raining}

@app.get("/simulate_race")
def simulate_race():
    """Simular una carrera completa de 10 vueltas."""
    global is_raining

    # Orden inicial de los pilotos
    standings = pilots.copy()
    random.shuffle(standings)

    # Resultados por vuelta
    race_results = []

    for lap in range(1, 11):
        events = []

        # Simular entradas a pits (10% de probabilidad por piloto)
        for i, pilot in enumerate(standings):
            if random.random() < 0.1:
                events.append(f"{pilot} entra a pits en la vuelta {lap}.")

        # Cambios de posición aleatorios
        if random.random() < 0.3:  # 30% de probabilidad de cambio de posiciones
            pos1, pos2 = random.sample(range(len(standings)), 2)
            standings[pos1], standings[pos2] = standings[pos2], standings[pos1]
            events.append(f"{standings[pos2]} intercambia posición con {standings[pos1]}.")

        # Guardar los resultados de la vuelta
        race_results.append({
            "lap": lap,
            "raining": is_raining,
            "standings": standings.copy(),
            "events": events
        })

        # Cambiar la condición climática (20% de probabilidad por vuelta)
        if random.random() < 0.2:
            is_raining = not is_raining

    # Resultado final
    return {
        "race_results": race_results,
        "winner": standings[0]
    }

@app.get("/simulate_lap")
def simulate_lap(current_standings: list[str] = Query(..., description="Posiciones actuales de los pilotos.")):
    """Simular una sola vuelta."""
    global is_raining

    events = []

    # Convertir las posiciones actuales a una lista mutable
    standings = current_standings.copy()

    # Simular entradas a pits (10% de probabilidad por piloto)
    for i, pilot in enumerate(standings):
        if random.random() < 0.1:
            events.append(f"{pilot} entra a pits.")

    # Cambios de posición aleatorios
    if random.random() < 0.3:  # 30% de probabilidad de cambio de posiciones
        pos1, pos2 = random.sample(range(len(standings)), 2)
        standings[pos1], standings[pos2] = standings[pos2], standings[pos1]
        events.append(f"{standings[pos2]} intercambia posición con {standings[pos1]}.")

    # Cambiar la condición climática (20% de probabilidad por vuelta)
    if random.random() < 0.2:
        is_raining = not is_raining

    return {
        "standings": standings,
        "raining": is_raining,
        "events": events
    }
