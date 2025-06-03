# 0_AGENTE_GOSOM/src/core_logic.py

import logging
import os
import subprocess
import pandas as pd
import json
from datetime import datetime
import time # Para simulación si la necesitaras aquí, o para el scraper real



# --- Definición de gmaps_column_names (CRUCIAL QUE COINCIDA CON LA SALIDA DE GOSOM) ---
gmaps_column_names = [
    'input_id', 'link', 'title', 'category', 'address', 'open_hours', 'popular_times',
    'website', 'phone', 'plus_code', 'review_count', 'review_rating', 'reviews_per_rating',
    'latitude', 'longitude', 'cid', 'status', 'descriptions', 'reviews_link', 'thumbnail',
    'timezone', 'price_range', 'data_id', 'images', 'reservations', 'order_online',
    'menu', 'owner', 'complete_address', 'about', 'user_reviews', 
    'emails' # Incluida porque usaremos el flag -email
    # Si usaras --extra-reviews, aquí iría 'user_reviews_extended'
]

# --- Clase StyledLogger ---
class StyledLogger:
    def __init__(self, logger_name='CoreLogicLogger', log_file_path='core_logic_agent.log', level=logging.INFO):
        self.logger = logging.getLogger(logger_name)
        
        # Solo configurar handlers si no existen para este logger específico
        # Esto evita duplicar handlers si la clase se instancia múltiples veces con el mismo logger_name
        if not self.logger.handlers: 
            self.logger.setLevel(level)
            self.logger.propagate = False 

            formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s:%(module)s:%(funcName)s:%(lineno)d] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

            try:
                log_dir = os.path.dirname(log_file_path)
                if log_dir and not os.path.exists(log_dir): 
                    os.makedirs(log_dir, exist_ok=True)
                
                fh = logging.FileHandler(log_file_path, encoding='utf-8')
                fh.setFormatter(formatter)
                self.logger.addHandler(fh)
            except Exception as e:
                print(f"ERROR CRITICO (StyledLogger en core_logic.py): No se pudo crear FileHandler para '{log_file_path}'. Error: {e}")
        
        self.HEADER_ART_TEXT = """
        ********************************************************************************
        *                     G M A P S   S C R A P E R   A G E N T                    *
        *                          (Core Logic Operations)                           *
        ********************************************************************************
        """
        self.SECTION_SEPARATOR = "=" * 70
        self.SUB_SECTION_SEPARATOR = "-" * 50
        self.SUCCESS_ART = "[ OK ]"
        self.ERROR_ART = "[FAIL]"
        self.WARNING_ART = "[WARN]"
        self.INFO_ART = "[INFO]"
        self.DEBUG_ART = "[DEBUG]"

    def _log(self, level, message, art=""):
        self.logger.log(level, f"{art} {message}".strip())

    def print_header_art_to_console(self): 
        """Imprime el header ASCII a la consola (si este logger tiene un StreamHandler)."""
        print(self.HEADER_ART_TEXT) # Siempre imprime a la consola donde corre el script Python
        self.info("Logger de Core Logic Inicializado (mensaje al archivo de log).")

    def get_header_art_text(self): 
        return self.HEADER_ART_TEXT

    def section(self, title): self._log(logging.INFO, f"\n{self.SECTION_SEPARATOR}\n{str(title).upper()}\n{self.SECTION_SEPARATOR}")
    def subsection(self, title): self._log(logging.INFO, f"\n{self.SUB_SECTION_SEPARATOR}\n{str(title)}\n{self.SUB_SECTION_SEPARATOR}")
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


# --- Función para cargar keywords desde CSV ---
def load_keywords_from_csv_core(config_dir_path, city_key, logger_instance):
    logger_instance.debug(f"Intentando cargar keywords para '{city_key}' desde directorio '{config_dir_path}'")
    filepath = os.path.join(config_dir_path, f'keywords_{city_key.lower()}.csv')
    keywords = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip()]
        if keywords:
            logger_instance.success(f"Cargadas {len(keywords)} keywords para '{city_key}' desde '{filepath}'")
        else:
            logger_instance.warning(f"Archivo de keywords para '{city_key}' está vacío o no contiene keywords válidas: '{filepath}'")
    except FileNotFoundError:
        logger_instance.error(f"Archivo de keywords NO encontrado para '{city_key}': '{filepath}'")
    except Exception as e:
        logger_instance.error(f"Error inesperado al cargar keywords para '{city_key}' desde '{filepath}': {e}", exc_info=True)
    return keywords

# --- Función para ejecutar el scraper Docker ---
def run_gmaps_scraper_docker_core(
    keywords_list, 
    city_name_key, 
    depth_from_ui, 
    extract_emails_flag,
    config_dir_path,       
    raw_csv_folder_path,   
    gmaps_coords_dict,     
    language_code,         
    default_config_depth,  
    results_prefix,        
    logger_instance
):
    logger_instance.subsection(f"Iniciando scraping Docker para ciudad: '{city_name_key.capitalize()}'")

    if not keywords_list:
        logger_instance.warning(f"No hay keywords para scrapear para '{city_name_key}'. Omitiendo.")
        return None

    city_info = gmaps_coords_dict.get(city_name_key.lower())
    if not city_info:
        logger_instance.error(f"No se encontraron coordenadas/info para '{city_name_key}' en la configuración (gmaps_coords_dict).")
        return None
    
    lat = city_info.get('latitude')
    lon = city_info.get('longitude')
    
    if lat is None or lon is None:
        logger_instance.error(f"Latitud o longitud faltantes para '{city_name_key}'. Coordenadas recibidas: {city_info}")
        return None

    current_depth = default_config_depth 
    if depth_from_ui is not None:
        try:
            parsed_depth_ui = int(depth_from_ui)
            if 1 <= parsed_depth_ui <= 20: 
                current_depth = parsed_depth_ui
                logger_instance.info(f"Usando profundidad de búsqueda de UI: {current_depth}")
            else:
                logger_instance.warning(f"Profundidad de UI '{depth_from_ui}' fuera de rango. Usando de config: {current_depth}.")
        except (ValueError, TypeError):
            logger_instance.warning(f"Valor de profundidad de UI inválido '{depth_from_ui}'. Usando de config: {current_depth}.")
    else:
         logger_instance.info(f"No se especificó profundidad en UI. Usando profundidad de config: {current_depth}")
            
    logger_instance.info(f"Profundidad final para GOSOM: {current_depth}. Extracción de emails: {extract_emails_flag}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_output_filename = f"{results_prefix}{city_name_key.lower()}_{timestamp}.csv"
    raw_output_filepath_host = os.path.join(raw_csv_folder_path, raw_output_filename)
    raw_output_filepath_container = f"/app/data/raw/{raw_output_filename}"

    temp_queries_filename = f"temp_queries_{city_name_key.lower()}_{timestamp}.txt"
    temp_queries_filepath_host = os.path.join(config_dir_path, temp_queries_filename)
    temp_queries_filepath_container = f"/app/config/{temp_queries_filename}"

    try:
        os.makedirs(os.path.dirname(temp_queries_filepath_host), exist_ok=True)
        os.makedirs(os.path.dirname(raw_output_filepath_host), exist_ok=True)

        logger_instance.info(f"Creando archivo temporal de queries en: {temp_queries_filepath_host}")
        with open(temp_queries_filepath_host, 'w', encoding='utf-8') as f:
            for kw in keywords_list:
                f.write(f"{kw}\n")
        logger_instance.success(f"Archivo temporal de queries creado con {len(keywords_list)} keywords.")

        logger_instance.info(f"Creando archivo de salida CSV vacío en: {raw_output_filepath_host}")
        with open(raw_output_filepath_host, 'w', encoding='utf-8') as f:
            pass 
        logger_instance.success("Archivo de salida CSV vacío creado.")
        
        abs_config_dir_path = os.path.abspath(config_dir_path)
        abs_raw_csv_folder_path = os.path.abspath(raw_csv_folder_path)
        logger_instance.debug(f"Ruta absoluta host para volumen config: {abs_config_dir_path}")
        logger_instance.debug(f"Ruta absoluta host para volumen raw_data: {abs_raw_csv_folder_path}")

        docker_command = [
            "docker", "run", "--rm", 
            "-v", f"{abs_config_dir_path}:/app/config:ro",
            "-v", f"{abs_raw_csv_folder_path}:/app/data/raw",
            "gosom/google-maps-scraper",
            "-lang", language_code, 
            "-depth", str(current_depth),
            "-input", temp_queries_filepath_container, 
            "-results", raw_output_filepath_container,
            "-exit-on-inactivity", "3m", 
            "-geo", f"{lat},{lon}"
        ]
        if extract_emails_flag: 
            docker_command.append("-email")

        logger_instance.info(f"Ejecutando comando Docker: {' '.join(docker_command)}")
        
        process = subprocess.run(docker_command, capture_output=True, text=True, encoding='utf-8', errors='replace', check=False)

        if process.stdout: 
            logger_instance.debug(f"GOSOM STDOUT ({city_name_key}):\n{process.stdout[:2000]}...")
        if process.stderr: 
            logger_instance.info(f"GOSOM STDERR ({city_name_key}) (puede contener info/warnings):\n{process.stderr[:2000]}...")

        if process.returncode == 0:
            logger_instance.success(f"Comando Docker para '{city_name_key}' finalizado con código 0.")
            if os.path.exists(raw_output_filepath_host) and os.path.getsize(raw_output_filepath_host) > 0:
                 logger_instance.success(f"Archivo CSV crudo generado y NO VACÍO: {raw_output_filepath_host}")
                 return raw_output_filepath_host 
            elif os.path.exists(raw_output_filepath_host):
                 logger_instance.warning(f"Archivo CSV crudo generado pero está VACÍO: {raw_output_filepath_host}")
                 return raw_output_filepath_host 
            else:
                 logger_instance.error(f"Comando Docker OK, pero el archivo de salida NO FUE ENCONTRADO en host: {raw_output_filepath_host}")
                 return None
        else:
            logger_instance.error(f"Comando Docker para '{city_name_key}' falló con código de retorno: {process.returncode}")
            return None

    except FileNotFoundError: 
        logger_instance.critical("Comando 'docker' no encontrado. ¿Docker instalado y en PATH?", exc_info=True)
        return None
    except Exception as e:
        logger_instance.critical(f"Excepción en run_gmaps_scraper_docker_core ({city_name_key}): {e}", exc_info=True)
        return None
    finally:
        if os.path.exists(temp_queries_filepath_host):
            try: 
                os.remove(temp_queries_filepath_host)
                logger_instance.info(f"Archivo temporal de queries eliminado: {temp_queries_filepath_host}")
            except Exception as e_remove:
                logger_instance.warning(f"No se pudo eliminar el archivo temporal de queries '{temp_queries_filepath_host}': {e_remove}")

# --- Función para transformar los datos ---
def transform_gmaps_data_core(df_raw, city_key_origin, logger_instance):
    def extract_address_components(json_str_or_data):
        index_names = ['parsed_street', 'parsed_city_comp', 'parsed_postal_code', 'parsed_state', 'parsed_country']
        try:
            if pd.isna(json_str_or_data): 
                return pd.Series([pd.NA]*len(index_names), index=index_names)
            
            data_to_load = str(json_str_or_data) if not isinstance(json_str_or_data, dict) else json_str_or_data
            data = json.loads(data_to_load) if isinstance(data_to_load, str) else data_to_load
            
            if isinstance(data, dict):
                return pd.Series([
                    data.get('street'), data.get('city'), data.get('postal_code'), 
                    data.get('state'), data.get('country')
                ], index=index_names)
            else: 
                logger_instance.debug(f"Dato de dirección no es un dict después de parsear: {data}")
                return pd.Series([pd.NA]*len(index_names), index=index_names)
        except json.JSONDecodeError:
            logger_instance.debug(f"JSONDecodeError al parsear dirección: '{json_str_or_data}'") 
            return pd.Series([pd.NA]*len(index_names), index=index_names)
        except Exception as e:
             logger_instance.warning(f"Excepción al parsear dirección: {e}. Dato: '{json_str_or_data}'", exc_info=False)
             return pd.Series([pd.NA]*len(index_names), index=index_names)

    logger_instance.subsection(f"Transformando datos para: {city_key_origin.capitalize()}")
    if df_raw.empty:
        logger_instance.warning(f"DataFrame crudo para {city_key_origin.capitalize()} está vacío. No hay nada que transformar.")
        return pd.DataFrame(columns=gmaps_column_names) 

    df = df_raw.copy()

    logger_instance.info("Convirtiendo tipos de datos numéricos...")
    numeric_cols = ['review_count', 'review_rating', 'latitude', 'longitude']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            logger_instance.warning(f"Columna numérica esperada '{col}' no encontrada. Se creará con NA.")
            df[col] = pd.NA 

    if 'complete_address' in df.columns:
        logger_instance.info("Parseando 'complete_address'...")
        address_components_df = df['complete_address'].apply(extract_address_components)
        df = pd.concat([df, address_components_df], axis=1)
        logger_instance.success("Componentes de dirección parseados y añadidos.")
    else:
        logger_instance.warning("Columna 'complete_address' no encontrada.")
        for col_name in ['parsed_street', 'parsed_city_comp', 'parsed_postal_code', 'parsed_state', 'parsed_country']:
            if col_name not in df.columns: df[col_name] = pd.NA

    df['search_origin_city'] = city_key_origin.capitalize()
    
    relevant_columns = [
        'title', 'category', 'address', 
        'parsed_street', 'parsed_city_comp', 'parsed_postal_code', 'parsed_state', 'parsed_country', 
        'website', 'phone', 'emails', 
        'review_count', 'review_rating', 'latitude', 'longitude', 
        'link', 'search_origin_city'
    ]
    
    for col in relevant_columns:
        if col not in df.columns:
            logger_instance.debug(f"Añadiendo columna faltante '{col}' con NA antes de la selección final.")
            df[col] = pd.NA
            
    df_processed = df[relevant_columns].copy()
    logger_instance.success(f"Seleccionadas {len(df_processed.columns)} columnas relevantes.")
    
    if 'phone' in df_processed.columns:
        df_processed.loc[:, 'phone'] = df_processed['phone'].astype(str).str.replace(r'[^\d\+\s\(\)-]', '', regex=True).str.strip()
        df_processed.loc[df_processed['phone'].isin(['nan', 'None', '', '<NA>']), 'phone'] = pd.NA

    if 'emails' in df_processed.columns:
        df_processed.loc[:, 'emails'] = df_processed['emails'].astype(str).str.strip()
        df_processed.loc[df_processed['emails'].isin(['nan', 'None', '', '<NA>']), 'emails'] = pd.NA
        
    if 'category' in df_processed.columns:
        df_processed.loc[:, 'category'] = df_processed['category'].astype(str).str.split(',').str[0].str.strip()
        df_processed.loc[df_processed['category'].isin(['nan', 'None', '', '<NA>']), 'category'] = pd.NA
        
    logger_instance.info(f"Transformación completada para {city_key_origin.capitalize()}. {len(df_processed)} registros procesados.")
    return df_processed

# --- Función Orquestadora Principal ---
def process_city_data_core(
    city_key, keywords_list, depth_from_ui, extract_emails_flag, 
    config_params_dict, paths_config_dict, logger_instance
):
    logger_instance.section(f"Iniciando Proceso Completo para Ciudad: {city_key.capitalize()}")
    
    gmaps_coords_dict = config_params_dict.get('gmaps_coordinates', {})
    language_code = config_params_dict.get('language', 'es')
    default_config_depth_val = config_params_dict.get('default_depth', 1) 
    results_prefix_val = config_params_dict.get('results_filename_prefix', 'gmaps_data_')
    
    config_dir_path_val = paths_config_dict.get('CONFIG_DIR')
    raw_csv_folder_path_val = paths_config_dict.get('RAW_DATA_DIR')

    if not all([config_dir_path_val, raw_csv_folder_path_val]):
        logger_instance.critical("CONFIG_DIR o RAW_DATA_DIR no definidos en paths_config_dict.")
        return pd.DataFrame(columns=gmaps_column_names), None 

    raw_csv_path = run_gmaps_scraper_docker_core(
        keywords_list=keywords_list, city_name_key=city_key, depth_override=depth_from_ui, 
        extract_emails_flag=extract_emails_flag, config_dir_path=config_dir_path_val,
        raw_csv_folder_path=raw_csv_folder_path_val, gmaps_coords_dict=gmaps_coords_dict,
        language_code=language_code, default_config_depth=default_config_depth_val, 
        results_prefix=results_prefix_val, logger_instance=logger_instance
    )

    if not raw_csv_path or not os.path.exists(raw_csv_path):
        logger_instance.error(f"Scraping para {city_key} no generó archivo CSV válido en '{raw_csv_path}'.")
        return pd.DataFrame(columns=gmaps_column_names), raw_csv_path 

    df_raw = pd.DataFrame() 
    try:
        logger_instance.info(f"Intentando cargar CSV crudo: {raw_csv_path}")
        df_raw = pd.read_csv(
            raw_csv_path, header=None, names=gmaps_column_names, 
            encoding='utf-8', on_bad_lines='warn', low_memory=False
        )
        logger_instance.success(f"CSV crudo cargado para {city_key}: {len(df_raw)} filas.")
        
        if df_raw.empty and os.path.getsize(raw_csv_path) > 0:
             logger_instance.warning(f"CSV {raw_csv_path} no vacío pero leído como DF vacío.")
    except pd.errors.EmptyDataError:
         logger_instance.warning(f"CSV crudo {raw_csv_path} está vacío (EmptyDataError).")
         df_raw = pd.DataFrame(columns=gmaps_column_names)
    except Exception as e:
        logger_instance.error(f"Error al cargar CSV crudo {raw_csv_path}: {e}", exc_info=True)
        return pd.DataFrame(columns=gmaps_column_names), raw_csv_path
        
    df_transformado = transform_gmaps_data_core(df_raw, city_key, logger_instance)
    logger_instance.success(f"Proceso para {city_key} finalizado. {len(df_transformado)} registros listos.")
    return df_transformado, raw_csv_path