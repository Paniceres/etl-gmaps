import streamlit as st
import json
import os
import pandas as pd
import sys
import time
from datetime import datetime
from threading import Thread
import threading
import queue 
import logging # IMPORTACIÓN AÑADIDA



# --- Añadir src al PYTHONPATH para importar core_logic ---
APP_ROOT_DIR = os.path.dirname(__file__) if '__file__' in locals() else os.getcwd()
SRC_DIR = os.path.join(APP_ROOT_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

CORE_LOGIC_LOADED = False
# Definir Dummies ANTES del try-except
class DummyLogger:
    def __init__(self, *args, **kwargs): self.name = kwargs.get('logger_name', 'DummyLogger')
    def _log_print(self, level, msg, art): print(f"{datetime.now().strftime('%H:%M:%S')} [{level}] ({self.name}) {art} {msg}")
    def info(self, msg, art="[INFO]"): self._log_print("INFO", msg, art)
    def error(self, msg, exc_info=False, art="[FAIL]"): self._log_print("ERROR", msg, art)
    def warning(self, msg, art="[WARN]"): self._log_print("WARNING", msg, art)
    def success(self, msg, art="[OK]"): self._log_print("SUCCESS", msg, art)
    def section(self, title): self._log_print("INFO", f"SECTION: {str(title).upper()}", "")
    def subsection(self, title): self._log_print("INFO", f"SUBSECTION: {str(title)}", "")
    def print_header_art_to_console(self): print(f"--- DUMMY LOGGER HEADER ({self.name}) ---")
    def get_header_art_text(self): return f"--- DUMMY LOGGER HEADER ({self.name}) ---"
    def critical(self, msg, exc_info=False, art="[CRIT]"): self._log_print("CRITICAL", msg, art)
    def debug(self, msg, art="[DEBUG]"): self._log_print("DEBUG", msg, art)

def dummy_load_keywords_func(*args): return ["dummy_kw1", "dummy_kw2"]
def dummy_process_city_func(*args, **kwargs): 
    logger_instance = kwargs.get('logger_instance', DummyLogger(logger_name="DummyProcessCity"))
    city_key = kwargs.get('city_key', 'dummy_city')
    logger_instance.error(f"Usando process_city_data_core DUMMY para {city_key}.")
    time.sleep(0.2) 
    dummy_df = pd.DataFrame({
        'title':['dummy place ' + city_key], 'emails':[f'd@{city_key}.co'], 'link':[f'd.{city_key}.co'], 
        'category':['Dummy'], 'search_origin_city':[city_key], 'website': [f'http://{city_key}.com'], 
        'latitude': [-38.0], 'longitude':[-68.0], 'review_count': [5], 'review_rating': [4.0],
        'address': ['Dummy Addr'], 'parsed_street': ['Street X'], 'parsed_city_comp': [city_key],
        'parsed_postal_code': ['0000'], 'parsed_state': ['StateX'], 'parsed_country': ['CountryX'],
        'phone': ['12345']
    })
    # Asegurar que el dummy DF tenga todas las columnas de gmaps_column_names_list_app si se va a usar para stats
    for col in gmaps_column_names_list_app_ref: # Usar referencia a la lista que se usará
        if col not in dummy_df.columns:
            dummy_df[col] = pd.NA
    return dummy_df, f"dummy_raw_{city_key}.csv"

StyledLogger_cls_app = DummyLogger
gmaps_column_names_list_app_ref = ['title', 'emails', 'link', 'category', 'search_origin_city', 'website', 'latitude', 'longitude',
                               'review_count', 'review_rating', 'address', 'parsed_street', 'parsed_city_comp', 
                               'parsed_postal_code', 'parsed_state', 'parsed_country', 'phone'] 
load_keywords_from_csv_func_app = dummy_load_keywords_func
process_city_data_func_app = dummy_process_city_func

try:
    from core_logic import StyledLogger, gmaps_column_names, load_keywords_from_csv_core, process_city_data_core
    StyledLogger_cls_app = StyledLogger
    gmaps_column_names_list_app_ref = gmaps_column_names # Referencia a la lista real
    load_keywords_from_csv_func_app = load_keywords_from_csv_core
    process_city_data_func_app = process_city_data_core
    CORE_LOGIC_LOADED = True
    print("INFO (app_streamlit): core_logic.py cargado exitosamente.")
except ImportError as e:
    print(f"ERROR CRITICO (app_streamlit): No se pudo importar de 'core_logic.py': {e}. Usando Dummies.")
except Exception as e_general: # Captura otros posibles errores durante la importación
    print(f"ERROR CRITICO GENERAL (app_streamlit) durante importación de core_logic: {e_general}. Usando Dummies.")

# --- Configuración de Rutas y Parámetros ---
CONFIG_DIR_APP = os.path.join(APP_ROOT_DIR, 'config')
DATA_DIR_APP = os.path.join(APP_ROOT_DIR, 'data')
RAW_DATA_DIR_APP = os.path.join(DATA_DIR_APP, 'raw')
PROCESSED_DATA_DIR_APP = os.path.join(DATA_DIR_APP, 'processed')
LOGS_DIR_APP = os.path.join(DATA_DIR_APP, 'logs')

os.makedirs(RAW_DATA_DIR_APP, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR_APP, exist_ok=True)
os.makedirs(LOGS_DIR_APP, exist_ok=True)

CONFIG_FILE_PATH_APP = os.path.join(CONFIG_DIR_APP, 'parameters_default.json')
CORE_LOGIC_LOG_FILENAME_DEFAULT_APP = 'agent_core_logic.log' 

FALLBACK_CONFIG_APP = {
    'gmaps_coordinates': {'neuquen_fb': {'latitude': -38.9516, 'longitude': -68.0591, 'radius':10000, 'zoom':14}},
    'default_depth': 1, 'language': 'es', 'results_filename_prefix': 'gmaps_data_',
    'log_filename': CORE_LOGIC_LOG_FILENAME_DEFAULT_APP
}
config_params_app = {}
try:
    with open(CONFIG_FILE_PATH_APP, 'r', encoding='utf-8') as f:
        config_params_app = json.load(f)
    print(f"INFO (app_streamlit): Archivo de config '{CONFIG_FILE_PATH_APP}' cargado.")
except Exception as e_cfg:
    print(f"ADVERTENCIA (app_streamlit): No se pudo cargar '{CONFIG_FILE_PATH_APP}'. Usando config de fallback. Error: {e_cfg}")
    config_params_app = FALLBACK_CONFIG_APP

# --- Loggers ---
streamlit_ui_log_filename = "streamlit_ui_events.log"
streamlit_ui_log_path_app = os.path.join(LOGS_DIR_APP, streamlit_ui_log_filename)
ui_logger = StyledLogger_cls_app(logger_name="StreamlitAppUI", log_file_path=streamlit_ui_log_path_app, level=logging.DEBUG)

core_logic_log_filename_cfg = config_params_app.get('log_filename', FALLBACK_CONFIG_APP['log_filename'])
core_logic_log_file_path_app = os.path.join(LOGS_DIR_APP, core_logic_log_filename_cfg)

# --- Inicializar Session State ---
default_ss_vals = {
    'selected_cities_keywords_ui': {}, 'processed_city_data_results': {}, 'scraping_done': False,
    'scraping_in_progress': False, 'final_df_consolidated': pd.DataFrame(), 
    'last_selected_cities': list(config_params_app.get('gmaps_coordinates', FALLBACK_CONFIG_APP['gmaps_coordinates']).keys())[:1],
    'last_search_depth': config_params_app.get('default_depth', FALLBACK_CONFIG_APP['default_depth']),
    'last_extract_emails': True, 'log_messages_queue': queue.Queue(),
    'current_process_status': "Listo para iniciar.", 'current_log_display': ""
}
for key, value in default_ss_vals.items():
    if key not in st.session_state: st.session_state[key] = value

# --- Funciones Auxiliares de UI ---
def get_paths_config_dict_app():
    return {'CONFIG_DIR': CONFIG_DIR_APP, 'RAW_DATA_DIR': RAW_DATA_DIR_APP,
            'PROCESSED_DATA_DIR': PROCESSED_DATA_DIR_APP, 'LOGS_DIR': LOGS_DIR_APP}

class QueueLogHandler(logging.Handler):
    def __init__(self, log_q):
        super().__init__()
        self.log_q = log_q
        # Usar un formato más simple para los logs que van a la UI
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))
    def emit(self, record): self.log_q.put(self.format(record))

# --- Función que se ejecuta en el Thread ---
# --- Función que se ejecuta en el Thread ---
def execute_scraping_task_threaded(
    selected_cities_list_thread, depth_ui_thread, emails_ui_thread, 
    cfg_params_thread, paths_cfg_thread, log_q_thread
):
    # Crear instancia de logger DENTRO del thread
    current_thread_id = threading.get_ident() # Ya tenías esta corrección aquí
    thread_logger_instance = StyledLogger_cls_app(
        logger_name=f"CoreLogicThread-{current_thread_id}", # Y aquí
        log_file_path=core_logic_log_file_path_app, 
        level=logging.DEBUG
    )
    
    # Configurar el QueueLogHandler
    has_queue_handler = any(isinstance(h, QueueLogHandler) for h in thread_logger_instance.logger.handlers)
    if not has_queue_handler:
        queue_handler_thread = QueueLogHandler(log_q_thread)
        thread_logger_instance.logger.addHandler(queue_handler_thread)
    thread_logger_instance.logger.propagate = False

    try:
        log_q_thread.put("PROCESO_START:Iniciando tarea de scraping...")
        # CORRECCIÓN AQUÍ:
        thread_logger_instance.section(f"Nueva Tarea (Thread: {current_thread_id})") 
        thread_logger_instance.info(f"Ciudades: {selected_cities_list_thread}, Prof: {depth_ui_thread}, Emails: {emails_ui_thread}")
        
        temp_processed_city_data_thread = {}
        temp_all_city_dfs_thread = []
        
        for i, city_k_thread in enumerate(selected_cities_list_thread):
            log_q_thread.put(f"STATUS_UPDATE:Procesando {city_k_thread.capitalize()} ({i+1}/{len(selected_cities_list_thread)})...")
            
            keywords_str_ui = st.session_state.selected_cities_keywords_ui.get(city_k_thread, "")
            keywords_list_ui = [kw.strip() for kw in keywords_str_ui.splitlines() if kw.strip()]
            
            if not keywords_list_ui:
                msg_no_kw = f"Sin keywords para {city_k_thread.capitalize()}. Omitiendo."
                thread_logger_instance.warning(msg_no_kw)
                log_q_thread.put(f"INFO:{msg_no_kw}")
                continue
            
            df_transformed_city, raw_path_city = process_city_data_func_app( # Esta es process_city_data_core si CORE_LOGIC_LOADED es True
                city_key=city_k_thread, keywords_list=keywords_list_ui, depth_from_ui=depth_ui_thread, 
                extract_emails_flag=emails_ui_thread, config_params_dict=cfg_params_thread, 
                paths_config_dict=paths_cfg_thread, logger_instance=thread_logger_instance
            )
            
            temp_processed_city_data_thread[city_k_thread] = {'df': df_transformed_city, 'raw_path': raw_path_city}
            
            if df_transformed_city is not None and not df_transformed_city.empty:
                temp_all_city_dfs_thread.append(df_transformed_city)
                log_q_thread.put(f"SUCCESS:{city_k_thread.capitalize()} procesada ({len(df_transformed_city)} prosp). Raw: {os.path.basename(str(raw_path_city or 'N/A'))}")
            elif df_transformed_city is not None:
                log_q_thread.put(f"INFO:{city_k_thread.capitalize()} (0 prosp). Raw: {os.path.basename(str(raw_path_city or 'N/A'))}")
            else:
                log_q_thread.put(f"ERROR:Falló {city_k_thread.capitalize()}. Raw: {os.path.basename(str(raw_path_city or 'N/A'))}")
        
        final_df_payload_thread = pd.DataFrame(columns=gmaps_column_names_list_app_ref) 
        if temp_all_city_dfs_thread:
            try:
                final_df_payload_thread = pd.concat(temp_all_city_dfs_thread, ignore_index=True)
            except Exception as e_concat:
                thread_logger_instance.error(f"Error al concatenar DataFrames: {e_concat}", exc_info=True)
                log_q_thread.put(f"ERROR_CRITICAL_THREAD:Error al consolidar datos: {e_concat}")
        
        log_q_thread.put({"type": "FINAL_RESULTS", "data": final_df_payload_thread, 
                          "processed_city_data": temp_processed_city_data_thread})
        thread_logger_instance.section("Tarea de Scraping (Thread) Finalizada")

    except Exception as e_thread_main:
        thread_logger_instance.critical(f"Error mayor en thread de scraping: {str(e_thread_main)}", exc_info=True)
        log_q_thread.put({"type": "CRITICAL_ERROR", "message": str(e_thread_main)})
    finally:
        log_q_thread.put("THREAD_COMPLETE_SIGNAL")


# --- UI ---
st.set_page_config(page_title="Agente GOSOM ETL", layout="wide", initial_sidebar_state="expanded")

# Placeholder para el Header ASCII en la UI, se llenará al final o si no hay scraping
header_placeholder_ui_main = st.empty() 

st.title('🚀✨ Agente GOSOM ETL')
st.markdown("Herramienta para extraer y procesar leads de Google Maps.")

if not CORE_LOGIC_LOADED:
    st.error("¡ADVERTENCIA CRÍTICA! El módulo 'core_logic.py' no pudo cargar. La funcionalidad de scraping estará DESHABILITADA. Revisa la consola del servidor Streamlit para errores de importación detallados.")

with st.sidebar:
    st.header('⚙️ Configurar Tarea')
    gmaps_coords_opts = list(config_params_app.get('gmaps_coordinates', {}).keys())
    
    selected_cities_keys_ui = st.multiselect(
        '🏙️ Seleccionar Ciudad(es)', options=gmaps_coords_opts, 
        default=st.session_state.last_selected_cities, 
        disabled=st.session_state.scraping_in_progress
    )
    if selected_cities_keys_ui != st.session_state.last_selected_cities:
        st.session_state.last_selected_cities = selected_cities_keys_ui
    
    if selected_cities_keys_ui:
        st.subheader("✏️ Keywords por Ciudad")
        for city_k_ui in selected_cities_keys_ui:
            if city_k_ui not in st.session_state.selected_cities_keywords_ui:
                kws = load_keywords_from_csv_func_app(CONFIG_DIR_APP, city_k_ui, ui_logger)
                st.session_state.selected_cities_keywords_ui[city_k_ui] = "\n".join(kws)
            
            st.session_state.selected_cities_keywords_ui[city_k_ui] = st.text_area(
                label=f'Keywords para {city_k_ui.capitalize()}', 
                value=st.session_state.selected_cities_keywords_ui[city_k_ui], 
                key=f'kw_ta_{city_k_ui}', height=100, 
                disabled=st.session_state.scraping_in_progress
            )
    
    depth_ui_val = st.number_input('🎯 Profundidad', min_value=1, max_value=20, 
                               value=int(st.session_state.last_search_depth), 
                               disabled=st.session_state.scraping_in_progress,
                               help="Número de 'páginas' de resultados a scrapear por keyword.")
    st.session_state.last_search_depth = depth_ui_val
    
    emails_ui_val = st.checkbox('📧 ¿Extraer Emails? (⚠️ Puede tardar más)', 
                            value=st.session_state.last_extract_emails, 
                            disabled=st.session_state.scraping_in_progress)
    st.session_state.last_extract_emails = emails_ui_val
    
    if st.button('🚀 Iniciar Scraping', 
                 disabled=st.session_state.scraping_in_progress or not CORE_LOGIC_LOADED, 
                 type="primary", use_container_width=True):
        if not selected_cities_keys_ui: 
            st.warning('Por favor, selecciona al menos una ciudad.')
        elif not CORE_LOGIC_LOADED: 
            st.error("No se puede iniciar: 'core_logic.py' no cargó correctamente.")
        else:
            st.session_state.current_process_status = "Iniciando tarea..."
            st.session_state.current_log_display = "" 
            while not st.session_state.log_messages_queue.empty():
                try: st.session_state.log_messages_queue.get_nowait()
                except queue.Empty: break
            
            st.session_state.scraping_in_progress = True 
            st.session_state.scraping_done = False
            st.session_state.processed_city_data_results = {}
            st.session_state.final_df_consolidated = pd.DataFrame()
            
            ui_logger.info(f"Botón 'Iniciar Scraping' presionado. Ciudades: {selected_cities_keys_ui}")
            
            thread = Thread(target=execute_scraping_task_threaded, args=(
                selected_cities_keys_ui, depth_ui_val, emails_ui_val, 
                config_params_app, get_paths_config_dict_app(), st.session_state.log_messages_queue
            ))
            st.session_state.scraping_thread = thread
            thread.start()
            st.rerun()


# --- Área Principal ---
main_area_placeholder = st.empty() # Usar un placeholder para toda el área principal

if st.session_state.scraping_in_progress:
    with main_area_placeholder.container(): # Escribir dentro del placeholder
        st.header("⏳ Progreso del Scraping...")
        status_text_placeholder_live = st.empty()
        log_display_placeholder_live = st.empty()
        
        new_log_entries = []
        final_results_from_queue = None
        critical_error_from_queue = None
        thread_completed_signal_received = False

        while not st.session_state.log_messages_queue.empty():
            try:
                msg_item = st.session_state.log_messages_queue.get_nowait()
                if isinstance(msg_item, dict): 
                    if msg_item.get("type") == "FINAL_RESULTS": final_results_from_queue = msg_item
                    elif msg_item.get("type") == "CRITICAL_ERROR": critical_error_from_queue = msg_item
                elif isinstance(msg_item, str):
                    if msg_item == "THREAD_COMPLETE_SIGNAL": thread_completed_signal_received = True; break
                    elif msg_item.startswith("PROCESO_") or msg_item.startswith("STATUS_") :
                        st.session_state.current_process_status = msg_item.split(":", 1)[1]
                    new_log_entries.append(msg_item)
            except queue.Empty: break
        
        if new_log_entries:
            st.session_state.current_log_display += "\n".join(new_log_entries) + "\n"
            st.session_state.current_log_display = "\n".join(st.session_state.current_log_display.splitlines()[-200:]) # Mantener últimas 200 líneas

        status_text_placeholder_live.info(st.session_state.current_process_status)
        log_display_placeholder_live.code(st.session_state.current_log_display, language='log')

        current_thread_ui_check = st.session_state.get('scraping_thread')
        if thread_completed_signal_received or not (current_thread_ui_check and current_thread_ui_check.is_alive()):
            # El thread terminó (ya sea por señal o porque is_alive() es False)
            st.session_state.scraping_in_progress = False
            st.session_state.scraping_done = True
            if final_results_from_queue:
                st.session_state.final_df_consolidated = final_results_from_queue['data']
                st.session_state.processed_city_data_results = final_results_from_queue['processed_city_data']
            if critical_error_from_queue:
                st.session_state.current_process_status = f"ERROR CRÍTICO: {critical_error_from_queue['message']}"
            ui_logger.info("Thread de scraping ha finalizado (detectado por señal o is_alive). Actualizando UI a estado 'done'.")
            st.rerun() # Forzar re-render para mostrar sección de resultados
        else: # El thread sigue vivo y no hemos recibido la señal de fin
            time.sleep(1) 
            st.rerun()

elif st.session_state.scraping_done:
    with main_area_placeholder.container(): # Escribir dentro del placeholder
        st.header("🏁 Tarea de Scraping Completada")
        st.info(f"Estado final del proceso: {st.session_state.current_process_status}")

        # MOVER EL HEADER ASCII AQUÍ
        if CORE_LOGIC_LOADED and hasattr(ui_logger, 'get_header_art_text'):
             st.code(ui_logger.get_header_art_text(), language='text')
        elif not CORE_LOGIC_LOADED and hasattr(DummyLogger((),{}), 'get_header_art_text'):
             st.code(DummyLogger((),{}).get_header_art_text(), language='text')
        
        st.subheader("📜 Logs Detallados de la Ejecución")
        with st.expander("Ver Logs de Operaciones y UI", expanded=True): # Expandido por defecto
            log_tab_core_final, log_tab_ui_final = st.tabs(["Log Core Logic", "Log Eventos UI"])
            def read_log_file_content_final(fp, max_lines=300):
                try:
                    if os.path.exists(fp):
                        with open(fp, 'r', encoding='utf-8', errors='ignore') as f: 
                            return "".join(f.readlines()[-max_lines:])
                    return f"Archivo de log no encontrado o vacío: {fp}"
                except Exception as e_log_read: return f"Error al leer log {fp}: {e_log_read}"

            with log_tab_core_final:
                st.caption(f"Últimas líneas de: {core_logic_log_file_path_app}")
                st.code(read_log_file_content_final(core_logic_log_file_path_app), language='log', line_numbers=True)
            with log_tab_ui_final:
                st.caption(f"Últimas líneas de: {streamlit_ui_log_path_app}")
                st.code(read_log_file_content_final(streamlit_ui_log_path_app), language='log', line_numbers=True)
        
        st.markdown("---") 

        st.header("📊 Resultados y Estadísticas")
        df_final = st.session_state.final_df_consolidated
        
        res_tab_data, res_tab_stats = st.tabs(["📄 Datos Procesados", "📈 Resumen"])
        
        with res_tab_data: 
            st.subheader("Datos Consolidados y Procesados")
            if df_final is not None and not df_final.empty: # Chequeo más robusto
                st.dataframe(df_final) 
                try:
                    csv_dl_bytes = df_final.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(label="📥 Descargar CSV Consolidado", data=csv_dl_bytes,
                                       file_name=f"gmaps_prospectos_consolidados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                       mime='text/csv', key="download_consolidated_main")
                except Exception as e_csv_dl: st.error(f"Error al generar CSV para descarga: {e_csv_dl}")

                st.subheader("CSVs Crudos Individuales (por ciudad procesada)")
                if st.session_state.processed_city_data_results:
                    for city_res_key, city_res_data in st.session_state.processed_city_data_results.items():
                        raw_path_res = city_res_data.get('raw_path')
                        df_city_processed = city_res_data.get('df')
                        if raw_path_res and os.path.exists(raw_path_res):
                            with open(raw_path_res, "rb") as fp_raw:
                                st.download_button(
                                    label=f"📥 Crudo - {city_res_key.capitalize()} ({len(df_city_processed) if df_city_processed is not None else 'N/A'} filas procesadas)",
                                    data=fp_raw, file_name=os.path.basename(raw_path_res),
                                    mime="text/csv", key=f"download_raw_{city_res_key}"
                                )
                        elif raw_path_res: # Si el path existe pero el archivo no (fallo en GOSOM)
                            st.caption(f"Archivo crudo para {city_res_key.capitalize()} no generado o vacío. Path: {raw_path_res}")
                        else: # Si el path es None
                             st.caption(f"No hubo intento de generar archivo crudo para {city_res_key.capitalize()} o falló muy temprano.")
                else:
                    st.info("No hay información de archivos crudos individuales disponible.")
            else: 
                st.info("No hay datos procesados para mostrar o descargar.")
        
        with res_tab_stats: 
            st.subheader("Análisis General de Prospectos")
            if df_final is not None and not df_final.empty:
                df_unique_stats = df_final.drop_duplicates(subset=['link'], keep='first') if 'link' in df_final.columns else df_final
                total_unique_prospectos = len(df_unique_stats)
                st.metric("Prospectos Únicos (por link Gmaps)", f"{total_unique_prospectos}")
                
                cols_m_stats = st.columns(3)
                email_c_stats = df_unique_stats['emails'].notna().sum() if 'emails' in df_unique_stats.columns else 0
                cols_m_stats[0].metric("📧 Con Email", f"{email_c_stats} ({ (email_c_stats/total_unique_prospectos*100) if total_unique_prospectos > 0 else 0 :.1f}%)")
                
                web_c_stats = df_unique_stats['website'].notna().sum() if 'website' in df_unique_stats.columns else 0
                cols_m_stats[1].metric("🌐 Con Website", f"{web_c_stats} ({ (web_c_stats/total_unique_prospectos*100) if total_unique_prospectos > 0 else 0 :.1f}%)")
                
                phone_c_stats = df_unique_stats['phone'].notna().sum() if 'phone' in df_unique_stats.columns else 0
                cols_m_stats[2].metric("📞 Con Teléfono", f"{phone_c_stats} ({ (phone_c_stats/len(df_unique_stats)*100) if total_unique_prospectos > 0 else 0 :.1f}%)")

                if 'search_origin_city' in df_unique_stats.columns and not df_unique_stats['search_origin_city'].dropna().empty:
                    st.subheader("Prospectos por Ciudad de Origen")
                    st.bar_chart(df_unique_stats['search_origin_city'].value_counts())
                
                if 'category' in df_unique_stats.columns and not df_unique_stats['category'].dropna().empty:
                    st.subheader("Top 10 Categorías")
                    st.bar_chart(df_unique_stats['category'].value_counts().nlargest(10))

                if 'latitude' in df_unique_stats.columns and 'longitude' in df_unique_stats.columns:
                    df_map_data_final = df_unique_stats[['latitude', 'longitude']].dropna()
                    if not df_map_data_final.empty:
                        st.subheader("🗺️ Distribución Geográfica")
                        st.map(df_map_data_final.head(5000))
            else: 
                st.info("No hay datos procesados para mostrar estadísticas.")
else: # Estado inicial
    with main_area_placeholder.container(): # Escribir dentro del placeholder
        st.info("⬅️ Configura una tarea en la barra lateral y presiona 'Iniciar Scraping' para comenzar.")
        # Mostrar el header ASCII aquí solo si core_logic cargó bien y la UI está en estado inicial
        if CORE_LOGIC_LOADED and hasattr(ui_logger, 'get_header_art_text'):
            st.code(ui_logger.get_header_art_text(), language='text')
        elif not CORE_LOGIC_LOADED and hasattr(DummyLogger((),{}), 'get_header_art_text'):
             st.code(DummyLogger((),{}).get_header_art_text(), language='text')

# --- Pie de página ---
st.sidebar.markdown("---")
st.sidebar.caption(f"Agente GOSOM ETL - MVP v0.3 | Core Logic: {'Cargado OK' if CORE_LOGIC_LOADED else 'FALLÓ / DUMMY'}")