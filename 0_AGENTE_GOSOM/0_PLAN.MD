**Visión General del Agente (Estado Ideal - según "Diseño Pipeline ETL"):**

* Un proyecto independiente (`Paniceres/google-maps-scraper-etl`, un fork de `gosom/google-maps-scraper`).
* Dockerizado, con una API RESTful (FastAPI) para gestión programática.
* Extrae datos de Google Maps, los transforma (normaliza, deduplica).
* Carga los datos directamente en una base de datos PostgreSQL (staging).
* Configurable vía variables de entorno.
* Con logging detallado y tests.
* Integrable en un workflow de orquestación (Argo).

**Estructura de Carpetas Propuesta para `0_AGENTE_GOSOM` (Mantenemos la misma, soporta la evolución):**

```
ETL-GMAPS/
├── 0_AGENTE_GOSOM/
│   ├── README.md
│   ├── OBJETIVOS_AGENTE_MVP.md  # Roadmap MVP (lo crearemos ahora)
│   ├── config/
│   │   ├── keywords_neuquen.csv
│   │   ├── keywords_general_roca.csv
│   │   └── parameters_default.json
│   ├── notebooks/
│   │   ├── 1_EDA_GOSOM_Avalian.ipynb
│   │   ├── 2_MVP_Scraping_Transform_CSV.ipynb # Notebook principal para el MVP
│   ├── src/                          # Para código Python modular futuro
│   │   ├── __init__.py
│   │   ├── scraper_module.py       # Futura lógica de scraping
│   │   ├── transformer_module.py   # Futura lógica de transformación
│   │   └── db_loader_module.py     # Futura lógica de carga a BD
│   ├── data/
│   │   ├── raw/                    # CSVs crudos (gitignore)
│   │   ├── processed/              # CSVs procesados (gitignore)
│   │   └── logs/                   # Logs en archivo (gitignore)
│   ├── tests/                        # Futuros tests
│   ├── Dockerfile                  # Futuro Dockerfile
│   └── requirements.txt            # pandas, jupyter, (futuro: fastapi, psycopg2-binary, etc.)
│
├── .gitignore
└── ...
```

**Archivo `0_AGENTE_GOSOM/OBJETIVOS_AGENTE_MVP.md` (Roadmap MVP e Iterativo):**

```markdown
# Objetivos y Roadmap MVP del Agente Google Maps ETL (GOSOM)

Este documento describe el plan de desarrollo incremental para el Agente Google Maps ETL, comenzando con un Mínimo Producto Viable (MVP) y evolucionando hacia la solución ideal descrita en el "Diseño Pipeline ETL" del proyecto Avalian.

## Fase 1: MVP - Extracción, Transformación Básica y Guardado en CSV (Dentro de Jupyter Notebook)

**Objetivo Principal:** Tener un flujo funcional dentro de un Jupyter Notebook que pueda:
1.  Leer configuraciones de búsqueda (keywords, parámetros).
2.  Ejecutar el scraper GOSOM de forma programática.
3.  Recibir los datos (CSV crudo).
4.  Aplicar transformaciones esenciales (limpieza, parseo de campos clave).
5.  Guardar los datos procesados en un nuevo archivo CSV.
6.  Realizar un EDA enfocado en Avalian sobre los datos obtenidos.
7.  Implementar logging básico a un archivo de texto.

### Hitos MVP (Desarrollo dentro de `notebooks/2_MVP_Scraping_Transform_CSV.ipynb`):

1.  **Configuración y EDA Inicial (Completado/En Progreso):**
    - [x] Setup de GOSOM (Docker Web UI) para pruebas iniciales.
    - [x] EDA básico sobre la salida de GOSOM (`notebooks/1_EDA_GOSOM_Avalian.ipynb`).
    - [ ] **Acción:** Finalizar el EDA enfocado en Avalian (inputs: CSV de GOSOM, outputs: insights y gráficos relevantes para prospectos Avalian).
2.  **Gestión de Configuración de Búsqueda:**
    - [ ] Crear archivos de configuración para keywords (`config/keywords_ciudad.csv`) y parámetros (`config/parameters_default.json`).
    - [ ] En el notebook MVP, implementar lógica para leer estas configuraciones.
3.  **Ejecución Programática del Scraper GOSOM:**
    - [ ] En el notebook MVP, usar `subprocess` para llamar al comando `docker run gosom/google-maps-scraper ...` (o el binario del fork si ya está disponible).
    - [ ] Pasar dinámicamente las keywords y parámetros leídos de los archivos de configuración.
    - [ ] Capturar la salida del scraper (asegurarse de que los CSVs se guarden en `data/raw/`).
4.  **Carga y Transformación Básica de Datos:**
    - [ ] En el notebook MVP, leer los CSVs crudos de `data/raw/` en DataFrames de Pandas.
    - [ ] Implementar funciones de transformación esenciales:
        - Selección de columnas relevantes para Avalian.
        - Limpieza básica (manejo de tipos, nulos en campos críticos).
        - Parseo de `complete_address` para extraer `city`, `street`, etc. (usando la función `extract_city_from_gmaps` ya desarrollada).
        - (Opcional MVP) Deduplicación simple si se ejecutan múltiples búsquedas que podrían solaparse.
5.  **Guardado de Datos Procesados:**
    - [ ] Guardar los DataFrames transformados como un nuevo archivo CSV en `data/processed/`.
    - [ ] Considerar un formato de nombre que indique la fuente y la fecha.
6.  **Logging Básico:**
    - [ ] Implementar logging simple a un archivo en `data/logs/agent_gmaps_mvp.log` usando el módulo `logging` de Python. Registrar inicio/fin de scraping, número de registros, errores básicos.

**Entregable del MVP:** Un Jupyter Notebook funcional que orquesta el proceso E-T-L (a CSV), con configuraciones externas y logging básico. Este notebook sirve como prueba de concepto y base para futuras iteraciones.

## Fase 2: Refactorización a Scripts Python Modulares y Carga a PostgreSQL

**Objetivo Principal:** Mover la lógica del notebook MVP a scripts Python reutilizables y comenzar la integración con la base de datos PostgreSQL de staging.

### Hitos:
1.  **Estructuración del Código en `src/`:**
    - [ ] Crear `src/scraper_module.py`: Mover la lógica de ejecución de GOSOM.
    - [ ] Crear `src/transformer_module.py`: Mover las funciones de transformación.
    - [ ] Crear `src/file_handler_module.py`: (Opcional) Lógica para manejar archivos CSV.
    - [ ] Crear un script principal (ej. `src/run_etl_gmaps_to_db.py`) que orqueste los módulos.
2.  **Integración con PostgreSQL:**
    - [ ] Definir el esquema final de las tablas en PostgreSQL para los datos de G উনিaps (ej. `companies_gmaps`, `contacts_gmaps` o directamente a las tablas `companies` y `contacts` del diseño del pipeline, mapeando los campos).
    - [ ] Crear `src/db_loader_module.py` con funciones para conectar (usando variables de entorno para `DATABASE_URL`) y cargar DataFrames a PostgreSQL (INSERT/UPDATE, manejo de duplicados a nivel de BD).
    - [ ] Modificar el script principal para usar `db_loader_module.py` en lugar de guardar en CSV procesado.
3.  **Mejoras en Logging y Configuración:**
    - [ ] Implementar un logging más estructurado en los scripts Python.
    - [ ] Asegurar que toda la configuración crítica (DB_URL, rutas, etc.) se gestione vía variables de entorno o un archivo de configuración central.
4.  **Tests Unitarios Iniciales:**
    - [ ] Escribir tests básicos para `transformer_module.py` y `db_loader_module.py`.

**Entregable Fase 2:** Scripts Python funcionales que realizan el ETL completo desde Google Maps hasta la base de datos PostgreSQL staging.

## Fase 3: API RESTful, Dockerización y Preparación para Orquestación (Hacia el Estado Ideal)

**Objetivo Principal:** Encapsular la lógica de los scripts en una API RESTful con FastAPI, dockerizar el agente y prepararlo para la integración con Argo, alineándose con el "Diseño Pipeline ETL".

### Hitos:
1.  **Desarrollo de API con FastAPI (`src/main_api.py`):**
    - [ ] Definir y implementar los endpoints (ej. `POST /api/v1/scrape` para iniciar una tarea ETL completa).
    - [ ] Usar Pydantic para validación de datos de entrada/salida.
    - [ ] Integrar la lógica de los módulos de `src/` en los endpoints.
    - [ ] Considerar tareas en background (FastAPI BackgroundTasks o Celery) para operaciones de scraping largas.
2.  **Dockerización:**
    - [ ] Crear `Dockerfile` para empaquetar la aplicación FastAPI y sus dependencias (incluyendo el scraper GOSOM si se integra directamente o se usa un fork compilado).
    - [ ] Construir y probar la imagen Docker.
3.  **Gestión de Estado de Tareas (si la API es asíncrona):**
    - [ ] Implementar un mecanismo simple para rastrear el estado de las tareas de scraping (ej. en memoria, o una tabla simple en la BD).
4.  **Mejoras en Tests:**
    - [ ] Escribir tests de integración para la API.
5.  **Documentación de la API:**
    - [ ] Asegurar que Swagger UI/Redoc estén funcionales y documenten la API.

**Entregable Fase 3:** Un agente Google Maps ETL dockerizado, controlable vía API REST, listo para ser desplegado y orquestado.

## Fase 4 y Posteriores: Despliegue, Orquestación, Monitoreo y Optimización Continua

-   Despliegue en Kubernetes (Civo).
-   Integración con Argo Workflows.
-   Implementación de logging centralizado y monitoreo avanzado.
-   Optimización de rendimiento y robustez.
-   (Opcional) Si el fork `Paniceres/google-maps-scraper-etl` se desarrolla significativamente, integrar esas mejoras (ej. salida directa a Python en lugar de CSV, o carga directa a BD desde el scraper Go si se implementa la funcionalidad de `-writer` para PostgreSQL).

---
```
