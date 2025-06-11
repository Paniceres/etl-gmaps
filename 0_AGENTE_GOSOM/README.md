# 🚀✨ Agente GOSOM ETL - Especificación de la Interfaz Streamlit 📊🤖

---

## 🎯 Objetivo General de la UI 

Proporcionar una **interfaz web simple y amigable** para configurar, ejecutar y monitorear tareas de scraping de Google Maps con el **Agente GOSOM ETL**, así como visualizar, analizar y descargar los datos procesados.

---

## 📐 Layout General

La interfaz se divide en dos áreas principales:

-   🖥️ **Barra Lateral (Sidebar):** Para controles de configuración y acciones clave.
-   📊 **Área Principal (Main Area):** Para mostrar logs, resultados, tablas y gráficos estadísticos.

---

## 🛠️ Componentes y Funcionalidades Detalladas

### 1. ⚙️ Configuración de la Tarea de Scraping (Sidebar)

Permite al usuario definir los parámetros para ejecutar el scraping de Google Maps.

-   ✨ **Título:** "Configurar Nueva Tarea de Scraping"
-   🌍 **Widget 1: Selección de Ciudad(es)**
    -   **Tipo:** `st.multiselect` (seleccionar múltiples ciudades)
    -   **Opciones:** Cargadas dinámicamente desde las claves del diccionario `GMAPS_COORDINATES` en `parameters_default.json`
    -   **Label:** "Seleccionar Ciudad(es) a Procesar"
-   📝 **Widget 2: Gestión de Keywords por Ciudad**
    -   Se muestran dinámicamente tras seleccionar ciudades
    -   **Cada ciudad tiene un `st.text_area`** con keywords precargadas desde `keywords_<ciudad>.csv` usando `load_keywords_from_csv()`
    -   **Editable:** El usuario puede añadir, modificar o eliminar palabras clave
    -   **Label:** "Keywords para [Nombre de la Ciudad]"
    -   *Futuro:* Botón opcional para guardar cambios localmente (`"Guardar Keywords para [Ciudad]"`)
-   🔍 **Widget 3: Profundidad de Búsqueda (`depth`)**
    -   **Tipo:** `st.number_input` o `st.slider`
    -   **Label:** "Profundidad de Búsqueda"
    -   **Valor por defecto:** Leído desde `DEFAULT_DEPTH` en `parameters_default.json`
    -   **Rango sugerido:** De 1 a 20
-   📧 **Widget 4: Activar Extracción de Emails**
    -   **Tipo:** `st.checkbox`
    -   **Label:** "¿Extraer Emails? (Puede tardar más)"
    -   **Valor por defecto:** `True`
-   ▶️ **Widget 5: Botón de Inicio**
    -   **Tipo:** `st.button`
    -   **Label:** "🚀 Iniciar Scraping"

---

### 2. 📈 Monitoreo de Progreso (Main Area)

Mantiene informado al usuario sobre el estado de la ejecución.

-   ✨ **Título:** "Progreso de la Tarea"
-   ⏳ **Indicador de Actividad:** `st.spinner("Scraping en progreso...")` mientras se ejecuta
-   📜 **Registro del Proceso (Log):**
    -   **Implementación actual (MVP):** Mostrar contenido del archivo `agent_gmaps_mvp.log` tras finalizar la tarea
    -   **Visualización:** Usar `st.code` o `st.text_area` para legibilidad
    -   *Futuro:* Mostrar últimas líneas del log en tiempo real si es posible
-   🚧 **Barra de Progreso (Opcional Avanzado):** `st.progress` si se puede estimar el total de operaciones

---

### 3. 📊 Visualización de Resultados (Main Area - Pestañas/Secciones)

Mostrar los datos obtenidos y permitir su análisis y descarga.

#### 📁 Pestaña/Sección 1: Datos Crudos (por ciudad)

-   Seleccionar ciudad de entre las procesadas
-   Mostrar vista previa del CSV crudo usando `st.dataframe`
-   Añadir botón `st.download_button` para descargar el CSV específico de esa ciudad

#### ✅ Pestaña/Sección 2: Datos Procesados y Consolidados

*   Esta sección es crucial para la gestión centralizada de los leads.
*   **CSV Madre:** El archivo `/data/consolidated/consolidated_leads.csv` actúa como el **"CSV Madre"**, almacenando todos los leads consolidados de las diferentes ejecuciones de scraping a lo largo del tiempo.
*   **Consolidación:** Cuando se ejecuta una nueva tarea de scraping (Etapa 1) y se llega a esta etapa (Etapa 3), los nuevos datos raspados (`final_df_all_cities`) se consolidan con el CSV Madre existente.
*   **Deduplicación:** El proceso de consolidación incluye una lógica de **deduplicación** que compara los nuevos leads con los existentes en el CSV Madre, añadiendo solo aquellos que son únicos (basado principalmente en el 'link' y 'title' del lead).
*   **Visualización:** Se muestra el contenido actual del CSV Madre (`/data/consolidated/consolidated_leads.csv`) usando `st.dataframe`.
*   **Generación de Chunks:** Permite generar archivos CSV más pequeños (chunks) para la asignación de leads a vendedores. Los leads asignados se marcan en el CSV Madre utilizando columnas como `fecha_asignacion` e `id_chunk`. Los archivos chunk generados se guardan en el directorio `/data/chunks/`.
*   **Dependencia de Lógica Central:** Esta etapa depende fuertemente del módulo `core_logic.py` para operaciones como la validación de integridad del CSV Madre, la comparación y filtrado de nuevos datos (deduplicación), y la lógica detallada de la generación de chunks. Si `core_logic.py` no carga correctamente, algunas funcionalidades de esta etapa podrían verse limitadas o no estar disponibles.
---

## 📁 Ubicaciones de Archivos Clave

A continuación, se listan las ubicaciones de directorios y archivos importantes utilizados por la aplicación:

    *   **CSV Madre Consolidado:** `/data/consolidated/consolidated_leads.csv`
    *   **Archivos Chunk Generados:** `/data/chunks/`
*   **Botón de Descarga:** Se proporciona un botón `st.download_button` para descargar la versión actual del CSV Madre consolidado con el label: "**Descargar CSV Madre Consolidado**".

#### 📈 Pestaña/Sección 3: Resumen y Estadísticas (Mini-EDA)

-   **Contadores Clave (`st.metric`):** Muestra métricas relevantes calculadas a partir del CSV Madre consolidado.
    *   🔢 Total de prospectos
    *   📧 Prospectos con email
    *   🌐 Prospectos con sitio web
-   **Gráficos (`st.bar_chart`):** Visualizaciones basadas en los datos del CSV Madre consolidado.
    *   🏙️ Distribución por ciudad de origen
    *   🏆 Top 5 categorías de negocios encontrados
-   🗺️ *Opcional:* Mapa (`st.map`) de coordenadas geográficas si están disponibles

---
---



---

## 🚶‍♂️ Flujo de Usuario Típico

1.  Usuario accede a la aplicación Streamlit desde el navegador
2.  En la barra lateral:
    -   Selecciona una o varias ciudades
    -   Edita keywords si es necesario
    -   Define profundidad y activa/desactiva extracción de emails
3.  Hace clic en "🚀 Iniciar Scraping"
4.  Mientras se ejecuta:
    -   Ve un spinner indicando actividad
    -   Al finalizar, muestra el log completo del proceso
5.  Una vez terminado:
    -   Ve los datos procesados, estadísticas y gráficos
    -   Puede descargar los CSVs generados

---

## 📂 Archivos de Configuración y Datos Importantes

-   **Configuración de Parámetros Generales:** `/config/parameters_default.json`
-   **Configuración de Keywords por Ciudad:** `/config/keywords_<ciudad>.csv`
-   **Logs de Ejecución:** `/data/logs/agent_gmaps_mvp.log` y `/data/logs/streamlit_ui_events.log`
---




---

*¡Gracias por leer esta documentación! 
El Agente GOSOM ETL sigue evolucionando para ofrecer una herramienta sólida y eficiente para el proyecto Avalian.* 🌟