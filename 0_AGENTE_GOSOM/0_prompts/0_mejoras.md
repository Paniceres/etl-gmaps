# 🚀 Plan de Mejoras para Agente GOSOM ETL (Agosto 2025)

## 🔧 Colores del BrandKit
| Categoría       | HEX          | RGB         |
|-----------------|--------------|-------------|
| **Primary**     | `#F3C04F`    | `rgb(243,192,79)` |
| **Secondary 1** | `#3C1B43`    | `rgb(60,27,67)`   |
| **Secondary 2** | `#922D50`    | `rgb(146,45,80)`  |
| **Secondary 3** | `#4C2E05`    | `rgb(76,46,5)`    |

---

## 🎨 Mejoras Visuales y UX/UI

### [ ] Aplicar Tema Corporativo al Streamlit
**Prioridad:** Alta 🚨  
**Descripción:** Integrar colores del brandkit y logo en la interfaz.  
**Sugerencia:**  
- CSS personalizado y `st.image("logo.png")`.  
**Criterio:** Diseño/Branding  
**Archivos Afectados:** `app_streamlit.py`

---

### [ ] Rediseño de la Barra Lateral
**Prioridad:** Media 🟡  
**Descripción:** Organizar controles de configuración.  
**Sugerencia:**  
- Usar `st.expander()` y `st.columns()`.  
**Criterio:** UX/UI  
**Archivos Afectados:** `app_streamlit.py`

---

## ⚙️ Mejoras Técnicas

### [ ] Sistema de Registro de Jobs de Scraping
**Prioridad:** Alta 🚨  
**Descripción:** Crear `data/jobs/scrape_jobs.csv` para registrar parámetros y resultados.  
**Sugerencia:**  
- Columnas: `id,fecha,hora,ciudades,keywords,depth,filas_extraidas,error`.  
- Actualizar automáticamente al finalizar cada tarea.  
**Criterio:** Rendimiento/Seguimiento  
**Archivos Afectados:** `core_logic.py`, `app_streamlit.py`

---

### [ ] Deduplicación Automática
**Prioridad:** Alta 🚨  
**Descripción:** Evitar registros duplicados usando `link` + `title`.  
**Sugerencia:**  
- `pandas.drop_duplicates(subset=['link', 'title'])`.  
**Criterio:** Calidad de Datos  
**Archivos Afectados:** `transformer_module.py`

---

### [ ] Validación de Integridad de CSV
**Prioridad:** Media 🟡  
**Descripción:** Asegurar que los CSV tengan columnas obligatorias.  
**Sugerencia:**  
- Script de validación post-scraping con `pandas`.  
**Criterio:** Calidad de Datos  
**Archivos Afectados:** `core_logic.py`, `app_streamlit.py`

---

### [ ] Comparación de Datos Nuevos vs. CSV Principal
**Prioridad:** Media 🟡  
**Descripción:** Evitar duplicados al unir datos nuevos con el CSV principal.  
**Sugerencia:**  
- Script que compare `scrape_jobs.csv` con nuevos datos antes de guardar.  
**Criterio:** Calidad de Datos  
**Archivos Afectados:** `core_logic.py`, `app_streamlit.py`

---

## 📈 Roadmap Ejecutivo

### Fase 1: MVP (Completado 70%)
- [x] ETL básico en Jupyter Notebook  
- [ ] Configuración externa (`parameters_default.json`)  
- [ ] Logging estructurado  

### Fase 2: Modularización (En Progreso)
- [ ] Scripts Python para scraper, transformación y carga  
- [ ] Integración con CSV (`scrape_jobs.csv`)  

---

## 🛠️ Estado Actual de Mejoras

| Título | Prioridad | Estado | Justificación |
|--------|-----------|--------|---------------|
| Aplicar tema corporativo | ⚠️ Alta | [x] Completada | Implemented custom CSS and added logo in app_streamlit.py to apply corporate theme. |
| Registro automático de jobs | ⚠️ Alta | [x] Completada | Implemented CSV logging for job details in core_logic.py and app_streamlit.py. |
| Deduplicación por link+title | ⚠️ Alta | [x] Completada | Functionality for deduplication using link and title is implemented in transformer_module.py. |
| Rediseño de la Barra Lateral | 🟡 Media | [x] Completada | Sidebar controls organized using st.expander() and st.columns() in app_streamlit.py. |
| Validación de integridad de CSV | 🟡 Media | [x] Completada | Implemented pandas-based CSV integrity validation in core_logic.py and integrated into app_streamlit.py. |
| Mapa dinámico de resultados | 🟡 Media | [ ] Pendiente | No evidence of implementation for dynamic map visualization found. |
| Comparación de datos nuevos con CSV principal | 🟡 Media | [x] Completada | Implemented data comparison and duplicate removal before saving to CSV in core_logic.py and app_streamlit.py. |
| Exportar CSV con filtros dinámicos | 🟢 Baja | [ ] Pendiente | Future task from "Mejoras Futuras" section. |
| Optimizar tiempo de carga de datos | 🟢 Baja | [ ] Pendiente | Future task from "Mejoras Futuras" section. |

---

## 📌 Notas Adicionales
- **Logo:** Incluir en la cabecera de la app.
- **CSV Principal:** `data/jobs/scrape_jobs.csv` será el registro central.  
- **Próximo Paso:** Ejecutar prompt para implementar sistema de registro de jobs.

---

## 📄 Historial de Tareas Realizadas

| Título | Prioridad | Fecha | Descripción | Nota |
|--------|-----------|-------|-------------|------|
| Quitar logs antiguos y moverlos al final | Alta 🚨 | 2025-06-06 10:30 | Logs debajo de gráficos | Implementado en `app_streamlit.py` |
| Mostrar contadores de tiempo y filas | Alta 🚨 | 2025-06-06 14:20 | Contadores en tiempo real | Añadido en `app_streamlit.py` |
| Limpiar logs entre ejecuciones | Alta 🚨 | 2025-06-07 09:15 | Vaciar cola de logs antes de nueva ejecución | Implementado en `app_streamlit.py` |

*   **Aplicar tema corporativo**
    *   **Fecha de Completación:** 2024-07-30 10:00
    *   **Nota:** Custom CSS for theme colors and `st.image("logo.png")` were added to `app_streamlit.py` to apply the corporate theme.

*   **Registro automático de jobs**
    *   **Fecha de Completación:** 2024-07-30 10:05
    *   **Nota:** Added a `log_job` function to write job parameters and results to `data/jobs/scrape_jobs.csv`. This function is called after each job completion.

*   **Rediseño de la Barra Lateral**
    *   **Fecha de Completación:** 2024-07-30 10:15
    *   **Nota:** The sidebar in `app_streamlit.py` was reorganized using `st.expander()` and `st.columns()` to better group and present the configuration controls.

*   **Validación de integridad de CSV**
    *   **Fecha de Completación:** 2024-07-30 10:20
    *   **Nota:** A function was added to `core_logic.py` to validate mandatory columns in scraped CSVs using pandas, and this validation is now performed and reported to the user in `app_streamlit.py` after each scraping job.



---

## 📂 Estructura de Archivos

```
0_AGENTE_GOSOM/
├── app_streamlit.py
├── src/
│   ├── core_logic.py
│   └── transformer_module.py
├── data/
│   ├── logs/
│   ├── raw/
│   ├── processed/
│   └── jobs/
│       └── scrape_jobs.csv
├── config/
│   └── parameters_default.json
└── mejora.md
```

---

## 🧠 Consideraciones Finales

- **CSV como base de datos:** Reemplazar PostgreSQL por `scrape_jobs.csv` para evitar dependencias externas.
- **Rendimiento:** Priorizar optimización de lectura/escritura de CSV.
- **Seguridad:** Validar permisos de escritura en directorios críticos (`data/jobs/`).

