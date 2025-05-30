# Agente Google Maps ETL (GOSOM) para Proyecto Avalian

Este agente es responsable de extraer datos de Google Maps, transformarlos y prepararlos para su carga en la base de datos de staging del proyecto Avalian. Actualmente, se encuentra en fase de desarrollo MVP utilizando Jupyter Notebooks.

## Propósito
El objetivo principal de este agente es generar prospectos (empresas, profesionales, etc.) a partir de Google Maps para alimentar los equipos de ventas (humanos y de IA) de Avalian.

## Fase Actual: MVP con Jupyter Notebooks
La funcionalidad actual se centra en el notebook: `notebooks/2_MVP_Scraping_Transform_CSV.ipynb`.

Este notebook permite:
1.  Leer configuraciones de búsqueda (keywords, parámetros) desde la carpeta `config/`.
2.  Ejecutar el scraper `gosom/google-maps-scraper` (vía Docker) de forma programática.
3.  Almacenar los resultados crudos en `data/raw/`.
4.  Aplicar transformaciones básicas (limpieza, parseo de campos).
5.  Guardar los datos procesados en `data/processed/`.
6.  Realizar un EDA enfocado en Avalian sobre los datos extraídos.
7.  Registrar logs básicos en `data/logs/`.

## Configuración (para el MVP Notebook)

1.  **Instalar dependencias:**
    ```bash
    pip install pandas jupyter matplotlib seaborn
    ```
2.  **Asegurar que Docker esté corriendo.**
3.  **Configurar búsquedas:**
    *   Añadir/modificar archivos CSV en `config/` con las keywords (ej. `keywords_neuquen.csv`). Una keyword por línea.
    *   Ajustar parámetros en `config/parameters_default.json` (ej. lenguaje, profundidad de búsqueda).
4.  **Ejecutar el Notebook:**
    *   Abrir y ejecutar las celdas de `notebooks/2_MVP_Scraping_Transform_CSV.ipynb`.

## Estructura de Carpetas Relevante
-   `config/`: Archivos de configuración para las búsquedas.
-   `notebooks/`: Jupyter Notebooks para exploración, ejecución del MVP y análisis.
-   `data/raw/`: Salida CSV cruda del scraper GOSOM.
-   `data/processed/`: Salida CSV procesada y transformada.
-   `data/logs/`: Archivos de log del agente.

## Roadmap
Consultar el archivo `OBJETIVOS_AGENTE_MVP.md` para ver el plan de desarrollo detallado y las futuras fases.

## Datos Generados (CSV)
Los CSVs generados contienen información detallada de los listings de Google Maps. Las columnas principales incluyen (pero no se limitan a):
- `title`: Nombre del negocio.
- `category`: Categoría del negocio.
- `address` / `complete_address`: Dirección.
- `phone`: Número de teléfono.
- `website`: Sitio web.
- `review_count`, `review_rating`: Información de reseñas.
- `latitude`, `longitude`: Coordenadas.
- `parsed_city`: Ciudad extraída de la dirección.
*(Añadir más detalles a medida que el esquema de transformación se solidifique)*

---