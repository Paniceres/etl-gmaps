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
    # Intentamos importar las funciones y clases específicas que necesitamos
    from core_logic import StyledLogger, gmaps_column_names, load_keywords_from_csv_core, process_city_data_core
    CORE_LOGIC_LOADED = True
except ImportError as e:
    st.error(f"Error crítico al importar módulos de 'core_logic.py': {e}. Asegúrate de que '0_AGENTE_GOSOM/src/core_logic.py' exista y no tenga errores de sintaxis.")
    # Definir dummies para que la UI no se rompa completamente
    class DummyLogger:
        def __init__(self, *args, **kwargs): pass
        def info(self, msg, art=""): print(f"DUMMY_INFO: {msg}") # Añadido art para compatibilidad
        def error(self, msg, exc_info=False, art=""): print(f"DUMMY_ERROR: {msg}")
        def warning(self, msg, art=""): print(f"DUMMY_WARN: {msg}")
        def success(self, msg, art=""): print(f"DUMMY_SUCCESS: {msg}")
        def section(self, msg): print(f"DUMMY_SECTION: {msg}")
        def subsection(self, msg): print(f"DUMMY_SUBSECTION: {msg}")
        def print_header_art(self): print("DUMMY LOGGER HEADER")
        def critical(self, msg, exc_info=False, art=""): print(f"DUMMY_CRITICAL: {msg}")
        def debug(self, msg, art=""): print(f"DUMMY_DEBUG: {msg}")

    def load_keywords_from_csv_core(*args): return ["dummy_keyword"]
    def process_city_data_core(*args, **kwargs): 
        logger_instance = kwargs.get('logger_instance', DummyLogger())
        logger_instance.error("Usando process_city_data_core DUMMY debido a error de importación.")
        return pd.DataFrame({'title':['dummy place'], 'emails':['dummy@example.com'], 'link': ['http://dummy.com'], 'category':['Dummy'], 'search_origin_city':['dummy']})
    
    gmaps_column_names = ['title', 'emails', 'link', 'category', 'search_origin_city'] 
    StyledLogger = DummyLogger # Usar la clase dummy
    # CORE_LOGIC_LOADED sigue siendo False


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
    # Este print irá a la consola donde corre Streamlit, no a la UI de Streamlit aún.
    print(f"ADVERTENCIA DE APP_STREAMLIT: No se pudo cargar '{CONFIG_FILE_PATH}'. Usando config de fallback. Error: {e}")
    config_params = FALLBACK_CONFIG

# --- Instanciar Logger (de core_logic si está cargado) ---
core_log_filename = config_params.get('log_filename', FALLBACK_CONFIG['log_filename']) # Nombre de archivo para logs de core_logic
streamlit_logger_instance = StyledLogger(logger_name="StreamlitAppUI", log_file_path=os.path.join(LOGS_DIR, "streamlit_ui_events.log"))


# --- Inicializar Session State ---
default_session_state = {
    'selected_cities_keywords': {},
    'scraping_done': False,
    'scraping_in_progress': False,
    'final_df': pd.DataFrame(), # DataFrame consolidado y procesado
    'last_selected_cities': [],
    'last_search_depth': config_params.get('default_depth', 1),
    'last_extract_emails': True
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- UI de la Aplicación Streamlit ---
st.set_page_config(page_title="Agente GOSOM ETL", layout="wide", initial_sidebar_state="expanded")
if hasattr(streamlit_logger_instance, 'print_header_art'): 
    streamlit_logger_instance.print_header_art() # Imprime en consola
st.title('🚀✨ Agente GOSOM ETL')
st.markdown("Herramienta para extraer y procesar leads de Google Maps.")

if not CORE_LOGIC_LOADED:
    st.error("¡ADVERTENCIA CRÍTICA! El módulo 'core_logic.py' no se pudo cargar. La funcionalidad de scraping no estará disponible. Revisa la consola para errores de importación.")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header('⚙️ Configurar Tarea')
    
    gmaps_coordinates_options = list(config_params.get('gmaps_coordinates', {}).keys())
    if not gmaps_coordinates_options and CORE_LOGIC_LOADED:
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
                    keywords_list = load_keywords_from_csv_core(CONFIG_DIR, city_key, streamlit_logger_instance) 
                    st.session_state.selected_cities_keywords[city_key] = "\n".join(keywords_list)
                else: # Fallback
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
        value=int(st.session_state.last_search_depth), 
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
        else:
            st.session_state.scraping_in_progress = True
            st.session_state.scraping_done = False 
            st.session_state.final_df = pd.DataFrame() # Limpiar DataFrame anterior
            
            paths_config_for_core = {
                'CONFIG_DIR': CONFIG_DIR, 'RAW_DATA_DIR': RAW_DATA_DIR,
                'PROCESSED_DATA_DIR': PROCESSED_DATA_DIR, 'LOGS_DIR': LOGS_DIR,
                'RESULTS_FILENAME_PREFIX': config_params.get('results_filename_prefix', 'gmaps_data_')
            }
            
            # Usar el logger de Streamlit para mensajes de UI, y el logger de core_logic para operaciones de backend
            streamlit_logger_instance.section(f"Nueva Tarea de Scraping Iniciada desde UI")
            streamlit_logger_instance.info(f"Ciudades: {selected_cities_keys}, Profundidad: {search_depth_val}, Extraer Emails: {extract_emails_val}")

            temp_dfs_list = [] 

            for city_key in selected_cities_keys:
                keywords_str = st.session_state.selected_cities_keywords.get(city_key, "")
                keywords_list_for_city = [kw.strip() for kw in keywords_str.splitlines() if kw.strip()]

                if not keywords_list_for_city:
                    streamlit_logger_instance.warning(f"No hay keywords para {city_key.capitalize()} en la UI. Omitiendo.")
                    st.warning(f"No hay keywords para {city_key.capitalize()}. Se omite para esta ciudad.")
                    continue
                
                with st.spinner(f'⚙️ Procesando: {city_key.capitalize()}... (Esto puede tardar varios minutos)'):
                    df_transformado_ciudad = process_city_data_core(
                        city_key, keywords_list_for_city, search_depth_val, extract_emails_val,
                        config_params, paths_config_for_core, streamlit_logger_instance # Pasar el logger de la UI para que loguee ahí también
                    )
                
                if df_transformado_ciudad is not None and not df_transformado_ciudad.empty:
                    temp_dfs_list.append(df_transformado_ciudad)
                    st.success(f'Proceso para {city_key.capitalize()} completado. {len(df_transformado_ciudad)} prospectos procesados.')
                elif df_transformado_ciudad is not None and df_transformado_ciudad.empty:
                     st.warning(f"Proceso para {city_key.capitalize()} completado, pero no se encontraron/procesaron datos.")
                else: 
                    st.error(f'Proceso para {city_key.capitalize()} falló críticamente. Revisa los logs en la consola o en el archivo.')
            
            if temp_dfs_list:
                st.session_state.final_df = pd.concat(temp_dfs_list, ignore_index=True)
            
            st.session_state.scraping_done = True
            st.session_state.scraping_in_progress = False
            if not st.session_state.final_df.empty:
                st.balloons()
            streamlit_logger_instance.section("Tarea de Scraping desde UI Finalizada")

# --- ÁREA PRINCIPAL: Mostrar Resultados y Logs ---
if not st.session_state.scraping_in_progress: 
    if st.session_state.scraping_done:
        st.header("📊 Resultados de la Tarea")
        tab_stats, tab_data, tab_logs = st.tabs(["Resumen y Estadísticas", "Datos Procesados", "Log Completo"])

        with tab_stats: 
            st.subheader("Análisis General")
            if not st.session_state.final_df.empty:
                df_display = st.session_state.final_df.copy() 
                
                if 'link' in df_display.columns: # Asegurarse que 'link' exista para deduplicar
                    initial_count = len(df_display)
                    df_display.drop_duplicates(subset=['link'], keep='first', inplace=True)
                    deduplicated_count = initial_count - len(df_display)
                    if deduplicated_count > 0: streamlit_logger_instance.info(f"Streamlit display: {deduplicated_count} duplicados ocultados para visualización.")
                
                total_prospectos_display = len(df_display)
                st.metric("Prospectos Únicos (por link de Gmaps)", f"{total_prospectos_display}")

                cols_metrics = st.columns(2)
                email_col = 'emails'
                website_col = 'website'

                if email_col in df_display.columns:
                    con_email = df_display[email_col].notna().sum()
                    cols_metrics[0].metric("📧 Con Emails", f"{con_email} ({ (con_email/total_prospectos_display*100) if total_prospectos_display > 0 else 0 :.1f}%)")
                else: cols_metrics[0].metric("📧 Con Emails", "N/A")

                if website_col in df_display.columns:
                    con_website = df_display[website_col].notna().sum()
                    cols_metrics[1].metric("🌐 Con Sitios Web", f"{con_website} ({ (con_website/total_prospectos_display*100) if total_prospectos_display > 0 else 0 :.1f}%)")
                else: cols_metrics[1].metric("🌐 Con Sitios Web", "N/A")
            
                if 'search_origin_city' in df_display.columns and not df_display['search_origin_city'].empty:
                    st.subheader("Prospectos por Ciudad")
                    st.bar_chart(df_display['search_origin_city'].value_counts())

                if 'category' in df_display.columns and not df_display['category'].empty:
                    st.subheader("Top 5 Categorías")
                    st.bar_chart(df_display['category'].value_counts().nlargest(5))
            else:
                st.info("No hay datos procesados para mostrar estadísticas.")

        with tab_data: 
            st.subheader("Vista Previa de Datos Consolidados y Procesados")
            if not st.session_state.final_df.empty:
                st.dataframe(st.session_state.final_df)
                try:
                    csv_download = st.session_state.final_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(label="📥 Descargar CSV Consolidado", data=csv_download,
                                       file_name=f"gmaps_prospectos_consolidados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                       mime='text/csv')
                except Exception as e_csv: st.error(f"Error al generar CSV para descarga: {e_csv}")
            else: st.info("No hay datos procesados para mostrar o descargar.")
                
        with tab_logs: 
            st.subheader("Log Detallado del Proceso")
            log_file_to_display = os.path.join(LOGS_DIR, core_log_filename) # Path al log de core_logic
            try:
                def read_log_file(file_path, max_lines=500):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: lines = f.readlines()
                        return "".join(lines[-max_lines:])
                    except: return f"No se pudo leer el archivo de log: {file_path}"
                
                log_content = read_log_file(log_file_to_display) 
                st.text_area("Log de Operaciones (core_logic)", value=log_content, height=400, key='log_display_core_logic', disabled=True)
            except Exception as e: st.error(f"Error al mostrar el archivo de log: {e}")

    elif not st.session_state.scraping_in_progress :
         st.info("⬅️ Configura una tarea en la barra lateral y presiona 'Iniciar Scraping' para comenzar.")

# Para depuración:
# with st.expander("Ver Session State (DEBUG)"):
#    st.write(st.session_state)