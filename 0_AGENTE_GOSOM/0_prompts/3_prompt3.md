✅ Prompt 3: Registrar Tareas Completadas en Archivo de Seguimiento (Optimizado)
Objetivo del Agente: Actuar como un agente de IA autónomo para mantener un registro actualizado y consolidado de todas las tareas de mejora que han sido marcadas como [x] Completada en el archivo 0_mejoras.md. El agente debe asegurar la consistencia del formato y la eliminación de entradas duplicadas en el archivo de seguimiento (4_registro_tareas.md).
Instrucciones Detalladas para el Agente:
1.
Acceso y Análisis del Archivo de Origen (0_mejoras.md):
◦
Lee el contenido completo del archivo 0_mejoras.md.
◦
Identifica todas las filas dentro de la sección de la tabla "Estado de las Mejoras" donde la columna "Estado" contenga el valor literal [x] Completada.
◦
Si no se encuentra ninguna tarea completada, notifica este hecho y finaliza la ejecución sin modificar ningún archivo.
2.
Extracción de Detalles de Tareas Completadas:
◦
Para cada tarea identificada en el paso anterior, extrae y almacena los valores de las siguientes columnas de la misma fila de la tabla:
▪
"Título"
▪
"Prioridad"
▪
"Descripción"
▪
"Justificación" (Este campo será utilizado como la "Nota" o "comentario adicional" en el archivo de registro).
◦ 
3.
Gestión y Consolidación del Archivo de Seguimiento (4_registro_tareas.md):
◦
Verifica si el archivo 4_registro_tareas.md existe.
◦
Si el archivo 4_registro_tareas.md NO existe:
▪
Crea el archivo con el nombre especificado.
▪
Añade el encabezado principal: ## 📋 Registro de Tareas Completadas.
▪
Inserta la cabecera de la tabla Markdown: | Título | Prioridad |   | Descripción | Nota |.
▪
Inserta la línea separadora de la tabla Markdown: |--------|-----------|-------|-------------|------|.
◦
Si el archivo 4_registro_tareas.md YA existe:
▪
Lee el contenido completo existente de 4_registro_tareas.md.
▪
Analiza la tabla de registro existente para identificar las tareas que ya han sido documentadas, prestando especial atención a la columna "Título" para la detección de duplicados. Esta capacidad de almacenamiento y recuperación basados en memoria es clave para evitar redundancias.
▪
Prepara una lista de títulos de tareas ya presentes en 4_registro_tareas.md.
4.
Registro de Nuevas Tareas y Prevención de Duplicados:
◦
Para cada tarea extraída en el Paso 2:
▪
Compara su "Título" con la lista de títulos de tareas ya presentes en 4_registro_tareas.md.
▪
Si la tarea NO ha sido registrada previamente:
•
Formatea la información extraída (Título, Prioridad,  , Descripción, Justificación/Nota) como una nueva fila de la tabla Markdown.
•
Añade esta nueva fila al final de la tabla en 4_registro_tareas.md.
▪
Si la tarea YA ha sido registrada, ignórala para evitar la duplicación de entradas.
5.
Formato de las Entradas de la Tabla:
◦
Cada nueva entrada en la tabla de 4_registro_tareas.md debe seguir estrictamente el formato: | [Título de la tarea] | [Prioridad] |  | [Descripción completa] | [Nota/Justificación] |
◦
Asegúrate de que el contenido de cada celda se ajuste dentro de las columnas sin problemas de formato (ej. no incluir saltos de línea dentro de la celda si el Markdown lo interpreta incorrectamente).
6.
Guardado y Confirmación de la Operación:
◦
Guarda todos los cambios realizados en el archivo 4_registro_tareas.md.
◦
Reporta la finalización exitosa de la operación, incluyendo un resumen de cuántas nuevas tareas fueron registradas. En caso de cualquier incidencia o si no se encontraron tareas que registrar, notifica el resultado correspondiente.
Ejemplo de Salida Esperada ( después de la ejecución):
## 📋 Registro de Tareas Completadas

| Título | Prioridad |  | Descripción | Nota |
|--------|-----------|-------|-------------|------|
| Añadir mensajes de error visuales claros | Alta 🚨 | | No hay mensaje visual claro cuando no se carga `parameters_default.json`. | Se añadió `st.error()` en bloque de carga de configuración. |
| Encapsular lógica de st.session_state | Media 🟡 | 2 | La gestión del estado está dispersa y poco legible. | Se encapsuló en una clase `AppState`. |