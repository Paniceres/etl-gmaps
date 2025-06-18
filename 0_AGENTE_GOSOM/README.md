# 🚀✨ Agente GOSOM - Especificación de la Interfaz Streamlit (Actualizada) 📊🤖

---

## 🎯 Objetivo General de la UI 

Proporcionar una **interfaz web simple y amigable** para configurar, ejecutar y monitorear tareas de scraping de Google Maps con el **Agente GOSOM**, generando **CSVs crudos por ciudad** que se procesarán en el **ETL Central**.

---

## 📐 Layout General

La interfaz se divide en dos áreas principales:

-   🖥️ **Barra Lateral (Sidebar):** Para controles de configuración y acciones clave.
-   📊 **Área Principal (Main Area):** Para mostrar logs, resultados y CSVs crudos.
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

Mostrar los datos crudos obtenidos y permitir su descarga.

-   Seleccionar ciudad de entre las procesadas
-   Mostrar vista previa del CSV crudo usando `st.dataframe`
-   Añadir botón `st.download_button` para descargar el CSV específico de esa ciudad

---

## 📁 Ubicaciones de Archivos Clave

A continuación, se listan las ubicaciones de directorios y archivos importantes utilizados por la aplicación:

-   **CSVs Crudos:** `/data/raw/<ciudad>_<timestamp>.csv`
-   **Logs de Ejecución:** `/data/logs/agent_gmaps_mvp.log` y `/data/logs/streamlit_ui_events.log`

---

## 🚶‍♂️ Flujo de Usuario Típico

1.  Usuario accede a la aplicación Streamlit desde el navegador
2.  En la barra lateral:
    -   Configura las opciones de scraping (ciudades, keywords, profundidad, extracción de emails).
3.  Hace clic en "🚀 Iniciar Scraping".
4.  Mientras se ejecuta:
    -   Ve un spinner indicando actividad
    -   Al finalizar, muestra el log completo del proceso
5.  Una vez terminado:
    -   Descarga los CSVs crudos generados

---

## 📂 Archivos de Configuración y Datos Importantes

-   **Configuración de Parámetros Generales:** `/config/parameters_default.json`
-   **Configuración de Keywords por Ciudad:** `/config/keywords_<ciudad>.csv`
-   **Logs de Ejecución:** `/data/logs/agent_gmaps_mvp.log` y `/data/logs/streamlit_ui_events.log`

---

*¡Gracias por leer esta documentación! 
El Agente GOSOM sigue evolucionando para ofrecer una herramienta sólida y eficiente para el proyecto Avalian.* 🌟

---

**Note:** Data consolidation, deduplication, and further ETL processes are handled by a separate Central ETL.

