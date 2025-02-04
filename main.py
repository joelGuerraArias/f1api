# main.py
import os
import time

# Verificar si la variable está cargada
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

print("🔍 Iniciando verificación...")
print("-----------------------------")

if OPENROUTER_KEY:
    print("✅ OPENROUTER_API_KEY detectada CORRECTAMENTE")
    print(f"📝 Caracteres de la clave: {len(OPENROUTER_KEY)}")
else:
    print("❌ ERROR: OPENROUTER_API_KEY NO detectada")

print("-----------------------------")

# Mantener el contenedor activo para ver logs
while True:
    time.sleep(3600)  # Esperar 1 hora para no saturar



