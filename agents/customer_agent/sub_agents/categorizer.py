from google.adk.agents import LlmAgent 

import psutil
import json

def get_system_resource_usage():
    """
    Consulta los valores de uso de CPU, RAM y Disco en porcentaje.

    Esta herramienta es ideal para agentes que necesitan monitorear el estado 
    básico de los recursos del sistema en el que se están ejecutando.

    Returns:
        str: Una cadena de texto formateada como JSON que contiene el porcentaje 
            de uso de CPU, RAM y Disco.
            Ejemplo de salida: 
            {"cpu_percent": 25.5, "ram_percent": 40.2, "disk_percent": 75.8}
    """
    print("------------- get_system_resource_usage called ----------------")
    try:
        # 1. Uso de CPU (se recomienda un intervalo para una medición precisa)
        # El intervalo de 1 segundo es bloqueante, pero necesario para una lectura significativa
        cpu_p = psutil.cpu_percent(interval=1) 
        
        # 2. Uso de RAM (Memoria Virtual)
        ram_p = psutil.virtual_memory().percent
        
        # 3. Uso de Disco (Se usa la partición raíz o principal)
        # Nota: En entornos de producción con múltiples discos, es posible que
        # debas iterar sobre psutil.disk_partitions() y verificar el uso de cada uno.
        disk_p = psutil.disk_usage('/').percent
        
        # Creamos el diccionario con los resultados
        resource_data = {
            "cpu_percent": cpu_p,
            "ram_percent": ram_p,
            "disk_percent": disk_p
        }
        print(json.dumps(resource_data))
        # Devolvemos el diccionario serializado como una cadena JSON
        return json.dumps(resource_data)

    except Exception as e:
        # Manejo de errores: Si psutil falla o hay un problema de permisos
        error_data = {
            "error": "Could not retrieve system resources",
            "details": str(e)
        }
        return json.dumps(error_data)

# --- Ejemplo de Uso ---
# print(get_system_resource_usage())

CategorizerAgent = LlmAgent( 
    name= "categorizer" , 
    model= "gemini-2.0-flash" , 
    description= "Un agente que analiza el texto sin procesar de las consultas de los clientes y lo clasifica en una de tres categorías predefinidas" , 
    instruction= """ 
            Eres el Agente Categorizador de Consultas en un flujo de Procesamiento de Consultas de Clientes. 
            Tu tarea es analizar el texto de la consulta proporcionada por el cliente y 
            clasificarlo en una de las tres categorías predefinidas: "Soporte Técnico", "Facturación" o "Consulta General". 
                
            **Entrada** 
                TU ejecutar la herramienta 'get_system_resource_usage' para obtener el uso actual de los recursos del sistema antes de procesar la consulta.
                El usuario proporcionará la Consulta del Cliente. 
                
            **Reglas de Clasificación:** 
                
                Soporte Técnico - Activado por palabras clave/frases: 
                    - internet, red, wifi, conexión, conectividad 
                    - inicio de sesión, contraseña, acceso a la cuenta, autenticación 
                    - software, aplicación, programa, actualización, mejora, instalación 
                    - error, fallo, bloqueo, congelamiento, lentitud, rendimiento, no funciona, roto 
                
                Facturación - Activado por palabras clave/frases: 
                    - factura, facturación, factura, extracto, pago, cargo, tarifa, costo 
                    - reembolso, crédito, disputa, sobrecargo, suscripción, plan 
                    - saldo de cuenta, transacción, compra, cancelación (relacionada con la facturación) 
                
                Consulta general - Categoría predeterminada para: 
                    - Preguntas generales sobre servicios/productos 
                    - Solicitudes de información, comentarios, horario comercial 
                    - Cualquier consulta que no se ajuste claramente a Soporte técnico o Facturación 
                
                Ejemplo: 
                    Consulta del cliente: "Mi internet no funciona después de la actualización, ¡por favor, ayúdenme!" 
                
                Resultado: 
                { 
                    "original_inquiry": "Mi internet no funciona después de la actualización, ¡por favor, ayúdenme!", 
                    "category": "Soporte técnico" 
                } 
                
                Ejemplo: 
                Consulta del cliente: "Me cobraron dos veces mi suscripción, necesito un reembolso" 
                
                Resultado: 
                { 
                    "original_inquiry": "Me cobraron dos veces mi suscripción, necesito un reembolso", 
                    "category":"Facturación" 
                } 
                
                Ejemplo:
                Consulta del cliente: "¿Cuál es su horario comercial?" 
                
                Su respuesta: 
                { 
                    "original_inquiry": "¿Cuál es su horario comercial?", 
                    "category": "Consulta general" 
                } 
                
                Luego de categorizar la consulta, incluye en tu respuesta el uso actual de los recursos del sistema dentro del json en el siguiente formato:
                "metrics_info": "{cpu_percent: XX.X, ram_percent: XX.X, disk_percent: XX.X}"

                IMPORTANTE: Su respuesta completa DEBE ser JSON válido en el formato exacto que se muestra arriba, nada más. """ , 
                tools=[get_system_resource_usage],
                output_key= "category_response" , 
)