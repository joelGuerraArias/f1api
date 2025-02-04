# main.py
import os

api_key = os.getenv("OPENROUTER_API_KEY")

print("🔍 Prueba de variable OPENROUTER_API_KEY:")
print("----------------------------------------")

if api_key:
    # Muestra solo los primeros 6 y últimos 4 caracteres por seguridad
    masked_key = f"{api_key[:6]}...{api_key[-4:]}"
    print(f"✅ Clave detectada: {masked_key}")
    print(f"📌 Longitud total: {len(api_key)} caracteres")
else:
    print("❌ ERROR: Clave NO detectada")

print("----------------------------------------")

# Mantener el contenedor activo para ver logs
while True:
    pass



