# 0_AGENTE_GOSOM/0_prompts/0_Futuro.md

# Ideas para el Futuro del Agente GOSOM ETL

Aquí se listan ideas y posibles mejoras para futuras versiones del Agente GOSOM ETL, basadas en discusiones, la información del scraper original y oportunidades de optimización.


- Mejoras en la Etapa 2 (Revisión de Resultados): Explorar la adición de otras visualizaciones o formas de revisar los datos scrapeados (ej. gráficos de distribución por categoría, etc.).
- Validaciones y Feedback Adicional: Implementar validaciones más detalladas en la UI (ej. verificar si las ciudades seleccionadas existen en la configuración, si las keywords no están vacías antes de iniciar) y mejorar el feedback al usuario.
- Integrar el "Fast Mode" del Scraper: Evaluar la utilidad de integrar el 'Fast Mode' del scraper original (-fast-mode flag) como una opción en la UI, entendiendo que extrae menos datos pero más rápido para resultados cercanos. Determinar si los datos extraídos en este modo son suficientes para nuestros casos de uso actuales.
- Transición de Base de Datos (PostgreSQL): Aunque la estrategia actual es usar CSVs como base de datos, mantener en consideración la opción de integrar una base de datos más robusta como PostgreSQL en el futuro si la cantidad de datos o la complejidad de la gestión lo requieren, según lo mencionado en el README.md original.
- Mapa dinámico de resultados | 🟡 Media | [ ] Pendiente 

