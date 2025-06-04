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

-   Mostrar `final_df_all_cities` con `st.dataframe`
-   Botón `st.download_button` para descargar el CSV consolidado con label:  
    "**Descargar CSV Procesado Consolidado**"

#### 📈 Pestaña/Sección 3: Resumen y Estadísticas (Mini-EDA)

-   **Contadores Clave (`st.metric`):**
    -   🔢 Total de prospectos
    -   📧 Prospectos con email
    -   🌐 Prospectos con sitio web
-   **Gráficos (`st.bar_chart`):**
    -   🏙️ Distribución por ciudad de origen
    -   🏆 Top 5 categorías de negocios encontrados
-   🗺️ *Opcional:* Mapa (`st.map`) de coordenadas geográficas si están disponibles

---

### 4. 📂 Gestión de Archivos de Configuración (Opcional Avanzado - Sidebar)

Funciones avanzadas para usuarios técnicos.

-   👀 Visualizar/editar el contenido de `parameters_default.json`
-   ⬆️ Subir nuevos archivos CSV de keywords

---

## 🧩 Lógica de Backend Reutilizada y Adaptada

Se reutilizan funciones del notebook MVP y se adaptan para la interfaz:

-   `load_keywords_from_csv(city_name_key)` – Carga keywords iniciales
-   `run_gmaps_scraper_docker(keywords_list, city_name_key, depth_override, extract_emails_flag)` – Ejecuta scraping Dockerizado
-   `transform_gmaps_data(df_raw, city_key_origin)` – Limpieza y transformación de datos
-   Lógica de **orquestación** (celda 4 del notebook) – Iterar sobre ciudades seleccionadas
-   Lógica de **carga y combinación** (celda 5 del notebook) – Unir CSVs por ciudad en un único DataFrame

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

## 🧠 Consideraciones Técnicas

-   💡 **Manejo de Estado:** Uso de `st.session_state` para mantener datos persistentes entre interacciones
-   🔄 **Ejecución Asíncrona:** Evaluar si `run_gmaps_scraper_docker()` debe ejecutarse de forma no bloqueante para evitar que la UI se congele
-   📂 **Gestión de Rutas:** Verificar rutas relativas a archivos de log, configuración y datos
-   🛡️ **Validación de Entrada:** Asegurar que hay ciudades seleccionadas y keywords no vacías antes de iniciar el scraping

---

## ✅ Estado Actual de la Aplicación Streamlit

| Característica | Estado |
|----------------|--------|
| Título de la app e interfaz general | ✅ Completado |
| Configuración de tareas y parámetros | ✅ Completado |
| Visualización de logs post-ejecución | ✅ Completado |
| Sección de resultados y estadísticas | ✅ Completado |
| Pestañas de datos crudos y descarga | 🏗️ Pendiente |
| Gestión avanzada de archivos de configuración | 🏗️ Pendiente |

---

## 📄 Código Fuente

Disponible en el repositorio del proyecto, dentro del script de la interfaz Streamlit.

---

*¡Gracias por leer esta documentación! El Agente GOSOM ETL sigue evolucionando para ofrecer una herramienta sólida y eficiente para el proyecto Avalian.* 🌟