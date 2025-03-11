#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto de entrada principal para la aplicación de Sura Scraper.
"""

import os
import argparse
from dotenv import load_dotenv

from app.api import create_app
from app.scraper import run_scraper

def parse_args():
    parser = argparse.ArgumentParser(description='Sura Scraper API')
    parser.add_argument('--extract', action='store_true', help='Ejecutar extracción')
    parser.add_argument('--term', type=str, default='seguros colectivos', help='Término de búsqueda')
    parser.add_argument('--max-results', type=int, default=5, help='Máximo número de resultados')
    parser.add_argument('--no-headless', action='store_true', help='Mostrar navegador durante la extracción')
    parser.add_argument('--port', type=int, default=8080, help='Puerto para la API')
    parser.add_argument('--debug', action='store_true', help='Ejecutar en modo debug')
    return parser.parse_args()

def main():
    # Cargar variables de entorno
    load_dotenv()
    
    # Parsear argumentos
    args = parse_args()
    
    # Si se solicita extracción, ejecutar scraper
    if args.extract:
        print(f"Ejecutando extracción para '{args.term}' (máx {args.max_results} resultados)")
        results = run_scraper(
            headless=not args.no_headless,
            search_term=args.term,
            max_results=args.max_results
        )
        print(f"Extracción completada: {len(results)} resultados")
    
    # Iniciar API
    app = create_app()
    port = int(os.environ.get('PORT', args.port))
    debug = os.environ.get('DEBUG', str(args.debug)).lower() in ('true', '1', 't')
    
    print(f"Iniciando API en puerto {port} (debug: {debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)

# Para compatibilidad con Gunicorn
app = create_app()

if __name__ == '__main__':
    main()