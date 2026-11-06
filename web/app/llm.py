"""Adaptador Cohere. El PROMPT lo redacta el alumnado."""
import os
import requests

LLM_MODE = os.getenv("LLM_MODE", "mock").lower()
COHERE_MODEL = os.getenv("COHERE_MODEL", "command-r7b-12-2024")


def generar_itinerario(contexto: dict) -> tuple[str, str]:
    """Devuelve (texto_itinerario, prompt_usado).
    `contexto` incluye: ciudad, tipo_turismo, duracion_horas,
    preferencias, meteorologia y lista de lugares REALES de la fuente.
    """
    if LLM_MODE == "mock":
        return _simulador(contexto), "[SIMULADOR: sin llamada a modelo]"

    if LLM_MODE != "cohere":
        raise ValueError("LLM_MODE debe ser 'mock' o 'cohere'")

    api_key = os.getenv("COHERE_API_KEY", "")
    if not api_key:
        raise RuntimeError("Falta COHERE_API_KEY (pedirla al docente)")

    # Preparacion de lista de lugares verificados para el prompt
    lugares_disponibles = contexto.get("lugares", [])
    if not lugares_disponibles:
        texto_lugares = "No hay lugares verificados disponibles en este momento."    
    else:
        texto_lugares = "\n".join([f"- {lugar.get('nombre', 'Desconocido')} (Tipo: {lugar.get('tipo', 'N/A')}) - Lat: {lugar.get('lat', 'N/A')}, Lon: {lugar.get('lon', 'N/A')}" for lugar in lugares_disponibles])

    # Diseño de Prompt [Ayuda de Gemini 3.8 Pro]
    prompt = f"""Eres un asistente de turismo experto. Tu ÚNICA tarea es diseñar un itinerario lógico y atractivo con los siguientes datos:
- Ciudad: {contexto.get('ciudad', 'Desconocida')}
- Tipo de turismo: {contexto.get('tipo_turismo', 'general')}
- Duración disponible: {contexto.get('duracion_horas', 2)} horas
- Preferencias adicionales: {contexto.get('preferencias', 'Ninguna')}
- Condiciones meteorológicas actuales: {contexto.get('meteorologia', 'Desconocidas')}

    Lugares Verificados Disponibles (con latitud y longitud):{texto_lugares}

    REGLAS ESTRICTAS QUE DEBES CUMPLIR:
    1. Selecciona entre 3 y 5 paradas exclusivamente de la lista de 'LUGARES VERIFICADOS DISPONIBLES'.
    2. Para cada parada del itinerario, DEBES incluir explícitamente sus coordenadas (latitud y longitud).
    3. Justifica el itinerario adaptándolo a las 'Condiciones meteorológicas actuales'.
    4. NO inventes lugares, monumentos, restaurantes, ni horarios de apertura bajo ninguna circunstancia.
    5. Si la lista de lugares está vacía o tiene menos de 3 opciones, indícalo claramente al usuario y haz lo mejor que puedas con lo que hay.
    """

    # Llamada HTTP a Cohere Chat V2
    url = "https://api.cohere.com/v2/chat"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "model": COHERE_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        respuesta = requests.post(url, headers=headers, json=payload, timeout=15)

        # Gestionar errores HTTP específicos lanzando EXCEPCIONES SOLICITADAS (R-PR1) (RuntimeError)
        if respuesta.status_code == 401:
            raise RuntimeError("Error 401: Clave API de Cohere inválida o no autorizada.")
        elif respuesta.status_code == 429:
            raise RuntimeError("Error 429: Se ha excedido el límite de peticiones al modelo. Intenta más tarde.")
        
        # Lanza request.exceptions.HTTPError para otros códigos HTTP (500, etc.)
        respuesta.raise_for_status() 
        
        datos_json = respuesta.json()

        # Extraer texto devuelto de Cohere V2
        texto_generado = datos_json.get("message", {}).get("content", [{}])[0].get("text", "")
        
        if not texto_generado:
             raise RuntimeError("Error: El modelo devolvió una respuesta vacía.")
             
        return texto_generado, prompt

    # Las excepciones ahora se propagan adecuadamente para que el orquestador actúe (ej: devolviendo 502)
    except requests.exceptions.Timeout:
        raise RuntimeError("Error: Se agotó el tiempo de espera al consultar al modelo (timeout).")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error de conexión con la API: {str(e)}")



def _simulador(contexto: dict) -> str:

    """Salida no generativa para pruebas y para cuando no hay credenciales."""
    lugares = contexto.get("lugares") or []
    ciudad = contexto.get("ciudad", "la ciudad")
    tipo = contexto.get("tipo_turismo", "libre")
    nombres = [x.get("nombre", "Lugar sin nombre") for x in lugares[:4]]
    visitas = "\n".join(f"{i}. {nombre}" for i, nombre in enumerate(nombres, 1))
    if not visitas:
        visitas = "No hay lugares verificados disponibles."
    return f"[MODO SIMULACIÓN - NO ES IA]\nPlan {tipo} en {ciudad}:\n{visitas}"