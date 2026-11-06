import os
import requests
from unittest.mock import patch, MagicMock

# Importación corregida a nivel de app
from app.llm import generar_itinerario

#Datos de Prueba
contexto_base = {
    "ciudad": "Valencia",
    "tipo_turismo": "cultural",
    "duracion_horas": 4,
    "preferencias": "con niños",
    "meteorologia": "soleado, 20°C",
    "lugares": [
        {"nombre": "Ciudad de las Artes", "tipo": "museo"},
        {"nombre": "Oceanogràfic", "tipo": "acuario"},
        {"nombre": "Museo de las Ciencias", "tipo": "museo"}
    ]
}

#Impresión por terminal
def ejecutar_test(nombre, funcion_test):
    try:
        funcion_test()
        print(f"\033[92m✅ PASÓ\033[0m | {nombre}")
    except AssertionError as e:
        print(f"\033[91m❌ FALLÓ\033[0m | {nombre} -> {str(e)}")
    except Exception as e:
        print(f"\033[91m💥 ERROR\033[0m | {nombre} -> Excepción inesperada: {type(e).__name__}: {str(e)}")

#Test que prueban llm.py
@patch("app.llm.LLM_MODE", "mock")
def test_1_modo_simulador():
    texto, prompt = generar_itinerario(contexto_base)
    assert "[MODO SIMULACIÓN" in texto, "El texto no indica que es una simulación"
    assert prompt == "[SIMULADOR: sin llamada a modelo]", "El prompt devuelto es incorrecto"

@patch("app.llm.LLM_MODE", "cohere")
@patch.dict(os.environ, {"COHERE_API_KEY": "test_key"})
@patch("app.llm.requests.post") # Corregido el path del mock
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
    texto, _ = generar_itinerario(contexto_base)
    assert "tiempo de espera" in texto.lower() or "timeout" in texto.lower(), "No se manejó el timeout correctamente"

@patch("app.llm.LLM_MODE", "cohere")
@patch.dict(os.environ, {"COHERE_API_KEY": "test_key"})
@patch("app.llm.requests.post")
def test_4_error_401_no_autorizado(mock_post):
    mock_respuesta = MagicMock()
    mock_respuesta.status_code = 401
    mock_post.return_value = mock_respuesta
    texto, _ = generar_itinerario(contexto_base)
    assert "no autorizada" in texto.lower() or "inválida" in texto.lower(), "No se manejó el error 401"

@patch("app.llm.LLM_MODE", "cohere")
@patch.dict(os.environ, {"COHERE_API_KEY": "test_key"})
@patch("app.llm.requests.post")
def test_5_error_429_limite_peticiones(mock_post):
    mock_respuesta = MagicMock()
    mock_respuesta.status_code = 429
    mock_post.return_value = mock_respuesta
    texto, _ = generar_itinerario(contexto_base)
    assert "límite" in texto.lower() or "excedido" in texto.lower(), "No se manejó el error 429"

@patch("app.llm.LLM_MODE", "cohere")
@patch.dict(os.environ, {"COHERE_API_KEY": "test_key"})
@patch("app.llm.requests.post")
def test_6_respuesta_vacia(mock_post):
    mock_respuesta = MagicMock()
    mock_respuesta.status_code = 200
    mock_respuesta.json.return_value = {"message": {"content": [{"text": ""}]}}
    mock_post.return_value = mock_respuesta
    texto, _ = generar_itinerario(contexto_base)
    assert "vacía" in texto.lower() or "error" in texto.lower(), "No se manejó la respuesta vacía"

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

#Ejecución de tests con corrección de color 
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
    
    print("-" * 50 + "\n🎯 TESTS FINALIZADOS\n")