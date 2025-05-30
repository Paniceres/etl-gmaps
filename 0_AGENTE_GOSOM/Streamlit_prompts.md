Prompts Específicos (Iterativos):
Prompt para la Estructura Básica y Sidebar:
"Basado en la especificación, genera el código Streamlit inicial para:
1. El título de la aplicación: 'Agente GOSOM ETL'.
2. Una barra lateral con el título 'Configurar Nueva Tarea de Scraping'.
3. Dentro de la sidebar, un widget `st.multiselect` para 'Seleccionar Ciudad(es) a Procesar'. Las opciones deben cargarse dinámicamente desde las claves de un diccionario `GMAPS_COORDINATES` (puedes simular este diccionario por ahora, ej. `{'neuquen': {...}, 'general_roca': {...}}`).
4. Un widget `st.number_input` para 'Profundidad de Búsqueda', con valor por defecto 2, min 1, max 20.
5. Un widget `st.checkbox` para '¿Extraer Emails?', con valor por defecto True.
6. Un botón `st.button` con el label 'Iniciar Scraping'.
Por ahora, al presionar el botón, solo imprime los valores seleccionados."
Use code with caution.
Prompt para la Gestión Dinámica de Keywords:
"Ahora, expande la sidebar. Cuando se selecciona una o más ciudades en el multiselect:
1. Para cada ciudad seleccionada, muestra un `st.text_area`.
2. El label del text_area debe ser 'Keywords para [Nombre de la Ciudad]'.
3. El contenido inicial del text_area debe cargarse usando la función `load_keywords_from_csv(nombre_ciudad)` (asume que esta función existe y devuelve una lista de strings; convierte la lista a un string con saltos de línea para el text_area).
4. Permite que el usuario edite estas keywords.
(Opcional avanzado para después: cómo guardar las keywords editadas de vuelta al archivo CSV)."
Use code with caution.
Prompt para la Lógica de Ejecución del Scraping (al presionar el botón):
"Cuando se presiona el botón 'Iniciar Scraping':
1. Para cada ciudad seleccionada y sus keywords (obtenidas del text_area correspondiente):
    a. Muestra un `st.spinner(f'Scraping para {ciudad} en progreso...')`.
    b. Llama a la función `run_gmaps_scraper_docker(lista_keywords, ciudad, profundidad, extraer_emails_flag)`. Asume que esta función existe y devuelve la ruta al archivo CSV crudo generado, o None si falla. (Necesitarás adaptar la firma de `run_gmaps_scraper_docker` para tomar el flag de extraer_emails).
    c. Muestra un mensaje de éxito o error usando `st.success` o `st.error`.
    d. Almacena las rutas de los archivos CSV crudos generados.
(Por ahora, no te preocupes por el log en tiempo real, solo el spinner y el mensaje final)."
Use code with caution.
Ajuste Necesario en run_gmaps_scraper_docker (en tu notebook o futuro core_logic.py):
Deberás modificar la función para que tome un parámetro extract_emails=True/False y añada/quite el flag -email del docker_command correspondientemente.
Prompt para Carga y Transformación de Datos (después del scraping):
"Después de que todas las tareas de scraping hayan finalizado (o simulado):
1. Usa las rutas de los archivos CSV crudos recolectados.
2. Para cada archivo, lee el CSV en un DataFrame de Pandas (usando `gmaps_column_names` predefinida).
3. Llama a la función `transform_gmaps_data(df_crudo, ciudad_origen)` (asume que existe).
4. Concatena todos los DataFrames procesados en un único DataFrame final.
5. Muestra una vista previa de este DataFrame final en el área principal usando `st.dataframe(df_final.head())`.
6. Añade un botón `st.download_button` para descargar este DataFrame final como 'gmaps_prospectos_consolidados.csv'."
Use code with caution.
Prompt para la Pestaña de Resumen/EDA:
"En el área principal, añade una sección o pestaña para 'Resumen y Estadísticas'.
1. Si el DataFrame final procesado no está vacío:
    a. Muestra el total de prospectos con `st.metric`.
    b. Calcula y muestra el total de prospectos con email y con sitio web.
    c. Muestra un `st.bar_chart` con el conteo de prospectos por `search_origin_city`.
    d. Muestra un `st.bar_chart` con las top 5 `category`."
Use code with caution.
Prompt para Mostrar Logs (versión simple post-ejecución):
"En el área principal, después de que el scraping finalice, muestra las últimas 100 líneas (o todo el contenido si es corto) del archivo de log `agent_gmaps_mvp.log`. Puedes usar `st.text_area` o `st.code`."