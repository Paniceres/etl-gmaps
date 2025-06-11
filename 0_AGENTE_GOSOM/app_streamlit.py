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


# --- Definición de Rutas Base ---
try:
    APP_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError: 
    APP_ROOT_DIR = os.getcwd() 


print(f"DEBUG (app_streamlit INIT): APP_ROOT_DIR={APP_ROOT_DIR}") # Quitar para producción


SRC_DIR = os.path.join(APP_ROOT_DIR, 'src')
CONFIG_DIR_APP = os.path.join(APP_ROOT_DIR, 'config')
DATA_DIR_APP = os.path.join(APP_ROOT_DIR, 'data')

# New directory for clean data
CITY_CLEAN_DATA_DIR_APP = os.path.join(DATA_DIR_APP, 'city_clean')
CONSOLIDATED_DATA_DIR_APP = os.path.join(DATA_DIR_APP, 'consolidated') # Corrected path for consolidated

# Correct path for consolidated mother CSV - MUST be defined AFTER CONSOLIDATED_DATA_DIR_APP
CONSOLIDATED_MOTHER_CSV_PATH_APP = os.path.join(CONSOLIDATED_DATA_DIR_APP, 'consolidated_leads.csv')

# New directory for clean data
CITY_CLEAN_DATA_DIR_APP = os.path.join(DATA_DIR_APP, 'city_clean')
CONSOLIDATED_DATA_DIR_APP = os.path.join(DATA_DIR_APP, 'consolidated') # Corrected path for consolidated
LOGS_DIR_APP = os.path.join(DATA_DIR_APP, 'logs')
RAW_DATA_DIR_APP = os.path.join(DATA_DIR_APP, 'raw')
CHUNKS_DATA_DIR_APP = os.path.join(DATA_DIR_APP, 'chunks')

JOBS_DATA_DIR_APP = os.path.join(DATA_DIR_APP, 'jobs') # Moved after DATA_DIR_APP is defined

# Ensure all necessary directories are created
for dir_path_init in [SRC_DIR, CONFIG_DIR_APP, DATA_DIR_APP, LOGS_DIR_APP, RAW_DATA_DIR_APP, JOBS_DATA_DIR_APP, CHUNKS_DATA_DIR_APP, CITY_CLEAN_DATA_DIR_APP, CONSOLIDATED_DATA_DIR_APP]:
 try: os.makedirs(dir_path_init, exist_ok=True)
    except Exception as e_mkdir_init_loop: print(f"ERROR (app_streamlit INIT): Creando dir {dir_path_init}: {e_mkdir_init_loop}")
    
if SRC_DIR not in sys.path: sys.path.insert(0, SRC_DIR) # Use insert(0, ...) for higher priority
MOTHER_CSV_PATH_APP = os.path.join(JOBS_DATA_DIR_APP, 'scrape_jobs.csv') # Path for job logs, not consolidated leads
CORE_LOGIC_LOADED = False
class DummyLogger:
    def __init__(self, *args, **kwargs): self.name = kwargs.get('logger_name', 'DummyLoggerUI')
    def _log_print(self, level, msg, art): print(f"{datetime.now().strftime('%H:%M:%S')} [{level}] ({self.name}) {art} {msg}")
    def info(self, msg, art="[INFO]"): self._log_print("INFO", msg, art)
    def error(self, msg, exc_info=False, art="[FAIL]"): self._log_print("ERROR", msg, art);print(msg) # Print error to console too
    def warning(self, msg, art="[ATEN]"): self._log_print("WARNING", msg, art)
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
import pandas as pd # Import pandas after potentially setting up dummy functions
def dummy_process_city_func(*args, **kwargs): 
    logger_instance = kwargs.get('logger_instance', DummyLogger(logger_name="DummyProcCity")) # type: ignore
    city_key = kwargs.get('city_key', 'dummy_city')
    time.sleep(0.1); log_q_thread.put(f"GOSOM_LOG:Dummy GOSOM log 1 para {city_key}")
    time.sleep(0.1); log_q_thread.put(f"GOSOM_LOG:Dummy GOSOM log 2 para {city_key}")
    dummy_df = pd.DataFrame({'title':['dummy ' + city_key], 'emails':['d@e.co'], 'link':['d.co'], 'lat': [0.0], 'lon': [0.0]}) # Added lat/lon for dummy
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
 from core_logic import StyledLogger, gmaps_column_names, load_keywords_from_csv_core, process_city_data_core, compare_and_filter_new_data_core, validate_csv_integrity_core # Import the validation function
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
 ui_logger.info(f"Configuración cargada desde {os.path.basename(CONFIG_FILE_PATH_APP)}.")
except Exception as e_config_load:
    ui_logger.critical(f"No se pudo cargar el archivo de configuración {CONFIG_FILE_PATH_APP}: {e_config_load}", exc_info=True)
    config_params_app = FALLBACK_CONFIG_APP
 
# Define logger instance for Streamlit UI
streamlit_ui_log_filename = "streamlit_ui_events.log"
streamlit_ui_log_path_app = os.path.join(LOGS_DIR_APP, streamlit_ui_log_filename) 
ui_logger = StyledLogger_cls_app(logger_name="StreamlitAppUI", log_file_path=streamlit_ui_log_path_app, level=logging.INFO) # Changed default level to INFO for UI log

core_logic_log_filename_cfg = config_params_app.get('log_filename', FALLBACK_CONFIG_APP['log_filename'])
CORE_LOGIC_LOG_FILE_PATH_APP = os.path.join(LOGS_DIR_APP, core_logic_log_filename_cfg)

# Default session state values - Define them outside the function calls # type: ignore
default_ss_vals = {
    'selected_cities_keywords_ui': {}, 'processed_city_data_results': {}, 'scraping_done': False,
    'scraping_in_progress': False, 'final_df_consolidated': pd.DataFrame(columns=gmaps_column_names_list_app), 
    'last_selected_cities': list(config_params_app.get('gmaps_coordinates', {}).keys())[:1] if config_params_app.get('gmaps_coordinates') else [], # Fallback a dict vacío
    'last_search_depth': int(config_params_app.get('default_depth', 1)),
    'last_extract_emails': True, 'log_messages_queue': queue.Queue(),
    'current_process_status': "Listo para iniciar.", 'current_log_display': "Logs de la operación aparecerán aquí...\n",
    'start_time': None, 'cumulative_row_count': 0, 'stop_scraping_flag': False,
    'live_csv_row_counts': {}, # {city_key: count}
}
for key, value in default_ss_vals.items():
    if key not in st.session_state: st.session_state[key] = value

def get_paths_config_dict_app():
    """Returns a dict with paths to various directories."""
    return {'CONFIG_DIR': CONFIG_DIR_APP, 'RAW_DATA_DIR': RAW_DATA_DIR_APP,
            'LOGS_DIR': LOGS_DIR_APP}


def generate_clean_city_csvs(processed_city_data, output_dir, logger_instance):
    """
    Generates clean CSVs for each city from processed data,
    selecting 'title', 'emails', and 'phone' columns (translated for output).
    """
    logger_instance.section("Generando CSVs Limpios por Ciudad")
    if not os.path.exists(output_dir):
        logger_instance.warning(f"Directorio de salida no encontrado: {output_dir}. Intentando crearlo.")
        # Ensure parent data directory also exists
        os.makedirs(os.path.dirname(output_dir), exist_ok=True)
        try:
            os.makedirs(output_dir)
        except OSError as e:
            logger_instance.critical(f"No se pudo crear el directorio de salida {output_dir}: {e}", exc_info=True)
            return

    for city, data in processed_city_data.items():
        df = data.get('df_transformed') # Use df_transformed as per core_logic 
        if df is not None and not df.empty:
            # Check for critical columns before proceeding
            required_cols = ['title', 'emails']
 if not all(col in df.columns for col in required_cols):
 logger_instance.warning(f"Datos para {city} no contienen todas las columnas requeridas ({', '.join(required_cols)}). Saltando generación de CSV limpio.")
                continue

            # Select specified columns, handling potential missing 'phone'
            clean_cols = ['title', 'emails']
            if 'phone' in df.columns:
 clean_cols.append('phone')
 else:
                logger_instance.warning(f"Columna 'phone' no encontrada en los datos de {city}. CSV limpio generado sin esta columna.")

 clean_df = df[clean_cols].copy() # Use .copy() to avoid SettingWithCopyWarning

            # Rename columns for the clean CSV output
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

        elif df is None:
 logger_instance.warning(f"No hay DataFrame procesado para {city}. Saltando generación de CSV limpio.") # Translated message
        elif df.empty: 
 # Use info level as it's not an error # Translated message
 logger_instance.info(f"DataFrame vacío para {city}. No se generó CSV limpio.")
 
def consolidate_scraped_data(new_data_df: pd.DataFrame, logger_instance=DummyLogger()) -> bool:
    """
    Consolidates newly scraped data (new_data_df) with the existing consolidated mother CSV.
    Loads the mother CSV, merges, removes duplicates based on 'link' and 'title',
    and saves the updated DataFrame back to the mother CSV path.
    Initializes an empty DataFrame if the mother CSV doesn't exist or is empty.

    Args:
 new_data_df: DataFrame containing the newly scraped data.
 logger_instance: Logger instance for logging messages.

    Returns:
 True if consolidation was successful, False otherwise.
    """
    mother_csv_path = CONSOLIDATED_MOTHER_CSV_PATH_APP # Use the global consolidated path
    logger_instance.section("Consolidando Nuevos Datos con CSV Madre")
 
    if new_data_df is None or new_data_df.empty:
        logger_instance.warning("No hay nuevos datos para consolidar.")
 return True # Considered successful as there was nothing to add
 
    try:
 # Try to load the existing mother CSV
 try:
            if os.path.exists(mother_csv_path) and os.stat(mother_csv_path).st_size > 0:
                df_mother = pd.read_csv(mother_csv_path, dtype=str) # Read as string to avoid type issues
                logger_instance.info(f"CSV Madre existente cargado desde {mother_csv_path} ({len(df_mother)} filas).")
 else:
 # Initialize empty DataFrame with columns that *will* be needed + those from new data # Use pd.NA for future compatibility.
                # Ensure essential columns for consolidation/tracking are present
                initial_cols = ['link', 'title', 'emails', 'phone', 'search_origin_city', 'fecha_asignacion', 'id_chunk', 'estado_asignacion', 'asignado_a', 'lat', 'lon']
                # Add any columns from new_data_df that are not in initial_cols
                all_cols = list(set(initial_cols + list(new_data_df.columns)))
                df_mother = pd.DataFrame(columns=all_cols)
                logger_instance.info("CSV Madre no encontrado o vacío. Creando nuevo CSV Madre.")
 except (FileNotFoundError, pd.errors.EmptyDataError):
            # This case should be handled by the outer if/else, but being defensive
            df_mother = pd.DataFrame(columns=new_data_df.columns) # Start with columns from new data if file issue
 logger_instance.warning(f"Error al cargar CSV Madre o estaba vacío. Iniciando con DataFrame vacío. ({mother_csv_path})") # Pass the path to the consolidated mother CSV for the compare_and_filter_new_data_core function
 except Exception as e_load:
 logger_instance.error(f"Error inesperado al cargar CSV Madre: {e_load}", exc_info=True)
            logger_instance.info(f"CSV Madre existente cargado desde {mother_csv_path} ({len(df_mother)} filas).")
            
        # Use the refined deduplication function from core_logic
 # Pass the path to the mother CSV for the compare_and_filter_new_data_core function
        df_unique_new_data = compare_and_filter_new_data_core(new_data_df, mother_csv_path, logger_instance) # Use the function imported from core_logic

        if df_unique_new_data is None or df_unique_new_data.empty:
            logger_instance.info("No se encontraron nuevos registros únicos para añadir al CSV Madre.")
 return True # Considered successful as no unique data was found
 
        num_new_unique = len(df_unique_new_data)
        logger_instance.info(f"Se encontraron {num_new_unique} nuevos registros únicos para añadir.")
 
        # Append only the unique new data to the mother DataFrame
        df_consolidated = pd.concat([df_mother, df_unique_new_data], ignore_index=True).reset_index(drop=True)
 
        # Ensure assignment columns exist and initialize for new rows (added by the unique new data)
        if 'estado_asignacion' not in df_consolidated.columns:
            df_consolidated['estado_asignacion'] = 'Pendiente'
        if 'asignado_a' not in df_consolidated.columns:
            df_consolidated['asignado_a'] = '' # Or pd.NA or None

        df_consolidated.to_csv(mother_csv_path, index=False)
        logger_instance.success(f"CSV Madre actualizado en {mother_csv_path}. Se añadieron {num_new_unique} nuevos registros. Total: {len(df_consolidated)} filas.")
 return True # Indicate success
 except (IOError, OSError) as e_io:
        logger_instance.critical(f"Error de E/S al leer o escribir el CSV Madre en {mother_csv_path}: {e_io}", exc_info=True)
 return False # Indicate failure
 except Exception as e_general:
        logger_instance.critical(f"Error inesperado durante la consolidación del CSV Madre en {mother_csv_path}: {e_general}", exc_info=True)
 return False # Indicate failure
 

def generate_lead_chunks(output_dir, chunk_size=30, logger_instance=DummyLogger()):
    """
    Generates chunks of leads (nombre, mail, telefono) from the mother CSV,
    tracks assigned leads, and saves chunks as separate CSVs per city.
    """
    logger_instance.section("Generando Chunks de Leads para Vendedores")
    generated_chunk_files = {} # Initialize here to return even on early exit

    mother_csv_path = CONSOLIDATED_MOTHER_CSV_PATH_APP # Use the global consolidated path

    if not os.path.exists(mother_csv_path) or os.stat(mother_csv_path).st_size == 0:
 logger_instance.warning(f"CSV Madre no encontrado o vacío en {mother_csv_path}. No se pueden generar chunks.")
        return generated_chunk_files

    if not os.path.exists(output_dir):
        logger_instance.warning(f"Directorio de salida para chunks no encontrado: {output_dir}. Intentando crearlo.")
        try:
            os.makedirs(output_dir)
        except OSError as e:
            # Check if the error is because the directory already exists from another process/thread
            if not os.path.exists(output_dir): # Double check if it still doesn't exist
                logger_instance.critical(f"No se pudo crear el directorio de salida {output_dir}: {e}", exc_info=True)
                return generated_chunk_files
            logger_instance.critical(f"No se pudo crear el directorio de salida {output_dir}: {e}", exc_info=True)
            return

    try:
        df_mother = pd.read_csv(mother_csv_path)
        logger_instance.info(f"CSV Madre cargado desde {mother_csv_path} ({len(df_mother)} filas).")
    except Exception as e:
        logger_instance.critical(f"Error al cargar CSV Madre desde {mother_csv_path}: {e}", exc_info=True)
        return generated_chunk_files

    # Ensure tracking and required columns exist in the loaded DataFrame
    for col in ['fecha_asignacion', 'id_chunk']:
        if col not in df_mother.columns:
            df_mother[col] = pd.NA # Initialize with NA if missing. Use pd.NA for future compatibility. # Ensure required columns exist before proceeding

    required_cols_for_chunking = ['city', 'title', 'emails', 'link'] # 'link' is needed for deduplication check implicitly via mother CSV read
 if not all(col in df_mother.columns for col in required_cols_for_chunking): # Ensure required columns exist before proceeding
        missing_cols = [col for col in required_cols_for_chunking if col not in df_mother.columns]
        logger_instance.critical(f"Columnas requeridas ({', '.join(missing_cols)}) no encontradas en el CSV Madre. No se pueden generar chunks.")
        return generated_chunk_files

    # Check for basic data integrity: title and emails should not be completely missing in relevant rows
 if df_mother[['title', 'emails']].dropna(how='all').empty and len(df_mother) > 0: # Check if there are any rows with at least title or email
        logger_instance.warning("El CSV Madre parece estar vacío o las columnas 'title' y 'emails' están vacías en todas las filas.")

    # Filter unassigned leads
    df_unassigned = df_mother[df_mother['fecha_asignacion'].isna()].copy() # Use .isna() for pd.NA and .copy()
    logger_instance.info(f"{len(df_unassigned)} leads sin asignar encontrados.")

    if df_unassigned.empty:
        logger_instance.info("No hay leads sin asignar para generar chunks.")
        return {} # Return an empty dict

    # Get unique cities from unassigned leads
    cities_with_unassigned = df_unassigned['city'].unique() # Assuming 'city' column exists
    logger_instance.info(f"Ciudades con leads sin asignar: {list(cities_with_unassigned)}")

    chunk_count = 0
    updated_indices = [] # To track which rows in the mother CSV need updating
 generated_chunk_files = {} # To store city -> list of chunk files
 
    for city in cities_with_unassigned:
        df_city_unassigned = df_unassigned[df_unassigned['city'] == city].copy()
        if df_city_unassigned.empty:
            continue # Should not happen based on cities_with_unassigned, but safe check

        num_chunks_city = (len(df_city_unassigned) + chunk_size - 1) // chunk_size
        logger_instance.info(f"Generando {num_chunks_city} chunks de {chunk_size} leads para {city.capitalize()}...")

        for i in range(0, len(df_city_unassigned), chunk_size):
            chunk_count += 1
            df_chunk = df_city_unassigned.iloc[i:i + chunk_size].copy()
            
            # Check if the chunk dataframe is empty (should not happen with the loop range, but safe)
            if df_chunk.empty:
                logger_instance.warning(f"Chunk vacío generado for {city} at index {i}. Skipping.")
                continue

            # Select only the required columns for the chunk CSV
            chunk_cols = ['title', 'emails']
            if 'phone' in df_chunk.columns:
 chunk_cols.append('phone')
 else:
                logger_instance.warning(f"Columna 'phone' no encontrada en chunk {chunk_count} ({city}). Generando sin telefono.")

            df_chunk_export = df_chunk[chunk_cols]
            # Rename columns to "nombre del local", "mail", "telefono" for the chunk CSV 
            rename_map = {'title': 'nombre del local', 'emails': 'mail'}
            if 'phone' in chunk_cols:
                rename_map['phone'] = 'telefono'
            df_chunk_export = df_chunk_export.rename(columns=rename_map)

            # Generate unique chunk ID (e.g., City-Timestamp-ChunkNum)
            timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
            chunk_id = f"{city.replace(' ', '_')}-{timestamp_str}-Chunk{i//chunk_size + 1}"

            chunk_file_path = os.path.join(output_dir, f'{chunk_id}.csv')
            try:
                df_chunk_export.to_csv(chunk_file_path, index=False) # Save the renamed chunk # Optionally, you could skip updating mother CSV for this chunk if save failed
                logger_instance.success(f"Chunk {chunk_id} guardado en {chunk_file_path} ({len(df_chunk_export)} leads).")
            except Exception as e_save:
                 logger_instance.error(f"Error al guardar chunk {chunk_id} en {chunk_file_path}: {e_save}", exc_info=True)
                 # Optionally, you could skip updating mother CSV for this chunk if save failed
                 continue 

            if city not in generated_chunk_files: generated_chunk_files[city] = []
            generated_chunk_files[city].append(os.path.basename(chunk_file_path))

            # Update the mother CSV: mark leads as assigned
            # Get the original indices from the mother CSV for the leads in this chunk
            original_indices = df_chunk.index # Get the original indices from the slice
            df_mother.loc[original_indices, 'fecha_asignacion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df_mother.loc[original_indices, 'id_chunk'] = chunk_id 
            updated_indices.extend(original_indices)

    if updated_indices:
        # Save the updated mother CSV
        df_mother.to_csv(mother_csv_path, index=False)
        logger_instance.success(f"CSV Madre actualizado en {mother_csv_path} con información de asignación para {len(updated_indices)} leads.")

    return generated_chunk_files


# --- Custom CSS for Brand Kit Colors ---
brand_kit_colors = {
    "Primary": "#F3C04F",
    "Secondary 1": "#3C1B43",
    "Secondary 2": "#922D50",
    "Secondary 3": "#4C2E05",
}

custom_css = f"""
<style>
/* General text and link color */
body {{ color: {brand_kit_colors["Secondary 1"]}; }}
a {{ color: {brand_kit_colors["Primary"]}; }}
/* Sidebar background */
[data-testid="stSidebar"] {{ background-color: {brand_kit_colors["Secondary 3"]}; }}
/* Primary button color */
div.stButton > button {{ background-color: {brand_kit_colors["Primary"]}; color: white; }}
/* Expander header color */
details summary {{ color: {brand_kit_colors["Secondary 1"]}; }}
</style>
"""

class QueueLogHandler(logging.Handler):
    def __init__(self, log_q):
        super().__init__(); self.log_q = log_q
        self.setFormatter(logging.Formatter('%(asctime)s-%(levelname)s: %(message)s',datefmt='%H:%M:%S'))
    def emit(self, record): self.log_q.put(self.format(record))

def execute_scraping_task_threaded(
 # --- Arguments to pass to the thread ---
    core_logic_log_file_path_app,
    selected_cities_list_thread, keywords_per_city_thread_dict,
 depth_ui_thread, emails_ui_thread,
    cfg_params_thread, paths_cfg_thread, log_q_thread ):
    current_thread_id = threading.get_ident()
    log_path_for_thread_core = core_logic_log_file_path_app 

    # Limpiar logs de la cola al inicio de cada ejecución
 while not log_q_thread.empty(): # Check if handler is of type QueueLogHandler
 try: log_q_thread.get_nowait()
 except queue.Empty: pass # Defensive

    thread_core_logger = StyledLogger_cls_app(logger_name=f"CoreLogicThread-{current_thread_id}",
 log_file_path=log_path_for_thread_core, level=logging.DEBUG)
 # Limpiar handlers de cola existentes para evitar duplicados si el thread se reutiliza (aunque no es el caso aquí)
    for handler_to_remove in list(thread_core_logger.logger.handlers):
        if isinstance(handler_to_remove, QueueLogHandler): # Check if handler is of type QueueLogHandler
 thread_core_logger.logger.removeHandler(handler_to_remove)

    queue_handler_for_thread = QueueLogHandler(log_q_thread) # Pass logger to core_logic
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

            # --- Validation: Before Scraping (Optional but good practice - mainly checks config) ---
            # Could add a check here if needed, but core_logic functions already handle missing inputs

            # --- Core Logic Call: Run Scraper ---
            # process_city_data_core includes run_gmaps_scraper_docker_core
            # It returns the path to the raw CSV if successful
            # Validation of the raw CSV will happen immediately after its creation within core_logic or here.
            # Let's place the raw CSV validation *after* process_city_data_func_app returns the raw path.

            df_transformed_city, raw_path_city = process_city_data_func_app(
 log_q_streamlit=log_q_thread, # Pass the queue to core_logic # type: ignore
 city_key=city_k_thread, keywords_list=keywords_list_for_city, # type: ignore
                depth_from_ui=depth_ui_thread, extract_emails_flag=emails_ui_thread,
 config_params_dict=cfg_params_thread, paths_config_dict=paths_cfg_thread, # type: ignore
 logger_instance=thread_core_logger, # Pass logger to core_logic
)\
            
            # --- Validation: After Raw CSV Generation & Transformation ---
            # Check if raw_path_city is valid and points to a file that was (attempted to be) created
            is_raw_csv_valid = False
            if raw_path_city and os.path.exists(raw_path_city) and os.path.getsize(raw_path_city) > 0:
                # Validate the raw CSV structure if needed - this check is now more crucial after the raw file is generated
                # Let's rely on the transformation step to handle potential issues, but a validation here is also possible.
                # For now, let's ensure the transformed DF is valid.
                if df_transformed_city is not None and not df_transformed_city.empty:
                    # We could add column validation for the transformed DF here too if required_columns for transformed DF were defined
                    is_raw_csv_valid = True
                else:
                    thread_core_logger.warning(f"Raw data for {city_k_thread} was not transformed into a valid DataFrame. Skipping consolidation for this city.")

            temp_processed_city_data_thread[city_k_thread] = {'df_transformed': df_transformed_city, 'raw_path': raw_path_city, 'is_valid': is_raw_csv_valid}
            if df_transformed_city is not None and not df_transformed_city.empty:
                temp_all_city_dfs_thread.append(df_transformed_city) # Añadir solo DFs no vacíos
                log_q_thread.put(f"{LogMessageType.SUCCESS}:{city_k_thread.capitalize()} ({len(df_transformed_city)} prosp.).")
            elif df_transformed_city is not None:
                log_q_thread.put(f"{LogMessageType.INFO}:{city_k_thread.capitalize()} (0 prosp).")
 else: # Use type of message # Log critical error
                log_q_thread.put(f"{LogMessageType.ERROR}:Falló {city_k_thread.capitalize()}.")

        final_df_payload_thread = pd.DataFrame(columns=gmaps_column_names_list_app) # type: ignore
        if temp_all_city_dfs_thread:
            try:
 final_df_payload_thread = pd.concat(temp_all_city_dfs_thread, ignore_index=True) # type: ignore
            except Exception as e_concat:
 log_q_thread.put({"type": LogMessageType.CRITICAL_ERROR, "message": f"Concat Error: {e_concat}"})
 logger_instance.critical(f"Concat Error in thread: {e_concat}", exc_info=True)
        log_q_thread.put({"type": LogMessageType.FINAL_RESULTS, "data": final_df_payload_thread,
                          "processed_city_data": temp_processed_city_data_thread})
        thread_core_logger.section("Tarea Scraping (Thread) Finalizada")
    except Exception as e_thread_main:
        thread_core_logger.critical(f"Error mayor en thread: {str(e_thread_main)}", exc_info=True)
        log_q_thread.put({"type": LogMessageType.CRITICAL_ERROR, "message": str(e_thread_main)}) # Usar tipo de mensaje
    finally:
        log_q_thread.put(LogMessageType.THREAD_COMPLETE_SIGNAL)
        
# Function to get the highest priority task from 0_mejoras.md
def get_highest_priority_task():
    mejoras_file_path = os.path.join(APP_ROOT_DIR, '0_mejoras.md')
    high_priority_tasks = []
    try:
        with open(mejoras_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if "Alta 🚨" in line and "[ ] Pendiente" in line:
                    high_priority_tasks.append(line.strip())

        if not high_priority_tasks:
            return "No high-priority pending tasks found."

        # Check for the specific "colores del brandkit" task
        for task in high_priority_tasks:
            if "colores del brandkit" in task:
                return f"Prioridad Alta: {task.split('[ ] Pendiente', 1)[1].strip()}"

        # If the specific task is not found, return the first high-priority task
        return f"Prioridad Alta: {high_priority_tasks[0].split('[ ] Pendiente', 1)[1].strip()}"

    except FileNotFoundError:
        return f"Error: 0_mejoras.md not found at {mejoras_file_path}."
# --- Helper functions for state management ---
def get_scraping_state():
    """Returns a dict with keys related to scraping progress and state."""
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


# Apply custom CSS
st.markdown(custom_css, unsafe_allow_html=True)

st.set_page_config(page_title="Agente GOSOM ETL", layout="wide", initial_sidebar_state="expanded")

# --- Stage Management ---
stage_options = { 
    1: "Etapa 1: Configuración y Scraping",
    2: "Etapa 2: Revisión de Resultados",
    3: "Etapa 3: Procesamiento y Gestión de Leads"
}

# Navegación en la barra lateral 
st.sidebar.header("🗺️ Navegación")
selected_stage_sidebar = st.sidebar.radio("Seleccionar Etapa", options=list(stage_options.keys()), format_func=lambda x: stage_options[x])

# Update stage based on sidebar selection
if selected_stage_sidebar != st.session_state.stage:
    st.session_state.stage = selected_stage_sidebar
    # Optionally clear some session state data when changing stages, if needed
    # Example: if moving away from Stage 2/3, clear final_df_consolidated if not consolidated yet
    # if selected_stage_sidebar not in [2, 3] and not st.session_state.scraping_in_progress and not st.session_state.final_df_consolidated.empty:
    # st.warning("Datos de la última ejecución de scraping serán eliminados al cambiar de etapa si no han sido consolidados.")
        # st.session_state.final_df_consolidated = pd.DataFrame(columns=gmaps_column_names_list_app) # Decided not to clear automatically for now

# --- Main Content Area (Changes based on stage) ---
if st.session_state.stage == 1: # Configuración y Scraping
    st.header("⚙️ Configuración y Scraping") # Mantener header principal en español
    st.write("Define los parámetros para iniciar el proceso de extracción de leads.")
    
    # Use helper for scraping state
 scraping_state = get_scraping_state() # New subheader for clarity

 # Add introductory text when not scraping, positioned before scraping progress indicators
 if not scraping_state['scraping_in_progress']:
        st.subheader("Bienvenido a la Etapa de Configuración y Scraping")
        st.markdown("""
 Aquí puedes configurar los parámetros necesarios para iniciar la extracción de datos de Google Maps.
 
 **Sigue estos pasos para configurar y comenzar el scraping:**
 
 1.  **Selecciona las ciudades y define las palabras clave** en la sección "📍 Selección de Ubicación y Palabras Clave" en la **barra lateral izquierda**.
 2.  **Ajusta los parámetros avanzados** como la profundidad de búsqueda y la extracción de emails si es necesario, en la sección "⚙️ Parámetros Avanzados" de la barra lateral.
 3.  Una vez configurado, haz clic en el botón **'🚀 Iniciar Scraping'** en la sección "🚀 Controles de Ejecución" de la barra lateral para comenzar el proceso.
 
 Mientras el scraping esté en curso, verás el estado actual y los logs en tiempo real aquí en la Etapa 1.
 """)

    # Show prominent scraping progress indicators if in progress
    if scraping_state['scraping_in_progress']:
 st.subheader("Estado Actual del Scraping:") # Subtítulo para claridad
 if scraping_state['start_time']: # Use st.columns for the counters
            elapsed_time = datetime.now() - scraping_state['start_time']
            # Formatear tiempo transcurrido
 total_seconds = int(elapsed_time.total_seconds())
 hours = total_seconds // 3600
 minutes = (total_seconds % 3600) // 60
 seconds = total_seconds % 60
 time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            # Obtener la lista de ciudades seleccionadas para el progreso
 selected_cities = st.session_state.get('last_selected_cities', [])
 total_cities = len(selected_cities)

            # Contar cuántas ciudades ya tienen resultados parciales en live_csv_row_counts
 cities_with_progress = len(scraping_state['live_csv_row_counts'])

            # Use st.columns for the counters
            col1_count, col2_count, col3_count = st.columns(3) # Added metrics
 col1_count.metric("Estado General", scraping_state['current_process_status']) # Mensaje de estado más detallado
 col2_count.metric("Tiempo Transcurrido", time_str)
 col3_count.metric("Progreso Ciudades", f"{cities_with_progress}/{total_cities}") # Mostrar progreso de ciudades
        else:
            # Fallback display if start_time is unexpectedly None
            st.info(scraping_state['current_process_status'])

 # Mensajes informativos basados en el README.md
 st.warning("Nota: El scraper de Google Maps puede tardar al menos 3 minutos en mostrar los primeros resultados, incluso para pocas palabras clave.")
 st.warning("Nota sobre Detener: El proceso de Docker subyacente podría no detenerse instantáneamente al presionar 'Detener'. Puede tomar un tiempo en completarse la tarea actual o alcanzar un timeout.")

 st.info("Consulta los 'Logs en Vivo' en la barra lateral para detalles.") # Mantener mensaje existente


 # UI elements that are not moved to sidebar will remain here

if config_params_app == FALLBACK_CONFIG_APP: # Check if fallback config was used
    st.error(f"¡ADVERTENCIA! No se pudo cargar el archivo de configuración ({os.path.basename(CONFIG_FILE_PATH_APP)}). Usando configuración por defecto.")


# --- Sidebar ---
# Place the logo and a persistent title at the very top of the sidebar
with st.sidebar: 
    st.image(os.path.join(APP_ROOT_DIR, "logo.png"), width=100) # Use absolute path
    st.header("Agente GOSOM ETL") # Persistent title
    st.markdown("---") # Separator after title/logo

    # Navigation is already in the sidebar
    st.sidebar.header("🗺️ Navegación") # Navigation header
    selected_stage_sidebar = st.sidebar.radio("Seleccionar Etapa", options=list(stage_options.keys()), format_func=lambda x: stage_options[x], key="radio_stage_sidebar")
    st.markdown("---") # Separator after navigation

    # Usar helper para obtener estado de scraping
    scraping_state = get_scraping_state()
    # Expanders para organizar la configuración
    with st.expander("📍 Selección de Ubicación y Palabras Clave", expanded=True): 
        gmaps_coords_opts = list(config_params_app.get('gmaps_coordinates', {}).keys())
        selected_cities_keys_ui = st.multiselect(
            '🏙️ Seleccionar Ciudades', options=gmaps_coords_opts, 
 default=st.session_state.last_selected_cities, # type: ignore
 help="Selecciona una o más ciudades de la lista preconfigurada.",
 # Use a distinct key for the sidebar multiselect to avoid conflict with potential main area multiselect
 disabled=scraping_state['scraping_in_progress'], key="ms_cities_sidebar"
        ) 
        # Actualizar last_selected_cities si cambia
        if selected_cities_keys_ui != st.session_state.last_selected_cities:
 # Clear keywords for cities that are no longer selected
 for city_key in list(st.session_state.selected_cities_keywords_ui.keys()): # type: ignore
 if city_key not in selected_cities_keys_ui:
 del st.session_state.selected_cities_keywords_ui[city_key] # type: ignore
            st.session_state.last_selected_cities = selected_cities_keys_ui
            # Rerun to update the UI for keyword fields
            st.rerun()
        
        if selected_cities_keys_ui:
            st.subheader("✏️ Keywords por Ciudad")
 st.info("Introduce una keyword por línea en el campo de texto de cada ciudad seleccionada.")
            for city_k_ui in selected_cities_keys_ui:
                if city_k_ui not in st.session_state.selected_cities_keywords_ui: # type: ignore
                    kws = load_keywords_from_csv_func_app(CONFIG_DIR_APP, city_k_ui, ui_logger)
                    st.session_state.selected_cities_keywords_ui[city_k_ui] = "\n".join(kws)
                st.session_state.selected_cities_keywords_ui[city_k_ui] = st.text_area(
                    f'Keywords para {city_k_ui.capitalize()}',
                    st.session_state.selected_cities_keywords_ui.get(city_k_ui, ""), # type: ignore
 key=f'kw_ta_sidebar_{city_k_ui}', height=100, disabled=scraping_state['scraping_in_progress'],
 help=f"Lista de palabras clave para buscar en {city_k_ui.capitalize()}. Una por línea." # Added help text

    with st.expander("⚙️ Parámetros Avanzados", expanded=False): # Expandir en español
        depth_ui_val = st.number_input( 
            '🎯 Profundidad de Búsqueda', min_value=1, max_value=20, # Translated label
            value=int(st.session_state.last_search_depth),
            disabled=scraping_state['scraping_in_progress'], key="ni_depth_sidebar", # type: ignore
 help="Profundidad de búsqueda GOSOM. A mayor profundidad, más tiempo tarda."
        )
        st.session_state.last_search_depth = depth_ui_val
 
        emails_ui_val = st.checkbox(
            '📧 Extraer Correos Electrónicos', # Translated label
            value=st.session_state.last_extract_emails, # type: ignore
            disabled=scraping_state['scraping_in_progress'], key="cb_emails_sidebar",
 help="Marcar para intentar extraer emails (puede aumentar significativamente el tiempo)." # type: ignore
        )
        st.session_state.last_extract_emails = emails_ui_val
 # Translated subheader for controls
    st.markdown("---")
    st.subheader("🚀 Controles de Ejecución") # Translated subheader for controls
    col_btn_start_s, col_btn_stop_s = st.columns(2)
    
    # Check if all selected cities have non-empty keywords
    all_keywords_present = True
    if selected_cities_keys_ui:
        for city in selected_cities_keys_ui:
            if not st.session_state.selected_cities_keywords_ui.get(city, "").strip(): # type: ignore
                all_keywords_present = False
                break

    with col_btn_start_s:
 if st.button('🚀 Iniciar Scraping', key="btn_start_s_sidebar",
                     disabled=scraping_state['scraping_in_progress'] or not CORE_LOGIC_LOADED or not selected_cities_keys_ui or not all_keywords_present,
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
                st.session_state.processed_city_data_results = {} # Clear previous results
                st.session_state.final_df_consolidated = pd.DataFrame(columns=gmaps_column_names_list_app) # type: ignore
                keywords_for_thread_dict = st.session_state.selected_cities_keywords_ui.copy()
                ui_logger.info(f"Btn 'Iniciar'. Ciudades: {selected_cities_keys_ui}, Prof: {depth_ui_val}, Emails: {emails_ui_val}")
 # Start the scraping thread
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

 # --- Job Logging Logic ---
    # This block runs when the scraping thread is NOT in progress, but the UI state was just updated to done.
    # We check the queue processing block below to see if the thread completion signal was received.
    # The logging logic needs to happen AFTER the queue processing finishes and the state is updated.
    # The ideal place is right after the `while not st.session_state.log_messages_queue.empty():` loop
    # and after `scraping_in_progress` is set to False. This is handled below in the log processing block.

    st.markdown("---") # Separator before Job History
    st.subheader("📝 Historial de Jobs de Scraping") # Translated subheader

    # Function to log job details
    def log_scraping_job(cities, keywords_dict, depth, emails_extracted, row_count, error_status):
        """Logs the details of a scraping job to scrape_jobs.csv."""
        job_log_path = MOTHER_CSV_PATH_APP # Use the predefined path for job logs
        header = ['id', 'fecha', 'hora', 'ciudades', 'keywords', 'depth', 'emails_extracted', 'filas_extraidas', 'error']

        try:
            # Check if the file exists and is not empty to determine the next ID
            if os.path.exists(job_log_path) and os.stat(job_log_path).st_size > 0:
                df_jobs = pd.read_csv(job_log_path)
                next_id = len(df_jobs) + 1
                write_header = False # Don't write header if file exists and is not empty
            else:
                next_id = 1
                write_header = True # Write header if file is new or empty

            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            cities_str = ", ".join(cities)
            # Represent keywords dictionary as a string (e.g., JSON string or a simple list of all keywords)
            # For simplicity and readability, let's flatten the keywords into a single string
            all_keywords = []
            for city_k, kws in keywords_dict.items():
                all_keywords.extend([f"{city_k}:{kw.strip()}" for kw in kws.splitlines() if kw.strip()])
            keywords_str = "; ".join(all_keywords)

            # Prepare the data row
            job_data = {
                'id': next_id, 'fecha': date_str, 'hora': time_str, 'ciudades': cities_str,
                'keywords': keywords_str, 'depth': depth, 'emails_extracted': emails_extracted,
                'filas_extraidas': row_count, 'error': error_status
            }

            # Append to CSV
            df_new_job = pd.DataFrame([job_data])
            df_new_job.to_csv(job_log_path, mode='a', index=False, header=write_header)
            ui_logger.success(f"Job de scraping (ID: {next_id}) logged successfully.")

        except Exception as e:
            ui_logger.error(f"Error logging scraping job: {e}", exc_info=True)

    # Display job history
    try:
        # Use the correct path for the job logs
        if os.path.exists(MOTHER_CSV_PATH_APP) and os.stat(MOTHER_CSV_PATH_APP).st_size > 0:
            df_job_history = pd.read_csv(MOTHER_CSV_PATH_APP)
            st.write(f"Jobs previos encontrados: {len(df_job_history)}")
            st.dataframe(df_job_history)
        else:
            st.info("No se encontraron registros de jobs de scraping previos.")

    except FileNotFoundError:
        st.warning("Archivo de historial de jobs no encontrado.")
    except Exception as e:
        st.error(f"Error al cargar el historial de jobs: {e}")

    st.markdown("---") # Separator before version/status
    st.caption(f"Agente GOSOM ETL - MVP v0.7 | Lógica Principal: {'Cargada OK' if CORE_LOGIC_LOADED else 'FALLÓ / DUMMY'}")

if not CORE_LOGIC_LOADED and st.session_state.stage == 1: # Use the variable loaded from import, only show warning in Stage 1
 st.error("¡ADVERTENCIA CRÍTICA! El módulo 'core_logic.py' no pudo cargar correctamente. Usando funcionalidades limitadas (dummies). No se podrá realizar scraping real.") # Use helper function consistently

# --- Scraping Progress Section (Visible in Stage 1 and potentially Stage 2 if it finishes there) ---
if get_scraping_state()['scraping_in_progress']: # Use helper function consistently
 # Ensure this section is only visible in Stage 1 when scraping is active
 if st.session_state.stage != 1:
 st.session_state.stage = 1 # Force stage back to 1 if scraping starts from other stage somehow
    if scraping_state['start_time']:
    st.subheader("Logs en Vivo (Salida de GOSOM y Agente)") # Subheader en español
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
                elif isinstance(msg_item_ui, str) and (msg_item_ui.startswith(f"{LogMessageType.PROCESO_START}:") or msg_item_ui.startswith(f"{LogMessageType.STATUS_UPDATE}:")):
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

 log_display_placeholder_live.code(st.session_state.current_log_display, language='log', height=400) # Use helper to establish final state

    current_thread_ui_check_live = st.session_state.get('scraping_thread')
    # Rerun solo si el thread terminó o si hay una señal crítica
    if thread_completed_signal_received_ui or critical_error_payload_ui or not (current_thread_ui_check_live and current_thread_ui_check_live.is_alive()):
        # Usar helper para establecer el estado final
        # --- Job Logging Trigger ---
        # This is the ideal place to log the job. The thread has finished,
        # final results (or error) are available in the session state
        # (or indicated by critical_error_payload_ui), and the state is transitioning.

        final_row_count = len(st.session_state.get('final_df_consolidated', pd.DataFrame()))
        error_status = "OK"
        if critical_error_payload_ui:
            error_status = f"Error: {critical_error_payload_ui.get('message', 'Unknown Error')}"
        elif st.session_state.get('stop_scraping_flag', False):
             error_status = "Stopped by User"

 set_scraping_state(
 scraping_in_progress=False,
 scraping_done=True,
 start_time=None # Resetear tiempo
 )
        log_scraping_job(st.session_state.last_selected_cities, st.session_state.selected_cities_keywords_ui, st.session_state.last_search_depth, st.session_state.last_extract_emails, final_row_count, error_status)
 if final_results_payload_ui:
            st.session_state.final_df_consolidated = final_results_payload_ui['data']
            st.session_state.processed_city_data_results = final_results_payload_ui['processed_city_data']
            # cumulative_row_count ya se actualizó via message type ROW_COUNT_UPDATE si aplica, o lo manejamos al final
            # set_scraping_state(cumulative_row_count=final_results_payload_ui.get('final_cumulative_count', st.session_state.cumulative_row_count)) # Este tipo de mensaje no se envía realmente

        if critical_error_payload_ui:
            set_scraping_state(current_process_status=f"ERROR CRÍTICO: {critical_error_payload_ui.get('message', 'Detalles en logs')}") # Usar helper

        ui_logger.info("Thread finalizado. UI a estado 'done'.") # Log message in Spanish
        # Rerun para mostrar el estado final y los resultados
        st.rerun()
    # Eliminar el `elif` con `time.sleep` para reducir reruns innecesarios


elif st.session_state.stage == 2: # Review Results Stage
 elif st.session_state.stage == 2: # Revisión de Resultados
    st.header("📊 Revisar Resultados")
    st.write("Aquí puedes revisar los datos obtenidos en la última ejecución de scraping y visualizar su distribución geográfica.")

    # Add a subheader for the statistics section
    st.subheader("Estadísticas de Scraping")

    # Display the total number of rows scraped
    total_rows_scraped = len(st.session_state.get('final_df_consolidated', pd.DataFrame()))

 if total_rows_scraped > 0:
 st.info(f"Total de prospectos encontrados en la última ejecución: {total_rows_scraped}")

            # Calculate and display stats for email and phone
            final_df = st.session_state.get('final_df_consolidated', pd.DataFrame())
            num_with_email = 0
            if 'emails' in final_df.columns:
 # Calculate and display number of leads with emails
 num_with_email = 0
 if 'emails' in final_df.columns:
                num_with_email = final_df['emails'].dropna().astype(str).str.strip().astype(bool).sum()
 st.info(f"Prospectos con Email: {num_with_email}") # Translated label

 # Calculate and display number of leads with phone numbers
            num_with_phone = 0
            if 'phone' in final_df.columns:
                num_with_phone = final_df['phone'].dropna().astype(str).str.strip().astype(bool).sum()
            st.info(f"Prospectos con Email: {num_with_email}") # Translated label
            if 'phone' in final_df.columns:
 st.info(f"Prospectos con Teléfono: {num_with_phone}") # Translated label 

            # Display leads by city/category
 st.subheader("Resultados por Ciudad/Categoría:")
            for city, data in st.session_state.get('processed_city_data_results', {}).items(): # Use .get()
                df = data.get('df')
                if df is not None and not df.empty:
                    st.write(f"- **{city.capitalize()}:** {len(df)} prospectos")
                elif df is not None:
 # Use st.info for 0 results per city for clarity # Translated message
                     st.info(f"- **{city.capitalize()}:** 0 prospectos")
                else:
                    st.write(f"- **{city.capitalize()}:** Error al procesar")
    else:
        st.info("No hay datos de la última ejecución de scraping para mostrar estadísticas.")

    # Add a subheader for the map visualization
        st.subheader("Visualización en Mapa") # Translated subheader
 
        # Ensure DataFrame exists, is not empty, and has 'lat' and 'lon' columns before displaying map
 df_for_map = st.session_state.get('final_df_consolidated') # Ensure DataFrame exists, is not empty, and has 'lat' and 'lon' columns before displaying map
 # Placeholder for existing map visualization code
 # Ensure your existing map code is here, including checks for
 # DataFrame existence, non-emptiness, and 'lat'/'lon' columns.
 # Example of existing map code structure:
 # df_for_map = st.session_state.get('final_df_consolidated')
 # if df_for_map is not None and not df_for_map.empty and 'lat' in df_for_map.columns and 'lon' in df_for_map.columns:
 # st.map(df_for_map.dropna(subset=['lat', 'lon']))
 # else:
 # st.info("No hay datos válidos de latitud/longitud para mostrar en el mapa.")

 # Your existing map code will go here.
 # I will assume your existing code for displaying the map (with the checks)
 # is already in the correct location within this 'elif' block for stage 2.
 # I will add a placeholder comment for clarity.

 # Placeholder for existing map visualization code
 # Ensure your existing map code is here, including checks for
 # DataFrame existence, non-emptiness, and 'lat'/'lon' columns.
 # Example of existing map code structure:
 # df_for_map = st.session_state.get('final_df_consolidated')

        # Check if map data is available and valid
        map_data_available = False
        if df_for_map is not None and not df_for_map.empty:
            # Ensure 'lat' and 'lon' columns exist
            if 'lat' in df_for_map.columns and 'lon' in df_for_map.columns:
                # Check if 'lat' and 'lon' columns contain numeric data and are not null
                df_for_map_cleaned = df_for_map.dropna(subset=['lat', 'lon']).copy()
                df_for_map_cleaned['lat'] = pd.to_numeric(df_for_map_cleaned['lat'], errors='coerce')
                df_for_map_cleaned['lon'] = pd.to_numeric(df_for_map_cleaned['lon'], errors='coerce')
                
                if not df_for_map_cleaned.empty:
 # Calculate center coordinates # Translated message
                    center_lat = df_for_map_cleaned['lat'].mean()
                    center_lon = df_for_map_cleaned['lon'].mean()
 map_data_available = True

        # Display the map if valid data is available
        if map_data_available:
            try:
                # Check if lat and lon are numeric and not null
                # df_for_map_cleaned is already cleaned and checked above
 if not df_for_map_cleaned.empty and 'center_lat' in locals() and 'center_lon' in locals():
                    st.map(df_for_map_cleaned)
                else:
 st.info("No hay datos válidos de latitud/longitud para mostrar en el mapa.") # Translated message
            except Exception as e: # Catching general exception for robustness
                st.error(f"Error al mostrar el mapa: {e}")
        else: # Display translated message if map data is missing
 st.info("No hay datos válidos de latitud/longitud para mostrar en el mapa.") # Translated message

 # Add section for displaying complete data
 if not final_df.empty: # Only display if DataFrame is not empty
 st.subheader("Datos Completos") 
 st.dataframe(final_df)
 else:
 st.info("No hay datos disponibles para mostrar.") # Translated message

 # Button to proceed to Stage 3 - Keep this at the end of Stage 2
 if st.button("➡️ Procesar y Consolidar con CSV Madre", key="btn_goto_stage3"): # Translated button label
 st.session_state.stage = 3
 st.experimental_rerun()
 elif total_rows_scraped == 0: # Translated message
 st.warning("La última ejecución de scraping no encontró ningún prospecto.")

    elif st.session_state.scraping_in_progress: 
        st.info("Scraping en progreso. Espera a que termine para ver los resultados aquí.")

    elif not st.session_state.scraping_in_progress and not st.session_state.scraping_done:
 st.info("Ejecuta un scraping (Etapa 1) para ver los resultados y estadísticas aquí.")

elif st.session_state.stage == 3: # Consolidate and Chunk Stage

    # --- Placeholder for Merge Logic ---
 st.header("💾 Consolidar y Preparar para Vendedores") # Translated header # Add introductory text for Stage 3
 # Add introductory text for Stage 3
 st.markdown("""
En esta etapa, puedes gestionar los datos de los prospectos extraídos:

1.  **Consolidar Datos:** Integra los resultados de la última ejecución de scraping con el CSV Madre consolidado.
2.  **Visualizar CSV Madre:** Revisa todos los prospectos consolidados hasta la fecha.
3.  **Generar Chunks:** Crea archivos CSV más pequeños ("chunks") con leads pendientes de asignación para distribuir a los vendedores.
""")

 st.write("Aquí puedes consolidar los datos extraídos con el CSV madre y generar bloques (chunks) para los vendedores.")

    # --- Mother CSV Visualizer ---
    # The header was already translated to "Visualizador de CSV Madre Consolidado" in a previous step
    # Let's ensure it is correctly set here and not duplicated

 st.subheader(f"Visualizador de CSV Madre ({os.path.basename(CONSOLIDATED_MOTHER_CSV_PATH_APP)})") # Define required columns for mother CSV

    # --- Validation: Before Loading Mother CSV ---
    mother_csv_display_key = "mother_csv_dataframe_display"
    required_mother_cols = ['link', 'title', 'search_origin_city', 'fecha_asignacion', 'id_chunk'] # Define required columns for mother CSV

    df_mother_display = pd.DataFrame() # Initialize as empty

    if os.path.exists(CONSOLIDATED_MOTHER_CSV_PATH_APP) and os.stat(CONSOLIDATED_MOTHER_CSV_PATH_APP).st_size > 0:
        # Perform integrity validation before loading
        if CORE_LOGIC_LOADED and hasattr(core_logic, 'validate_csv_integrity_core'):
 validation_result, validation_message = validate_csv_integrity_core(CONSOLIDATED_MOTHER_CSV_PATH_APP, required_mother_cols, ui_logger)
 if validation_result:
                ui_logger.success("Integridad del CSV Madre OK.")
                # If valid, load the CSV
 try: # Mensaje en español
                    df_mother_display = pd.read_csv(CONSOLIDATED_MOTHER_CSV_PATH_APP, low_memory=False)
                    st.info(f"CSV Madre cargado: {len(df_mother_display)} filas.") # Mensaje en español
                except Exception as e_load_mother:
                    st.error(f"Error al cargar el CSV Madre a pesar de validación inicial: {e_load_mother}")
 elif not validation_result:
                st.error(f"Falló la validación de integridad del CSV Madre ({os.path.basename(CONSOLIDATED_MOTHER_CSV_PATH_APP)}). Por favor, revisa el archivo. Inicializando vacío.")
        else:
    # Load and display Mother CSV
 if os.path.exists(CONSOLIDATED_MOTHER_CSV_PATH_APP) and os.stat(CONSOLIDATED_MOTHER_CSV_PATH_APP).st_size > 0: # Mensaje en español
            df_mother_display = pd.read_csv(CONSOLIDATED_MOTHER_CSV_PATH_APP) 
            st.info(f"CSV Madre cargado: {len(df_mother_display)} filas.") # Mensaje en español

            # Option to order by city
            if 'city' in df_mother_display.columns:
                if st.checkbox("Ordenar por Ciudad", key=f"checkbox_order_mother_csv_city_{mother_csv_display_key}"):
                    df_mother_display = df_mother_display.sort_values(by='city').reset_index(drop=True)

            st.dataframe(df_mother_display)
        else:
 st.info("CSV Madre no encontrado o vacío. Extrae datos primero para crear uno.") # Mensaje en español # Ensure df_mother_display is defined
            df_mother_display = pd.DataFrame() # Ensure df_mother_display is defined
    else:
 st.info("CSV Madre no encontrado o vacío. Extrae datos primero para crear uno.") # Mensaje en español # Ensure df_mother_display is defined
        df_mother_display = pd.DataFrame() # Ensure df_mother_display is defined

    # --- Display Unassigned Leads (Translated header and text) ---
    st.subheader("Leads Pendientes de Asignación") 
    if not df_mother_display.empty and 'estado_asignacion' in df_mother_display.columns:
        df_unassigned = df_mother_display[df_mother_display['estado_asignacion'] == 'Pendiente'].copy() # Use .copy() to avoid SettingWithCopyWarning
        
 if not df_unassigned.empty: # Translated text
            st.info(f"Se encontraron {len(df_unassigned)} leads pendientes de asignación.") # Translated text
            st.dataframe(df_unassigned)
        else:
 st.info("No hay leads pendientes de asignación en el CSV Madre.") # Mensaje en español
    elif not df_mother_display.empty and 'estado_asignacion' not in df_mother_display.columns:
 st.warning("La columna 'estado_asignacion' no se encuentra en el CSV Madre. No se pueden mostrar leads pendientes.") # Mensaje en español
    else:
        st.info("Carga o consolida datos primero para ver leads pendientes de asignación.")

    # --- Consolidation Logic Trigger --- 
    st.subheader("Consolidar Datos Raspados Recientes") # Translated header
    st.markdown(f"""
        Integra los resultados de la última ejecución de scraping con el **CSV Madre** (`{os.path.join(DATA_DIR_APP, 'consolidated', 'consolidated_leads.csv')}`).
        Este proceso **deduplicará** automáticamente los leads basándose en el link y el título para evitar duplicados en el CSV Madre.
        Solo se añadirán los leads nuevos y únicos.
    """)

    total_scraped_in_stage2 = len(st.session_state.get('final_df_consolidated', pd.DataFrame()))
    
    if total_scraped_in_stage2 > 0: # Translated messages
 st.info(f"Hay {total_scraped_in_stage2} prospectos nuevos de la última ejecución de scraping listos para consolidar.") # Add a warning if the mother CSV doesn't seem to exist before consolidating
 # Add a warning if the mother CSV doesn't seem to exist before consolidating
 if not os.path.exists(CONSOLIDATED_MOTHER_CSV_PATH_APP):
                st.warning("El CSV Madre consolidado parece no existir. Se creará uno nuevo al consolidar.")
 # Pass the path to the consolidated mother CSV for consolidation
 elif os.stat(CONSOLIDATED_MOTHER_CSV_PATH_APP).st_size == 0:
                st.warning("El CSV Madre consolidado existe pero está vacío. Se creará uno nuevo al consolidar.")

        if st.button("Consolidar con CSV Madre", key="btn_consolidate_mother_csv"):
 # Pass the path to the consolidated mother CSV for consolidation
 # Call the modified function without the path argument
 consolidate_success = consolidate_scraped_data(st.session_state.final_df_consolidated, ui_logger)


            # Clear the consolidated data from session state after merging
 st.session_state.final_df_consolidated = pd.DataFrame(columns=gmaps_column_names_list_app)
            st.success("Consolidación completada. El CSV Madre ha sido actualizado.")
            st.experimental_rerun() # Rerun to reload and display the updated mother CSV
    else:
        st.info("No hay nuevos datos de scraping para consolidar. Ejecuta un scraping (Etapa 1).")

    # --- Chunking Section ---
    # Ensure df_mother_display is available for chunking logic
    if 'df_mother_display' not in locals():
        df_mother_display = pd.DataFrame() # Re-initialize if not set above

 st.subheader("Generar Chunks para Asignación") # Translated header # Get list of cities with unassigned leads from mother CSV for the selectbox

        # Get list of cities with unassigned leads from mother CSV for the selectbox
        try:
            if 'fecha_asignacion' in df_mother_display.columns and 'city' in df_mother_display.columns:
                cities_with_unassigned = df_mother_display[df_mother_display['fecha_asignacion'].isna()]['city'].unique().tolist()
 else:
                cities_with_unassigned = []
 st.warning("El CSV Madre no tiene las columnas 'fecha_asignacion' o 'city'. No se pueden generar chunks.") # Mensaje en español
        except Exception as e:
            cities_with_unassigned = []
            st.error(f"Error al leer CSV Madre para ciudades: {e}")

 # Disable chunk generation if no mother CSV or no unassigned leads
 if df_mother_display.empty:
            st.info("Carga o consolida datos primero para poder generar chunks.")
            can_generate_chunks = False
 else: can_generate_chunks = bool(cities_with_unassigned) # True if list is not empty # Pass logger instance

        selected_city_for_chunking = st.selectbox("Selecciona una Ciudad para Generar Chunks", options=cities_with_unassigned) 

        if st.button("Cortar Chunks de 30 Leads", key="btn_generate_chunks_ui", disabled=not selected_city_for_chunking or df_mother_display.empty or cities_with_unassigned == []): 
            st.write(f"Este botón generará archivos CSV en el directorio `{os.path.basename(CHUNKS_DATA_DIR_APP)}` con 30 leads cada uno para la ciudad seleccionada ({selected_city_for_chunking}). Los leads asignados se marcarán en el CSV Madre.")

            if selected_city_for_chunking:
 generated_files_dict = generate_lead_chunks(CONSOLIDATED_MOTHER_CSV_PATH_APP, CHUNKS_DATA_DIR_APP, chunk_size=30, logger_instance=ui_logger) # Pass logger instance


                if generated_files_dict:
                    st.success(f"Chunks generados para {selected_city_for_chunking.capitalize()}:")
                    for city, files in generated_files_dict.items():
                         st.info(f"{city}: {', '.join(files)}")
                else:
                    st.info(f"No se generaron chunks para {selected_city_for_chunking.capitalize()}. Posiblemente no hay leads sin asignar.")
 


                # After generating chunks, explicitly reload the mother CSV display data
                try:
 if os.path.exists(CONSOLIDATED_MOTHER_CSV_PATH_APP) and os.stat(CONSOLIDATED_MOTHER_CSV_PATH_APP).st_size > 0:
                        df_mother_display = pd.read_csv(CONSOLIDATED_MOTHER_CSV_PATH_APP)
 # The next rerun will pick up this updated df_mother_display
 except Exception as e:
                    st.error(f"Error al recargar el CSV Madre después de generar chunks: {e}")

                st.experimental_rerun() # Rerun to reload and display the updated mother CSV after chunking

st.sidebar.markdown("---")
st.sidebar.caption(f"Agente GOSOM ETL - MVP v0.7 | Lógica Principal: {'Cargada OK' if CORE_LOGIC_LOADED else 'FALLÓ / DUMMY'}")