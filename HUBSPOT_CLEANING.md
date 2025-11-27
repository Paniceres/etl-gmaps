# Script de Limpieza para HubSpot

Este script limpia y formatea los resultados del Google Maps Scraper para importarlos fácilmente a HubSpot.

## Uso

```bash
python3 clean_for_hubspot.py data/temp/archivo_raw.csv data/clean/archivo_hubspot.csv
```

## ¿Qué hace?

1. **Elimina columnas innecesarias** - Mantiene solo lo esencial para email marketing
2. **Divide direcciones** - Separa en: calle, ciudad, provincia
3. **Limpia URLs** - Formatea sitios web correctamente
4. **Genera CSV compatible** - Listo para importar a HubSpot

## Columnas de salida

- `title` - Nombre del negocio
- `category` - Tipo/categoría
- `street_address` - Dirección de la calle
- `city` - Ciudad
- `state` - Provincia/Estado
- `website` - Sitio web
- `phone` - Teléfono
- `emails` - Emails extraídos
- `latitude` - Latitud
- `longitude` - Longitud

## Ejemplo

### Entrada (results.csv)
```csv
input_id,link,title,category,address,...
uuid,https://...,Estudio Jurídico,"Law firm","Av. Roca 123, R8332 Gral. Roca, Río Negro",...
```

### Salida (hubspot_ready.csv)
```csv
title,category,street_address,city,state,website,phone,emails,latitude,longitude
Estudio Jurídico,Law firm,Av. Roca 123,Gral. Roca,Río Negro,http://...,0298-123,,-39.02,-67.57
```

## Importar a HubSpot

1. Ve a **Contacts** → **Import**
2. Sube `hubspot_ready.csv`
3. Mapea las columnas:
   - `title` → Company Name
   - `street_address` → Street Address
   - `city` → City
   - `state` → State/Region
   - `phone` → Phone Number
   - `website` → Website
   - `emails` → Email (si existe)
