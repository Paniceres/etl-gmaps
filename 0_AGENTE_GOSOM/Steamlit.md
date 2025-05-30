# Especificación de la Interfaz Streamlit para el Agente GOSOM ETL

## Objetivo General de la UI
Proporcionar una interfaz web simple y amigable para configurar y ejecutar tareas de scraping de Google Maps con el Agente GOSOM, monitorear su progreso y visualizar/descargar los resultados procesados.

## Layout General
- **Barra Lateral (Sidebar):** Para configuraciones principales y acciones.
- **Área Principal (Main Area):** Para mostrar logs, resultados, tablas y gráficos.

## Componentes y Funcionalidades

### 1. Configuración de la Tarea de Scraping (Sidebar)
    - **Título:** "Configurar Nueva Tarea de Scraping"
    - **Widget 1: Selección de Ciudad(es)**
        - **Tipo:** `st.multiselect` o `st.selectbox` (si es una a la vez).
        - **Opciones:** Cargar dinámicamente desde las claves del diccionario `GMAPS_COORDINATES` en `parameters_default.json` (ej. "Neuquén", "General Roca", etc.).
        - **Label:** "Seleccionar Ciudad(es) a Procesar"
    - **Widget 2: Gestión de Keywords (Dinámico según ciudad seleccionada)**
        - Al seleccionar una ciudad, mostrar un `st.text_area` pre-poblado con las keywords del archivo `keywords_<ciudad>.csv` correspondiente.
        - Permitir al usuario editar/añadir/eliminar keywords en esta área de texto.
        - **Label:** "Keywords para [Ciudad Seleccionada]"
        - **Botón (opcional):** "Guardar Keywords para [Ciudad]" (para actualizar el archivo CSV).
    - **Widget 3: Profundidad de Búsqueda (`depth`)**
        - **Tipo:** `st.number_input` o `st.slider`.
        - **Label:** "Profundidad de Búsqueda"
        - **Valor por defecto:** Leer de `DEFAULT_DEPTH` en `parameters_default.json`.
        - **Min/Max:** Ej. 1 a 20.
    - **Widget 4: Activar Extracción de Emails**
        - **Tipo:** `st.checkbox`.
        - **Label:** "¿Extraer Emails? (Puede tardar más)"
        - **Valor por defecto:** `True` (según el nuevo requisito).
    - **Widget 5: Botón de Inicio**
        - **Tipo:** `st.button`.
        - **Label:** "Iniciar Scraping"

### 2. Monitoreo de Progreso (Main Area)
    - **Título:** "Progreso de la Tarea"
    - **Indicador de Actividad:** Usar `st.spinner("Scraping en progreso...")` mientras la tarea se ejecuta.
    - **Log en Tiempo Real (Ideal):**
        - Mostrar las últimas N líneas del archivo de log (`agent_gmaps_mvp.log`) o la salida de `subprocess`.
        - Usar `st.text_area` o `st.code` para mostrar los logs.
        - Actualizar periódicamente (requiere manejo de estado y posiblemente threading si el proceso es bloqueante).
    - **Log al Finalizar (MVP):** Mostrar el contenido completo del log de la tarea una vez finalizada.
    - **Barra de Progreso (Opcional Avanzado):** Si podemos estimar el número de tareas.

### 3. Visualización de Resultados (Main Area - Pestañas o Secciones)
    - **Pestaña/Sección 1: Datos Crudos (por ciudad)**
        - Permitir seleccionar una ciudad de las procesadas.
        - Mostrar una vista previa del DataFrame crudo (salida de GOSOM) usando `st.dataframe`.
        - Opción para descargar el CSV crudo específico de esa ciudad.
    - **Pestaña/Sección 2: Datos Procesados y Consolidados**
        - Mostrar el DataFrame final consolidado (`final_df_all_cities`) usando `st.dataframe`.
        - **Botón:** "Descargar CSV Procesado Consolidado".
    - **Pestaña/Sección 3: Resumen y Estadísticas (Mini-EDA)**
        - **Contadores:**
            - Total de prospectos extraídos.
            - Total de prospectos con email.
            - Total de prospectos con sitio web.
            - Número de prospectos por ciudad.
        - **Gráficos:**
            - Gráfico de barras de las top N categorías de negocios encontradas.
            - (Opcional) Mapa de dispersión simple de los prospectos (si hay coordenadas).
        - Usar `st.metric`, `st.bar_chart`, `st.map`.

### 4. Gestión de Archivos de Configuración (Opcional Avanzado - Sidebar)
    - Poder ver/editar el contenido de `parameters_default.json` (con cuidado).
    - Poder subir nuevos archivos de keywords CSV.

## Lógica de Backend (Funciones a Reutilizar del Notebook MVP)
- `load_keywords_from_csv(city_name_key)`
- `run_gmaps_scraper_docker(keywords_list, city_name_key, depth_override, extract_emails_flag)` (modificar para aceptar flag de emails)
- `transform_gmaps_data(df_raw, city_key_origin)`
- Lógica de orquestación de Celda 4 (adaptada para ejecutarse al presionar el botón).
- Lógica de carga y combinación de Celda 5.

## Flujo de Usuario
1. Usuario abre la app Streamlit.
2. Selecciona ciudad(es), revisa/edita keywords, ajusta profundidad, marca extracción de emails.
3. Presiona "Iniciar Scraping".
4. La UI muestra un indicador de progreso y logs.
5. Al finalizar, se muestran los resultados procesados y las estadísticas.
6. Usuario puede descargar los CSVs.

## Consideraciones Técnicas
- Manejo de estado de Streamlit para procesos largos (evitar que la app se reinicie o pierda contexto).
- Ejecución de `subprocess` (para Docker) de forma no bloqueante si se quiere log en tiempo real.
- Rutas de archivos relativas al script de Streamlit.



____