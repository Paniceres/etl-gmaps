# 🚀✨ Agente GOSOM ETL: Interfaz de Usuario Streamlit y Código Fuente 📊🤖

¡Bienvenido a la documentación completa de la interfaz de usuario para el **Agente GOSOM ETL**! 🎉 Este documento unifica la especificación detallada de cómo funciona nuestra UI construida con Streamlit y el código fuente que la hace posible. Su objetivo es proporcionar una herramienta visual y sencilla para configurar, ejecutar, monitorear y analizar las tareas de scraping de Google Maps.

---

## 🗺️ Layout General de la Aplicación

La interfaz de usuario está organizada para facilitar la navegación y el uso:

*   ➡️ **Barra Lateral (Sidebar):** 🖱️ El centro de control interactivo donde el usuario define y ajusta los parámetros de la tarea de scraping antes de iniciarla.
*   🖥️ **Área Principal (Main Area):** 👀 La sección principal para mostrar el progreso de la ejecución, los logs detallados, las tablas de datos crudos y procesados, y los resúmenes con estadísticas y gráficos una vez que la tarea ha finalizado.

---

## 🧩 Funcionalidades y Componentes Clave

Cada elemento de la UI ha sido diseñado pensando en la eficiencia y la claridad:

### 1️⃣ Configuración de la Tarea de Scraping (Barra Lateral ➡️)

Esta sección guía al usuario en la preparación de cada nueva tarea de extracción:

*   ✨ **Título:** Visible como "⚙️ Configurar Nueva Tarea de Scraping" en la parte superior de la barra lateral.
*   📍 **Selección de Ciudad(es):**
    *   Tipo: `st.multiselect`. Permite seleccionar una o múltiples ubicaciones geográficas simultáneamente.
    *   Label: "**Seleccionar Ciudad(es) a Procesar**".
    *   Opciones: 🏙️ Se cargan dinámicamente a partir de las claves del diccionario `GMAPS_COORDINATES`, típicamente definido en `parameters_default.json` (ej. "neuquen", "general_roca", "allen", "cipolletti").
*   📝 **Gestión de Keywords por Ciudad:**
    *   Aparece condicionalmente solo si hay ciudades seleccionadas en el multiselect.
    *   ➡️ Por cada ciudad seleccionada, se muestra un `st.text_area` dedicado.
    *   Label: "✏️ **Keywords para [Nombre de la Ciudad]**".
    *   Contenido Inicial: Se precarga leyendo las palabras clave del archivo `keywords_<ciudad>.csv` asociado. Los usuarios pueden editar, añadir o eliminar keywords libremente.
    *   *💾 Función Opcional (Pendiente):* La capacidad de guardar las modificaciones realizadas en el `st.text_area` de vuelta al archivo CSV original (`keywords_<ciudad>.csv`).
*   🔢 **Profundidad de Búsqueda (`depth`):**
    *   Tipo: `st.number_input`. Proporciona un control claro para establecer el nivel de profundidad del scraping.
    *   Label: "🎯 **Profundidad de Búsqueda**".
    *   Valor por defecto: Se obtiene del parámetro `DEFAULT_DEPTH` configurado en `parameters_default.json`.
    *   Rango: Usualmente de 1 a 20, pero configurable según la necesidad del proyecto.
*   📧 **Activar Extracción de Emails:**
    *   Tipo: `st.checkbox`. Permite activar o desactivar la funcionalidad de búsqueda de emails.
    *   Label: "¿**Extraer Emails? (⚠️ Puede tardar más)**".
    *   Valor por defecto: Establecido como `True` por requisito.
*   ▶️ **Botón de Inicio:**
    *   Tipo: `st.button`. El activador principal de la tarea de scraping y procesamiento.
    *   Label: "🚀 **Iniciar Scraping**". Al hacer clic, se valida la configuración y se inicia la ejecución de la lógica de backend.

### 2️⃣ Monitoreo del Progreso (Área Principal 🖥️)

Mantener al usuario informado durante la ejecución es fundamental para una buena experiencia:

*   📰 **Título de la Sección:** "⏳ Progreso de la Tarea".
*   🔄 **Indicador de Actividad:** Se utiliza `st.spinner("⚙️ Scraping y procesamiento en progreso...")` para ofrecer un feedback visual mientras las operaciones están activas.
*   📜 **Registro de Proceso (Implementación Actual):**
    *   Una vez que la simulación o la ejecución real del proceso de scraping finaliza, se carga y muestra el contenido del archivo de log `agent_gmaps_mvp.log`.
    *   Se presentan las últimas 100 líneas del log (o todo el contenido si es menor) utilizando `st.code` o `st.text_area` dentro de esta sección.
    *   *Ideal (Opcional Avanzado):* ⏱️ Implementar la visualización de los logs en tiempo casi real si la ejecución del subproceso lo permite sin bloquear la UI.
*   📈 **Barra de Progreso (Opcional Avanzado):** Podría añadirse si es posible estimar la cantidad total de tareas o pasos a realizar.

### 3️⃣ Visualización de Resultados (Área Principal 🖥️)

Esta sección permite explorar y descargar los datos obtenidos y procesados. Podría organizarse usando `st.tabs` para una mejor navegación:

*   📊 **Título de la Sección:** "📈 Visualización de Resultados".
*   📉 **Pestaña/Sección: Datos Crudos (por ciudad) (🏗️ Pendiente)**
    *   💡 Permitir al usuario seleccionar una ciudad específica de las que fueron procesadas.
    *   ➡️ Mostrar una previsualización del `st.dataframe` correspondiente al archivo CSV crudo generado por GOSOM para esa ciudad.
    *   💾 Incluir un `st.download_button` para descargar el archivo CSV crudo específico de la ciudad seleccionada.
*   ✅ **Pestaña/Sección: Datos Procesados y Consolidados**
    *   Este es el resultado final: el `final_df_all_cities` consolidado de todas las ciudades seleccionadas y transformado.
    *   📈 Mostrar una previsualización de las primeras filas del DataFrame utilizando `st.dataframe`.
    *   📥 Añadir un botón destacado `st.download_button` con el label "**Descargar CSV Consolidado Procesado**". El nombre del archivo sugerido es `gmaps_prospectos_consolidados.csv`.
*   📊 **Pestaña/Sección: Resumen y Estadísticas (Mini-EDA)**
    *   Proporciona un análisis rápido de los datos obtenidos.
    *   🎯 **Contadores Clave:**
        *   `st.metric`: "**Total de Prospectos**" - Muestra el número total de filas en el `final_df`.
        *   `st.metric`: "📧 **Con Emails**" - Conteo de prospectos para los cuales se extrajo una dirección de email válida.
        *   `st.metric`: "🌐 **Con Sitios Web**" - Conteo de prospectos que tienen asociado un sitio web.
    *   🏙️ **Gráfico por Ciudad:** `st.bar_chart` que visualiza la distribución del número de prospectos por cada `search_origin_city`.
    *   🏆 **Gráfico Top Categorías:** `st.bar_chart` que muestra el conteo de las N categorías de negocios más frecuentes en el DataFrame consolidado (actualmente top 5).
    *   🗺️ *Opcional Avanzado:* Un `st.map` para visualizar la dispersión geográfica de los prospectos si las coordenadas son fiables.

### 4️⃣ Gestión de Archivos de Configuración (Opcional Avanzado - Barra Lateral 🔧)

Funcionalidad para usuarios que necesiten un control más granular sobre los parámetros de ejecución:

*   🔍 Permitir visualizar y, con precauciones, editar directamente el contenido del archivo `parameters_default.json`.
*   ⬆️ Opción para subir nuevos archivos CSV de keywords o gestionar los ya existentes en la estructura de carpetas.

---

## 🧠 Lógica de Backend a Reutilizar

Para construir esta UI, integraremos y adaptaremos funciones existentes de nuestro notebook MVP:

*   📖 `load_keywords_from_csv(city_name_key)`: Fundamental para cargar las keywords iniciales por ciudad.
*   ⚙️ `run_gmaps_scraper_docker(keywords_list, city_name_key, depth_override, extract_emails_flag)`: La función principal que orquesta el proceso de scraping (requiere adaptación para los parámetros de la UI, especialmente el flag `extract_emails`).
*   ✨ `transform_gmaps_data(df_raw, city_key_origin)`: Encargada de limpiar y preparar los datos crudos para el análisis.
*   🔗 Lógica de orquestación (adaptada de la Celda 4): La secuencia que itera sobre las ciudades seleccionadas, llama al scraper y al transformador.
*   🧩 Lógica de carga y combinación (adaptada de la Celda 5): El proceso de leer los CSVs generados por ciudad y unirlos en un único DataFrame final.

---

## 🚶‍♂️ Flujo de Usuario Típico

Una experiencia de usuario fluida paso a paso:

1.  🌐 El usuario accede a la aplicación Streamlit desde su navegador.
2.  🖱️ Interactúa con la barra lateral, seleccionando **ciudades** (una o varias).
3.  📝 Revisa y ajusta las **palabras clave** específicas que aparecen para las ciudades seleccionadas.
4.  🔢 Define la **profundidad de búsqueda** y activa/desactiva la **extracción de emails**.
5.  🚀 Hace clic en el botón "**Iniciar Scraping**".
6.  🔄 La UI en el área principal muestra un indicador de progreso y, posteriormente, el **log** detallado del proceso.
7.  ✅ Al finalizar la tarea, el área principal se actualiza mostrando las secciones de **resultados** y **estadísticas**.
8.  📊 El usuario explora la **previsualización** de los datos consolidados y el **resumen estadístico** con gráficos.
9.  💾 Si desea conservar los datos, utiliza el **botón de descarga** para obtener el CSV consolidado.

---

## 🛠️ Consideraciones Técnicas

Puntos clave a tener en cuenta durante el desarrollo e implementación:

*   🧠 **Manejo de Estado en Streamlit:** 💡 Es esencial usar `st.session_state` para mantener la persistencia de datos críticos (como las keywords editadas o el DataFrame final) a través de las re-ejecuciones del script que ocurren con las interacciones del usuario.
*   🔄 **Ejecución Asíncrona de Procesos:** Si la ejecución del scraper a través de Docker (`run_gmaps_scraper_docker`) es una operación que bloquea el hilo principal, será importante considerar cómo manejarla de forma asíncrona para evitar que la UI se congele. Mostrar el log al finalizar es un buen punto de partida (MVP).
*   📂 **Gestión de Rutas de Archivos:** Asegurar que todas las rutas a archivos de configuración, datos y logs sean gestionadas de forma robusta, preferiblemente utilizando rutas relativas o configurables para portabilidad.
*   🛡️ **Validación de Entrada:** Implementar verificaciones básicas para la entrada del usuario (ej. ¿hay ciudades seleccionadas?, ¿las keywords no están vacías?).

---

## ✅🚧 Tabla de Progreso Detallada

¡Nuestro plan de trabajo y lo que hemos logrado hasta ahora! 👇

| Característica de la UI Streamlit                                           | Estado      |\n| :-------------------------------------------------------------------------- | :---------- |\n| 🤖 Título de la aplicación: \'Agente GOSOM ETL\'                               | ✅ Completado |\n| ⚙️ Barra lateral: Título \'Configurar Nueva Tarea de Scraping\'                | ✅ Completado |\n| 🏙️ Barra lateral: Selección de Ciudad(es) con `st.multiselect` (opciones dinámicas) | ✅ Completado |\n| ✏️ Barra lateral: Gestión de Keywords por ciudad con `st.text_area` (carga/edición) | ✅ Completado |\n| 🔢 Barra lateral: Profundidad de Búsqueda con `st.number_input`              | ✅ Completado |\n| 📧 Barra lateral: Checkbox \'¿Extraer Emails?\' (`st.checkbox`)               | ✅ Completado |\n| 🚀 Barra lateral: Botón \'Iniciar Scraping\' (`st.button`)                   | ✅ Completado |\n| ⏳ Área principal: Sección \'Progreso de la Tarea\'                            | ✅ Completado |\
| ✨ Área principal (Progreso): Indicador de actividad (`st.spinner`)        | ✅ Completado |\
| 📜 Área principal (Progreso): Mostrar Log al Finalizar (`st.code` o `st.text_area`) | ✅ Completado |\
| 📊 Área principal: Sección \'Visualización de Resultados\'                     | ✅ Completado |\
| 📉 Área principal (Resultados): Pestaña/Sección \'Datos Crudos (por ciudad)\' | 🏗️ Pendiente |\
| 📝 Área principal (Resultados): Mostrar `st.dataframe` crudo                | 🏗️ Pendiente |\
| 💾 Área principal (Resultados): Opción descargar CSV crudo                   | 🏗️ Pendiente |\
| ✅ Área principal (Resultados): Pestaña/Sección \'Datos Procesados y Consolidados\' | ✅ Completado |\
| 📈 Área principal (Resultados): Mostrar `st.dataframe` consolidado         | ✅ Completado |\
| 📥 Área principal (Resultados): Botón \'Descargar CSV Procesado Consolidado\'  | ✅ Completado |\
| 📈 Área principal: Sección \'Resumen y Estadísticas\'                          | ✅ Completado |\
| 🎯 Área principal (Resumen): Contador \'Total de prospectos\' (`st.metric`)  | ✅ Completado |\
| 📧🌐 Área principal (Resumen): Contadores \'Con Email\' y \'Con Sitio Web\'     | ✅ Completado |\
| 🏙️📊 Área principal (Resumen): Gráfico \'Prospectos por Ciudad de Origen\'   | ✅ Completado |\
| 🏆📊 Área principal (Resumen): Gráfico \'Top 5 Categorías\'                     | ✅ Completado |\
| 🔧 Área principal (Opcional Avanzado): Gestión de Archivos de Configuración | 🏗️ Pendiente |\

---

## 🐍 Código Fuente de la Aplicación Streamlit

Aquí se encuentra el código Python que implementa la interfaz de usuario descrita anteriormente.