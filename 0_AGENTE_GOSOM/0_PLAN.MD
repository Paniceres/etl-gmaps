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
