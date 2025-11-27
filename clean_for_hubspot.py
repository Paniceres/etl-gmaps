#!/usr/bin/env python3
"""
Script para limpiar los resultados de Google Maps Scraper
y prepararlos para importar a HubSpot para email marketing.

Uso:
    python clean_for_hubspot.py results.csv hubspot_ready.csv
"""

import csv
import re
import sys


def parse_address(full_address):
    """
    Divide la dirección completa en street_address, city, state.
    
    Formato esperado: "Calle Número, CÓDIGO_POSTAL Ciudad, Provincia"
    Ejemplo: "Av. Gral. Julio Argentino Roca 1984 Planta Alta, R8332 Gral. Roca, Río Negro"
    
    Returns:
        tuple: (street_address, city, state)
    """
    if not full_address or full_address == '{}':
        return ('', '', '')
    
    # Remover comillas extras si existen
    full_address = full_address.strip('"')
    
    # Dividir por comas
    parts = [p.strip() for p in full_address.split(',')]
    
    if len(parts) < 2:
        # Si no hay suficientes partes, retornar vacío
        return (full_address, '', '')
    
    street_address = parts[0]  # Primera parte antes de la primera coma
    
    # La segunda parte debería tener el código postal y la ciudad
    # Ejemplo: "R8332 Gral. Roca"
    if len(parts) >= 2:
        # Buscar patrón de código postal (letras y números al inicio)
        middle_part = parts[1].strip()
        # Remover el código postal (patrón común: R8332, C1234, etc.)
        city = re.sub(r'^[A-Z]\d+\s+', '', middle_part).strip()
        if not city:
            city = middle_part
    else:
        city = ''
    
    # La tercera parte es la provincia/estado
    state = parts[2].strip() if len(parts) >= 3 else ''
    
    return (street_address, city, state)


def clean_website(website):
    """Limpia el formato del sitio web."""
    if not website or website == '{}':
        return ''
    
    # Si el website viene en formato /url?q=http://...
    if website.startswith('/url?q='):
        match = re.search(r'q=([^&]+)', website)
        if match:
            return match.group(1)
    
    return website


def clean_csv(input_file, output_file):
    """
    Lee el CSV de resultados y crea un CSV limpio para HubSpot.
    
    Columnas de salida:
    - title: Nombre del negocio
    - category: Categoría/Tipo de negocio
    - street_address: Dirección de la calle
    - city: Ciudad
    - state: Provincia/Estado
    - website: Sitio web
    - phone: Teléfono
    - emails: Emails (si se extrajeron)
    - latitude: Latitud
    - longitude: Longitud
    """
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        
        # Definir columnas de salida
        fieldnames = [
            'title',
            'category',
            'street_address',
            'city',
            'state',
            'website',
            'phone',
            'emails',
            'latitude',
            'longitude'
        ]
        
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            # Parsear la dirección
            street_address, city, state = parse_address(row.get('address', ''))
            
            # Limpiar el website
            website = clean_website(row.get('website', ''))
            
            # Crear fila limpia
            clean_row = {
                'title': row.get('title', ''),
                'category': row.get('category', ''),
                'street_address': street_address,
                'city': city,
                'state': state,
                'website': website,
                'phone': row.get('phone', ''),
                'emails': row.get('emails', ''),
                'latitude': row.get('latitude', ''),
                'longitude': row.get('longitude', '')
            }
            
            writer.writerow(clean_row)
    
    print(f"✅ Archivo limpio creado: {output_file}")
    print(f"   Listo para importar a HubSpot")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Uso: python clean_for_hubspot.py <input.csv> <output.csv>")
        print("Ejemplo: python clean_for_hubspot.py results.csv hubspot_ready.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    clean_csv(input_file, output_file)
