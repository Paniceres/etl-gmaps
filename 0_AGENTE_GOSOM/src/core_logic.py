# 0_AGENTE_GOSOM/src/core_logic.py

import logging
import os
import subprocess
import pandas as pd
import json
from datetime import datetime
import uuid
import time # Para el bucle de Popen y conteo de CSV
import streamlit as st # Para st.session_state.get('stop_scraping_flag')

# --- Constantes para tipos de mensajes de cola ---
class LogMessageType:
    """Define tipos de mensajes para la cola de comunicación entre thread y UI."""
    FINAL_RESULTS = "FINAL_RESULTS"
    CRITICAL_ERROR = "CRITICAL_ERROR"
    LIVE_ROW_COUNT = "LIVE_ROW_COUNT" # Conteo de filas actualizado mientras se escribe el CSV
    ROW_COUNT_UPDATE = "ROW_COUNT_UPDATE" # Acumulado total de filas procesadas por ciudad
    THREAD_COMPLETE_SIGNAL = "THREAD_COMPLETE_SIGNAL" # Señal de fin de thread
    PROCESO_START = "PROCESO_START" # Señal de inicio de procesamiento de ciudad
    STATUS_UPDATE = "STATUS_UPDATE" # Actualización de estado general del proceso
    GOSOM_LOG = "GOSOM_LOG" # Líneas de log directo de la salida de GOSOM
    CMD_DOCKER = "CMD_DOCKER" # Comando Docker ejecutado
    SUCCESS = "SUCCESS" # Mensaje de éxito de una operación
    INFO = "INFO" # Mensaje informativo
    ERROR = "ERROR" # Mensaje de error
    WARNING = "WARNING" # Mensaje de advertencia

# --- Definición de gmaps_column_names ---
gmaps_column_names = [
    'input_id', 'link', 'title', 'category', 'address', 'open_hours', 'popular_times',
    'website', 'phone', 'plus_code', 'review_count', 'review_rating', 'reviews_per_rating',
    'latitude', 'longitude', 'cid', 'status', 'descriptions', 'reviews_link', 'thumbnail',
    'timezone', 'price_range', 'data_id', 'images', 'reservations', 'order_online',
    'menu', 'owner', 'complete_address', 'about', 'user_reviews', 
    'emails' 
]

# --- Clase StyledLogger ---
class StyledLogger:
    def __init__(self, logger_name='CoreLogic', log_file_path='core_logic_agent.log', level=logging.INFO):
        self.logger = logging.getLogger(logger_name)
        
        if not self.logger.handlers: 
            self.logger.setLevel(level)
            self.logger.propagate = False 
            formatter = logging.Formatter('%(asctime)s-%(levelname)s [%(name)s:%(funcName)s:%(lineno)d] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            try:
                if not isinstance(log_file_path, (str, bytes, os.PathLike)):
                    print(f"ERROR (StyledLogger Init): log_file_path no es string: {log_file_path}. Usando fallback.")
                    log_file_path = f"{logger_name}_fallback.log"
                log_dir = os.path.dirname(log_file_path)
                if log_dir and not os.path.exists(log_dir): 
                    os.makedirs(log_dir, exist_ok=True)
                fh = logging.FileHandler(log_file_path, encoding='utf-8')
                fh.setFormatter(formatter)
                self.logger.addHandler(fh)
            except Exception as e:
                print(f"ERROR CRITICO (StyledLogger Init): No se pudo crear FileHandler para '{log_file_path}'. Error: {e}")
        
        self.HEADER_ART_TEXT = """
        ********************************************************************************
        *                     G M A P S   S C R A P E R   A G E N T                    *
        *                          (Core Logic Operations)                           *
        ********************************************************************************
        """
        self.SECTION_SEPARATOR = "=" * 70
        self.SUB_SECTION_SEPARATOR = "-" * 50
        self.SUCCESS_ART = "[OK]"
        self.ERROR_ART = "[FAIL]"
        self.WARNING_ART = "[WARN]"
        self.INFO_ART = "[INFO]"
        self.DEBUG_ART = "[DEBUG]"

    def _log(self, level, message, art=""): self.logger.log(level, f"{art} {message}".strip())
    def get_header_art_text(self): return self.HEADER_ART_TEXT
    def print_header_art_to_console(self): print(self.HEADER_ART_TEXT); self.info("Logger Core Logic (consola).")
    def section(self, title): self._log(logging.INFO, f"\n{self.SECTION_SEPARATOR}\n{str(title).upper()}\n{self.SECTION_SEPARATOR}", art="")
    def subsection(self, title): self._log(logging.INFO, f"\n{self.SUB_SECTION_SEPARATOR}\n{str(title)}\n{self.SUB_SECTION_SEPARATOR}", art="")
    def info(self, message): self._log(logging.INFO, message, self.INFO_ART)
    def success(self, message): self._log(logging.INFO, message, self.SUCCESS_ART)
    def warning(self, message): self._log(logging.WARNING, message, self.WARNING_ART)
    def error(self, message, exc_info=False):
        self._log(logging.ERROR, message, self.ERROR_ART)
        if exc_info: self.logger.exception("Detalles:")
    def critical(self, message, exc_info=False):
        self._log(logging.CRITICAL, message, f"{self.ERROR_ART} [CRITICAL]")
        if exc_info: self.logger.exception("Detalles Críticos:")
    def debug(self, message): self._log(logging.DEBUG, message, self.DEBUG_ART)

# --- Funciones Core ---
def load_keywords_from_csv_core(config_dir_path, city_key, logger_instance):
    # ... (Tu código de load_keywords_from_csv_core como lo tenías)
    logger_instance.debug(f"Intentando cargar kw para '{city_key}' desde dir '{config_dir_path}'")
    filepath = os.path.join(config_dir_path, f'keywords_{city_key.lower()}.csv')
    keywords = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip()]
        if keywords: logger_instance.success(f"Cargadas {len(keywords)} kw para '{city_key}' desde '{filepath}'")
        else: logger_instance.warning(f"Archivo kw para '{city_key}' vacío: '{filepath}'")
    except FileNotFoundError: logger_instance.error(f"Archivo kw NO encontrado para '{city_key}': '{filepath}'")
    except Exception as e: logger_instance.error(f"Error cargando kw para '{city_key}': {e}", exc_info=True)
    return keywords

def run_gmaps_scraper_docker_core(
    *, keywords_list, city_name_key, depth_from_ui, extract_emails_flag,
    config_dir_path, raw_csv_folder_path, gmaps_coords_dict, language_code, 
    default_config_depth_val, results_prefix, logger_instance, log_q_streamlit
):
    logger_instance.subsection(f"Scraping Docker: '{city_name_key.capitalize()}'")
    if not keywords_list: logger_instance.warning(f"No kw para '{city_name_key}'."); return None
    
    city_info = gmaps_coords_dict.get(city_name_key.lower())
    if not city_info or city_info.get('latitude') is None or city_info.get('longitude') is None:
        logger_instance.error(f"Coords inválidas para '{city_name_key}'."); return None
    lat, lon = city_info['latitude'], city_info['longitude']
    
    current_depth = default_config_depth_val
    if depth_from_ui is not None:
        try:
            parsed_depth_ui = int(depth_from_ui)
            if 1 <= parsed_depth_ui <= 20: current_depth = parsed_depth_ui
        except: pass # Mantener default_config_depth si hay error
    logger_instance.info(f"Profundidad GOSOM: {current_depth}. Emails: {extract_emails_flag}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_fn = f"{results_prefix}{city_name_key.lower()}_{ts}.csv"
    raw_fp_host = os.path.join(raw_csv_folder_path, raw_fn)
    raw_fp_cont = f"/app/data/raw/{raw_fn}"
    tmp_kw_fn = f"tmp_kw_{city_name_key.lower()}_{ts}.txt"
    tmp_kw_fp_host = os.path.join(config_dir_path, tmp_kw_fn)
    tmp_kw_fp_cont = f"/app/config/{tmp_kw_fn}"

    try:
        os.makedirs(os.path.dirname(tmp_kw_fp_host), exist_ok=True)
        os.makedirs(os.path.dirname(raw_fp_host), exist_ok=True)
        with open(tmp_kw_fp_host, 'w', encoding='utf-8') as f:
            for kw in keywords_list: f.write(f"{kw}\n")
        with open(raw_fp_host, 'w', encoding='utf-8') as f: pass
        
        abs_cfg_dir = os.path.abspath(config_dir_path)
        abs_raw_dir = os.path.abspath(raw_csv_folder_path)
        
        docker_cmd_list = [
            "docker", "run", "--rm", 
            "-v", f"{abs_cfg_dir}:/app/config:ro", 
            "-v", f"{abs_raw_dir}:/app/data/raw",
            "gosom/google-maps-scraper",
            "-lang", language_code, "-depth", str(current_depth),
            "-input", tmp_kw_fp_cont, "-results", raw_fp_cont,
            "-exit-on-inactivity", "2m", "-geo", f"{lat},{lon}" # Reducido exit-on-inactivity
        ]
        if extract_emails_flag: docker_cmd_list.append("-email")
        
        cmd_str_for_log = ' '.join(docker_cmd_list)
        logger_instance.info(f"Ejecutando: {cmd_str_for_log}")
        log_q_streamlit.put(f"{LogMessageType.CMD_DOCKER}:{cmd_str_for_log}")

        process = subprocess.Popen(docker_cmd_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding='utf-8', errors='replace', bufsize=1, universal_newlines=True)
        
        last_row_count_update_time = time.time()
        
        for stdout_line in iter(process.stdout.readline, ''):
            clean_line = stdout_line.strip()
            if clean_line:
                log_q_streamlit.put(f"GOSOM_LOG:{clean_line}")
                # logger_instance.debug(f"GOSOM ({city_name_key}): {clean_line}") # Redundante con la cola
            
            if st.session_state.get('stop_scraping_flag', False):
                logger_instance.warning(f"DETENER para {city_name_key}. Terminando Docker...")
                log_q_streamlit.put(f"{LogMessageType.INFO}:Intentando detener Docker para {city_name_key}...")
                process.terminate()
                try: process.wait(timeout=3) # Reducir timeout de espera
                except subprocess.TimeoutExpired: process.kill()
                log_q_streamlit.put(f"INFO:Docker para {city_name_key} detenido por usuario.")
                return None
            
            if time.time() - last_row_count_update_time > 2: # Chequear cada 2 segundos
                if os.path.exists(raw_fp_host):
                    try:
                        with open(raw_fp_host, 'r', encoding='utf-8', errors='ignore') as f_rc:
                             # Contar líneas no vacías para aproximar filas de datos
                            current_rows = sum(1 for line_rc in f_rc if line_rc.strip()) 
                        log_q_streamlit.put({LogMessageType.LIVE_ROW_COUNT: current_rows, "city": city_name_key}) # Usar constante como clave
                    except Exception as e_rc: logger_instance.debug(f"Error conteo CSV vivo: {e_rc}")
                last_row_count_update_time = time.time()
        
        process.stdout.close()
        return_code = process.wait()
        
        if return_code == 0:
            logger_instance.success(f"Docker OK para '{city_name_key}'.")
            final_rows = 0
            if os.path.exists(raw_fp_host):
                with open(raw_fp_host, 'r', encoding='utf-8', errors='ignore') as f_fc:
                    final_rows = sum(1 for line_fc in f_fc if line_fc.strip())
                log_q_streamlit.put({LogMessageType.LIVE_ROW_COUNT: final_rows, "city": city_name_key}) # Última actualización
                if final_rows > 0:
                    logger_instance.success(f"CSV ({final_rows} filas): {raw_fp_host}")
                    return raw_fp_host
                else:
                    logger_instance.warning(f"CSV generado pero VACÍO (0 filas): {raw_fp_host}")
                    return raw_fp_host 
            else:
                logger_instance.error(f"Docker OK, pero archivo NO ENCONTRADO: {raw_fp_host}")
                return None
        else:
            logger_instance.error(f"Docker falló para '{city_name_key}'. Código: {return_code}")
            log_q_streamlit.put(f"{LogMessageType.ERROR}:Docker falló {city_name_key}. Código: {return_code}")
            return None
    except FileNotFoundError:
        logger_instance.critical("Comando 'docker' no encontrado.", exc_info=True)
        log_q_streamlit.put({LogMessageType.CRITICAL_ERROR: "Comando 'docker' no encontrado."})
        return None
    except Exception as e:
        logger_instance.critical(f"Excepción en Docker exec ({city_name_key}): {e}", exc_info=True)
        log_q_streamlit.put({LogMessageType.CRITICAL_ERROR: f"Excepción Docker ({city_name_key}): {str(e)[:200]}"}) # Limitar longitud del mensaje
        return None
    finally:
        if os.path.exists(tmp_kw_fp_host):
            try: os.remove(tmp_kw_fp_host)
            except: pass

def validate_csv_integrity_core(csv_filepath, required_columns, logger_instance):
    """
    Valida la integridad de un archivo CSV, asegurando que contenga las columnas requeridas.

    Args:
        csv_filepath (str): Ruta completa al archivo CSV a validar.
        required_columns (list): Lista de nombres de columnas que deben estar presentes.
        logger_instance (StyledLogger): Instancia del logger para registrar mensajes.

    Returns:
        bool: True si el CSV es válido y contiene todas las columnas requeridas, False en caso contrario.
    """
    logger_instance.subsection(f"Validando Integridad CSV: '{os.path.basename(csv_filepath)}'")
    try:
        df = pd.read_csv(csv_filepath, nrows=0) # Leer solo el encabezado
        missing_cols = [col for col in required_columns if col not in df.columns]
        if not missing_cols: logger_instance.success(f"Integridad CSV OK. Columnas requeridas presentes.")
        else: logger_instance.error(f"Integridad CSV FALLIDA. Faltan columnas: {', '.join(missing_cols)}")
        return not missing_cols
    except FileNotFoundError: logger_instance.error(f"Archivo CSV no encontrado: {csv_filepath}"); return False
    except pd.errors.EmptyDataError: logger_instance.error(f"Archivo CSV vacío: {csv_filepath}"); return False
    except Exception as e: logger_instance.error(f"Error validando integridad CSV {csv_filepath}: {e}", exc_info=True); return False

def compare_and_filter_new_data_core(df_new, main_csv_filepath, logger_instance):
 """
 Compara nuevos datos con el CSV principal para filtrar duplicados.
 Duplicados se definen por la combinación de 'link' y 'title'.

 Args:
 df_new (pd.DataFrame): DataFrame con los datos recién scrapeados y transformados.
 main_csv_filepath (str): Ruta completa al archivo CSV principal (scrape_jobs.csv).
        logger_instance (StyledLogger): Instancia del logger.

 Returns:
 pd.DataFrame: DataFrame con los nuevos datos que no son duplicados.
 """
    logger_instance.subsection("Comparando datos nuevos con CSV principal para deduplicación")
    if not os.path.exists(main_csv_filepath) or os.path.getsize(main_csv_filepath) == 0:
        logger_instance.info(f"CSV principal consolidado no existe o está vacío '{main_csv_filepath}'. Todos los datos nuevos ({len(df_new)} registros) son considerados únicos.")
        return df_new

    try:
        df_main = pd.read_csv(main_csv_filepath, encoding='utf-8', low_memory=False)
        logger_instance.info(f"CSV principal consolidado cargado con {len(df_main)} registros para comparación.")

        # Realizar un merge para identificar filas en df_new que no están en df_main
        merged_df = pd.merge(df_new, df_main[['link', 'title']], on=['link', 'title'], how='left', indicator=True)
        df_unique_new = merged_df[merged_df['_merge'] == 'left_only'].drop('_merge', axis=1)

        logger_instance.success(f"Comparación completa. Se encontraron {len(df_unique_new)} registros nuevos únicos de {len(df_new)}.")
        return df_unique_new

    except Exception as e:
        logger_instance.error(f"Error comparando datos nuevos con CSV principal {main_csv_filepath}: {e}", exc_info=True)
        logger_instance.warning("Ocurrió un error durante la comparación. Retornando DataFrame nuevo sin filtrar por seguridad.")
        return df_new

def transform_gmaps_data_core(df_raw, city_key_origin, logger_instance):
    """
    Transforms raw data from Google Maps scraper output into a cleaned DataFrame,
    filtering columns based on user selection from the Streamlit UI.
    """
    # Local helper function (ensure this is defined within or accessible by this function)
    def extract_address_components(json_str_or_data):
        index_names = ['parsed_street', 'parsed_city_comp', 'parsed_postal_code', 'parsed_state', 'parsed_country']
        try:
            if pd.isna(json_str_or_data) or json_str_or_data == '{}': return pd.Series([pd.NA]*len(index_names), index=index_names)
            data = json.loads(str(json_str_or_data)) if not isinstance(json_str_or_data, dict) else json_str_or_data
            if isinstance(data, dict): return pd.Series([data.get('street'), data.get('city'), data.get('postal_code'), data.get('state'), data.get('country')], index=index_names)
            return pd.Series([pd.NA]*len(index_names), index=index_names) # Retorna NA si no es dict
        except: return pd.Series([pd.NA]*len(index_names), index=index_names)


    logger_instance.subsection(f"Transformando: {city_key_origin.capitalize()}")
    if not isinstance(df_raw, pd.DataFrame) or df_raw.empty:
        logger_instance.warning(f"DF crudo para {city_key_origin} vacío. No se transforma.")
        # Retornar un DataFrame vacío con las columnas seleccionadas por el usuario si están disponibles
        # Accedemos a st.session_state para obtener las columnas seleccionadas
        # Usar un conjunto por defecto si st.session_state no está disponible (ej. al correr sin Streamlit)
        # Consideramos las columnas esenciales + las parseadas de la dirección + lat/lon como un buen conjunto por defecto
        address_parse_cols = ['parsed_street', 'parsed_city_comp', 'parsed_postal_code', 'parsed_state', 'parsed_country']
        default_essential_plus = ['title', 'emails', 'phone', 'address', 'link', 'website', 'cid'] + address_parse_cols + ['latitude', 'longitude']
        default_columns = list(dict.fromkeys(default_essential_plus + ['search_origin_city']))

        selected_cols = st.session_state.get('selected_columns', default_columns) # Usar las columnas seleccionadas o el default

        # Asegurarse de que 'search_origin_city' esté siempre incluida incluso en un DF vacío
        if 'search_origin_city' not in selected_cols:
             selected_cols.append('search_origin_city')

        # Asegurarse de que las columnas parseadas estén incluidas si 'complete_address' está seleccionada en la UI, incluso en un DF vacío
        if 'complete_address' in selected_cols:
             for parsed_col in address_parse_cols:
                 if parsed_col not in selected_cols:
                      selected_cols.append(parsed_col)

        # Limpiar duplicados
        selected_cols = list(dict.fromkeys(selected_cols))

        return pd.DataFrame(columns=selected_cols)

    df = df_raw.copy()

    # --- Asegurar que las columnas de dirección parseada existan antes de intentar usarlas ---
    # Esto es necesario porque extract_address_components devuelve estas columnas.
    address_parse_cols = ['parsed_street', 'parsed_city_comp', 'parsed_postal_code', 'parsed_state', 'parsed_country']
    for col in address_parse_cols:
        if col not in df.columns:
            df[col] = pd.NA


    numeric_cols = ['review_count', 'review_rating', 'latitude', 'longitude']
    for col in numeric_cols:
        if col in df.columns:
            # Convertir a numérico, manteniendo NA para errores
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            # Si la columna no existe, añadirla con NA
            df[col] = pd.NA


    if 'complete_address' in df.columns:
        address_components_df = df['complete_address'].apply(extract_address_components)
        # Concatenar solo si hay datos parseados válidos
        if not address_components_df.empty:
             df = pd.concat([df, address_components_df], axis=1)
    # No necesitamos un else aquí porque ya inicializamos las columnas parseadas con NA


    df['search_origin_city'] = city_key_origin.capitalize()

    # --- MODIFICACIÓN AQUÍ: Usar las columnas seleccionadas por el usuario ---
    # Obtener las columnas seleccionadas de st.session_state
    # Si no existen en session_state (ej. se corre core_logic.py directamente), usar un conjunto por defecto (las esenciales + address components + lat/lon)
    # Consideramos las columnas esenciales + las parseadas de la dirección + lat/lon como un buen conjunto por defecto
    default_essential_plus = ['title', 'emails', 'phone', 'address', 'link', 'website', 'cid'] + address_parse_cols + ['latitude', 'longitude']

    # Asegurarse de que las columnas por defecto no tengan duplicados
    default_columns = list(dict.fromkeys(default_essential_plus + ['search_origin_city']))


    selected_columns_from_ui = st.session_state.get('selected_columns', default_columns) # Usar las columnas por defecto si no hay selección


    # Asegurarse de que 'search_origin_city' esté siempre incluida si no está seleccionada explícitamente
    if 'search_origin_city' not in selected_columns_from_ui:
        columns_to_process = selected_columns_from_ui + ['search_origin_city']
    else:
        columns_to_process = selected_columns_from_ui

    # Asegurarse de que las columnas parseadas de la dirección estén incluidas si 'complete_address' está seleccionada
    if 'complete_address' in columns_to_process:
        for parsed_col in address_parse_cols:
            if parsed_col not in columns_to_process: # Check if already in list before appending
                columns_to_process.append(parsed_col)

    # Asegurarse de que lat y lon estén incluidas si se usa el mapa (aunque el mapa usa el df consolidado final, es seguro tenerlas aquí)
    if 'latitude' in columns_to_process and 'longitude' not in columns_to_process:
         columns_to_process.append('longitude')
    if 'longitude' in columns_to_process and 'latitude' not in columns_to_process:
         columns_to_process.append('latitude')


    # Eliminar duplicados en la lista final de columnas a procesar
    columns_to_process = list(dict.fromkeys(columns_to_process))


    # Filtrar las columnas del DataFrame
    # Asegurarse de que las columnas seleccionadas existan en el DataFrame crudo
    existing_selected_columns = [col for col in columns_to_process if col in df.columns]

    # Si no hay columnas seleccionadas existentes, retornar un DataFrame vacío con las columnas seleccionadas deseadas
    if not existing_selected_columns:
        logger_instance.warning(f"Ninguna de las columnas seleccionadas ({', '.join(columns_to_process)}) existe en los datos crudos para {city_key_origin}. Retornando DataFrame vacío con columnas seleccionadas.")
        return pd.DataFrame(columns=columns_to_process)


    df_processed = df[existing_selected_columns].copy()
    # --- FIN MODIFICACIÓN ---


    # --- Resto del código de limpieza y procesamiento de columnas ---
    # Asegurarse de que estas columnas existan antes de intentar limpiarlas y que estén en existing_selected_columns
    cols_to_clean = ['phone', 'emails', 'category', 'website', 'title']
    for col_clean in cols_to_clean:
        if col_clean in df_processed.columns and col_clean in existing_selected_columns: # Doble verificación
            df_processed[col_clean] = df_processed[col_clean].astype(str).str.strip()
            df_processed.loc[df_processed[col_clean].isin(['nan', 'None', '', '<NA>']), col_clean] = pd.NA
            if col_clean == 'phone':
                # Aplicar limpieza de teléfono solo si la columna existe después del filtrado
                df_processed[col_clean] = df_processed[col_clean].astype(str).str.replace(r'[^\d\+\s\(\)-]', '', regex=True)
            if col_clean == 'category':
                 # Asegurarse de que la columna es tipo string antes de dividir
                df_processed[col_clean] = df_processed[col_clean].astype(str).str.split(',').str[0].str.strip()


    # Asegurarse de que las columnas parseadas de la dirección también se limpien si están presentes y seleccionadas
    for parsed_col in address_parse_cols:
        if parsed_col in df_processed.columns and parsed_col in existing_selected_columns:
             df_processed[parsed_col] = df_processed[parsed_col].astype(str).str.strip()
             df_processed.loc[df_processed[parsed_col].isin(['nan', 'None', '', '<NA>']), parsed_col] = pd.NA


    logger_instance.success(f"Transformación OK para {city_key_origin}. {len(df_processed)} regs con {len(df_processed.columns)} columnas seleccionadas/existentes.")
    return df_processed

def process_city_data_core(
    *, city_key, keywords_list, depth_from_ui, extract_emails_flag, 
    config_params_dict, paths_config_dict, logger_instance, log_q_streamlit
):
    # ... (Tu función process_city_data_core COMPLETA de la respuesta anterior,
    #      asegurándote que llame a run_gmaps_scraper_docker_core con el argumento
    #      log_q_for_streamlit_updates=log_q_streamlit)
    logger_instance.section(f"Proceso Ciudad: {city_key.capitalize()}")
    gmaps_coords_dict = config_params_dict.get('gmaps_coordinates', {})
    language_code = config_params_dict.get('language', 'es')
    default_config_depth = config_params_dict.get('default_depth', 1) 
    results_prefix = config_params_dict.get('results_filename_prefix', 'gmaps_data_')
    config_dir_path = paths_config_dict.get('CONFIG_DIR')
    raw_csv_folder_path = paths_config_dict.get('RAW_DATA_DIR')

    if not all([config_dir_path, raw_csv_folder_path, gmaps_coords_dict is not None, language_code, results_prefix]):
        logger_instance.critical("Faltan params config en process_city_data_core.")
        return pd.DataFrame(columns=gmaps_column_names), None 
    
    raw_csv_path = run_gmaps_scraper_docker_core(
        keywords_list=keywords_list, city_name_key=city_key,
        depth_from_ui=depth_from_ui, extract_emails_flag=extract_emails_flag,
        config_dir_path=config_dir_path, raw_csv_folder_path=raw_csv_folder_path,
        gmaps_coords_dict=gmaps_coords_dict, language_code=language_code,
        default_config_depth_val=default_config_depth, 
        results_prefix=results_prefix, logger_instance=logger_instance,
 log_q_streamlit=log_q_streamlit
    )
    
    if not raw_csv_path or not os.path.exists(raw_csv_path):
 logger_instance.error(f"Scraping para {city_key} no generó CSV o archivo no existe: '{raw_csv_path}'.")
        return pd.DataFrame(columns=gmaps_column_names), raw_csv_path

    df_raw = pd.DataFrame(columns=gmaps_column_names) 
    try:
        if os.path.getsize(raw_csv_path) == 0:
            logger_instance.warning(f"CSV crudo {raw_csv_path} vacío (0 bytes).")
            return pd.DataFrame(columns=gmaps_column_names), raw_csv_path
        
        # Leer para chequear columnas
        temp_df_chk = pd.read_csv(raw_csv_path, header=None, encoding='utf-8', nrows=1, low_memory=False)
        num_cols_file = temp_df_chk.shape[1]
        cols_to_use = gmaps_column_names
        if num_cols_file != len(gmaps_column_names):
            logger_instance.warning(f"CSV cols: {num_cols_file}, Esperadas: {len(gmaps_column_names)}. Path: {raw_csv_path}.")
            if num_cols_file < len(gmaps_column_names): cols_to_use = gmaps_column_names[:num_cols_file]
        
        df_raw = pd.read_csv(raw_csv_path, header=None, names=cols_to_use, encoding='utf-8', on_bad_lines='warn', low_memory=False, usecols=range(len(cols_to_use)) if num_cols_file > len(cols_to_use) else None)
        logger_instance.success(f"CSV crudo cargado para {city_key}: {len(df_raw)} filas.")
    except pd.errors.EmptyDataError: logger_instance.warning(f"CSV crudo {raw_csv_path} vacío (EmptyDataError).")
    except Exception as e_load: logger_instance.error(f"Error cargando CSV crudo {raw_csv_path}: {e_load}", exc_info=True); return pd.DataFrame(columns=gmaps_column_names), raw_csv_path
        
    df_transformado = transform_gmaps_data_core(df_raw, city_key, logger_instance)
    logger_instance.success(f"Proceso para {city_key} finalizado. {len(df_transformado)} registros.")
    
    # --- Registro de Job de Scraping ---
    job_log_filepath = paths_config_dict.get('JOB_LOG_FILE') # Obtener la ruta del log de jobs
    if job_log_filepath:
        try:
            job_id = str(uuid.uuid4()) # ID único por job
            now = datetime.now()
            fecha = now.strftime("%Y-%m-%d")
            hora = now.strftime("%H:%M:%S")
            ciudades_str = city_key # Registrar la ciudad procesada en este job
            keywords_str = "; ".join(keywords_list) # Separar palabras clave por ;
            depth_val = depth_from_ui if depth_from_ui is not None else default_config_depth
            filas_extraidas = len(df_transformado)
            
            # Determinar si hubo un error significativo
            error_msg = ""
            if df_transformado.empty and os.path.exists(raw_csv_path) and os.path.getsize(raw_csv_path) > 0:
                 error_msg = "CSV crudo con errores de formato o sin datos válidos"
            elif not os.path.exists(raw_csv_path) or (os.path.exists(raw_csv_path) and os.path.getsize(raw_csv_path) == 0):
                 error_msg = "No se generó CSV crudo o está vacío"
            
            log_entry = f'"{job_id}","{fecha}","{hora}","{ciudades_str}","{keywords_str}",{depth_val},{filas_extraidas},"{error_msg}"'
            
            with open(job_log_filepath, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
            logger_instance.success(f"Job registrado en: {job_log_filepath}")
        except Exception as e:
            logger_instance.error(f"Error registrando job de scraping: {e}", exc_info=True)
    return df_transformado, raw_csv_path