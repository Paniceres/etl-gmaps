# Este agente GOSOM MVP (Producto Mínimo Viable) se encarga
# exclusivamente de la configuración y ejecución del scraping,
# guardando los resultados como CSVs crudos en /data/raw/.
# La consolidación, deduplicación, generación de chunks y cualquier
# otro procesamiento posterior son responsabilidad de la Central ETL.
import streamlit as st
import json
import os
import sys
import time
from datetime import datetime, timedelta
from threading import Thread
import threading
import queue
import logging
import pandas as pd


# --- Definición de Rutas Base ---
try:
    # Intenta obtener la ruta del script en ejecución.
    APP_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Si falla (p. ej., en un entorno interactivo), usa el directorio de trabajo actual.
    APP_ROOT_DIR = os.getcwd()

# Mensaje de depuración para verificar la ruta raíz de la aplicación.
# print(f"DEBUG (app_streamlit INIT): APP_ROOT_DIR={APP_ROOT_DIR}") # Quitar para producción

# Definición de directorios clave de la aplicación.
SRC_DIR = os.path.join(APP_ROOT_DIR, 'src')
CONFIG_DIR_APP = os.path.join(APP_ROOT_DIR, 'config')
DATA_DIR_APP = os.path.join(APP_ROOT_DIR, 'data')

# Nuevo directorio para datos limpios.
CITY_CLEAN_DATA_DIR_APP = os.path.join(DATA_DIR_APP, 'city_clean')
# Ruta corregida para datos consolidados.
CONSOLIDATED_DATA_DIR_APP = os.path.join(DATA_DIR_APP, 'consolidated')

# Ruta correcta para el CSV madre consolidado - DEBE definirse DESPUÉS de CONSOLIDATED_DATA_DIR_APP.
CONSOLIDATED_MOTHER_CSV_PATH_APP = os.path.join(CONSOLIDATED_DATA_DIR_APP, 'consolidated_leads.csv')

# Otros directorios de datos.
LOGS_DIR_APP = os.path.join(DATA_DIR_APP, 'logs')
RAW_DATA_DIR_APP = os.path.join(DATA_DIR_APP, 'raw')
CHUNKS_DATA_DIR_APP = os.path.join(DATA_DIR_APP, 'chunks')
# Movido después de la definición de DATA_DIR_APP.
JOBS_DATA_DIR_APP = os.path.join(DATA_DIR_APP, 'jobs')

# Asegurar que todos los directorios necesarios sean creados al iniciar.
for dir_path_init in [SRC_DIR, CONFIG_DIR_APP, DATA_DIR_APP, LOGS_DIR_APP, RAW_DATA_DIR_APP, JOBS_DATA_DIR_APP, CHUNKS_DATA_DIR_APP, CITY_CLEAN_DATA_DIR_APP, CONSOLIDATED_DATA_DIR_APP]:
    try:
        os.makedirs(dir_path_init, exist_ok=True)
    except Exception as e_mkdir_init_loop:
        print(f"ERROR (app_streamlit INIT): Creando dir {dir_path_init}: {e_mkdir_init_loop}")

# Añadir el directorio 'src' al path de Python para poder importar módulos locales.
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR) # Usar insert(0, ...) para mayor prioridad.

# Ruta para los registros de jobs, no para los leads consolidados.
MOTHER_CSV_PATH_APP = os.path.join(JOBS_DATA_DIR_APP, 'scrape_jobs.csv')
CORE_LOGIC_LOADED = False # Flag para verificar si la lógica principal se cargó correctamente.

class DummyLogger:
    """Una clase de logger falsa para usar si la lógica principal no se carga."""
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('logger_name', 'DummyLoggerUI')
    def _log_print(self, level, msg, art):
        print(f"{datetime.now().strftime('%H:%M:%S')} [{level}] ({self.name}) {art} {msg}")
    def info(self, msg, art="[INFO]"):
        self._log_print("INFO", msg, art)
    def error(self, msg, exc_info=False, art="[FAIL]"):
        self._log_print("ERROR", msg, art)
        print(msg) # Imprimir error en la consola también.
    def warning(self, msg, art="[ATEN]"):
        self._log_print("WARNING", msg, art)
    def success(self, msg, art="[OK]"):
        self._log_print("SUCCESS", msg, art)
    def section(self, title):
        self._log_print("INFO", f"SECTION: {str(title).upper()}", "")
    def subsection(self, title):
        self._log_print("INFO", f"SUBSECTION: {str(title)}", "")
    def get_header_art_text(self):
        return f"--- DUMMY LOGGER HEADER ({self.name}) ---\n(core_logic.py no cargó)"
    def critical(self, msg, exc_info=False, art="[CRIT]"):
        self._log_print("CRITICAL", msg, art)
        print(msg)
    def debug(self, msg, art="[DEBUG]"):
        self._log_print("DEBUG", msg, art)
    def __getattr__(self, name):
        if name == 'logger':
            _dummy_py_logger = logging.getLogger(self.name + "_int_dummy")
            return _dummy_py_logger
        return lambda *args, **kwargs: None

def dummy_load_keywords_func(*args, **kwargs):
    """Función dummy que devuelve una lista de keywords de ejemplo."""
    return ["dummy_kw1", "dummy_kw2"]

gmaps_column_names_list_app_fallback = ['title', 'emails', 'link']

def dummy_process_city_func(*args, **kwargs):
    """Función dummy para procesar datos de una ciudad si la lógica principal falla."""
    logger_instance = kwargs.get('logger_instance', DummyLogger(logger_name="DummyProcCity"))
    city_key = kwargs.get('city_key', 'dummy_city')
    log_q_thread = kwargs.get('log_q_streamlit')
    time.sleep(0.1)
    if log_q_thread: log_q_thread.put(f"GOSOM_LOG:Dummy GOSOM log 1 para {city_key}")
    time.sleep(0.1)
    if log_q_thread: log_q_thread.put(f"GOSOM_LOG:Dummy GOSOM log 2 para {city_key}")
    # Se añadió lat/lon para el dummy.
    dummy_df = pd.DataFrame({'title':['dummy ' + city_key], 'emails':['d@e.co'], 'link':['d.co'], 'lat': [0.0], 'lon': [0.0]})
    for col in gmaps_column_names_list_app_fallback:
        if col not in dummy_df.columns:
            dummy_df[col] = pd.NA
    if log_q_thread:
        log_q_thread.put({"type": "LIVE_ROW_COUNT", "city": city_key, "count": len(dummy_df)})
        log_q_thread.put({"type": "ROW_COUNT_UPDATE", "city": city_key, "count": len(dummy_df),
                          "cumulative_count": st.session_state.get('cumulative_row_count',0) + len(dummy_df) })
    return dummy_df, f"dummy_raw_{city_key}.csv"

# Asignar la clase DummyLogger como valor por defecto.
StyledLogger_cls_app = DummyLogger

# --- Constantes para Tipos de Mensajes en la Cola ---
# Usar una clase para simular un Enum, mejor que literales string.
class LogMessageType:
    FINAL_RESULTS = "FINAL_RESULTS"
    CRITICAL_ERROR = "CRITICAL_ERROR"
    LIVE_ROW_COUNT = "LIVE_ROW_COUNT"
    ROW_COUNT_UPDATE = "ROW_COUNT_UPDATE" # Usado en dummy, no en core logic actual, pero mantenido.
    THREAD_COMPLETE_SIGNAL = "THREAD_COMPLETE_SIGNAL"
    PROCESO_START = "PROCESO_START"       # Prefijo para inicio de proceso por ciudad/tarea.
    STATUS_UPDATE = "STATUS_UPDATE"       # Prefijo para updates de estado intermedio.
    GOSOM_LOG = "GOSOM_LOG"               # Prefijo para logs directos de la salida de GOSOM (docker).
    CMD_DOCKER = "CMD_DOCKER"             # Prefijo para el comando docker ejecutado.

# Asignación de funciones y valores dummy por defecto.
gmaps_column_names_list_app = gmaps_column_names_list_app_fallback
load_keywords_from_csv_func_app = dummy_load_keywords_func
process_city_data_func_app = dummy_process_city_func

# Intenta importar la lógica principal; si falla, usa las funciones dummy.
try:
    # Importar la función de validación.
    from core_logic import StyledLogger, gmaps_column_names, load_keywords_from_csv_core, process_city_data_core
    StyledLogger_cls_app = StyledLogger
    gmaps_column_names_list_app = gmaps_column_names
    load_keywords_from_csv_func_app = load_keywords_from_csv_core
    process_city_data_func_app = process_city_data_core
    CORE_LOGIC_LOADED = True
except ImportError as e:
    print(f"ERROR CRITICO (app_streamlit): No se pudo importar de 'core_logic.py': {e}. Usando Dummies.")
except Exception as e_general:
    print(f"ERROR CRITICO GENERAL (app_streamlit) durante importación de core_logic: {e_general}. Usando Dummies.")

CONFIG_FILE_PATH_APP = os.path.join(CONFIG_DIR_APP, 'parameters_default.json')
CORE_LOGIC_LOG_FILENAME_DEFAULT_APP = 'agent_core_logic.log'
# Configuración de respaldo si no se encuentra el archivo JSON.
FALLBACK_CONFIG_APP = {
    'gmaps_coordinates': {'neuquen_fb': {'latitude': -38.9516, 'longitude': -68.0591, 'radius':10000, 'zoom':14}},
    'default_depth': 1, 'language': 'es', 'results_filename_prefix': 'gmaps_data_',
    'log_filename': CORE_LOGIC_LOG_FILENAME_DEFAULT_APP
}
config_params_app = {}

# Define la instancia de logger para la UI de Streamlit ANTES de usarla.
streamlit_ui_log_filename = "streamlit_ui_events.log"
streamlit_ui_log_path_app = os.path.join(LOGS_DIR_APP, streamlit_ui_log_filename)
# Se cambió el nivel por defecto a INFO para el log de la UI.
ui_logger = StyledLogger_cls_app(logger_name="StreamlitAppUI", log_file_path=streamlit_ui_log_path_app, level=logging.INFO)

# Carga la configuración desde el archivo JSON.
try:
    with open(CONFIG_FILE_PATH_APP, 'r', encoding='utf-8') as f:
        config_params_app = json.load(f)
    ui_logger.info(f"Configuración cargada desde {os.path.basename(CONFIG_FILE_PATH_APP)}.")
except Exception as e_config_load:
    ui_logger.critical(f"No se pudo cargar el archivo de configuración {CONFIG_FILE_PATH_APP}: {e_config_load}", exc_info=True)
    config_params_app = FALLBACK_CONFIG_APP

core_logic_log_filename_cfg = config_params_app.get('log_filename', FALLBACK_CONFIG_APP['log_filename'])
CORE_LOGIC_LOG_FILE_PATH_APP = os.path.join(LOGS_DIR_APP, core_logic_log_filename_cfg)

# Valores por defecto para el estado de la sesión - definirlos fuera de las llamadas a funciones.
default_ss_vals = {
    'selected_cities_keywords_ui': {}, 'processed_city_data_results': {}, 'scraping_done': False,
    'scraping_in_progress': False, 'final_df_consolidated': pd.DataFrame(columns=gmaps_column_names_list_app),
    'last_selected_cities': list(config_params_app.get('gmaps_coordinates', {}).keys())[:1] if config_params_app.get('gmaps_coordinates') else [], # Respaldo a un dict vacío.
    'last_search_depth': int(config_params_app.get('default_depth', 1)),
    'last_extract_emails': True, 'log_messages_queue': queue.Queue(),
    'current_process_status': "Listo para iniciar.", 'current_log_display': "Logs de la operación aparecerán aquí...\n",
    'start_time': None, 'cumulative_row_count': 0, 'stop_scraping_flag': False,
    'live_csv_row_counts': {}, # Diccionario en formato {city_key: count}.
    'stage': 1, # Etapa inicial.
}
for key, value in default_ss_vals.items():
    if key not in st.session_state:
        st.session_state[key] = value

def get_paths_config_dict_app():
    """Devuelve un diccionario con las rutas a varios directorios."""
    return {'CONFIG_DIR': CONFIG_DIR_APP, 'RAW_DATA_DIR': RAW_DATA_DIR_APP,
            'LOGS_DIR': LOGS_DIR_APP}

def generate_clean_city_csvs(processed_city_data, output_dir, logger_instance):
    """
    Genera CSVs limpios para cada ciudad a partir de los datos procesados,
    seleccionando las columnas 'title', 'emails' y 'phone' (traducidas para la salida).
    """
    logger_instance.section("Generando CSVs Limpios por Ciudad")
    if not os.path.exists(output_dir):
        logger_instance.warning(f"Directorio de salida no encontrado: {output_dir}. Intentando crearlo.")
        # Asegurarse de que el directorio de datos padre también exista.
        os.makedirs(os.path.dirname(output_dir), exist_ok=True)
        try:
            os.makedirs(output_dir)
        except OSError as e:
            logger_instance.critical(f"No se pudo crear el directorio de salida {output_dir}: {e}", exc_info=True)
            return

    for city, data in processed_city_data.items():
        # Usar df_transformed según la lógica del core.
        df = data.get('df_transformed')
        if df is not None and not df.empty:
            # Verificar columnas críticas antes de proceder.
            required_cols = ['title', 'emails']
            if not all(col in df.columns for col in required_cols):
                logger_instance.warning(f"Datos para {city} no contienen todas las columnas requeridas ({', '.join(required_cols)}). Saltando generación de CSV limpio.")
                continue

            # Seleccionar columnas especificadas, manejando la posible ausencia de 'phone'.
            clean_cols = ['title', 'emails']
            if 'phone' in df.columns:
                clean_cols.append('phone')
            else:
                logger_instance.warning(f"Columna 'phone' no encontrada en los datos de {city}. CSV limpio generado sin esta columna.")

            # Usar .copy() para evitar SettingWithCopyWarning.
            clean_df = df[clean_cols].copy()

            # Renombrar columnas para la salida del CSV limpio.
            rename_map = {'title': 'nombre del local', 'emails': 'mail'}
            if 'phone' in clean_cols:
                rename_map['phone'] = 'telefono'
            clean_df = clean_df.rename(columns=rename_map)

            clean_file_path = os.path.join(output_dir, f'{city}_clean.csv')

            try:
                clean_df.to_csv(clean_file_path, index=False)
                logger_instance.success(f"CSV limpio para {city.capitalize()} guardado en {clean_file_path}")
            except Exception as e_save:
                logger_instance.error(f"Error al guardar el CSV limpio para {city.capitalize()} en {clean_file_path}: {e_save}", exc_info=True)

# --- CSS Personalizado para Colores del Brand Kit ---
brand_kit_colors = {
    "Primary": "#F3C04F",
    "Secondary 1": "#3C1B43",
    "Secondary 2": "#922D50",
    "Secondary 3": "#4C2E05",
}

custom_css = f"""
<style>
/* Color general de texto y enlaces */
body {{ color: {brand_kit_colors["Secondary 1"]}; }}
a {{ color: {brand_kit_colors["Primary"]}; }}
/* Fondo de la barra lateral */
[data-testid="stSidebar"] {{ background-color: {brand_kit_colors["Secondary 3"]}; }}
/* Color del botón primario */
div.stButton > button {{ background-color: {brand_kit_colors["Primary"]}; color: white; }}
/* Color del encabezado del expander */
details summary {{ color: {brand_kit_colors["Secondary 1"]}; }}
</style>
"""

class QueueLogHandler(logging.Handler):
    """Manejador de logs que emite registros a una cola (queue)."""
    def __init__(self, log_q):
        super().__init__()
        self.log_q = log_q
        self.setFormatter(logging.Formatter('%(asctime)s-%(levelname)s: %(message)s',datefmt='%H:%M:%S'))
    def emit(self, record):
        self.log_q.put(self.format(record))

def execute_scraping_task_threaded(
    core_logic_log_file_path_app,
    selected_cities_list_thread, keywords_per_city_thread_dict,
    depth_ui_thread, emails_ui_thread,
    cfg_params_thread, paths_cfg_thread,
    log_q_thread):
    """Ejecuta la tarea de scraping en un hilo separado."""
    current_thread_id = threading.get_ident()
    log_path_for_thread_core = core_logic_log_file_path_app

    # Limpiar logs de la cola al inicio de cada ejecución del hilo.
    while not log_q_thread.empty():
        try:
            log_q_thread.get_nowait()
        except queue.Empty:
            pass # Defensivo.

    thread_core_logger = StyledLogger_cls_app(logger_name=f"CoreLogicThread-{current_thread_id}",
                                              log_file_path=log_path_for_thread_core, level=logging.DEBUG)
    # Limpiar handlers de cola existentes para evitar duplicados si el hilo se reutiliza.
    for handler_to_remove in list(thread_core_logger.logger.handlers):
        if isinstance(handler_to_remove, QueueLogHandler):
            thread_core_logger.logger.removeHandler(handler_to_remove)

    # Pasar logger a core_logic.
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
            # Verificar la flag de detención de Streamlit a través de session_state.
            # NOTA: Acceder a st.session_state desde otro hilo NO es directamente seguro,
            # pero para esta flag simple y lectura periódica es un workaround común en Streamlit.
            # Un enfoque más robusto sería pasar la flag a través de la cola o un objeto compartido Thread-safe.
            if st.session_state.get('stop_scraping_flag', False):
                log_q_thread.put(f"INFO:Scraping detenido para {city_k_thread.capitalize()}.")
                break # Salir del bucle for de ciudades.

            log_q_thread.put(f"{LogMessageType.STATUS_UPDATE}:Procesando {city_k_thread.capitalize()} ({i+1}/{len(selected_cities_list_thread)})...")
            keywords_str_for_city = keywords_per_city_thread_dict.get(city_k_thread, "")
            keywords_list_for_city = [kw.strip() for kw in keywords_str_for_city.splitlines() if kw.strip()]
            if not keywords_list_for_city:
                log_q_thread.put(f"WARNING:No se encontraron keywords para {city_k_thread.capitalize()}. Omitiendo.")
                continue

            # --- Llamada a la Lógica Principal: Ejecutar Scraper ---
            # process_city_data_core incluye run_gmaps_scraper_docker_core.
            # Devuelve la ruta al CSV crudo si tiene éxito.
            df_transformed_city, raw_path_city = process_city_data_func_app(

                log_q_streamlit=log_q_thread,  # Pasar la cola a core_logic.
                city_key=city_k_thread,
                keywords_list=keywords_list_for_city,
                depth_from_ui=depth_ui_thread,
                extract_emails_flag=emails_ui_thread,
                config_params_dict=cfg_params_thread,
                paths_config_dict=paths_cfg_thread, # Pasar logger a core_logic.
                logger_instance=thread_core_logger,
 fast_mode_enabled=st.session_state.get('fast_mode', False), # Obtener y pasar el estado del fast mode.
            )

            # --- Validación: Después de la Generación y Transformación del CSV Crudo ---
            # Comprobar si raw_path_city es válido y apunta a un archivo que se creó (o se intentó crear).
            is_raw_csv_valid = False
            if raw_path_city and os.path.exists(raw_path_city) and os.path.getsize(raw_path_city) > 0:
                # Por ahora, nos aseguramos de que el DF transformado sea válido.
                if df_transformed_city is not None and not df_transformed_city.empty:
                    is_raw_csv_valid = True
                else:
                    thread_core_logger.warning(f"Los datos crudos de {city_k_thread} no se transformaron en un DataFrame válido. Omitiendo consolidación para esta ciudad.")

            temp_processed_city_data_thread[city_k_thread] = {'df_transformed': df_transformed_city, 'raw_path': raw_path_city, 'is_valid': is_raw_csv_valid, 'df': df_transformed_city}
            if df_transformed_city is not None and not df_transformed_city.empty:
                # Añadir solo DFs no vacíos.
                temp_all_city_dfs_thread.append(df_transformed_city)
                log_q_thread.put(f"SUCCESS:{city_k_thread.capitalize()} ({len(df_transformed_city)} prosp.).")
            elif df_transformed_city is not None:
                log_q_thread.put(f"INFO:{city_k_thread.capitalize()} (0 prosp).")
            else:
                # Registrar error crítico.
                log_q_thread.put(f"ERROR:Falló {city_k_thread.capitalize()}.")

        final_df_payload_thread = pd.DataFrame(columns=gmaps_column_names_list_app)
        if temp_all_city_dfs_thread:
            try:
                final_df_payload_thread = pd.concat(temp_all_city_dfs_thread, ignore_index=True)
            except Exception as e_concat:
                log_q_thread.put({"type": LogMessageType.CRITICAL_ERROR, "message": f"Error de Concat: {e_concat}"})
                thread_core_logger.critical(f"Error de Concat en el hilo: {e_concat}", exc_info=True)

        log_q_thread.put({"type": LogMessageType.FINAL_RESULTS, "data": final_df_payload_thread,
                          "processed_city_data": temp_processed_city_data_thread})
        thread_core_logger.section("Tarea de Scraping (Thread) Finalizada")
    except Exception as e_thread_main:
        thread_core_logger.critical(f"Error mayor en el hilo: {str(e_thread_main)}", exc_info=True)
        # Usar tipo de mensaje.
        log_q_thread.put({"type": LogMessageType.CRITICAL_ERROR, "message": str(e_thread_main)})
    finally:
        log_q_thread.put(LogMessageType.THREAD_COMPLETE_SIGNAL)


def get_highest_priority_task():
    """Obtiene la tarea de más alta prioridad desde 0_mejoras.md."""
    mejoras_file_path = os.path.join(APP_ROOT_DIR, '0_mejoras.md')
    high_priority_tasks = []
    try:
        with open(mejoras_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if "Alta 🚨" in line and "[ ] Pendiente" in line:
                    high_priority_tasks.append(line.strip())

        if not high_priority_tasks:
            return "No se encontraron tareas pendientes de alta prioridad."

        # Comprobar la tarea específica de "colores del brandkit".
        for task in high_priority_tasks:
            if "colores del brandkit" in task:
                return f"Prioridad Alta: {task.split('[ ] Pendiente', 1)[1].strip()}"

        # Si no se encuentra la tarea específica, devolver la primera de alta prioridad.
        return f"Prioridad Alta: {high_priority_tasks[0].split('[ ] Pendiente', 1)[1].strip()}"

    except FileNotFoundError:
        return f"Error: 0_mejoras.md no encontrado en {mejoras_file_path}."

# --- Funciones de ayuda para la gestión del estado ---
def get_scraping_state():
    """Devuelve un dict con claves relacionadas con el progreso y estado del scraping."""
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
    """Actualiza el estado de scraping en st.session_state basado en kwargs."""
    for key, value in kwargs.items():
        if key in ['scraping_in_progress', 'scraping_done', 'start_time', 'current_process_status', 'cumulative_row_count', 'live_csv_row_counts', 'stop_scraping_flag']:
            st.session_state[key] = value

# Configuración de la página de Streamlit.
st.set_page_config(page_title="Agente GOSOM ETL", layout="wide", initial_sidebar_state="expanded")
# Aplicar CSS personalizado.
st.markdown(custom_css, unsafe_allow_html=True)

# --- Barra Lateral (Sidebar) ---
with st.sidebar:
    st.image(os.path.join(APP_ROOT_DIR, "main-logo-black.jpeg"), width=100)
    st.markdown("---")

    # --- Gestión de Etapas ---
    stage_options = {
        1: "Etapa 1: Configuración y Scraping"
    }
    st.header("🗺️ Navegación")
    selected_stage_sidebar = st.radio(
        "Seleccionar Etapa",
        options=list(stage_options.keys()),
        format_func=lambda x: stage_options[x],
        key="radio_stage_sidebar"
    )
    # Actualizar la etapa según la selección de la barra lateral.
    if selected_stage_sidebar != st.session_state.stage:
        st.session_state.stage = selected_stage_sidebar
        st.rerun() # Volver a ejecutar para actualizar la vista.
    st.markdown("---")

    # Usar helper para obtener el estado del scraping.
    scraping_state = get_scraping_state()
    # Expanders para organizar la configuración.
    with st.expander("📍 Selección de Ubicación y Palabras Clave", expanded=True):
        gmaps_coords_opts = list(config_params_app.get('gmaps_coordinates', {}).keys())
        selected_cities_keys_ui = st.multiselect(
            '🏙️ Seleccionar Ciudades',
            options=gmaps_coords_opts,
            default=st.session_state.last_selected_cities,
            help="Selecciona una o más ciudades de la lista preconfigurada.",
            disabled=scraping_state['scraping_in_progress'],
            key="ms_cities_sidebar"
        )
        # Actualizar last_selected_cities si cambia.
        if selected_cities_keys_ui != st.session_state.last_selected_cities:
            # Limpiar keywords de las ciudades que ya no están seleccionadas.
            for city_key in list(st.session_state.selected_cities_keywords_ui.keys()):
                if city_key not in selected_cities_keys_ui:
                    del st.session_state.selected_cities_keywords_ui[city_key]
            st.session_state.last_selected_cities = selected_cities_keys_ui
            st.rerun()

        if selected_cities_keys_ui:
            st.subheader("✏️ Keywords por Ciudad")
            st.info("Introduce una keyword por línea en el campo de texto de cada ciudad seleccionada.")
            for city_k_ui in selected_cities_keys_ui:
                if city_k_ui not in st.session_state.selected_cities_keywords_ui:
                    kws = load_keywords_from_csv_func_app(CONFIG_DIR_APP, city_k_ui, ui_logger)
                    st.session_state.selected_cities_keywords_ui[city_k_ui] = "\n".join(kws)
                st.session_state.selected_cities_keywords_ui[city_k_ui] = st.text_area(
                    f'Keywords para {city_k_ui.capitalize()}',
                    st.session_state.selected_cities_keywords_ui.get(city_k_ui, ""),
                    key=f'kw_ta_sidebar_{city_k_ui}', height=100, disabled=scraping_state['scraping_in_progress'],
                    help=f"Lista de palabras clave para buscar en {city_k_ui.capitalize()}. Una por línea."
                )

    with st.expander("⚙️ Parámetros Avanzados", expanded=False):
        depth_ui_val = st.number_input(
            '🎯 Profundidad de Búsqueda',
            min_value=1, max_value=20,
            value=int(st.session_state.last_search_depth),
            disabled=scraping_state['scraping_in_progress'], key="ni_depth_sidebar",
            help="Profundidad de búsqueda GOSOM. A mayor profundidad, más tiempo tarda."
        )
        st.session_state.last_search_depth = depth_ui_val
        emails_ui_val = st.checkbox(
            '📧 Extraer Correos Electrónicos',
            value=st.session_state.last_extract_emails,
            disabled=scraping_state['scraping_in_progress'], key="cb_emails_sidebar",
            help="Marcar para intentar extraer emails (puede aumentar significativamente el tiempo)."
        )
        st.session_state.last_extract_emails = emails_ui_val

    st.markdown("---")
    with st.expander("⚡ Modos Especiales", expanded=False):
        fast_mode_ui_val = st.checkbox(
            '⚡️ Modo Rápido (Fast Mode)',
            value=st.session_state.get('fast_mode', False),
 disabled=scraping_state['scraping_in_progress'], key="cb_fast_mode_sidebar",
 help="Activa el 'Fast Mode' de GOSOM (puede funcionar mejor en algunos casos, pero podría ser menos estable)."
 )
    st.subheader("🚀 Controles de Ejecución")
    col_btn_start_s, col_btn_stop_s = st.columns(2)

    # Comprobar si todas las ciudades seleccionadas tienen keywords no vacías.
    all_keywords_present = True
    if not selected_cities_keys_ui:
        all_keywords_present = False
    else:
        for city in selected_cities_keys_ui:
            if not st.session_state.selected_cities_keywords_ui.get(city, "").strip():
                all_keywords_present = False
                break

    with col_btn_start_s:
        if st.button('🚀 Iniciar Scraping', key="btn_start_s_sidebar", disabled=scraping_state['scraping_in_progress'] or not CORE_LOGIC_LOADED or not all_keywords_present):
            if not selected_cities_keys_ui:
                st.warning('⚠️ Selecciona al menos una ciudad para iniciar el scraping.')
            elif not CORE_LOGIC_LOADED:
                st.error("❌ El módulo 'core_logic.py' no cargó correctamente. No se puede iniciar el scraping real.")
            elif not all_keywords_present:
                st.warning("⚠️ Faltan palabras clave para algunas ciudades seleccionadas.")
            else:
                set_scraping_state(
                    current_process_status="Iniciando...", start_time=datetime.now(),
                    cumulative_row_count=0, live_csv_row_counts={city: 0 for city in selected_cities_keys_ui},
                    stop_scraping_flag=False, scraping_in_progress=True, scraping_done=False
                )
                st.session_state.current_log_display = "Iniciando Logs...\n"
                st.session_state.current_log_lines = []
                # Limpiar resultados anteriores.
                st.session_state.processed_city_data_results = {}
                st.session_state.final_df_consolidated = pd.DataFrame(columns=gmaps_column_names_list_app)
                keywords_for_thread_dict = st.session_state.selected_cities_keywords_ui.copy()
                ui_logger.info(f"Btn 'Iniciar'. Ciudades: {selected_cities_keys_ui}, Prof: {depth_ui_val}, Emails: {emails_ui_val}")
                # Iniciar el hilo de scraping.
                thread = Thread(target=execute_scraping_task_threaded, args=(
                    CORE_LOGIC_LOG_FILE_PATH_APP,
                    selected_cities_keys_ui, keywords_for_thread_dict,
                    depth_ui_val, emails_ui_val, config_params_app, get_paths_config_dict_app(),
 st.session_state.log_messages_queue
                ))
                st.session_state.scraping_thread = thread
                thread.start()
                st.rerun()

    with col_btn_stop_s:
        if st.button('🛑 Detener Scraping', key="btn_stop_s_sidebar", disabled=not scraping_state['scraping_in_progress'], use_container_width=True):
            if scraping_state['scraping_in_progress']:
                set_scraping_state(stop_scraping_flag=True)
                ui_logger.warning("Solicitud de DETENER scraping.")
                st.warning("Intentando detener scraping... (Proceso Docker actual podría necesitar completarse o timeout)")

    # --- Lógica de Registro de Jobs ---
    st.markdown("---")
    st.subheader("📝 Historial de Jobs de Scraping")

    def log_scraping_job(cities, keywords_dict, depth, emails_extracted, row_count, error_status):
        """Registra los detalles de un job de scraping en scrape_jobs.csv."""
        job_log_path = MOTHER_CSV_PATH_APP
        header = ['id', 'fecha', 'hora', 'ciudades', 'keywords', 'depth', 'emails_extracted', 'filas_extraidas', 'error']
        try:
            # Comprobar si el archivo existe y no está vacío para determinar el siguiente ID.
            next_id = 1
            write_header = True
            if os.path.exists(job_log_path) and os.stat(job_log_path).st_size > 0:
                df_jobs = pd.read_csv(job_log_path)
                if not df_jobs.empty:
                    next_id = len(df_jobs) + 1
                write_header = False # No escribir el encabezado si el archivo existe y no está vacío.

            now = datetime.now()
            # Aplanar las keywords en una sola cadena para simplicidad y legibilidad.
            all_keywords = []
            for city_k, kws in keywords_dict.items():
                all_keywords.extend([f"{city_k}:{kw.strip()}" for kw in kws.splitlines() if kw.strip()])

            # Preparar la fila de datos.
            job_data = {
                'id': next_id, 'fecha': now.strftime("%Y-%m-%d"), 'hora': now.strftime("%H:%M:%S"),
                'ciudades': ", ".join(cities), 'keywords': "; ".join(all_keywords), 'depth': depth,
                'emails_extracted': emails_extracted, 'filas_extraidas': row_count, 'error': error_status
            }

            # Añadir al CSV.
            df_new_job = pd.DataFrame([job_data])
            df_new_job.to_csv(job_log_path, mode='a', index=False, header=write_header)
            ui_logger.success(f"Job de scraping (ID: {next_id}) registrado exitosamente.")

        except Exception as e:
            ui_logger.error(f"Error al registrar el job de scraping: {e}", exc_info=True)

    # Mostrar historial de jobs.
    try:
        # Usar la ruta correcta para los registros de jobs.
        if os.path.exists(MOTHER_CSV_PATH_APP) and os.stat(MOTHER_CSV_PATH_APP).st_size > 0:
            df_job_history = pd.read_csv(MOTHER_CSV_PATH_APP)
            st.write(f"Jobs previos encontrados: {len(df_job_history)}")
            st.dataframe(df_job_history.tail()) # Mostrar los últimos para relevancia.
        else:
            st.info("No se encontraron registros de jobs de scraping previos.")

    except FileNotFoundError:
        st.warning("Archivo de historial de jobs no encontrado.")
    except Exception as e:
        st.error(f"Error al cargar el historial de jobs: {e}")

    st.markdown("---")
    st.caption(f"Agente GOSOM ETL - MVP v0.7 | Lógica Principal: {'Cargada OK' if CORE_LOGIC_LOADED else 'FALLÓ / DUMMY'}")


# --- Área de Contenido Principal (Cambia según la etapa) ---

# Comentario para indicar que Etapas 2 y 3 fueron removidas
# y que el procesamiento posterior es manejado por el ETL Central.
st.markdown("---")
st.warning("Nota: Las funcionalidades de consolidación, estadísticas y gestión de leads (Etapas 2 y 3) han sido retiradas de este agente.")
st.info("Este agente ahora se enfoca únicamente en el scraping y generación de CSVs crudos. Un ETL Central debe encargarse del procesamiento posterior.")
if st.session_state.stage == 1:
    st.header("⚙️ Configuración y Scraping")
    scraping_state = get_scraping_state()

    # Mostrar texto introductorio cuando no se está scrapeando.
    if not scraping_state['scraping_in_progress']:
        st.markdown("""
        ### Bienvenido a la Etapa de Configuración y Scraping
        Aquí puedes configurar los parámetros para iniciar la extracción de datos de Google Maps.
        - **Paso 1:** Selecciona las ciudades y define las palabras clave en la barra lateral.
        - **Paso 2:** Ajusta los parámetros avanzados si es necesario.
        - **Paso 3:** Haz clic en **'🚀 Iniciar Scraping'** para comenzar.
        """)
    if config_params_app == FALLBACK_CONFIG_APP:
        st.error(f"¡ADVERTENCIA! No se pudo cargar el archivo de configuración ({os.path.basename(CONFIG_FILE_PATH_APP)}). Usando configuración por defecto.")
    if not CORE_LOGIC_LOADED:
        st.error("¡ADVERTENCIA CRÍTICA! El módulo 'core_logic.py' no pudo cargar. Usando funcionalidades limitadas (dummies). No se podrá realizar scraping real.")

    # Mostrar indicadores de progreso prominentes si está en curso.
    if scraping_state['scraping_in_progress']:
        st.subheader("Estado Actual del Scraping:")
        if scraping_state['start_time']:
            elapsed_time = datetime.now() - scraping_state['start_time']
            total_seconds = int(elapsed_time.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            selected_cities = st.session_state.get('last_selected_cities', [])
            total_cities = len(selected_cities)
            cities_with_progress = len(scraping_state['live_csv_row_counts'])

            col1_count, col2_count, col3_count = st.columns(3)
            col1_count.metric("Estado General", scraping_state['current_process_status'])
            col2_count.metric("Tiempo Transcurrido", time_str)
            col3_count.metric("Progreso Ciudades", f"{cities_with_progress}/{total_cities}")
        else:
            # Visualización de respaldo si start_time es None inesperadamente.
            st.info(scraping_state['current_process_status'])

        st.warning("Nota: El scraper puede tardar al menos 3 minutos en mostrar los primeros resultados.")
        st.warning("Nota sobre Detener: El proceso podría no detenerse instantáneamente.")

        # --- Sección de Progreso del Scraping (Visible en Etapa 1) ---
        st.subheader("Logs en Vivo (Salida de GOSOM y Agente)")
        log_display_placeholder_live = st.empty()

        final_results_payload_ui = None
        critical_error_payload_ui = None
        thread_completed_signal_received_ui = False
        MAX_LIVE_LOG_LINES = 200
        new_log_entries_list_ui = []

        while not st.session_state.log_messages_queue.empty():
            try:
                msg_item_ui = st.session_state.log_messages_queue.get_nowait()
                if isinstance(msg_item_ui, dict):
                    msg_type = msg_item_ui.get("type")
                    if msg_type == LogMessageType.FINAL_RESULTS:
                        final_results_payload_ui = msg_item_ui
                    elif msg_type == LogMessageType.CRITICAL_ERROR:
                        critical_error_payload_ui = msg_item_ui
                    elif msg_type == LogMessageType.LIVE_ROW_COUNT:
                        current_live_counts = get_scraping_state()['live_csv_row_counts'].copy()
                        current_live_counts[msg_item_ui["city"]] = msg_item_ui["count"]
                        set_scraping_state(live_csv_row_counts=current_live_counts)
                    elif msg_type == LogMessageType.ROW_COUNT_UPDATE:
                        set_scraping_state(cumulative_row_count=msg_item_ui["cumulative_count"])
                elif isinstance(msg_item_ui, str):
                    if msg_item_ui == LogMessageType.THREAD_COMPLETE_SIGNAL:
                        thread_completed_signal_received_ui = True
                        break
                    elif msg_item_ui.startswith(f"{LogMessageType.PROCESO_START}:") or msg_item_ui.startswith(f"{LogMessageType.STATUS_UPDATE}:"):
                        set_scraping_state(current_process_status=msg_item_ui.split(":", 1)[1])
                    elif msg_item_ui.startswith(f"{LogMessageType.GOSOM_LOG}:") or msg_item_ui.startswith(f"{LogMessageType.CMD_DOCKER}:"):
                        new_log_entries_list_ui.append(msg_item_ui.split(":", 1)[1])
                    elif not msg_item_ui.startswith("DEBUG:") and not msg_item_ui.startswith("INFO:[CoreLogicThread"):
                        new_log_entries_list_ui.append(msg_item_ui)
            except queue.Empty:
                break

        if new_log_entries_list_ui:
            if 'current_log_lines' not in st.session_state or not isinstance(st.session_state.current_log_lines, list):
                st.session_state.current_log_lines = []
            st.session_state.current_log_lines.extend(new_log_entries_list_ui)
            st.session_state.current_log_lines = st.session_state.current_log_lines[-MAX_LIVE_LOG_LINES:]
            st.session_state.current_log_display = "\n".join(st.session_state.current_log_lines)

        log_display_placeholder_live.code(st.session_state.current_log_display, language='log')

        current_thread_ui_check_live = st.session_state.get('scraping_thread')
        # Volver a ejecutar solo si el hilo terminó o si hay una señal crítica.
        thread_is_finished = thread_completed_signal_received_ui or not (current_thread_ui_check_live and current_thread_ui_check_live.is_alive())

        if thread_is_finished or critical_error_payload_ui:
            # --- Disparador de Registro de Job ---
            # Este es el lugar ideal para registrar el job. El hilo ha terminado.
            if final_results_payload_ui:
                st.session_state.final_df_consolidated = final_results_payload_ui['data']
                st.session_state.processed_city_data_results = final_results_payload_ui['processed_city_data']

            final_row_count = len(st.session_state.get('final_df_consolidated', pd.DataFrame()))
            error_status = "OK"
            if critical_error_payload_ui:
                error_status = f"Error: {critical_error_payload_ui.get('message', 'Error Desconocido')}"
                set_scraping_state(current_process_status=f"ERROR CRÍTICO: {error_status}")
            elif st.session_state.get('stop_scraping_flag', False):
                error_status = "Detenido por el usuario"

            # Usar helper para establecer el estado final.
            set_scraping_state(scraping_in_progress=False, scraping_done=True, start_time=None) # Resetear tiempo.
            log_scraping_job(
                st.session_state.last_selected_cities, st.session_state.selected_cities_keywords_ui,
                st.session_state.last_search_depth, st.session_state.last_extract_emails,
                final_row_count, error_status
            )
            ui_logger.info("Thread finalizado. UI a estado 'done'.")
            st.rerun() # Volver a ejecutar para mostrar el estado final y los resultados.
        else:
            time.sleep(1) # Tasa de refresco para los logs en vivo.
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"Agente GOSOM ETL - MVP v0.7 | Lógica Principal: {'Cargada OK' if CORE_LOGIC_LOADED else 'FALLÓ / DUMMY'}")