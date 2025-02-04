import os

# 🔹 Mostrar todas las variables de entorno disponibles en Railway
print("🔍 Variables de entorno detectadas en Railway:")
print(os.environ)

# 🔹 Intentar obtener la clave de OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🔹 Verificar si la clave está disponible
if not OPENAI_API_KEY:
    raise ValueError("❌ ERROR: No se encontró la clave de OpenAI. Verifica las variables de entorno en Railway.")

print("✅ Clave de OpenAI encontrada correctamente.")


