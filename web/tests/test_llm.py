import os
import requests
from unittest.mock import patch, MagicMock

# Importación de la función a testear
from app.llm import generar_itinerario

# Datos de prueba act con lat y long
contexto_base = {
    "ciudad": "Valencia",
    "tipo_turismo": "cultural",
    "duracion_horas": 4,
    "preferencias": "con niños",
    "meteorologia": "soleado, 20°C",
    "lugares": [
        {"nombre": "Ciudad de las Artes", "tipo": "museo", "lat": 39.4536, "lon": -0.3471},
        {"nombre": "Oceanogràfic", "tipo": "acuario", "lat": 39.4529, "lon": -0.3468},
        {"nombre": "Museo de las Ciencias", "tipo": "museo", "lat": 39.4561, "lon": -0.3486}
    ]
}

# Sistema de reporte por terminal
def ejecutar_test(nombre, funcion_test):
    try:
        funcion_test()
        print(f"\033[92m✅ PASÓ\033[0m | {nombre}")
    except AssertionError as e:
        print(f"\033[91m❌ FALLÓ\033[0m | {nombre} -> {str(e)}")
    except Exception as e:
        print(f"\033[91m💥 ERROR\033[0m | {nombre} -> Excepción inesperada: {type(e).__name__}: {str(e)}")

#Teststststs
@patch("app.llm.LLM_MODE", "mock")
def test_1_modo_simulador():
    texto, prompt = generar_itinerario(contexto_base)
    assert "[MODO SIMULACIÓN" in texto, "El texto no indica que es una simulación"
    assert prompt == "[SIMULADOR: sin llamada a modelo]", "El prompt devuelto es incorrecto"

@patch("app.llm.LLM_MODE", "cohere")
@patch.dict(os.environ, {"COHERE_API_KEY": "test_key"})
@patch("app.llm.requests.post")
def test_2_exito_http_200(mock_post):
    mock_respuesta = MagicMock()
    mock_respuesta.status_code = 200
    mock_respuesta.json.return_value = {"message": {"content": [{"text": "Ruta perfecta"}]}}
    mock_post.return_value = mock_respuesta
    
    texto, prompt = generar_itinerario(contexto_base)
    assert "Ruta perfecta" in texto, f"Texto inesperado: {texto}"
    assert "Valencia" in prompt, "El prompt no contiene la ciudad"
    mock_post.assert_called_once()

@patch("app.llm.LLM_MODE", "cohere")
@patch.dict(os.environ, {"COHERE_API_KEY": "test_key"})
@patch("app.llm.requests.post")
def test_3_error_timeout(mock_post):
    mock_post.side_effect = requests.exceptions.Timeout("Timeout")
    try:
        generar_itinerario(contexto_base)
        assert False, "Debería haber lanzado RuntimeError por Timeout"
    except RuntimeError as e:
        assert "tiempo de espera" in str(e).lower() or "timeout" in str(e).lower()

@patch("app.llm.LLM_MODE", "cohere")
@patch.dict(os.environ, {"COHERE_API_KEY": "test_key"})
@patch("app.llm.requests.post")
def test_4_error_401_no_autorizado(mock_post):
    mock_respuesta = MagicMock()
    mock_respuesta.status_code = 401
    mock_post.return_value = mock_respuesta
    try:
        generar_itinerario(contexto_base)
        assert False, "Debería haber lanzado RuntimeError por Error 401"
    except RuntimeError as e:
        assert "no autorizada" in str(e).lower() or "inválida" in str(e).lower()

@patch("app.llm.LLM_MODE", "cohere")
@patch.dict(os.environ, {"COHERE_API_KEY": "test_key"})
@patch("app.llm.requests.post")
def test_5_error_429_limite_peticiones(mock_post):
    mock_respuesta = MagicMock()
    mock_respuesta.status_code = 429
    mock_post.return_value = mock_respuesta
    try:
        generar_itinerario(contexto_base)
        assert False, "Debería haber lanzado RuntimeError por Error 429"
    except RuntimeError as e:
        assert "límite" in str(e).lower() or "excedido" in str(e).lower()

@patch("app.llm.LLM_MODE", "cohere")
@patch.dict(os.environ, {"COHERE_API_KEY": "test_key"})
@patch("app.llm.requests.post")
def test_6_respuesta_vacia(mock_post):
    mock_respuesta = MagicMock()
    mock_respuesta.status_code = 200
    mock_respuesta.json.return_value = {"message": {"content": [{"text": ""}]}}
    mock_post.return_value = mock_respuesta
    try:
        generar_itinerario(contexto_base)
        assert False, "Debería haber lanzado RuntimeError por respuesta vacía"
    except RuntimeError as e:
        assert "vacía" in str(e).lower()

@patch("app.llm.LLM_MODE", "cohere")
@patch.dict(os.environ, {"COHERE_API_KEY": "test_key"})
@patch("app.llm.requests.post")
def test_7_sin_lugares_verificados(mock_post):
    contexto_vacio = contexto_base.copy()
    contexto_vacio["lugares"] = []
    
    mock_respuesta = MagicMock()
    mock_respuesta.status_code = 200
    mock_respuesta.json.return_value = {"message": {"content": [{"text": "Sin lugares"}]}}
    mock_post.return_value = mock_respuesta
    
    texto, prompt = generar_itinerario(contexto_vacio)
    assert "No hay lugares verificados disponibles" in prompt, "El prompt no avisó de la falta de lugares"

@patch("app.llm.LLM_MODE", "cohere")
@patch.dict(os.environ, {"COHERE_API_KEY": ""}, clear=True) 
def test_8_falta_api_key():
    try:
        generar_itinerario(contexto_base)
        assert False, "Debería haber lanzado RuntimeError por falta de API Key"
    except RuntimeError:
        pass 

# NUEVO TEST: Validación estricta de inyección de coordenadas
@patch("app.llm.LLM_MODE", "cohere")
@patch.dict(os.environ, {"COHERE_API_KEY": "test_key"})
@patch("app.llm.requests.post")
def test_9_prompt_contiene_coordenadas(mock_post):
    mock_respuesta = MagicMock()
    mock_respuesta.status_code = 200
    mock_respuesta.json.return_value = {"message": {"content": [{"text": "Ruta generada"}]}}
    mock_post.return_value = mock_respuesta
    
    texto, prompt = generar_itinerario(contexto_base)
    
    # Verificamos que el lugar y sus coordenadas exactas se inyectan en el prompt
    assert "Ciudad de las Artes" in prompt, "El prompt omite el nombre del lugar"
    assert "39.4536" in prompt and "-0.3471" in prompt, "BUG: El prompt omite las coordenadas (lat/lon) a pesar de requerirlas en las instrucciones"


# ==========================================
# EJECUCIÓN DEL SUITE
# ==========================================
if __name__ == "__main__":
    print("\n🚀 INICIANDO BATERÍA DE TESTS (LLM - Cohere)\n" + "-"*50)
    
    ejecutar_test("Modo Simulador activo (LLM_MODE=mock)", test_1_modo_simulador)
    ejecutar_test("Llamada exitosa a Cohere (HTTP 200)", test_2_exito_http_200)
    ejecutar_test("Gestión de error por Timeout", test_3_error_timeout)
    ejecutar_test("Gestión de error de credenciales (HTTP 401)", test_4_error_401_no_autorizado)
    ejecutar_test("Gestión de límite de peticiones (HTTP 429)", test_5_error_429_limite_peticiones)
    ejecutar_test("Gestión de respuesta de texto vacía", test_6_respuesta_vacia)
    ejecutar_test("Inyección de texto cuando no hay lugares", test_7_sin_lugares_verificados)
    ejecutar_test("Excepción si no hay API Key configurada", test_8_falta_api_key)
    ejecutar_test("Inyección de lugares con coordenadas en el prompt", test_9_prompt_contiene_coordenadas)
    
    print("-" * 50 + "\n🎯 TESTS FINALIZADOS\n")