# 0_AGENTE_GOSOM/src/core_logic.py

import logging
import os
import subprocess
import pandas as pd
import json
from datetime import datetime

# --- Clase StyledLogger ---
class StyledLogger:
    def __init__(self, logger_name='CoreLogicLogger', log_file_path='core_logic_agent.log', level=logging.INFO):
        self.logger = logging.getLogger(logger_name)
        
        if not self.logger.handlers: 
            self.logger.setLevel(level)
            self.logger.propagate = False 

            formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s:%(funcName)s:%(lineno)d] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

            try:
                log_dir = os.path.dirname(log_file_path)
                if log_dir and not os.path.exists(log_dir): 
                    os.makedirs(log_dir, exist_ok=True)
                
                fh = logging.FileHandler(log_file_path, encoding='utf-8')
                fh.setFormatter(formatter)
                self.logger.addHandler(fh)
            except Exception as e:
                print(f"Error al crear FileHandler para logs en core_logic ({log_file_path}): {e}")

            sh = logging.StreamHandler() 
            sh.setFormatter(formatter)
            self.logger.addHandler(sh)
        
        self.HEADER_ART = """
        ********************************************************************************
        *                     G M A P S   S C R A P E R   A G E N T                    *
        *                         ( Avalian Project - MVP )                          *
        *                          (Core Logic Operations)                           *
        ********************************************************************************
        """
        self.SECTION_SEPARATOR = "=" * 80
        self.SUB_SECTION_SEPARATOR = "-" * 60
        self.SUCCESS_ART = "[ OK ]"
        self.ERROR_ART = "[FAIL]"
        self.WARNING_ART = "[WARN]"
        self.INFO_ART = "[INFO]"
        self.DEBUG_ART = "[DEBUG]"

    def _log(self, level, message, art=""):
        self.logger.log(level, f"{art} {message}".strip())

    def print_header_art(self): 
        print(self.HEADER_ART) # Para la consola donde corre Streamlit, si se llama desde app_streamlit

    def section(self, title): self._log(logging.INFO, f"\n{self.SECTION_SEPARATOR}\n{title.upper()}\n{self.SECTION_SEPARATOR}")
    def subsection(self, title): self._log(logging.INFO, f"\n{self.SUB_SECTION_SEPARATOR}\n{title}\n{self.SUB_SECTION_SEPARATOR}")
    def info(self, message): self._log(logging.INFO, message, self.INFO_ART)
    def success(self, message): self._log(logging.INFO, message, self.SUCCESS_ART)
    def warning(self, message): self._log(logging.WARNING, message, self.WARNING_ART)
    def error(self, message, exc_info=False):
        self._log(logging.ERROR, message, self.ERROR_ART)
        if exc_info: self.logger.exception("Detalles de la excepción:")
    def critical(self, message, exc_info=False):
        self._log(logging.CRITICAL, message, f"{self.ERROR_ART} [CRITICAL]")
        if exc_info: self.logger.exception("Detalles de la excepción crítica:")
    def debug(self, message): self._log(logging.DEBUG, message, self.DEBUG_ART)

# --- Definición de gmaps_column_names ---
gmaps_column_names = [
    'input_id', 'link', 'title', 'category', 'address', 'open_hours', 'popular_times',
    'website', 'phone', 'plus_code', 'review_count', 'review_rating', 'reviews_per_rating',
    'latitude', 'longitude', 'cid', 'status', 'descriptions', 'reviews_link', 'thumbnail',
    'timezone', 'price_range', 'data_id', 'images', 'reservations', 'order_online',
    'menu', 'owner', 'complete_address', 'about', 'user_reviews', 
    'emails'
]

# --- Función para cargar keywords desde CSV ---
def load_keywords_from_csv_core(config_dir_path, city_key, logger_instance):
    keywords_file_path = os.path.join(config_dir_path, f'keywords_{city_key.lower()}.csv')
    keywords = []
    try:
        with open(keywords_file_path, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip()]
        
        if keywords:
            logger_instance.success(f"Cargadas {len(keywords)} keywords para '{city_key}' desde {keywords_file_path}")
        else:
            logger_instance.warning(f"Archivo de keywords para '{city_key}' está vacío o no contiene keywords válidas: {keywords_file_path}")
    except FileNotFoundError:
        logger_instance.error(f"Archivo de keywords no encontrado para '{city_key}': {keywords_file_path}")
    except Exception as e:
        logger_instance.error(f"Error inesperado al cargar keywords para '{city_key}': {e}", exc_info=True)
    return keywords

# --- Función para ejecutar el scraper Docker ---
def run_gmaps_scraper_docker_core(
    keywords_list, city_name_key, depth_override, extract_emails_flag,
    config_dir_path, raw_csv_folder_path, gmaps_coords_dict, 
    language_code, default_config_depth, results_prefix, logger_instance
):
    logger_instance.subsection(f"Iniciando scraping para ciudad: '{city_name_key.capitalize()}'")

    if not keywords_list:
        logger_instance.warning(f"No hay keywords para scrapear para '{city_name_key}'. Omitiendo.")
        return None

    city_info = gmaps_coords_dict.get(city_name_key.lower())
    if not city_info:
        logger_instance.error(f"No se encontraron coordenadas para '{city_name_key}'.")
        return None
    
    lat = city_info.get('latitude')
    lon = city_info.get('longitude')
    
    if lat is None or lon is None:
        logger_instance.error(f"Latitud o longitud faltantes para '{city_name_key}'. Coords: {city_info}")
        return None

    current_depth = default_config_depth
    if depth_override is not None:
        try:
            current_depth_ui = int(depth_override)
            if current_depth_ui > 0: current_depth = current_depth_ui
            else: logger_instance.warning(f"Profundidad UI inválida ({depth_override}). Usando config: {current_depth}.")
        except (ValueError, TypeError): logger_instance.warning(f"Valor de profundidad UI inválido '{depth_override}'. Usando config: {current_depth}.")
            
    logger_instance.info(f"Usando profundidad de búsqueda: {current_depth}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_output_filename = f"{results_prefix}{city_name_key.lower()}_{timestamp}.csv"
    raw_output_filepath_host = os.path.join(raw_csv_folder_path, raw_output_filename)
    raw_output_filepath_container = f"/app/data/raw/{raw_output_filename}"

    temp_queries_filename = f"temp_queries_{city_name_key.lower()}_{timestamp}.txt"
    temp_queries_filepath_host = os.path.join(config_dir_path, temp_queries_filename)
    temp_queries_filepath_container = f"/app/config/{temp_queries_filename}"

    try:
        os.makedirs(raw_csv_folder_path, exist_ok=True)
        os.makedirs(config_dir_path, exist_ok=True)

        with open(temp_queries_filepath_host, 'w', encoding='utf-8') as f:
            for kw in keywords_list: f.write(f"{kw}\n")
        logger_instance.success(f"Archivo temporal de queries creado: {temp_queries_filepath_host} con {len(keywords_list)} keywords.")

        with open(raw_output_filepath_host, 'w', encoding='utf-8') as f: pass 
        logger_instance.success(f"Archivo de salida CSV vacío creado en host: {raw_output_filepath_host}")
        
        docker_command = [
            "docker", "run", "--rm", 
            "-v", f"{config_dir_path}:/app/config:ro",
            "-v", f"{raw_csv_folder_path}:/app/data/raw",
            "gosom/google-maps-scraper",
            "-lang", language_code, "-depth", str(current_depth),
            "-input", temp_queries_filepath_container, "-results", raw_output_filepath_container,
            "-exit-on-inactivity", "3m", "-geo", f"{lat},{lon}"
        ]
        if extract_emails_flag: docker_command.append("-email")

        logger_instance.info(f"Comando Docker: {' '.join(docker_command)}")
        
        process = subprocess.run(docker_command, capture_output=True, text=True, encoding='utf-8', errors='replace', check=False)

        if process.stdout: logger_instance.debug(f"GOSOM STDOUT ({city_name_key}):\n{process.stdout[:2000]}...")
        if process.stderr: logger_instance.warning(f"GOSOM STDERR ({city_name_key}):\n{process.stderr[:2000]}...")

        if process.returncode == 0:
            logger_instance.success(f"Comando Docker OK para '{city_name_key}'.")
            if os.path.exists(raw_output_filepath_host) and os.path.getsize(raw_output_filepath_host) > 0:
                 logger_instance.success(f"CSV crudo generado: {raw_output_filepath_host}")
                 return raw_output_filepath_host 
            elif os.path.exists(raw_output_filepath_host):
                 logger_instance.warning(f"CSV crudo generado por Docker está VACÍO: {raw_output_filepath_host}")
                 return raw_output_filepath_host 
            else:
                 logger_instance.error(f"Comando Docker OK, pero archivo de salida NO ENCONTRADO: {raw_output_filepath_host}")
                 return None
        else:
            logger_instance.error(f"Comando Docker falló para '{city_name_key}'. Código: {process.returncode}")
            return None
    except FileNotFoundError:
        logger_instance.critical("Comando 'docker' no encontrado. ¿Docker instalado y en PATH?", exc_info=True)
        return None
    except Exception as e:
        logger_instance.critical(f"Excepción en run_gmaps_scraper_docker_core ({city_name_key}): {e}", exc_info=True)
        return None
    finally:
        if os.path.exists(temp_queries_filepath_host):
            try: os.remove(temp_queries_filepath_host)
            except Exception as e_remove: logger_instance.warning(f"No se pudo eliminar temp_queries: {e_remove}")

# --- Función para transformar los datos ---
def transform_gmaps_data_core(df_raw, city_key_origin, logger_instance):
    def extract_address_components(json_str_or_data):
        # ... (la misma función extract_address_components que tenías) ...
        try:
            if pd.isna(json_str_or_data): return pd.Series([pd.NA]*5, index=['parsed_street', 'parsed_city_comp', 'parsed_postal_code', 'parsed_state', 'parsed_country'])
            data = json.loads(str(json_str_or_data)) if isinstance(json_str_or_data, str) else json_str_or_data
            if isinstance(data, dict):
                return pd.Series([data.get('street'), data.get('city'), data.get('postal_code'), data.get('state'), data.get('country')], index=['parsed_street', 'parsed_city_comp', 'parsed_postal_code', 'parsed_state', 'parsed_country'])
            return pd.Series([pd.NA]*5, index=['parsed_street', 'parsed_city_comp', 'parsed_postal_code', 'parsed_state', 'parsed_country'])
        except: return pd.Series([pd.NA]*5, index=['parsed_street', 'parsed_city_comp', 'parsed_postal_code', 'parsed_state', 'parsed_country'])

    logger_instance.subsection(f"Transformando datos para: {city_key_origin.capitalize()}")
    if df_raw.empty:
        logger_instance.warning(f"DataFrame crudo vacío para {city_key_origin}. No hay nada que transformar.")
        return pd.DataFrame() 
    df = df_raw.copy()
    numeric_cols = ['review_count', 'review_rating', 'latitude', 'longitude']
    for col in numeric_cols:
        if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')
        else: df[col] = pd.NA
    if 'complete_address' in df.columns:
        address_components_df = df['complete_address'].apply(extract_address_components)
        df = pd.concat([df, address_components_df], axis=1)
    else:
        for col_name in ['parsed_street', 'parsed_city_comp', 'parsed_postal_code', 'parsed_state', 'parsed_country']: df[col_name] = pd.NA
    df['search_origin_city'] = city_key_origin.capitalize()
    relevant_columns = [
        'title', 'category', 'address', 'parsed_street', 'parsed_city_comp', 'parsed_postal_code', 'parsed_state', 'parsed_country',
        'website', 'phone', 'emails', 'review_count', 'review_rating', 'latitude', 'longitude', 'link', 'search_origin_city'
    ]
    for col in relevant_columns:
        if col not in df.columns: df[col] = pd.NA
    df_processed = df[relevant_columns].copy()
    if 'phone' in df_processed.columns:
        df_processed.loc[:, 'phone'] = df_processed['phone'].astype(str).str.replace(r'[^\d\+\s\(\)-]', '', regex=True).str.strip()
        df_processed.loc[df_processed['phone'].isin(['nan', 'None', '']), 'phone'] = pd.NA
    if 'emails' in df_processed.columns:
        df_processed.loc[:, 'emails'] = df_processed['emails'].astype(str).str.strip()
        df_processed.loc[df_processed['emails'].isin(['nan', 'None', '']), 'emails'] = pd.NA
    if 'category' in df_processed.columns:
        df_processed.loc[:, 'category'] = df_processed['category'].astype(str).str.split(',').str[0].str.strip()
        df_processed.loc[df_processed['category'].isin(['nan', 'None', '']), 'category'] = pd.NA
    logger_instance.success(f"Transformación completada para {city_key_origin.capitalize()}. {len(df_processed)} registros.")
    return df_processed

# --- Función Orquestadora Principal ---
def process_city_data_core(city_key, keywords_list, depth, extract_emails_flag, config_params, paths_config, logger_instance):
    logger_instance.section(f"Procesando Ciudad Completa: {city_key.capitalize()}")
    gmaps_coords_dict = config_params.get('gmaps_coordinates', {})
    language_code = config_params.get('language', 'es')
    default_config_depth_val = config_params.get('default_depth', 1)
    results_prefix = config_params.get('results_filename_prefix', 'gmaps_data_')
    config_dir_path = paths_config.get('CONFIG_DIR')
    raw_csv_folder_path = paths_config.get('RAW_DATA_DIR')

    if not all([config_dir_path, raw_csv_folder_path, results_prefix, language_code, gmaps_coords_dict]):
        logger_instance.critical("Faltan parámetros de config esenciales en process_city_data_core.")
        return pd.DataFrame()

    raw_csv_path = run_gmaps_scraper_docker_core(
        keywords_list, city_key, depth, extract_emails_flag,
        config_dir_path, raw_csv_folder_path, gmaps_coords_dict,
        language_code, default_config_depth_val, results_prefix, logger_instance
    )
    if not raw_csv_path or not os.path.exists(raw_csv_path):
        logger_instance.error(f"No se generó CSV crudo para {city_key} o no se encontró.")
        return pd.DataFrame()
    df_raw = pd.DataFrame() 
    try:
        df_raw = pd.read_csv(
            raw_csv_path, header=None, names=gmaps_column_names, 
            encoding='utf-8', on_bad_lines='warn', low_memory=False
        )
        logger_instance.success(f"CSV crudo cargado para {city_key}: {len(df_raw)} filas, {len(df_raw.columns)} columnas.")
        if df_raw.empty and os.path.getsize(raw_csv_path) > 0 :
             logger_instance.warning(f"CSV crudo {raw_csv_path} no está vacío pero se leyó como DataFrame vacío.")
    except pd.errors.EmptyDataError:
         logger_instance.warning(f"Archivo CSV crudo {raw_csv_path} está vacío.")
    except Exception as e:
        logger_instance.error(f"Error al cargar CSV crudo {raw_csv_path}: {e}", exc_info=True)
        return pd.DataFrame()
    df_transformado = transform_gmaps_data_core(df_raw, city_key, logger_instance)
    logger_instance.success(f"Proceso completo para {city_key.capitalize()} finalizado. {len(df_transformado)} registros.")
    return df_transformado