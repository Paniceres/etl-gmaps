# 🎉 Agente GOSOM ETL - Especificación de la Interfaz Streamlit 🚀

## 🎯 Objetivo General de la UI

Proporcionar una interfaz web ✨ simple y amigable ✨ para configurar y ejecutar tareas de scraping de Google Maps con el Agente GOSOM, monitorear su progreso y visualizar/descargar los resultados procesados.

## 📐 Layout General

-   🖥️ **Barra Lateral (Sidebar):** Para configuraciones principales y acciones importantes.
-   📊 **Área Principal (Main Area):** Para mostrar logs, resultados detallados, tablas de datos y gráficos estadísticos.

## 🛠️ Componentes y Funcionalidades Detalladas

### 1. ⚙️ Configuración de la Tarea de Scraping (Sidebar)

Esta sección permite al usuario definir los parámetros para la ejecución del scraping.

-   ✨ **Título:** "Configurar Nueva Tarea de Scraping"
-   🌍 **Widget 1: Selección de Ciudad(es)**
    -   **Tipo:** `st.multiselect` (para seleccionar una o varias ciudades).
    -   **Opciones:** Cargadas dinámicamente desde las **claves** del diccionario `GMAPS_COORDINATES` (ej. "Neuquén", "General Roca", etc.) que se encuentran en `parameters_default.json`.
    -   **Label:** **"Seleccionar Ciudad(es) a Procesar"**
-   📝 **Widget 2: Gestión de Keywords (Dinámico según ciudad seleccionada)**
    -   Una vez que se selecciona una o más ciudades, se mostrará un área de texto para cada una.
    -   El contenido inicial del `st.text_area` se **pre-poblará** con las keywords cargadas desde el archivo `keywords_<ciudad>.csv` correspondiente utilizando la función `load_keywords_from_csv()`.
    -   Se permitirá al usuario **editar**, **añadir** o **eliminar** keywords directamente en esta área de texto.
    -   **Label:** **"Keywords para [Nombre de la Ciudad Seleccionada]"**
    -   ➡️ **Botón (Opcional para el futuro):** **"Guardar Keywords para [Ciudad]"** (Implementación para actualizar el archivo CSV en disco).
-   🔍 **Widget 3: Profundidad de Búsqueda (`depth`)**
    -   **Tipo:** `st.number_input` (más preciso) o `st.slider` (más visual).
    -   **Label:** **"Profundidad de Búsqueda"**
    -   **Valor por defecto:** Se leerá del parámetro `DEFAULT_DEPTH` definido en `parameters_default.json`.
    -   **Rango Min/Max:** Por ejemplo, de **1** a **20**.
-   📧 **Widget 4: Activar Extracción de Emails**
    -   **Tipo:** `st.checkbox`.
    -   **Label:** **"¿Extraer Emails? (Puede tardar más)"**
    -   **Valor por defecto:** **`True`** (según el requisito actualizado).
-   ▶️ **Widget 5: Botón de Inicio**
    -   **Tipo:** `st.button`.
    -   **Label:** **"🚀 Iniciar Scraping"**

### 2. 📈 Monitoreo de Progreso (Main Area)

Esta sección mantendrá informado al usuario sobre el estado de la ejecución.

-   ✨ **Título:** "Progreso de la Tarea"
-   ⏳ **Indicador de Actividad:** Se mostrará un `st.spinner("Scraping en progreso...")` mientras la tarea esté activa.
-   📜 **Log del Proceso:**
    -   **Implementación MVP (Actual):** Mostrar el contenido completo del archivo de log (`agent_gmaps_mvp.log`) una vez que la tarea haya **finalizado**.
    -   **Mejora (Ideal):** Mostrar las **últimas N líneas** del log en **tiempo real** (requiere manejo de estado avanzado o ejecución no bloqueante del proceso de scraping).
    -   **Visualización:** Utilizar `st.text_area` o `st.code` para presentar los logs de forma legible.
-   🚧 **Barra de Progreso (Opcional Avanzado):** Si es posible estimar el número total de operaciones, se podría añadir un `st.progress`.

### 3. 📊 Visualización de Resultados (Main Area - Pestañas o Secciones)

Una vez completado el scraping y el procesamiento, se mostrarán los resultados. Esta sección podría organizarse en pestañas o sub-secciones claras.

-   📁 **Pestaña/Sección 1: Datos Crudos (por ciudad)**
    -   Se permitirá seleccionar una ciudad de las que fueron procesadas en la ejecución actual.
    -   Mostrar una **vista previa** (`st.dataframe`) del DataFrame cargado directamente del CSV crudo (la salida original de GOSOM).
    -   Incluir una **opción de descarga** (`st.download_button`) para obtener el CSV crudo específico de la ciudad seleccionada.
-   ✅ **Pestaña/Sección 2: Datos Procesados y Consolidados**
    -   Mostrar el **DataFrame final consolidado** (`final_df_all_cities`) que combina los datos procesados de todas las ciudades utilizando `st.dataframe`.
    -   Añadir un **botón de descarga** (`st.download_button`) con el label **"Descargar CSV Procesado Consolidado"**.
-   📈 **Pestaña/Sección 3: Resumen y Estadísticas (Mini-EDA)**
    -   Proporcionar un análisis rápido y visual de los resultados.
    -   **Contadores (`st.metric`):**
        -   🔢 **Total de prospectos extraídos.**
        -   📧 **Total de prospectos con email.**
        -   🌐 **Total de prospectos con sitio web.**
        -   🏙️ **Número de prospectos por ciudad de origen.**
    -   **Gráficos:**
        -   📊 **Gráfico de barras (`st.bar_chart`)** mostrando las **top N categorías** de negocios encontradas.
        -   🗺️ **Mapa de dispersión simple (`st.map`)** de los prospectos si se han extraído las coordenadas geográficas.

### 4. 📂 Gestión de Archivos de Configuración (Opcional Avanzado - Sidebar)

Funcionalidad para gestionar los archivos que controlan la configuración.

-   👀 **Visualizar/Editar:** Posibilidad de ver y, con precaución, editar el contenido del archivo `parameters_default.json`.
-   ⬆️ **Subir Archivos:** Opción para subir nuevos archivos de keywords en formato CSV.

## 🧩 Lógica de Backend (Funciones a Reutilizar/Adaptar)

Se integrarán y adaptarán funciones existentes, principalmente del notebook MVP.

-   `load_keywords_from_csv(city_name_key)`: Para cargar las palabras clave.
-   `run_gmaps_scraper_docker(keywords_list, city_name_key, depth_override, extract_emails_flag)`: Adaptar para aceptar el flag de extracción de emails.
-   `transform_gmaps_data(df_raw, city_key_origin)`: Para procesar los DataFrames crudos.
-   La lógica de **orquestación** de la Celda 4 (en el notebook): Adaptarla para que se ejecute de forma secuencial o paralela al presionar el botón "Iniciar Scraping".
-   La lógica de **carga y combinación** de la Celda 5 (en el notebook): Para consolidar los resultados.

## 🚶‍♂️ Flujo de Usuario

1.  Usuario abre la aplicación Streamlit en su navegador.
2.  En la barra lateral, **selecciona** la(s) ciudad(es), **revisa/edita** las palabras clave asociadas, **ajusta** la profundidad de búsqueda y **marca** la opción de extracción de emails si la necesita.
3.  Presiona el botón **"🚀 Iniciar Scraping"**.
4.  En el área principal, la UI muestra un **indicador de progreso** y el **registro (log)** de la ejecución.
5.  Al finalizar la tarea, se muestran los **resultados procesados** en tablas y los **gráficos de estadísticas**.
6.  El usuario puede **descargar** los archivos CSV consolidados o individuales.

## 🧠 Consideraciones Técnicas

-   Keeping 🧠 **Manejo de estado de Streamlit:** Es crucial para mantener la información persistente entre las re-ejecuciones de la aplicación, especialmente para procesos largos o cuando se necesita recordar selecciones del usuario.
-   Running 🏃‍♂️ **Ejecución de `subprocess` (para Docker):** Considerar si se ejecutará de forma bloqueante (más simple) o no bloqueante (permite log en tiempo real, pero es más compleja).
-   File 📂 **Rutas de archivos:** Asegurarse de que todas las rutas a archivos de log, configuración y datos crudos sean correctas y relativas al script de Streamlit.
