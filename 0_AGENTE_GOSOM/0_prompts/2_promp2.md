## ✅ Prompt 2: Ejecutar y Marcar Tarea como Completada

Objetivo del Agente: Actuar como un agente de IA autónomo para identificar, implementar y documentar la completación de la tarea de mejora de más alta prioridad en el proyecto, siguiendo un flujo de trabajo estructurado.

### Instrucciones:
1. Identifica la primera tarea de más alta prioridad con estado `[ ] Pendiente` en `0_mejoras.md`.
    ◦ Lee el contenido completo del archivo 0_mejoras.md.
◦ Identifica la primera tarea en la tabla de "Estado de las Mejoras" que cumpla con ambos criterios:
▪ La columna "Prioridad" contenga el valor "Alta 🚨".
▪ La columna "Estado" contenga el valor literal [ ] Pendiente.

En caso de que múltiples tareas cumplan estos criterios, selecciona la primera tarea encontrada en el orden de aparición en el archivo.
◦
Si no se encuentra ninguna tarea "Alta 🚨" y "Pendiente", notifica este hecho y finaliza la ejecución.

2. Extrae la descripción, sugerencia y archivos afectados de esa tarea.
◦
De la fila de la tarea identificada en el paso anterior, extrae y almacena los valores de las siguientes columnas:
▪"Título"
▪
"Descripción"
▪
"Sugerencia"
▪
"Archivos Afectados"
3. Basándote en la **sugerencia**, genera el código necesario para implementar la mejora.

Utiliza la "Sugerencia" extraída como instrucción fundamental para generar el fragmento de código necesario que implemente la mejora.
◦
Considera el contexto tecnológico implícito por el valor de "Archivos Afectados" (por ejemplo, si es app_streamlit.py, genera código Python compatible con la librería Streamlit). Esta capacidad de generación de código es una de las fortalezas de los agentes de IA.

4. Aplica los cambios en el proyecto Firebase Studio.
Integra el código generado en el(los) archivo(s) especificado(s) en la variable "Archivos Afectados".
◦
Simula la aplicación de estos cambios en el entorno del proyecto Firebase Studio. Esto implica la modificación directa del archivo local. (Para un agente real, esto podría incluir comandos de despliegue o sincronización).
◦
Confirma internamente que la integración del código ha sido exitosa.
5. Vuelve a leer `0_mejoras.md`.
◦
Localiza la fila correspondiente a la tarea en la tabla "Estado de las Mejoras" dentro de 0_mejoras.md.
◦
Modifica el estado de esa tarea de [ ] Pendiente a [x] Completada.
◦
Añade una justificación concisa en la columna "Justificación" de esa misma fila, resumiendo la implementación del código y su impacto (por ejemplo: "Implementación de st.error() en app_streamlit.py para errores de carga de configuración. Probado con éxito en entorno de desarrollo.").
6. Cambia el estado de la tarea seleccionada a `[x] Completada`.
◦
Verifica si existe una sección titulada "Historial de Tareas Realizadas" en 0_mejoras.md. Si no existe, crea esta sección al final del archivo.
◦
Añade una nueva entrada detallada en esta sección, siguiendo estrictamente el formato del "Ejemplo de Salida Esperada" y utilizando la información de la tarea completada:
▪
La línea principal debe ser el Título de la tarea (ej. *   **Añadir mensajes de error visuales claros**).
▪
Debajo, añade la Fecha de Completación en formato AAAA-MM-DD HH:MM (utiliza la fecha y hora actual simulada por el agente).
▪
Incluye una "Nota" detallada que explique lo que se hizo, basándose en la "Sugerencia" original y la implementación del código (ej. "Se añadió st.error() para manejar FileNotFoundError y json.JSONDecodeError durante la carga de parameters_default.json en app_streamlit.py. Esto mejora la retroalimentación al usuario y la usabilidad de la aplicación.").
7. Añade una nueva línea en la sección "Historial de Tareas Realizadas" (si existe) o crea dicha sección.
◦
Guarda todos los cambios realizados en el archivo 0_mejoras.md para persistir la actualización.
Ejemplo de Flujo de Salida Esperada (contenido del  antes y después de la ejecución):
(Fragmento de 0_mejoras.md ANTES de la ejecución, mostrando la tarea pendiente)
## Estado de las Mejoras

| Título | Prioridad | Estado | Descripción | Sugerencia | Criterio | Archivos Afectados | Justificación |
|--------|-----------|--------|-------------|------------|----------|--------------------|---------------|
| Añadir mensajes de error visuales claros | Alta 🚨 | [ ] Pendiente | No hay mensaje visual claro cuando no se carga `parameters_default.json`. | Usar `st.error()` para mostrar mensajes críticos. | UX/UI | `app_streamlit.py` | |
| Encapsular lógica de st.session_state | Media 🟡 | [ ] Pendiente | La lógica de `st.session_state` está dispersa y acoplada. | Crear una clase o funciones dedicadas. | Modularidad/Limpieza de código | `app_streamlit.py` | |
(Fragmento de 0_mejoras.md DESPUÉS de la ejecución, mostrando la tarea completada y el historial)
## Estado de las Mejoras

| Título | Prioridad | Estado | Descripción | Sugerencia | Criterio | Archivos Afectados | Justificación |
|--------|-----------|--------|-------------|------------|----------|--------------------|---------------|
| Añadir mensajes de error visuales claros | Alta 🚨 | [x] Completada | No hay mensaje visual claro cuando no se carga `parameters_default.json`. | Usar `st.error()` para mostrar mensajes críticos. | UX/UI | `app_streamlit.py` | Implementación de `st.error()` en `app_streamlit.py` para errores de carga de configuración. Probado con éxito en entorno de desarrollo. |
| Encapsular lógica de st.session_state | Media 🟡 | [ ] Pendiente | La lógica de `st.session_state` está dispersa y acoplada. | Crear una clase o funciones dedicadas. | Modularidad/Limpieza de código | `app_streamlit.py` | |

## Nuevas Mejoras
- X
- Y

## Historial de Tareas Realizadas

*   **Añadir mensajes de error visuales claros**
    *   **Fecha de Completación:** 2025-06-06 10:30 (o la fecha y hora actual del agente)
    *   **Nota:** Se añadió `st.error()` para manejar `FileNotFoundError` y `json.JSONDecodeError` durante la carga de `parameters_default.json` en `app_streamlit.py`. Esto mejora la retroalimentación al usuario y la usabilidad de la aplicación.
8. Guarda el archivo actualizado.

### Ejemplo de salida esperada:
[ ] Añadir mensajes de error visuales claros  
Prioridad: Alta 🚨  
Descripción: No hay mensaje visual claro cuando no se carga `parameters_default.json`.  
Sugerencia: Usar `st.error()` para mostrar mensajes críticos.  
Criterio: UX/UI  
Archivos Afectados: `app_streamlit.py`  

[x] Añadir mensajes de error visuales claros  
Fecha de Completación: 2025-06-06 10:30  
Nota: Se añadió `st.error()` en bloque de carga de configuración.
