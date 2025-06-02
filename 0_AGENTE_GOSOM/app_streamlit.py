# 0_AGENTE_GOSOM/app_streamlit.py
import streamlit as st
import json
import os
import pandas as pd
import sys
from datetime import datetime 

# --- Añadir src al PYTHONPATH para importar core_logic ---
APP_ROOT_DIR = os.path.dirname(__file__) 
SRC_DIR = os.path.join(APP_ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

CORE_LOGIC_LOADED = False
try:
    from core_logic import StyledLogger, gmaps_column_names, load_keywords_from_csv_core, process_city_data_core
    CORE_LOGIC_LOADED = True
except ImportError as e:
    st.error(f"Error crítico al importar módulos de 'core_logic.py': {e}. Asegúrate de que '0_AGENTE_GOSOM/src/core_logic.py' exista y no tenga errores de sintaxis.")
    class DummyLogger: # Define Dummies si la importación falla
        def __init__(self, *args, **kwargs): pass
        def info(self, msg): print(f"DUMMY_INFO: {msg}")
        def error(self, msg, exc_info=False): print(f"DUMMY_ERROR: {msg}")
        def warning(self, msg): print(f"DUMMY_WARN: {msg}")
        def success(self, msg): print(f"DUMMY_SUCCESS: {msg}")
        def section(self, msg): print(f"DUMMY_SECTION: {msg}")
        def subsection(self, msg): print(f"DUMMY_SUBSECTION: {msg}")
        def print_header_art(self): print("DUMMY LOGGER HEADER")
    def load_keywords_from_csv_core(*args): return ["dummy_keyword"]
    def process_city_data_core(*args, **kwargs): 
        logger_instance = kwargs.get('logger_instance', DummyLogger())
        logger_instance.error("Usando process_city_data_core DUMMY debido a error de importación.")
        return pd.DataFrame({'title':['dummy place'], 'emails':['dummy@example.com']})
    gmaps_column_names = ['title', 'emails'] 
    StyledLogger = DummyLogger

# --- Configuración de Rutas ---
CONFIG_DIR = os.path.join(APP_ROOT_DIR, 'config')
DATA_DIR = os.path.join(APP_ROOT_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
LOGS_DIR = os.path.join(DATA_DIR, 'logs')

os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, 'parameters_default.json')

# --- Carga de Configuración Principal ---
FALLBACK_CONFIG = {
    'gmaps_coordinates': {'neuquen': {'latitude': -38.9516, 'longitude': -68.0591}},
    'default_depth': 1, 'language': 'es', 'results_filename_prefix': 'gmaps_data_',
    'log_filename': 'agent_gmaps_mvp_streamlit_fallback.log'
}
config_params = {}
try:
    with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
        config_params = json.load(f)
except Exception as e:
    # No usar st.warning aquí todavía porque el logger no está instanciado
    print(f"ADVERTENCIA: No se pudo cargar '{CONFIG_FILE_PATH}'. Usando config de fallback. Error: {e}")
    config_params = FALLBACK_CONFIG

# --- Instanciar Logger (de core_logic si está cargado) ---
core_log_filename = config_params.get('log_filename', FALLBACK_CONFIG['log_filename'])
logger = StyledLogger(logger_name="StreamlitAppLogger", log_file_path=os.path.join(LOGS_DIR, core_log_filename))


# --- Inicializar Session State ---
default_session_state = {
    'selected_cities_keywords': {},
    'raw_csv_paths': {}, # Este almacenará {city_key: path_al_csv_crudo}
    'scraping_done': False,
    'scraping_in_progress': False,
    'final_df': pd.DataFrame(),
    'last_selected_cities': [],
    'last_search_depth': config_params.get('default_depth', 1),
    'last_extract_emails': True
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- UI de la Aplicación Streamlit ---
st.set_page_config(page_title="Agente GOSOM ETL", layout="wide", initial_sidebar_state="expanded")
if hasattr(logger, 'print_header_art'): # Llamar solo si el logger real está cargado
    logger.print_header_art() 
st.title('🚀✨ Agente GOSOM ETL')
st.markdown("Herramienta para extraer y procesar leads de Google Maps.")

if not CORE_LOGIC_LOADED:
    st.error("¡ADVERTENCIA! El módulo 'core_logic.py' no se pudo cargar correctamente. La funcionalidad de scraping estará limitada o usará versiones dummy.")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header('⚙️ Configurar Tarea')
    
    gmaps_coordinates_options = list(config_params.get('gmaps_coordinates', {}).keys())
    if not gmaps_coordinates_options and CORE_LOGIC_LOADED: # Solo mostrar error si core_logic cargó pero no hay coords
        st.error("No se encontraron ciudades en 'parameters_default.json' [gmaps_coordinates].")
    
    selected_cities_keys = st.multiselect(
        '🏙️ Seleccionar Ciudad(es)',
        options=gmaps_coordinates_options,
        default=st.session_state.last_selected_cities,
        disabled=st.session_state.scraping_in_progress
    )
    st.session_state.last_selected_cities = selected_cities_keys

    if selected_cities_keys:
        st.subheader("✏️ Keywords por Ciudad")
        for city_key in selected_cities_keys:
            if city_key not in st.session_state.selected_cities_keywords:
                if CORE_LOGIC_LOADED:
                    keywords_list = load_keywords_from_csv_core(CONFIG_DIR, city_key, logger) ### CAMBIO ###
                    st.session_state.selected_cities_keywords[city_key] = "\n".join(keywords_list)
                else:
                    st.session_state.selected_cities_keywords[city_key] = f"dummy_kw1_for_{city_key}\ndummy_kw2_for_{city_key}"


            st.session_state.selected_cities_keywords[city_key] = st.text_area(
                label=f'Keywords para {city_key.capitalize()}',
                value=st.session_state.selected_cities_keywords[city_key],
                key=f'keywords_textarea_{city_key}', 
                height=150,
                disabled=st.session_state.scraping_in_progress
            )

    search_depth_val = st.number_input(
        '🎯 Profundidad de Búsqueda',
        min_value=1, max_value=20,
        value=int(st.session_state.last_search_depth), ### AJUSTE: Castear a int por si acaso
        disabled=st.session_state.scraping_in_progress,
        help="Número de 'páginas' de resultados a scrapear."
    )
    st.session_state.last_search_depth = search_depth_val

    extract_emails_val = st.checkbox(
        '📧 ¿Extraer Emails? (⚠️ Puede tardar más)',
        value=st.session_state.last_extract_emails, 
        disabled=st.session_state.scraping_in_progress
    )
    st.session_state.last_extract_emails = extract_emails_val

    if st.button('🚀 Iniciar Scraping', disabled=st.session_state.scraping_in_progress or not CORE_LOGIC_LOADED, type="primary"):
        if not selected_cities_keys:
            st.warning('Por favor, selecciona al menos una ciudad.')
        elif not CORE_LOGIC_LOADED:
            st.error("No se puede iniciar el scraping porque 'core_logic.py' no se cargó correctamente.")
        else:
            st.session_state.scraping_in_progress = True
            st.session_state.scraping_done = False 
            st.session_state.raw_csv_paths = {}    
            st.session_state.final_df = pd.DataFrame() 
            
            # Configuración de rutas para pasar a core_logic
            paths_config_for_core = {
                'CONFIG_DIR': CONFIG_DIR,
                'RAW_DATA_DIR': RAW_DATA_DIR,
                'PROCESSED_DATA_DIR': PROCESSED_DATA_DIR, # Aunque no se use directamente en process_city_data_core
                'LOGS_DIR': LOGS_DIR,
                'RESULTS_FILENAME_PREFIX': config_params.get('results_filename_prefix', 'gmaps_data_') ### AJUSTE ###
            }

            # Placeholder para los logs en la UI mientras se ejecuta
            log_placeholder = st.empty()
            main_area_status = st.empty()

            with main_area_status.container():
                 st.info("⚙️ Iniciando proceso de scraping y transformación...")
            
            logger.section(f"Nueva Tarea de Scraping Iniciada desde UI Streamlit") # Log al archivo
            logger.info(f"Ciudades: {selected_cities_keys}, Profundidad: {search_depth_val}, Extraer Emails: {extract_emails_val}")

            temp_dfs = [] # Lista para recolectar DataFrames transformados por ciudad

            for city_key in selected_cities_keys:
                keywords_str = st.session_state.selected_cities_keywords.get(city_key, "")
                keywords_list = [kw.strip() for kw in keywords_str.splitlines() if kw.strip()]

                if not keywords_list:
                    logger.warning(f"No hay keywords para {city_key.capitalize()} en la UI. Omitiendo.")
                    st.warning(f"No hay keywords para {city_key.capitalize()}. Se omite para esta ciudad.")
                    continue
                
                with main_area_status.container(): # Actualizar estado en la UI
                    st.info(f"⚙️ Procesando: {city_key.capitalize()}...")
                
                # Llamar a la función orquestadora de core_logic
                df_transformado_ciudad = process_city_data_core( ### CAMBIO ###
                    city_key, keywords_list, search_depth_val, extract_emails_val,
                    config_params, paths_config_for_core, logger # Pasa config_params y paths_config
                )
                
                if df_transformado_ciudad is not None and not df_transformado_ciudad.empty:
                    temp_dfs.append(df_transformado_ciudad)
                    # Recuperar el path del archivo crudo (esto es un poco hacky, idealmente process_city_data_core lo devolvería)
                    # Asumimos que el último archivo creado en RAW_DATA_DIR para esta ciudad es el nuestro.
                    # Esto necesita una forma más robusta de obtener el path del archivo crudo.
                    # Por ahora, no lo almacenamos en st.session_state.raw_csv_paths aquí.
                    with main_area_status.container():
                        st.success(f'Proceso para {city_key.capitalize()} completado. {len(df_transformado_ciudad)} prospectos procesados.')
                elif df_transformado_ciudad is not None and df_transformado_ciudad.empty:
                     with main_area_status.container():
                        st.warning(f"Proceso para {city_key.capitalize()} completado, pero no se encontraron/procesaron datos.")
                else: # df_transformado_ciudad es None (error crítico en core_logic)
                    with main_area_status.container():
                        st.error(f'Proceso para {city_key.capitalize()} falló críticamente. Revisa los logs.')
            
            if temp_dfs:
                st.session_state.final_df = pd.concat(temp_dfs, ignore_index=True)
            
            st.session_state.scraping_done = True
            st.session_state.scraping_in_progress = False
            if not st.session_state.final_df.empty:
                st.balloons()
            logger.section("Tarea de Scraping desde UI Streamlit Finalizada")
            main_area_status.empty() # Limpiar el mensaje de estado

# --- ÁREA PRINCIPAL: Mostrar Resultados y Logs ---
if not st.session_state.scraping_in_progress: # Solo mostrar si no está en progreso
    if st.session_state.scraping_done:
        st.header("📊 Resultados de la Tarea")
        tab_stats, tab_data, tab_logs = st.tabs(["Resumen y Estadísticas", "Datos Procesados", "Log Completo"])

        with tab_stats: 
            st.subheader("Análisis General")
            if not st.session_state.final_df.empty:
                df_display = st.session_state.final_df.copy() # Trabajar con una copia para no modificar el estado
                
                if 'link' in df_display.columns:
                    logger.subsection("Aplicando Deduplicación para visualización")
                    initial_count = len(df_display)
                    df_display.drop_duplicates(subset=['link'], keep='first', inplace=True)
                    # NO actualizamos st.session_state.final_df aquí, solo para visualización
                    deduplicated_count = initial_count - len(df_display)
                    if deduplicated_count > 0:
                        logger.info(f"Streamlit display: Se ocultaron {deduplicated_count} duplicados para visualización.")
                
                total_prospectos_display = len(df_display)
                st.metric("Prospectos Únicos (por link)", f"{total_prospectos_display}")

                cols_metrics = st.columns(2)
                email_col_name = 'emails' ### AJUSTE ###
                website_col_name = 'website' ### AJUSTE ###

                if email_col_name in df_display.columns:
                    con_email = df_display[email_col_name].notna().sum()
                    cols_metrics[0].metric("📧 Con Emails", f"{con_email} ({ (con_email/total_prospectos_display*100) if total_prospectos_display > 0 else 0 :.1f}%)")
                else:
                    cols_metrics[0].metric("📧 Con Emails", "N/A")

                if website_col_name in df_display.columns:
                    con_website = df_display[website_col_name].notna().sum()
                    cols_metrics[1].metric("🌐 Con Sitios Web", f"{con_website} ({ (con_website/total_prospectos_display*100) if total_prospectos_display > 0 else 0 :.1f}%)")
                else:
                    cols_metrics[1].metric("🌐 Con Sitios Web", "N/A")
            
                if 'search_origin_city' in df_display.columns and not df_display['search_origin_city'].empty:
                    st.subheader("Prospectos por Ciudad")
                    city_counts = df_display['search_origin_city'].value_counts()
                    st.bar_chart(city_counts)

                if 'category' in df_display.columns and not df_display['category'].empty:
                    st.subheader("Top 5 Categorías")
                    category_counts = df_display['category'].value_counts().nlargest(5)
                    st.bar_chart(category_counts)
            else:
                st.info("No hay datos procesados para mostrar estadísticas.")

        with tab_data: 
            st.subheader("Vista Previa de Datos Consolidados")
            if not st.session_state.final_df.empty:
                st.dataframe(st.session_state.final_df)
                
                try:
                    csv_download = st.session_state.final_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(
                        label="📥 Descargar CSV Consolidado",
                        data=csv_download,
                        file_name=f"gmaps_prospectos_consolidados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime='text/csv',
                    )
                except Exception as e_csv:
                    st.error(f"Error al generar CSV para descarga: {e_csv}")
            else:
                st.info("No hay datos procesados para mostrar o descargar.")
                
        with tab_logs: 
            st.subheader("Log Detallado del Proceso")
            try:
                # Leer las últimas N líneas (o una función para leer todo si es necesario)
                def read_log_file(file_path, max_lines=500):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        return "".join(lines[-max_lines:])
                    except FileNotFoundError:
                        return f"Archivo de log no encontrado: {file_path}"
                    except Exception as e:
                        return f"Error al leer log: {e}"
                
                log_content = read_log_file(os.path.join(LOGS_DIR, core_log_filename)) 
                st.text_area("Log Completo de Core Logic", value=log_content, height=400, key='log_display_area_main_full', disabled=True)
            except Exception as e:
                st.error(f"Error al mostrar el archivo de log: {e}")

    elif not st.session_state.scraping_in_progress: # Si no está en progreso y no ha terminado (estado inicial)
         st.info("⬅️ Configura una tarea en la barra lateral y presiona 'Iniciar Scraping' para comenzar.")

# Útil para depuración
# with st.expander("Ver Session State (Debug)"):
#    st.write(st.session_state)