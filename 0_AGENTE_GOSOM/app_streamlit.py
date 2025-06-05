import streamlit as st
import json
import os
import pandas as pd
import sys
import time
from datetime import datetime, timedelta 
from threading import Thread
import threading 
import queue 
import logging 


# --- Definición de Rutas Base ---
try:
    APP_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError: 
    APP_ROOT_DIR = os.getcwd() 


print(f"DEBUG (app_streamlit INIT): APP_ROOT_DIR={APP_ROOT_DIR}") # Quitar para producción


SRC_DIR = os.path.join(APP_ROOT_DIR, 'src')
CONFIG_DIR_APP = os.path.join(APP_ROOT_DIR, 'config')
DATA_DIR_APP = os.path.join(APP_ROOT_DIR, 'data')
LOGS_DIR_APP = os.path.join(DATA_DIR_APP, 'logs')
RAW_DATA_DIR_APP = os.path.join(DATA_DIR_APP, 'raw')
PROCESSED_DATA_DIR_APP = os.path.join(DATA_DIR_APP, 'processed')


for dir_path_init in [SRC_DIR, CONFIG_DIR_APP, DATA_DIR_APP, LOGS_DIR_APP, RAW_DATA_DIR_APP, PROCESSED_DATA_DIR_APP]:
    try: os.makedirs(dir_path_init, exist_ok=True)
    except Exception as e_mkdir_init_loop: print(f"ERROR (app_streamlit INIT): Creando dir {dir_path_init}: {e_mkdir_init_loop}")

if SRC_DIR not in sys.path: sys.path.append(SRC_DIR)


CORE_LOGIC_LOADED = False
class DummyLogger:
    def __init__(self, *args, **kwargs): self.name = kwargs.get('logger_name', 'DummyLoggerUI')
    def _log_print(self, level, msg, art): print(f"{datetime.now().strftime('%H:%M:%S')} [{level}] ({self.name}) {art} {msg}")
    def info(self, msg, art="[INFO]"): self._log_print("INFO", msg, art)
    def error(self, msg, exc_info=False, art="[FAIL]"): self._log_print("ERROR", msg, art);print(msg) # Print error to console too
    def warning(self, msg, art="[WARN]"): self._log_print("WARNING", msg, art)
    def success(self, msg, art="[OK]"): self._log_print("SUCCESS", msg, art)
    def section(self, title): self._log_print("INFO", f"SECTION: {str(title).upper()}", "")
    def subsection(self, title): self._log_print("INFO", f"SUBSECTION: {str(title)}", "")
    def get_header_art_text(self): return f"--- DUMMY LOGGER HEADER ({self.name}) ---\n(core_logic.py no cargó)"
    def critical(self, msg, exc_info=False, art="[CRIT]"): self._log_print("CRITICAL", msg, art);print(msg)
    def debug(self, msg, art="[DEBUG]"): self._log_print("DEBUG", msg, art)
    def __getattr__(self, name): 
        if name == 'logger': _dummy_py_logger = logging.getLogger(self.name + "_int_dummy"); return _dummy_py_logger
        return lambda *args, **kwargs: None
def dummy_load_keywords_func(*args, **kwargs): return ["dummy_kw1", "dummy_kw2"]
gmaps_column_names_list_app_fallback = ['title', 'emails', 'link'] 
def dummy_process_city_func(*args, **kwargs): 
    logger_instance = kwargs.get('logger_instance', DummyLogger(logger_name="DummyProcCity"))
    city_key = kwargs.get('city_key', 'dummy_city')
    time.sleep(0.1); log_q_thread.put(f"GOSOM_LOG:Dummy GOSOM log 1 para {city_key}")
    time.sleep(0.1); log_q_thread.put(f"GOSOM_LOG:Dummy GOSOM log 2 para {city_key}")
    dummy_df = pd.DataFrame({'title':['dummy ' + city_key], 'emails':['d@e.co'], 'link':['d.co']})
    for col in gmaps_column_names_list_app_fallback: 
        if col not in dummy_df.columns: dummy_df[col] = pd.NA
    log_q_thread.put({"type": "LIVE_ROW_COUNT", "city": city_key, "count": len(dummy_df)})
    log_q_thread.put({"type": "ROW_COUNT_UPDATE", "city": city_key, "count": len(dummy_df), 
                      "cumulative_count": st.session_state.get('cumulative_row_count',0) + len(dummy_df) })
    return dummy_df, f"dummy_raw_{city_key}.csv"


StyledLogger_cls_app = DummyLogger

# --- Constantes para Tipos de Mensajes en la Cola ---
# Usar una clase para simular un Enum, mejor que literales string
class LogMessageType:
    FINAL_RESULTS = "FINAL_RESULTS"
    CRITICAL_ERROR = "CRITICAL_ERROR"
    LIVE_ROW_COUNT = "LIVE_ROW_COUNT"
    ROW_COUNT_UPDATE = "ROW_COUNT_UPDATE" # Usado en dummy, no en core logic actual, pero mantenido
    THREAD_COMPLETE_SIGNAL = "THREAD_COMPLETE_SIGNAL"
    PROCESO_START = "PROCESO_START" # Prefijo para inicio de proceso por ciudad/tarea
    STATUS_UPDATE = "STATUS_UPDATE" # Prefijo para updates de estado intermedio
    GOSOM_LOG = "GOSOM_LOG" # Prefijo para logs directos de la salida de GOSOM (docker)
    CMD_DOCKER = "CMD_DOCKER" # Prefijo para el comando docker ejecutado
    # Se podrían añadir más si se filtran otros tipos de logs directamente en la cola
    # Por ahora, los logs 'INFO', 'ERROR', 'SUCCESS' etc. del logger pasan directo como string

gmaps_column_names_list_app = gmaps_column_names_list_app_fallback
load_keywords_from_csv_func_app = dummy_load_keywords_func
process_city_data_func_app = dummy_process_city_func

try:
    from core_logic import StyledLogger, gmaps_column_names, load_keywords_from_csv_core, process_city_data_core
    StyledLogger_cls_app = StyledLogger
    gmaps_column_names_list_app = gmaps_column_names 
    load_keywords_from_csv_func_app = load_keywords_from_csv_core
    process_city_data_func_app = process_city_data_core
    CORE_LOGIC_LOADED = True
    # Quitar prints de la consola de Streamlit, usar logs
    # print("INFO (app_streamlit): core_logic.py cargado exitosamente.")
except ImportError as e:
    print(f"ERROR CRITICO (app_streamlit): No se pudo importar de 'core_logic.py': {e}. Usando Dummies.")
except Exception as e_general: 
    print(f"ERROR CRITICO GENERAL (app_streamlit) durante importación de core_logic: {e_general}. Usando Dummies.")

CONFIG_FILE_PATH_APP = os.path.join(CONFIG_DIR_APP, 'parameters_default.json')
CORE_LOGIC_LOG_FILENAME_DEFAULT_APP = 'agent_core_logic.log' 
FALLBACK_CONFIG_APP = {
    'gmaps_coordinates': {'neuquen_fb': {'latitude': -38.9516, 'longitude': -68.0591, 'radius':10000, 'zoom':14}},
    'default_depth': 1, 'language': 'es', 'results_filename_prefix': 'gmaps_data_',
    'log_filename': CORE_LOGIC_LOG_FILENAME_DEFAULT_APP
}
config_params_app = {}
try:
    with open(CONFIG_FILE_PATH_APP, 'r', encoding='utf-8') as f: config_params_app = json.load(f)
    ui_logger.info(f"Configuración cargada desde {CONFIG_FILE_PATH_APP}.")
except Exception as e_config_load:
    ui_logger.critical(f"No se pudo cargar el archivo de configuración {CONFIG_FILE_PATH_APP}: {e_config_load}", exc_info=True)
    config_params_app = FALLBACK_CONFIG_APP

streamlit_ui_log_filename = "streamlit_ui_events.log"
streamlit_ui_log_path_app = os.path.join(LOGS_DIR_APP, streamlit_ui_log_filename) 
ui_logger = StyledLogger_cls_app(logger_name="StreamlitAppUI", log_file_path=streamlit_ui_log_path_app, level=logging.DEBUG)

core_logic_log_filename_cfg = config_params_app.get('log_filename', FALLBACK_CONFIG_APP['log_filename'])
core_logic_log_file_path_app = os.path.join(LOGS_DIR_APP, core_logic_log_filename_cfg)

default_ss_vals = {
    'selected_cities_keywords_ui': {}, 'processed_city_data_results': {}, 'scraping_done': False,
    'scraping_in_progress': False, 'final_df_consolidated': pd.DataFrame(columns=gmaps_column_names_list_app), 
    'last_selected_cities': list(config_params_app.get('gmaps_coordinates', {}).keys())[:1] if config_params_app.get('gmaps_coordinates') else [], # Fallback a dict vacío
    'last_search_depth': int(config_params_app.get('default_depth', 1)),
    'last_extract_emails': True, 'log_messages_queue': queue.Queue(),
    'current_process_status': "Listo para iniciar.", 'current_log_display': "Logs de la operación aparecerán aquí...\n",
    'start_time': None, 'cumulative_row_count': 0, 'stop_scraping_flag': False,
    'live_csv_row_counts': {} # {city_key: count}
}
for key, value in default_ss_vals.items():
    if key not in st.session_state: st.session_state[key] = value

def get_paths_config_dict_app():
    return {'CONFIG_DIR': CONFIG_DIR_APP, 'RAW_DATA_DIR': RAW_DATA_DIR_APP,
            'PROCESSED_DATA_DIR': PROCESSED_DATA_DIR_APP, 'LOGS_DIR': LOGS_DIR_APP}

class QueueLogHandler(logging.Handler):
    def __init__(self, log_q):
        super().__init__(); self.log_q = log_q
        self.setFormatter(logging.Formatter('%(asctime)s-%(levelname)s: %(message)s',datefmt='%H:%M:%S'))
    def emit(self, record): self.log_q.put(self.format(record))

def execute_scraping_task_threaded(
    selected_cities_list_thread, keywords_per_city_thread_dict,
 depth_ui_thread, emails_ui_thread,
    cfg_params_thread, paths_cfg_thread, log_q_thread ):
    current_thread_id = threading.get_ident()
    log_path_for_thread_core = core_logic_log_file_path_app 

    # Limpiar logs de la cola al inicio de cada ejecución
 while not log_q_thread.empty():
 try: log_q_thread.get_nowait()
 except queue.Empty: pass # Defensive

    thread_core_logger = StyledLogger_cls_app(logger_name=f"CoreLogicThread-{current_thread_id}",
                                          log_file_path=log_path_for_thread_core, level=logging.DEBUG)
    # Limpiar handlers de cola existentes para evitar duplicados si el thread se reutiliza (aunque no es el caso aquí)
    for handler_to_remove in list(thread_core_logger.logger.handlers):
        if isinstance(handler_to_remove, QueueLogHandler): # Check if handler is of type QueueLogHandler
 thread_core_logger.logger.removeHandler(handler_to_remove)

    queue_handler_for_thread = QueueLogHandler(log_q_thread)
    thread_core_logger.logger.addHandler(queue_handler_for_thread)
    thread_core_logger.logger.propagate = False
 
    try:
        log_q_thread.put(f"{LogMessageType.PROCESO_START}:Iniciando tarea de scraping...")
        thread_core_logger.section(f"Nueva Tarea (Thread: {current_thread_id})")
        thread_core_logger.info(f"Ciudades: {selected_cities_list_thread}, Prof: {depth_ui_thread}, Emails: {emails_ui_thread}")

        temp_processed_city_data_thread = {}
        temp_all_city_dfs_thread = []

        for i, city_k_thread in enumerate(selected_cities_list_thread):
            # Verificar la flag de detención de Streamlit a través de session_state
            # NOTA: Acceder a st.session_state desde otro thread NO es directamente seguro,
            # pero para esta flag simple y lectura periódica es un workaround común en Streamlit.
            # Un enfoque más robusto sería pasar la flag a través de la cola o un objeto compartido Thread-safe.
            if st.session_state.get('stop_scraping_flag', False): # type: ignore
                log_q_thread.put(f"{LogMessageType.INFO}:Scraping detenido para {city_k_thread.capitalize()}.")
                break # Salir del bucle for de ciudades
 
            log_q_thread.put(f"{LogMessageType.STATUS_UPDATE}:Procesando {city_k_thread.capitalize()} ({i+1}/{len(selected_cities_list_thread)})...")
            keywords_str_for_city = keywords_per_city_thread_dict.get(city_k_thread, "")
            keywords_list_for_city = [kw.strip() for kw in keywords_str_for_city.splitlines() if kw.strip()]
            if not keywords_list_for_city:
                log_q_thread.put(f"{LogMessageType.WARNING}:No keywords found for {city_k_thread.capitalize()}. Skipping.")
                continue

            df_transformed_city, raw_path_city = process_city_data_func_app(
 log_q_streamlit=log_q_thread, # Pass the queue to core_logic
 city_key=city_k_thread, keywords_list=keywords_list_for_city,
                depth_from_ui=depth_ui_thread, extract_emails_flag=emails_ui_thread,
 config_params_dict=cfg_params_thread, paths_config_dict=paths_cfg_thread,
 logger_instance=thread_core_logger, # Pass logger to core_logic
)\

            temp_processed_city_data_thread[city_k_thread] = {'df': df_transformed_city, 'raw_path': raw_path_city}
            if df_transformed_city is not None and not df_transformed_city.empty:
                temp_all_city_dfs_thread.append(df_transformed_city) # Añadir solo DFs no vacíos
                log_q_thread.put(f"{LogMessageType.SUCCESS}:{city_k_thread.capitalize()} ({len(df_transformed_city)} prosp.).")
            elif df_transformed_city is not None:
 log_q_thread.put(f"{LogMessageType.INFO}:{city_k_thread.capitalize()} (0 prosp).")
            else:
 log_q_thread.put(f"{LogMessageType.ERROR}:Falló {city_k_thread.capitalize()}.")

        final_df_payload_thread = pd.DataFrame(columns=gmaps_column_names_list_app)
        if temp_all_city_dfs_thread:
            try:
 final_df_payload_thread = pd.concat(temp_all_city_dfs_thread, ignore_index=True) # type: ignore
            except Exception as e_concat:
 log_q_thread.put({"type": LogMessageType.CRITICAL_ERROR, "message": f"Concat Error: {e_concat}"}) # Usar tipo de mensaje

        log_q_thread.put({"type": LogMessageType.FINAL_RESULTS, "data": final_df_payload_thread,
                          "processed_city_data": temp_processed_city_data_thread})
        thread_core_logger.section("Tarea Scraping (Thread) Finalizada")
    except Exception as e_thread_main:
        thread_core_logger.critical(f"Error mayor en thread: {str(e_thread_main)}", exc_info=True)
        log_q_thread.put({"type": LogMessageType.CRITICAL_ERROR, "message": str(e_thread_main)}) # Usar tipo de mensaje
    finally:
        log_q_thread.put(LogMessageType.THREAD_COMPLETE_SIGNAL)

# --- Helper functions for state management ---
def get_scraping_state():
    """Returns a dict with keys related to scraping progress."""
 return {
 'scraping_in_progress': st.session_state.get('scraping_in_progress', False),
 'scraping_done': st.session_state.get('scraping_done', False),
 'start_time': st.session_state.get('start_time', None),
 'current_process_status': st.session_state.get('current_process_status', "Listo para iniciar."),
 'cumulative_row_count': st.session_state.get('cumulative_row_count', 0),
 'live_csv_row_counts': st.session_state.get('live_csv_row_counts', {}),
 'stop_scraping_flag': st.session_state.get('stop_scraping_flag', False),
    }

def set_scraping_state(**kwargs):
    """Updates scraping state in st.session_state based on kwargs."""
 for key, value in kwargs.items():
 if key in ['scraping_in_progress', 'scraping_done', 'start_time', 'current_process_status',
 'cumulative_row_count', 'live_csv_row_counts', 'stop_scraping_flag']:
 st.session_state[key] = value


st.set_page_config(page_title="Agente GOSOM ETL", layout="wide", initial_sidebar_state="expanded")
st.title('🚀✨ Agente GOSOM ETL')
st.markdown("Herramienta para extraer y procesar leads de Google Maps.")

# NO mostrar el header ASCII de core_logic aquí en la UI. Se imprime en consola del server si core_logic carga.
if not CORE_LOGIC_LOADED:
 st.error("¡ADVERTENCIA CRÍTICA! El módulo 'core_logic.py' no pudo cargar correctamente. Usando funcionalidades limitadas (dummies).")

if config_params_app == FALLBACK_CONFIG_APP:
    st.error(f"¡ADVERTENCIA! No se pudo cargar el archivo de configuración ({os.path.basename(CONFIG_FILE_PATH_APP)}). Usando configuración por defecto.")


# --- Sidebar ---
with st.sidebar:
    st.header('⚙️ Configuración de Tarea')
    
    # Usar helper para obtener estado de scraping
    scraping_state = get_scraping_state()

    # Expanders para organizar la configuración
    with st.expander("📍 Selección de Ubicación y Palabras Clave", expanded=True):
        gmaps_coords_opts = list(config_params_app.get('gmaps_coordinates', {}).keys())
        selected_cities_keys_ui = st.multiselect(
            '🏙️ Seleccionar Ciudad(es)', options=gmaps_coords_opts,
            default=st.session_state.last_selected_cities,
            disabled=scraping_state['scraping_in_progress'], key="ms_cities_sidebar"
        )
        # Actualizar last_selected_cities si cambia
        if selected_cities_keys_ui != st.session_state.last_selected_cities:
            st.session_state.last_selected_cities = selected_cities_keys_ui

        if selected_cities_keys_ui:
            st.subheader("✏️ Keywords por Ciudad")
            for city_k_ui in selected_cities_keys_ui:
                if city_k_ui not in st.session_state.selected_cities_keywords_ui:
                    kws = load_keywords_from_csv_func_app(CONFIG_DIR_APP, city_k_ui, ui_logger)
                    st.session_state.selected_cities_keywords_ui[city_k_ui] = "\n".join(kws)
                st.session_state.selected_cities_keywords_ui[city_k_ui] = st.text_area(
                    f'Keywords para {city_k_ui.capitalize()}',
                    st.session_state.selected_cities_keywords_ui.get(city_k_ui, ""),
                    key=f'kw_ta_sidebar_{city_k_ui}', height=100, disabled=scraping_state['scraping_in_progress']
                )

    with st.expander("⚙️ Parámetros Avanzados", expanded=False):
        depth_ui_val = st.number_input(
            '🎯 Profundidad', min_value=1, max_value=20,
            value=int(st.session_state.last_search_depth),
            disabled=scraping_state['scraping_in_progress'], key="ni_depth_sidebar",
            help="Profundidad de búsqueda GOSOM. A mayor profundidad, más tiempo tarda."
        )
        st.session_state.last_search_depth = depth_ui_val

        emails_ui_val = st.checkbox(
            '📧 ¿Extraer Emails? (⚠️ Tarda más)',
            value=st.session_state.last_extract_emails,
            disabled=scraping_state['scraping_in_progress'], key="cb_emails_sidebar",
            help="Marcar para intentar extraer emails (puede aumentar significativamente el tiempo)."
        )
        st.session_state.last_extract_emails = emails_ui_val

    st.markdown("---")
    # Botones de control en dos columnas
    col_btn_start_s, col_btn_stop_s = st.columns(2)
    
    with col_btn_start_s:
        if st.button('🚀 Iniciar Scraping', key="btn_start_s_sidebar",
                     disabled=scraping_state['scraping_in_progress'] or not CORE_LOGIC_LOADED or not selected_cities_keys_ui,
                     type="primary", use_container_width=True):
            if not selected_cities_keys_ui:
                st.warning('Selecciona al menos una ciudad.')
            elif not CORE_LOGIC_LOADED:
                st.error("'core_logic.py' no cargó.")
            else:
                set_scraping_state(
                    current_process_status="Iniciando...", start_time=datetime.now(),
                    cumulative_row_count=0, live_csv_row_counts={city: 0 for city in selected_cities_keys_ui},
                    stop_scraping_flag=False, scraping_in_progress=True, scraping_done=False
                )
                st.session_state.current_log_display = "Iniciando Logs...\n"
                st.session_state.processed_city_data_results = {}
                st.session_state.final_df_consolidated = pd.DataFrame(columns=gmaps_column_names_list_app)
                keywords_for_thread_dict = st.session_state.selected_cities_keywords_ui.copy()
                ui_logger.info(f"Btn 'Iniciar'. Ciudades: {selected_cities_keys_ui}, Prof: {depth_ui_val}, Emails: {emails_ui_val}")

                thread = Thread(target=execute_scraping_task_threaded, args=(
                    selected_cities_keys_ui, keywords_for_thread_dict,
                    depth_ui_val, emails_ui_val, config_params_app, get_paths_config_dict_app(),
                    st.session_state.log_messages_queue
                ))
                st.session_state.scraping_thread = thread
                thread.start()
                st.rerun()

    with col_btn_stop_s:
        if st.button('🛑 Detener Scraping', key="btn_stop_s_sidebar",
                     disabled=not scraping_state['scraping_in_progress'], use_container_width=True):
            if scraping_state['scraping_in_progress']:
                set_scraping_state(stop_scraping_flag=True)
                ui_logger.warning("Solicitud de DETENER scraping.")
                st.warning("Intentando detener scraping... (Proceso Docker actual podría necesitar completarse o timeout)")

# --- Área Principal ---
# Usar helper para obtener estado de scraping
scraping_state = get_scraping_state()

if scraping_state['scraping_in_progress']:
    st.header("⏳ Progreso del Scraping...")
    if scraping_state['start_time']:
        elapsed_time = datetime.now() - scraping_state['start_time']
        time_str = str(timedelta(seconds=int(elapsed_time.total_seconds())))

        # Usar st.columns para los contadores
        col1_count, col2_count, col3_count = st.columns(3)
        col1_count.metric("Estado Actual", scraping_state['current_process_status'])
        col2_count.metric("Tiempo Transcurrido", time_str)
        # El contador de filas ahora será el total de los CSVs que se están formando
        total_live_rows = sum(scraping_state['live_csv_row_counts'].values())
        col3_count.metric("Filas en CSVs (aprox.)", total_live_rows)
    else:
        st.info(scraping_state['current_process_status'])

    st.subheader("Logs en Vivo (Salida de GOSOM y Agente)")
    log_display_placeholder_live = st.empty()

    new_log_entries_list_ui = []
    final_results_payload_ui = None
    critical_error_payload_ui = None
    thread_completed_signal_received_ui = False

    # Máximo de líneas de log a mostrar en vivo
    MAX_LIVE_LOG_LINES = 200

    while not st.session_state.log_messages_queue.empty():
        try:
            msg_item_ui = st.session_state.log_messages_queue.get_nowait()
            if isinstance(msg_item_ui, dict):
                msg_type = msg_item_ui.get("type") # type: ignore
                if msg_type == LogMessageType.FINAL_RESULTS: final_results_payload_ui = msg_item_ui
                elif msg_type == LogMessageType.CRITICAL_ERROR: critical_error_payload_ui = msg_item_ui
                elif msg_type == LogMessageType.LIVE_ROW_COUNT: # Para el contador de CSV en vivo
                     # Usar helper para actualizar el estado del contador
                     current_live_counts = get_scraping_state()['live_csv_row_counts'].copy()
                     current_live_counts[msg_item_ui["city"]] = msg_item_ui["count"] # type: ignore
                     set_scraping_state(live_csv_row_counts=current_live_counts)
                elif msg_type == LogMessageType.ROW_COUNT_UPDATE: # Acumulado final del thread (usado en dummy)
                     set_scraping_state(cumulative_row_count=msg_item_ui["cumulative_count"]) # type: ignore
            elif isinstance(msg_item_ui, str): # type: ignore
                if msg_item_ui == LogMessageType.THREAD_COMPLETE_SIGNAL:
                    thread_completed_signal_received_ui = True
                    break # Salir del bucle de la cola si recibimos la señal de fin
                elif msg_item_ui.startswith(f"{LogMessageType.PROCESO_START}:") or msg_item_ui.startswith(f"{LogMessageType.STATUS_UPDATE}:") :
                    # Usar helper para actualizar el estado del proceso
                    set_scraping_state(current_process_status=msg_item_ui.split(":", 1)[1])
                # Filtrar qué logs se muestran en la UI en vivo
                elif msg_item_ui.startswith(f"{LogMessageType.GOSOM_LOG}:") or msg_item_ui.startswith(f"{LogMessageType.CMD_DOCKER}:"):
                    new_log_entries_list_ui.append(msg_item_ui.split(":", 1)[1])
                # No mostrar todos los logs del core a menos que sean errores o warnings no capturados por prefijos específicos
                elif not msg_item_ui.startswith("DEBUG:") and not msg_item_ui.startswith("INFO:[CoreLogicThread"):
                    new_log_entries_list_ui.append(msg_item_ui)
        except queue.Empty:
 break

    if new_log_entries_list_ui:
        # Mantener el buffer de logs usando una lista y limitando su tamaño
        # Asegurarse de que current_log_lines existe e inicializar si es necesario (redundante con default_ss_vals pero seguro)
        if 'current_log_lines' not in st.session_state or not isinstance(st.session_state.current_log_lines, list):
            st.session_state.current_log_lines = []

        st.session_state.current_log_lines.extend(new_log_entries_list_ui)
        # Limitar al máximo de líneas
        st.session_state.current_log_lines = st.session_state.current_log_lines[-MAX_LIVE_LOG_LINES:]

        # Unir las líneas para mostrar
        st.session_state.current_log_display = "\n".join(st.session_state.current_log_lines)

    log_display_placeholder_live.code(st.session_state.current_log_display, language='log', height=400)

    current_thread_ui_check_live = st.session_state.get('scraping_thread')
    # Rerun solo si el thread terminó o si hay una señal crítica
    if thread_completed_signal_received_ui or critical_error_payload_ui or not (current_thread_ui_check_live and current_thread_ui_check_live.is_alive()):
        # Usar helper para establecer el estado final
 set_scraping_state(
 scraping_in_progress=False,
 scraping_done=True,
 start_time=None # Resetear tiempo
 )

 if final_results_payload_ui:
            st.session_state.final_df_consolidated = final_results_payload_ui['data']
            st.session_state.processed_city_data_results = final_results_payload_ui['processed_city_data']
            # cumulative_row_count ya se actualizó via message type ROW_COUNT_UPDATE si aplica, o lo manejamos al final
            # set_scraping_state(cumulative_row_count=final_results_payload_ui.get('final_cumulative_count', st.session_state.cumulative_row_count)) # Este tipo de mensaje no se envía realmente

        if critical_error_payload_ui:
            set_scraping_state(current_process_status=f"ERROR CRÍTICO: {critical_error_payload_ui.get('message', 'Detalles en logs')}") # Usar helper

        ui_logger.info("Thread finalizado. UI a estado 'done'.")
        # Rerun para mostrar el estado final y los resultados
        st.rerun()
    # Eliminar el `elif` con `time.sleep` para reducir reruns innecesarios

elif scraping_state['scraping_done']: # Usar helper para obtener estado
    # Orden: Título -> Resultados/Estadísticas -> Logs Detallados
    st.header("🏁 Tarea de Scraping Completada")
    st.info(f"Estado final del proceso: {scraping_state['current_process_status']}") # Usar helper

    st.header("📊 Resultados y Estadísticas") # Mover esta sección arriba
    res_tab_data, res_tab_stats = st.tabs(["📄 Datos Procesados", "📈 Resumen y Estadísticas"]) # Tabs should follow the header
    df_final = st.session_state.final_df_consolidated

    with res_tab_data: # Asegurarse de que esta sección está dentro de la tab
        # ... (resto de la pestaña de datos igual)
        if df_final is not None and not df_final.empty:
            st.dataframe(df_final)
            try:
                csv_dl_bytes = df_final.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(label="📥 Descargar CSV Consolidado", data=csv_dl_bytes,
                                   file_name=f"gmaps_prospectos_consolidados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                   mime='text/csv', key="download_consolidated_main_key")
            except Exception as e_csv_dl: st.error(f"Error al generar CSV para descarga: {e_csv_dl}")

            st.subheader("CSVs Crudos Individuales (si se generaron)")
            if st.session_state.processed_city_data_results:
                for city_res_key_dl, city_res_data_dl in st.session_state.processed_city_data_results.items():
                    raw_path_res_dl = city_res_data_dl.get('raw_path')
                    df_city_proc_dl = city_res_data_dl.get('df')
                    num_filas_proc_dl = len(df_city_proc_dl) if df_city_proc_dl is not None else 0
                    # Usar st.info/st.caption como estaba, o considerar st.warning si es un error de no generación
                    if raw_path_res_dl and os.path.exists(raw_path_res_dl) and os.path.getsize(raw_path_res_dl) > 0:
                        with open(raw_path_res_dl, "rb") as fp_raw_dl:
                            st.download_button(
                                label=f"📥 Crudo: {city_res_key_dl.capitalize()} ({num_filas_proc_dl} procesadas)",
                                data=fp_raw_dl, file_name=os.path.basename(raw_path_res_dl),
                                mime="text/csv", key=f"download_raw_{city_res_key_dl}"
                            )
                    elif raw_path_res_dl:
                         # Podríamos hacer esto un warning si el raw_path existe pero está vacío
 st.warning(f"Archivo crudo para {city_res_key_dl.capitalize()} no generado o vacío. Path: `{raw_path_res_dl}`")
                    else: # Esto es para casos donde process_city_data_func_app retornó None para raw_path
 st.error(f"Falló la generación de archivo crudo para {city_res_key_dl.capitalize()}.")
            else: st.info("No hay info de archivos crudos individuales.")
        else: st.info("No hay datos procesados para mostrar o descargar.")




    with res_tab_stats:
        st.subheader("Análisis General de Prospectos")
        if df_final is not None and not df_final.empty:
            df_unique_stats_display = df_final.drop_duplicates(subset=['link'], keep='first') if 'link' in df_final.columns else df_final
            total_unique_prospectos_display = len(df_unique_stats_display)
            st.metric("Prospectos Únicos (por link Gmaps)", f"{total_unique_prospectos_display}")

            cols_m_stats_display = st.columns(3)
            email_c_stats_val = df_unique_stats_display['emails'].notna().sum() if 'emails' in df_unique_stats_display.columns else 0
            cols_m_stats_display[0].metric("📧 Con Email", f"{email_c_stats_val} ({ (email_c_stats_val/total_unique_prospectos_display*100) if total_unique_prospectos_display > 0 else 0 :.1f}%)")

            web_c_stats_val = df_unique_stats_display['website'].notna().sum() if 'website' in df_unique_stats_display.columns else 0
            cols_m_stats_display[1].metric("🌐 Con Website", f"{web_c_stats_val} ({ (web_c_stats_val/total_unique_prospectos_display*100) if total_unique_prospectos_display > 0 else 0 :.1f}%)")

            phone_c_stats_val = df_unique_stats_display['phone'].notna().sum() if 'phone' in df_unique_stats_display.columns else 0
            cols_m_stats_display[2].metric("📞 Con Teléfono", f"{phone_c_stats_val} ({ (phone_c_stats_val/total_unique_prospectos_display*100) if total_unique_prospectos_display > 0 else 0 :.1f}%)")

            if 'search_origin_city' in df_unique_stats_display.columns and not df_unique_stats_display['search_origin_city'].dropna().empty:
                st.subheader("Prospectos por Ciudad")
                st.bar_chart(df_unique_stats_display['search_origin_city'].value_counts())

            if 'category' in df_unique_stats_display.columns and not df_unique_stats_display['category'].dropna().empty:
                st.subheader("Top 10 Categorías")
                st.bar_chart(df_unique_stats_display['category'].value_counts().nlargest(10))

            if 'latitude' in df_unique_stats_display.columns and 'longitude' in df_unique_stats_display.columns:
                df_map_data_final_display = df_unique_stats_display[['latitude', 'longitude']].dropna()
                if not df_map_data_final_display.empty:
                    st.subheader("🗺️ Distribución Geográfica")
                    st.map(df_map_data_final_display.head(5000))
        else:
            st.info("No hay datos procesados para mostrar estadísticas.")

    st.markdown("---")
    st.subheader("📜 Logs Detallados de la Ejecución Completada") # Este título va antes del expander
    with st.expander("Ver Logs de Operaciones y UI (Archivos)", expanded=False): # Colapsado por defecto
        log_tab_core_f, log_tab_ui_f = st.tabs(["Log Core Logic", "Log Eventos UI"])
        def read_log_file_content_final_fn(fp, max_lines=500): # Aumentar líneas para logs finales
            try:
                if os.path.exists(fp):
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as f: return "".join(f.readlines()[-max_lines:])
                return f"Log no encontrado o vacío: {fp}"
            except Exception as e_read_log_final: return f"Error leyendo log {fp}: {e_read_log_final}"

        with log_tab_core_f:
            st.caption(f"Path: {core_logic_log_file_path_app}")
            st.code(read_log_file_content_final_fn(core_logic_log_file_path_app, max_lines=500), language='log', line_numbers=True)
        with log_tab_ui_f:
            st.caption(f"Path: {streamlit_ui_log_path_app}")
            st.code(read_log_file_content_final_fn(streamlit_ui_log_path_app, max_lines=500), language='log', line_numbers=True)
else:
    st.info("⬅️ Configura una tarea en la barra lateral y presiona 'Iniciar Scraping' para comenzar.")

st.sidebar.markdown("---")
st.sidebar.caption(f"Agente GOSOM ETL - MVP v0.7 | Core Logic: {'Cargado OK' if CORE_LOGIC_LOADED else 'FALLÓ / DUMMY'}")
    thread_core_logger = StyledLogger_cls_app(logger_name=f"CoreLogicThread-{current_thread_id}", 
                                          log_file_path=log_path_for_thread_core, level=logging.DEBUG)
    for handler_to_remove in list(thread_core_logger.logger.handlers): # Limpiar handlers de cola
        if isinstance(handler_to_remove, QueueLogHandler): thread_core_logger.logger.removeHandler(handler_to_remove)
    queue_handler_for_thread = QueueLogHandler(log_q_thread)
    thread_core_logger.logger.addHandler(queue_handler_for_thread)
    thread_core_logger.logger.propagate = False

    try:
        log_q_thread.put(f"{LogMessageType.PROCESO_START}:Iniciando tarea de scraping...")
        thread_core_logger.section(f"Nueva Tarea (Thread: {current_thread_id})") 
        thread_core_logger.info(f"Ciudades: {selected_cities_list_thread}, Prof: {depth_ui_thread}, Emails: {emails_ui_thread}")
        
        temp_processed_city_data_thread = {}
        temp_all_city_dfs_thread = []
        
        for i, city_k_thread in enumerate(selected_cities_list_thread):
            if st.session_state.get('stop_scraping_flag', False):
                log_q_thread.put(f"{LogMessageType.INFO}:Scraping detenido para {city_k_thread.capitalize()}.")
                break # Salir del bucle for de ciudades
            log_q_thread.put(f"STATUS_UPDATE:Procesando {city_k_thread.capitalize()} ({i+1}/{len(selected_cities_list_thread)})...")
            keywords_str_for_city = keywords_per_city_thread_dict.get(city_k_thread, "")
            keywords_list_for_city = [kw.strip() for kw in keywords_str_for_city.splitlines() if kw.strip()]
            if not keywords_list_for_city: continue
            
            df_transformed_city, raw_path_city = process_city_data_func_app( 
 log_q_streamlit=log_q_thread, # Pasar la cola al core_logic
    city_key=city_k_thread, keywords_list=keywords_list_for_city, 
    depth_from_ui=depth_ui_thread, extract_emails_flag=emails_ui_thread,
    config_params_dict=cfg_params_thread, paths_config_dict=paths_cfg_thread, 
 logger_instance=thread_core_logger, # Pass logger to core_logic
)
            
            temp_processed_city_data_thread[city_k_thread] = {'df': df_transformed_city, 'raw_path': raw_path_city}
            if df_transformed_city is not None and not df_transformed_city.empty:
                temp_all_city_dfs_thread.append(df_transformed_city) # Añadir solo DFs no vacíos
                log_q_thread.put(f"{LogMessageType.SUCCESS}:{city_k_thread.capitalize()} ({len(df_transformed_city)} prosp).")
            elif df_transformed_city is not None: log_q_thread.put(f"{LogMessageType.INFO}:{city_k_thread.capitalize()} (0 prosp).")
            else: log_q_thread.put(f"{LogMessageType.ERROR}:Falló {city_k_thread.capitalize()}.")

        final_df_payload_thread = pd.DataFrame(columns=gmaps_column_names_list_app) 
        if temp_all_city_dfs_thread:
            try: final_df_payload_thread = pd.concat(temp_all_city_dfs_thread, ignore_index=True)
            except Exception as e_concat: log_q_thread.put(f"ERROR_CRITICAL_THREAD:Concat Error: {e_concat}")
            
        log_q_thread.put({"type": "FINAL_RESULTS", "data": final_df_payload_thread, 
                          "processed_city_data": temp_processed_city_data_thread})
        thread_core_logger.section("Tarea Scraping (Thread) Finalizada")
    except Exception as e_thread_main:
        thread_core_logger.critical(f"{LogMessageType.CRITICAL_ERROR}:Error mayor en thread: {str(e_thread_main)}", exc_info=True)
        log_q_thread.put({"type": "CRITICAL_ERROR", "message": str(e_thread_main)})
    finally:
        log_q_thread.put(LogMessageType.THREAD_COMPLETE_SIGNAL)

st.set_page_config(page_title="Agente GOSOM ETL", layout="wide", initial_sidebar_state="expanded")
st.title('🚀✨ Agente GOSOM ETL')
st.markdown("Herramienta para extraer y procesar leads de Google Maps.")

# NO mostrar el header ASCII de core_logic aquí en la UI. Se imprime en consola del server si core_logic carga.
if not CORE_LOGIC_LOADED:
    st.error("¡ADVERTENCIA CRÍTICA! El módulo 'core_logic.py' no pudo cargar correctamente. Usando funcionalidades limitadas (dummies).")

with st.sidebar:
    st.header('⚙️ Configurar Tarea')
    gmaps_coords_opts = list(config_params_app.get('gmaps_coordinates', {}).keys())
    selected_cities_keys_ui = st.multiselect('🏙️ Seleccionar Ciudad(es)', options=gmaps_coords_opts, 
                                           default=st.session_state.last_selected_cities, 
                                           disabled=st.session_state.scraping_in_progress, key="ms_cities")
    if selected_cities_keys_ui != st.session_state.last_selected_cities:
        st.session_state.last_selected_cities = selected_cities_keys_ui
    if selected_cities_keys_ui:
        st.subheader("✏️ Keywords por Ciudad")
        for city_k_ui in selected_cities_keys_ui:
            if city_k_ui not in st.session_state.selected_cities_keywords_ui:
                kws = load_keywords_from_csv_func_app(CONFIG_DIR_APP, city_k_ui, ui_logger)
                st.session_state.selected_cities_keywords_ui[city_k_ui] = "\n".join(kws)
            st.session_state.selected_cities_keywords_ui[city_k_ui] = st.text_area(
                f'Keywords para {city_k_ui.capitalize()}', 
                st.session_state.selected_cities_keywords_ui.get(city_k_ui, ""), 
                key=f'kw_ta_{city_k_ui}', height=100, disabled=st.session_state.scraping_in_progress)
    depth_ui_val = st.number_input('🎯 Profundidad', min_value=1, max_value=20, 
                               value=int(st.session_state.last_search_depth), 
                               disabled=st.session_state.scraping_in_progress, key="ni_depth",
                               help="Profundidad de búsqueda GOSOM.")
    st.session_state.last_search_depth = depth_ui_val
    emails_ui_val = st.checkbox('📧 ¿Extraer Emails? (⚠️ Tarda más)', 
                            value=st.session_state.last_extract_emails, 
                            disabled=st.session_state.scraping_in_progress, key="cb_emails")
    st.session_state.last_extract_emails = emails_ui_val
    
    col_btn_start_s, col_btn_stop_s = st.columns(2)
    with col_btn_start_s:
        if st.button('🚀 Iniciar Scraping', key="btn_start_s",
                    disabled=st.session_state.scraping_in_progress or not CORE_LOGIC_LOADED, 
                    type="primary", use_container_width=True):
            if not selected_cities_keys_ui: st.warning('Selecciona al menos una ciudad.')
            elif not CORE_LOGIC_LOADED: st.error("'core_logic.py' no cargó.")
            else:
                st.session_state.current_process_status = "Iniciando..."
                st.session_state.current_log_display = "Iniciando Logs...\n" 
                st.session_state.start_time = datetime.now()
                st.session_state.cumulative_row_count = 0
                st.session_state.live_csv_row_counts = {city: 0 for city in selected_cities_keys_ui} # Resetear contadores por ciudad
                st.session_state.stop_scraping_flag = False 
                st.session_state.scraping_in_progress = True 
                st.session_state.scraping_done = False
                st.session_state.processed_city_data_results = {}
                st.session_state.final_df_consolidated = pd.DataFrame(columns=gmaps_column_names_list_app)
                keywords_for_thread_dict = st.session_state.selected_cities_keywords_ui.copy()
                ui_logger.info(f"Btn 'Iniciar'. Ciudades: {selected_cities_keys_ui}, Prof: {depth_ui_val}, Emails: {emails_ui_val}")
                thread = Thread(target=execute_scraping_task_threaded, args=( # type: ignore
                    selected_cities_keys_ui, keywords_for_thread_dict,
                    depth_ui_val, emails_ui_val, 
                    config_params_app, get_paths_config_dict_app(), 
                    st.session_state.log_messages_queue
                ))
                st.session_state.scraping_thread = thread
                thread.start()
                st.rerun()
    with col_btn_stop_s:
        if st.button('🛑 Detener Scraping', key="btn_stop_s", 
                     disabled=not st.session_state.scraping_in_progress, use_container_width=True):
            if st.session_state.scraping_in_progress:
                st.session_state.stop_scraping_flag = True # type: ignore
                ui_logger.warning("Solicitud de DETENER scraping.")
                st.warning("Intentando detener scraping... (Proceso Docker actual podría necesitar completarse o timeout)")

# --- Área Principal ---
if st.session_state.scraping_in_progress:
    st.header("⏳ Progreso del Scraping...")
    if st.session_state.start_time:
        elapsed_time = datetime.now() - st.session_state.start_time
        time_str = str(timedelta(seconds=int(elapsed_time.total_seconds())))
        
        # Usar st.columns para los contadores
        col1_count, col2_count, col3_count = st.columns(3)
        col1_count.metric("Estado Actual", st.session_state.current_process_status)
        col2_count.metric("Tiempo Transcurrido", time_str)
        # El contador de filas ahora será el total de los CSVs que se están formando
        total_live_rows = sum(st.session_state.live_csv_row_counts.values())
        col3_count.metric("Filas en CSVs (aprox.)", total_live_rows)
    else:
        st.info(st.session_state.current_process_status)

    st.subheader("Logs en Vivo (Salida de GOSOM y Agente)")
    log_display_placeholder_live = st.empty()
        
    new_log_entries_list_ui = []
    final_results_payload_ui = None 
    critical_error_payload_ui = None 
    thread_completed_signal_received_ui = False 

    while not st.session_state.log_messages_queue.empty():
        try:
            msg_item_ui = st.session_state.log_messages_queue.get_nowait()
            if isinstance(msg_item_ui, dict):
                msg_type = msg_item_ui.get("type") # type: ignore
                if msg_type == LogMessageType.FINAL_RESULTS: final_results_payload_ui = msg_item_ui
                elif msg_type == LogMessageType.CRITICAL_ERROR: critical_error_payload_ui = msg_item_ui
                elif msg_type == LogMessageType.LIVE_ROW_COUNT: # Para el contador de CSV en vivo
                     st.session_state.live_csv_row_counts[msg_item_ui["city"]] = msg_item_ui["count"] # type: ignore
                elif msg_type == LogMessageType.ROW_COUNT_UPDATE: # Acumulado final del thread (usado en dummy)
                     st.session_state.cumulative_row_count = msg_item_ui["cumulative_count"] # type: ignore
            elif isinstance(msg_item_ui, str): # type: ignore
                if msg_item_ui == LogMessageType.THREAD_COMPLETE_SIGNAL:
                    thread_completed_signal_received_ui = True
                    break # Salir del bucle de la cola si recibimos la señal de fin
                elif msg_item_ui.startswith(f"{LogMessageType.PROCESO_START}:") or msg_item_ui.startswith(f"{LogMessageType.STATUS_UPDATE}:") :
                    st.session_state.current_process_status = msg_item_ui.split(":", 1)[1]
                # Filtrar qué logs se muestran en la UI en vivo
                elif msg_item_ui.startswith(f"{LogMessageType.GOSOM_LOG}:") or msg_item_ui.startswith(f"{LogMessageType.CMD_DOCKER}:"):
                    new_log_entries_list_ui.append(msg_item_ui.split(":", 1)[1])
                elif not msg_item_ui.startswith("DEBUG:") and not msg_item_ui.startswith("INFO:[CoreLogicThread"): # No mostrar todos los logs del core
                    new_log_entries_list_ui.append(msg_item_ui)
        except queue.Empty: 
             break
    
    if new_log_entries_list_ui:
        # Concatenar al string actual (manteniendo el enfoque simple por ahora)
        st.session_state.current_log_display += "\n".join(new_log_entries_list_ui) + "\n" 
        st.session_state.current_log_display = "\n".join(st.session_state.current_log_display.splitlines()[-100:]) # Últimas 100 líneas
    
    log_display_placeholder_live.code(st.session_state.current_log_display, language='log', height=400)

    current_thread_ui_check_live = st.session_state.get('scraping_thread')
    if thread_completed_signal_received_ui or not (current_thread_ui_check_live and current_thread_ui_check_live.is_alive()):
        st.session_state.scraping_in_progress = False
        st.session_state.scraping_done = True # type: ignore
        st.session_state.start_time = None 
        if final_results_payload_ui: 
            st.session_state.final_df_consolidated = final_results_payload_ui['data']
            st.session_state.processed_city_data_results = final_results_payload_ui['processed_city_data']
            st.session_state.cumulative_row_count = final_results_payload_ui.get('final_cumulative_count', st.session_state.cumulative_row_count)
        if critical_error_payload_ui: 
            st.session_state.current_process_status = f"ERROR CRÍTICO: {critical_error_payload_ui.get('message', 'Detalles en logs')}"
        ui_logger.info("Thread finalizado. UI a estado 'done'.")
        # Solo rerun aquí para actualizar la UI a "Tarea Completada"
        st.rerun()
    elif current_thread_ui_check_live and current_thread_ui_check_live.is_alive(): # type: ignore
        time.sleep(1.5) # Un poco más de tiempo entre reruns
        st.rerun()

elif st.session_state.scraping_done:
    # Orden: Título -> Resultados/Estadísticas -> Logs Detallados
    st.header("🏁 Tarea de Scraping Completada")
    st.info(f"Estado final del proceso: {st.session_state.current_process_status}")
    
    st.header("📊 Resultados y Estadísticas") # Mover esta sección arriba
    res_tab_data, res_tab_stats = st.tabs(["📄 Datos Procesados", "📈 Resumen y Estadísticas"]) # Tabs should follow the header
    df_final = st.session_state.final_df_consolidated
        # ... (resto de la pestaña de datos igual)
        if df_final is not None and not df_final.empty: 
            st.dataframe(df_final) 
            try:
                csv_dl_bytes = df_final.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(label="📥 Descargar CSV Consolidado", data=csv_dl_bytes,
                                   file_name=f"gmaps_prospectos_consolidados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                   mime='text/csv', key="download_consolidated_main_key")
            except Exception as e_csv_dl: st.error(f"Error al generar CSV para descarga: {e_csv_dl}")

            st.subheader("CSVs Crudos Individuales (si se generaron)")
            if st.session_state.processed_city_data_results:
                for city_res_key_dl, city_res_data_dl in st.session_state.processed_city_data_results.items():
                    raw_path_res_dl = city_res_data_dl.get('raw_path')
                    df_city_proc_dl = city_res_data_dl.get('df')
                    num_filas_proc_dl = len(df_city_proc_dl) if df_city_proc_dl is not None else 0 
                    if raw_path_res_dl and os.path.exists(raw_path_res_dl) and os.path.getsize(raw_path_res_dl) > 0:
                        with open(raw_path_res_dl, "rb") as fp_raw_dl:
                            st.download_button(
                                label=f"📥 Crudo: {city_res_key_dl.capitalize()} ({num_filas_proc_dl} procesadas)",
                                data=fp_raw_dl, file_name=os.path.basename(raw_path_res_dl),
                                mime="text/csv", key=f"download_raw_{city_res_key_dl}"
                            )
                    elif raw_path_res_dl: 
                        st.caption(f"Archivo crudo para {city_res_key_dl.capitalize()} no generado o vacío. Path: {raw_path_res_dl}")
            else: st.info("No hay info de archivos crudos individuales.")
        else: st.info("No hay datos procesados para mostrar o descargar.")
    
    
            
    with res_tab_stats: 
        st.subheader("Análisis General de Prospectos")
        if df_final is not None and not df_final.empty:
            df_unique_stats_display = df_final.drop_duplicates(subset=['link'], keep='first') if 'link' in df_final.columns else df_final
            total_unique_prospectos_display = len(df_unique_stats_display)
            st.metric("Prospectos Únicos (por link Gmaps)", f"{total_unique_prospectos_display}")
            
            cols_m_stats_display = st.columns(3)
            email_c_stats_val = df_unique_stats_display['emails'].notna().sum() if 'emails' in df_unique_stats_display.columns else 0
            cols_m_stats_display[0].metric("📧 Con Email", f"{email_c_stats_val} ({ (email_c_stats_val/total_unique_prospectos_display*100) if total_unique_prospectos_display > 0 else 0 :.1f}%)")
            
            web_c_stats_val = df_unique_stats_display['website'].notna().sum() if 'website' in df_unique_stats_display.columns else 0
            cols_m_stats_display[1].metric("🌐 Con Website", f"{web_c_stats_val} ({ (web_c_stats_val/total_unique_prospectos_display*100) if total_unique_prospectos_display > 0 else 0 :.1f}%)")

            phone_c_stats_val = df_unique_stats_display['phone'].notna().sum() if 'phone' in df_unique_stats_display.columns else 0
            cols_m_stats_display[2].metric("📞 Con Teléfono", f"{phone_c_stats_val} ({ (phone_c_stats_val/total_unique_prospectos_display*100) if total_unique_prospectos_display > 0 else 0 :.1f}%)")

            if 'search_origin_city' in df_unique_stats_display.columns and not df_unique_stats_display['search_origin_city'].dropna().empty:
                st.subheader("Prospectos por Ciudad")
                st.bar_chart(df_unique_stats_display['search_origin_city'].value_counts())
            
            if 'category' in df_unique_stats_display.columns and not df_unique_stats_display['category'].dropna().empty:
                st.subheader("Top 10 Categorías")
                st.bar_chart(df_unique_stats_display['category'].value_counts().nlargest(10))

            if 'latitude' in df_unique_stats_display.columns and 'longitude' in df_unique_stats_display.columns:
                df_map_data_final_display = df_unique_stats_display[['latitude', 'longitude']].dropna()
                if not df_map_data_final_display.empty:
                    st.subheader("🗺️ Distribución Geográfica")
                    st.map(df_map_data_final_display.head(5000))
        else: 
            st.info("No hay datos procesados para mostrar estadísticas.")
    
    st.markdown("---") 
    st.subheader("📜 Logs Detallados de la Ejecución Completada") # Este título va antes del expander
    with st.expander("Ver Logs de Operaciones y UI (Archivos)", expanded=False): # Colapsado por defecto
        log_tab_core_f, log_tab_ui_f = st.tabs(["Log Core Logic", "Log Eventos UI"])
        def read_log_file_content_final_fn(fp, max_lines=500): # Aumentar líneas para logs finales
            try:
                if os.path.exists(fp):
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as f: return "".join(f.readlines()[-max_lines:])
                return f"Log no encontrado o vacío: {fp}"
            except Exception as e_read_log_final: return f"Error leyendo log {fp}: {e_read_log_final}"

        with log_tab_core_f:
            st.caption(f"Path: {core_logic_log_file_path_app}")
            st.code(read_log_file_content_final_fn(core_logic_log_file_path_app, max_lines=500), language='log', line_numbers=True)
        with log_tab_ui_f:
            st.caption(f"Path: {streamlit_ui_log_path_app}")
            st.code(read_log_file_content_final_fn(streamlit_ui_log_path_app, max_lines=500), language='log', line_numbers=True)
else: 
    st.info("⬅️ Configura una tarea en la barra lateral y presiona 'Iniciar Scraping' para comenzar.")

st.sidebar.markdown("---")
st.sidebar.caption(f"Agente GOSOM ETL - MVP v0.7 | Core Logic: {'Cargado OK' if CORE_LOGIC_LOADED else 'FALLÓ / DUMMY'}")