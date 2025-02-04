import os
from dotenv import load_dotenv

# 🔹 Cargar variables de entorno
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ ERROR: No se encontró la clave de OpenAI. Verifica las variables de entorno en Railway.")

print("✅ Clave de OpenAI configurada correctamente.")



