# main.py
from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# Configurar clave de OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.route('/')
def home():
    return "✅ Servidor activo. Usa /chat para interactuar con Claude"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Verificar clave
        if not OPENROUTER_API_KEY:
            return jsonify({"error": "Clave API no configurada"}), 500
            
        # Obtener mensaje del usuario
        data = request.get_json()
        user_message = data.get('message', 'Hola')
        
        # Configurar solicitud a OpenRouter
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://my-app.railway.app",  # Cambia por tu URL
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "anthropic/claude-3-haiku",
            "messages": [{"role": "user", "content": user_message}]
        }
        
        # Debug: Imprimir en logs de Railway
        print("🔍 Enviando solicitud a OpenRouter...")
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        # Debug: Imprimir estado de la respuesta
        print(f"🔄 Código de estado: {response.status_code}")
        
        return jsonify(response.json())
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)



