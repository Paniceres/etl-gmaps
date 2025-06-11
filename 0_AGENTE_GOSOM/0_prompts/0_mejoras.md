
---
## 📄 2. `mejoras.md` (Solo lo Pendiente para el MVP)
# 🚀 Plan de Mejoras Pendientes - Agente GOSOM ETL (MVP)
## 📋 Tareas Pendientes


---

## 🎯 Próximos Pasos: Alcanzar el MVP

El objetivo del MVP es tener una interfaz funcional que permita:

1. Configurar y ejecutar un scraping.
2. Revisar los resultados básicos y filtrados.
3. Consolidar nuevos datos con el CSV Madre.
4. Generar chunks de leads listos para vendedores.

### Acciones Específicas

1. **Solucionar problema de escritura:**  
   Si persiste, aplicar edición manual en `app_streamlit.py` para integrar botones de consolidación y generación de chunks.

2. **Verificar flujo completo en la UI:**
   - Configurar y ejecutar scraping en Etapa 1.
   - Verificar resultados en Etapa 2.
   - Consolidar datos y generar chunks en Etapa 3.
   - Confirmar actualización de CSV Madre y creación correcta de chunks.

3. **Asegurar mensajes claros al usuario:**  
   Mensajes de éxito, error e información deben ser comprensibles y útiles.

---

## 🚀 Ideas para el Futuro

- Refinar deduplicación usando CID si necesario.
- Añadir más gráficos o visualizaciones en la Etapa 2.
- Integrar "Fast Mode" del scraper como opción en la UI.
- Conexcion a PostgreSQL.