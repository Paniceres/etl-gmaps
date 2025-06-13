# 0_AGENTE_GOSOM/0_prompts/0_Futuro.md

# Ideas para el Futuro del Agente GOSOM ETL

Aquí se listan ideas y posibles mejoras para futuras versiones del Agente GOSOM ETL, basadas en discusiones, la información del scraper original y oportunidades de optimización.


- Mejoras en la Etapa 2 (Revisión de Resultados): Explorar la adición de otras visualizaciones o formas de revisar los datos scrapeados (ej. gráficos de distribución por categoría, etc.).
- Validaciones y Feedback Adicional: Implementar validaciones más detalladas en la UI (ej. verificar si las ciudades seleccionadas existen en la configuración, si las keywords no están vacías antes de iniciar) y mejorar el feedback al usuario.
- Integrar el "Fast Mode" del Scraper: Evaluar la utilidad de integrar el 'Fast Mode' del scraper original (-fast-mode flag) como una opción en la UI, entendiendo que extrae menos datos pero más rápido para resultados cercanos. Determinar si los datos extraídos en este modo son suficientes para nuestros casos de uso actuales.
- Transición de Base de Datos (PostgreSQL): Aunque la estrategia actual es usar CSVs como base de datos, mantener en consideración la opción de integrar una base de datos más robusta como PostgreSQL en el futuro si la cantidad de datos o la complejidad de la gestión lo requieren, según lo mencionado en el README.md original.
- Mapa dinámico de resultados | 🟡 Media | [ ] Pendiente 

## Mejoras Futuras Sugeridas

- **Manejo de Errores más Detallado:** Implementar un manejo de errores más granular en `run_gmaps_scraper_docker_core` para capturar y reportar distintos tipos de fallos del proceso Docker o del scraper GOSOM.
- **Estrategia Robusta para Líneas CSV Incorrectas:** Mejorar el manejo de líneas incorrectas en los archivos CSV crudos (`on_bad_lines='warn'`) para asegurar la integridad de los datos, posiblemente omitiendo o intentando corregir líneas problemáticas.
- **Tamaño de Chunk Configurable:** Hacer que el tamaño de los chunks generados en `generate_lead_chunks` sea un parámetro configurable, idealmente a través del archivo `parameters_default.json`.
- **Comunicación Segura entre Hilos y Streamlit:** Implementar mecanismos de comunicación más seguros y robustos entre el hilo de scraping y la interfaz de Streamlit, evitando el acceso directo a `st.session_state` desde el hilo para operaciones que modifiquen el estado de la UI.





