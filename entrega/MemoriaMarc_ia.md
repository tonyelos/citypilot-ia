Las tecnologías de inteligencia artificial que has utilizado en esta memoria se dividen en dos categorías (planificación e implementación técnica):

1. **Gemini 3.1 Pro:** Utilizada como herramienta de **gestión y planificación**. Te sirvió para analizar el alcance del proyecto y estructurar el trabajo dividiéndolo de forma lógica en tres fases/roles individuales.
2. **Cohere (API Chat v2):** Utilizada como el **motor lógico (LLM) integrado** en tu código (`llm.py`). Se encarga de procesar el contexto (ciudad, clima, preferencias y coordenadas) para generar rutas de viaje dinámicas, con instrucciones estrictas (Prompt Engineering) para evitar alucinaciones.

A continuación, tienes la versión mejorada de tu memoria. Se ha estructurado con un formato mucho más profesional, utilizando terminología técnica adecuada (como *Prompt Engineering*, *Mocking* y *Manejo de Excepciones*) para que destaque como documentación de un proyecto de software:

---

# Memoria de Inteligencia Artificial: CityPilot-IA (Estudiante 2)

En este documento se detalla la implementación técnica y el uso de Inteligencia Artificial en el proyecto **CityPilot-IA** por parte del Estudiante 2. Se describen los procedimientos, el diseño de la integración del modelo de lenguaje, las correcciones iterativas realizadas tras la revisión de código (PR) y los resultados obtenidos.

### Datos del Proyecto

* **Estudiante:** Marc Joan Rodríguez López (Estudiante 2)
* **Equipo:** Yiao Tang, Luis Wesigner
* **Repositorio GitHub:** [citypilot-ia/tree/main](https://github.com/tonyelos/citypilot-ia/tree/main)
* **Archivos implementados:** `llm.py` y `test_llm.py`
* **Estado de las pruebas:** `test_llm.py` ejecutado con resultado satisfactorio.

---

## 1. Planificación Asistida por IA

El primer uso de Inteligencia Artificial en el ciclo de vida del proyecto fue en la fase de organización. Se utilizó **Gemini 3.1 Pro** para analizar los requisitos globales y estructurar el desarrollo en tres fases individuales y equilibradas.

Fruto de esta división, el rol asignado al **Estudiante 2** se centró exclusivamente en la **implementación de la Inteligencia Artificial** dentro de la aplicación, dotando al sistema de capacidad de decisión lógica.

## 2. Implementación del Modelo de Lenguaje (`llm.py`)

Esta tarea fue fundamental para dotar de inteligencia al orquestador, asegurando que el modelo trabaje estrictamente sobre datos reales y validados, mitigando el riesgo de alucinaciones.

### 2.1. Integración de la API y Entorno

* **Llamada HTTP:** Se implementó una conexión directa a la API de **Cohere Chat v2** mediante peticiones HTTP.
* **Entorno Mock:** Para optimizar recursos y no consumir cuota de la API durante el desarrollo, se configuró la variable de entorno `LLM_MODE=mock`. Esto permitió probar el flujo de la aplicación simulando las respuestas del modelo.

### 2.2. Diseño del Prompt (Prompt Engineering)

El sistema requiere un nivel alto de precisión, por lo que el prompt enviado a Cohere se diseñó con las siguientes variables y restricciones:

* **Contexto dinámico:** Se inyecta la ciudad, las preferencias del usuario, la duración del viaje, el clima actual y la lista de destinos verificados junto con sus coordenadas geográficas exactas.
* **Reglas estrictas:**
1. Generar una ruta razonada y lógica de 3 a 5 paradas.
2. Adaptar las sugerencias a las condiciones climáticas actuales.
3. **Prohibición explícita:** El modelo no puede inventar lugares ni asegurar que un establecimiento está abierto si no existe validación previa en los datos proporcionados.



## 3. Evolución, Revisión de Código (PR) y Corrección de Errores

Tras la primera iteración y la revisión (Pull Request), se detectaron y corrigieron los siguientes problemas críticos para garantizar la robustez del sistema:

* **Corrección de inyección de contexto (Bug de escritura):** En la línea 25 de `llm.py` se utilizaba la clave `contexto.get("lugare", [])` en lugar de `"lugares"`. Esto provocaba que el prompt siempre recibiera una lista vacía y respondiera que "No hay lugares verificados disponibles". Se corrigió para que el modelo reciba correctamente los puntos de interés.
* **Precisión geoespacial:** En la versión inicial, el prompt omitía las coordenadas de los destinos. Se actualizó la estructura de los datos enviados para incluir la latitud y longitud de cada lugar, permitiendo al modelo calcular y proponer rutas espacialmente coherentes.
* **Manejo de Excepciones HTTP:** Anteriormente, los errores de la API de Cohere (401 No Autorizado, 409 Conflicto, 429 Demasiadas Peticiones) se devolvían como cadenas de texto. El orquestador los interpretaba con un `estado=ok`, propagando el error en el flujo de la aplicación. Se implementó un manejo de excepciones adecuado que captura estos códigos HTTP, interrumpiendo el flujo incorrecto y permitiendo una recuperación o notificación clara al usuario.

## 4. Pruebas y Aseguramiento de Calidad (`test_llm.py`)

Para garantizar que los errores documentados no vuelvan a ocurrir, se implementaron pruebas automatizadas (`test_llm.py`):

* Se verifica que el modelo solo reciba y procese lugares que existen realmente en el contexto.
* Se valida que las coordenadas asociadas a cada lugar se están enviando correctamente al prompt.

## 5. Conclusiones

La implementación final de `llm.py` es robusta y tolerante a fallos. Gracias a la iteración sobre el prompt y a la correcta gestión de los errores de red de la API de Cohere, el sistema actual genera rutas precisas, coherentes con el clima y libres de alucinaciones, cumpliendo con los objetivos de inteligencia artificial del proyecto.