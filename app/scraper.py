import os
import json
import time
from datetime import datetime
from pathlib import Path
import asyncio
import nest_asyncio

# Aplicar nest_asyncio para permitir ejecutar loops anidados
try:
    nest_asyncio.apply()
except:
    print("No se pudo aplicar nest_asyncio, continuando sin él")

# Variable global para mantener un event loop por thread
thread_local_event_loops = {}

class SuraScraper:
    """
    Versión simplificada del scraper que devuelve datos de ejemplo de alta calidad.
    """
    
    def __init__(self, headless=True, timeout=30):
        """
        Inicializa el scraper.
        
        Args:
            headless (bool): No usado en esta versión simplificada.
            timeout (int): No usado en esta versión simplificada.
        """
        self.base_url = "https://seguros.sura.cl"
        self.results = []
        print("Inicializando SuraScraper en modo simplificado (datos de ejemplo)")
        
    def initialize(self):
        """Inicializa el scraper (simulado)."""
        print("Inicialización del scraper simulada correctamente")
        return True
    
    def close(self):
        """Cierra el scraper (simulado)."""
        print("Cierre del scraper simulado correctamente")
    
    def search_by_term(self, term, max_results=10):
        """
        Devuelve resultados de ejemplo para el término de búsqueda.
        
        Args:
            term (str): Término de búsqueda.
            max_results (int): Número máximo de resultados a devolver.
            
        Returns:
            list: Lista de resultados con título, descripción y URL.
        """
        print(f"Generando resultados de ejemplo para búsqueda: {term}")
        
        if "colectivo" in term.lower():
            self.results = self._create_colectivo_results()[:max_results]
        else:
            self.results = self._create_generic_results(term)[:max_results]
        
        return self.results
    
    def extract_page_content(self, url):
        """
        Devuelve contenido de ejemplo para una URL.
        
        Args:
            url (str): URL para la cual generar contenido de ejemplo.
            
        Returns:
            dict: Contenido de ejemplo para la URL.
        """
        print(f"Generando contenido de ejemplo para URL: {url}")
        
        # Extraer el nombre de la página de la URL
        page_name = url.split('/')[-1].replace('-', ' ').capitalize()
        if not page_name:
            page_name = "Seguros Sura"
        
        return {
            "url": url,
            "title": f"{page_name} | Seguros Sura Chile",
            "content_html": f"<div><h1>{page_name}</h1><p>Información de ejemplo sobre {page_name} en Seguros Sura Chile.</p></div>",
            "content_text": f"{page_name}\n\nInformación de ejemplo sobre {page_name} en Seguros Sura Chile.",
            "categories": ["Seguros", "Empresas", "Colectivos"],
            "images": [
                {"src": "https://seguros.sura.cl/logo.png", "alt": "Logo Sura"}
            ],
            "extracted_at": datetime.now().isoformat()
        }
    
    def save_results(self, filename="sura_results.json"):
        """
        Guarda los resultados en un archivo JSON.
        
        Args:
            filename (str): Nombre del archivo para guardar los resultados.
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        try:
            # Asegurar que la carpeta data existe
            os.makedirs("data", exist_ok=True)
            
            filepath = os.path.join("data", filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
                
            print(f"Resultados de ejemplo guardados en {filepath}")
            return True
        except Exception as e:
            print(f"Error al guardar resultados: {str(e)}")
            return False
    
    def extract_seguros_colectivos(self, max_pages=5):
        """
        Devuelve datos de ejemplo para seguros colectivos.
        
        Args:
            max_pages (int): No usado en esta versión simplificada.
            
        Returns:
            dict: Información de ejemplo sobre seguros colectivos.
        """
        print("Generando datos de ejemplo para seguros colectivos")
        
        results = self._create_seguros_colectivos_data()
        
        # Guardar los resultados
        self.results = results
        self.save_results("seguros_colectivos.json")
        
        return results
    
    def _create_colectivo_results(self):
        """Crea resultados de ejemplo para búsquedas relacionadas con seguros colectivos."""
        return [
            {
                "title": "Seguros Colectivos para Empresas | Sura",
                "description": "Protege a tus colaboradores con planes de salud, vida y ahorro a precios preferenciales. Nuestros seguros colectivos ofrecen beneficios exclusivos para empresas de todos los tamaños.",
                "url": "https://seguros.sura.cl/empresas/seguros-colectivos",
                "extracted_at": datetime.now().isoformat()
            },
            {
                "title": "Seguros de Vida Colectivos | Sura",
                "description": "El seguro de vida colectivo protege a tus colaboradores con coberturas por fallecimiento, invalidez y enfermedades graves. Incluye beneficios adicionales como asistencia funeral y adelanto de capital.",
                "url": "https://seguros.sura.cl/empresas/seguros-colectivos/vida",
                "extracted_at": datetime.now().isoformat()
            },
            {
                "title": "Seguros de Salud Colectivos | Sura",
                "description": "Ofrece acceso a los mejores centros médicos con reembolsos por gastos médicos, cobertura dental y beneficios de medicamentos. Planes personalizados según las necesidades de tu empresa.",
                "url": "https://seguros.sura.cl/empresas/seguros-colectivos/salud",
                "extracted_at": datetime.now().isoformat()
            },
            {
                "title": "Planes de Ahorro Colectivos | Sura",
                "description": "Facilita a tus colaboradores acumular un capital a través de aportes sistemáticos, con beneficios tributarios para empresas. Planes de inversión con rentabilidad competitiva.",
                "url": "https://seguros.sura.cl/empresas/seguros-colectivos/ahorro",
                "extracted_at": datetime.now().isoformat()
            },
            {
                "title": "Preguntas Frecuentes sobre Seguros Colectivos | Sura",
                "description": "Resolvemos tus dudas sobre la contratación, coberturas y beneficios de los seguros colectivos. Información clara sobre cómo funcionan los planes para empresas.",
                "url": "https://seguros.sura.cl/empresas/seguros-colectivos/preguntas-frecuentes",
                "extracted_at": datetime.now().isoformat()
            }
        ]
    
    def _create_generic_results(self, term):
        """Crea resultados de ejemplo para búsquedas genéricas."""
        term_clean = term.lower().replace(" ", "-")
        return [
            {
                "title": f"Resultados para: {term} | Sura",
                "description": f"Información sobre {term} disponible en Seguros Sura Chile.",
                "url": f"https://seguros.sura.cl/busqueda?q={term_clean}",
                "extracted_at": datetime.now().isoformat()
            },
            {
                "title": f"Seguros de {term.capitalize()} | Sura",
                "description": f"Conoce nuestras soluciones de seguros relacionadas con {term}.",
                "url": f"https://seguros.sura.cl/productos/{term_clean}",
                "extracted_at": datetime.now().isoformat()
            },
            {
                "title": f"Servicio al cliente - {term.capitalize()} | Sura",
                "description": f"Consulta información sobre nuestros servicios de {term} para clientes.",
                "url": f"https://seguros.sura.cl/servicio-cliente/{term_clean}",
                "extracted_at": datetime.now().isoformat()
            }
        ]
    
    def _create_seguros_colectivos_data(self):
        """Crea datos de ejemplo detallados para seguros colectivos."""
        return {
            "search_results": [
                {
                    "title": "Seguros Colectivos para Empresas | Sura",
                    "description": "Protege a tus colaboradores con planes de salud, vida y ahorro a precios preferenciales. Nuestros seguros colectivos ofrecen beneficios exclusivos para empresas de todos los tamaños.",
                    "url": "https://seguros.sura.cl/empresas/seguros-colectivos",
                    "extracted_at": datetime.now().isoformat()
                },
                {
                    "title": "Seguros de Vida Colectivos | Sura",
                    "description": "El seguro de vida colectivo protege a tus colaboradores con coberturas por fallecimiento, invalidez y enfermedades graves. Incluye beneficios adicionales como asistencia funeral y adelanto de capital.",
                    "url": "https://seguros.sura.cl/empresas/seguros-colectivos/vida",
                    "extracted_at": datetime.now().isoformat()
                },
                {
                    "title": "Seguros de Salud Colectivos | Sura",
                    "description": "Ofrece acceso a los mejores centros médicos con reembolsos por gastos médicos, cobertura dental y beneficios de medicamentos. Planes personalizados según las necesidades de tu empresa.",
                    "url": "https://seguros.sura.cl/empresas/seguros-colectivos/salud",
                    "extracted_at": datetime.now().isoformat()
                },
                {
                    "title": "Planes de Ahorro Colectivos | Sura",
                    "description": "Facilita a tus colaboradores acumular un capital a través de aportes sistemáticos, con beneficios tributarios para empresas. Planes de inversión con rentabilidad competitiva.",
                    "url": "https://seguros.sura.cl/empresas/seguros-colectivos/ahorro",
                    "extracted_at": datetime.now().isoformat()
                },
                {
                    "title": "Preguntas Frecuentes sobre Seguros Colectivos | Sura",
                    "description": "Resolvemos tus dudas sobre la contratación, coberturas y beneficios de los seguros colectivos. Información clara sobre cómo funcionan los planes para empresas.",
                    "url": "https://seguros.sura.cl/empresas/seguros-colectivos/preguntas-frecuentes",
                    "extracted_at": datetime.now().isoformat()
                }
            ],
            "pages_content": [
                {
                    "url": "https://seguros.sura.cl/empresas/seguros-colectivos",
                    "title": "Seguros Colectivos para Empresas | Sura Chile",
                    "content_html": "<div class='main-content'><h1>Seguros Colectivos</h1><p>En SURA entendemos que el bienestar de tus colaboradores es fundamental. Por eso, te ofrecemos soluciones de protección colectiva que se adaptan a las necesidades de tu empresa, sin importar su tamaño.</p><p>Nuestros seguros colectivos brindan coberturas de calidad a precios preferenciales, además de beneficios exclusivos para tus empleados y sus familias.</p></div>",
                    "content_text": "Seguros Colectivos\n\nEn SURA entendemos que el bienestar de tus colaboradores es fundamental. Por eso, te ofrecemos soluciones de protección colectiva que se adaptan a las necesidades de tu empresa, sin importar su tamaño.\n\nNuestros seguros colectivos brindan coberturas de calidad a precios preferenciales, además de beneficios exclusivos para tus empleados y sus familias.",
                    "categories": ["Empresas", "Seguros Colectivos"],
                    "images": [
                        {"src": "https://seguros.sura.cl/images/colectivos-banner.jpg", "alt": "Equipo de trabajo en oficina"}
                    ],
                    "extracted_at": datetime.now().isoformat()
                },
                {
                    "url": "https://seguros.sura.cl/empresas/seguros-colectivos/vida",
                    "title": "Seguros de Vida Colectivos | Sura Chile",
                    "content_html": "<div class='main-content'><h1>Seguro de Vida Colectivo</h1><p>Protege a tus colaboradores y sus familias con nuestro seguro de vida colectivo, que ofrece tranquilidad financiera ante eventos inesperados.</p><h2>Coberturas</h2><ul><li>Fallecimiento por cualquier causa</li><li>Invalidez total y permanente</li><li>Enfermedades graves</li><li>Gastos funerarios</li></ul></div>",
                    "content_text": "Seguro de Vida Colectivo\n\nProtege a tus colaboradores y sus familias con nuestro seguro de vida colectivo, que ofrece tranquilidad financiera ante eventos inesperados.\n\nCoberturas\n• Fallecimiento por cualquier causa\n• Invalidez total y permanente\n• Enfermedades graves\n• Gastos funerarios",
                    "categories": ["Empresas", "Seguros Colectivos", "Vida"],
                    "images": [
                        {"src": "https://seguros.sura.cl/images/vida-colectivo.jpg", "alt": "Familia protegida"}
                    ],
                    "extracted_at": datetime.now().isoformat()
                },
                {
                    "url": "https://seguros.sura.cl/empresas/seguros-colectivos/salud",
                    "title": "Seguros de Salud Colectivos | Sura Chile",
                    "content_html": "<div class='main-content'><h1>Seguro de Salud Colectivo</h1><p>Ofrece a tus colaboradores acceso a atención médica de calidad con nuestro seguro de salud colectivo.</p><h2>Beneficios</h2><ul><li>Reembolso de gastos médicos</li><li>Cobertura dental</li><li>Medicamentos con descuento</li><li>Maternidad</li><li>Consultas médicas</li></ul></div>",
                    "content_text": "Seguro de Salud Colectivo\n\nOfrece a tus colaboradores acceso a atención médica de calidad con nuestro seguro de salud colectivo.\n\nBeneficios\n• Reembolso de gastos médicos\n• Cobertura dental\n• Medicamentos con descuento\n• Maternidad\n• Consultas médicas",
                    "categories": ["Empresas", "Seguros Colectivos", "Salud"],
                    "images": [
                        {"src": "https://seguros.sura.cl/images/salud-colectivo.jpg", "alt": "Atención médica"}
                    ],
                    "extracted_at": datetime.now().isoformat()
                },
            ],
            "direct_page": {
                "url": "https://seguros.sura.cl/empresas/seguros-colectivos",
                "title": "Seguros Colectivos Empresariales | Sura Chile",
                "content_html": "<div class='main-content'><h1>Seguros Colectivos</h1><p>SURA ofrece seguros colectivos diseñados para brindar protección integral a los colaboradores de tu empresa.</p><h2>Nuestras soluciones</h2><ul><li>Seguro de Vida Colectivo</li><li>Seguro de Salud Colectivo</li><li>Plan de Ahorro Colectivo</li></ul><p>Contacta a nuestros ejecutivos especializados para diseñar un plan a la medida de tu empresa.</p></div>",
                "content_text": "Seguros Colectivos\n\nSURA ofrece seguros colectivos diseñados para brindar protección integral a los colaboradores de tu empresa.\n\nNuestras soluciones\n• Seguro de Vida Colectivo\n• Seguro de Salud Colectivo\n• Plan de Ahorro Colectivo\n\nContacta a nuestros ejecutivos especializados para diseñar un plan a la medida de tu empresa.",
                "categories": ["Empresas", "Seguros Colectivos"],
                "images": [
                    {"src": "https://seguros.sura.cl/images/empresas-colectivos.jpg", "alt": "Ejecutivos de negocios"}
                ],
                "extracted_at": datetime.now().isoformat()
            },
            "extracted_at": datetime.now().isoformat()
        }

# Función para ejecutar el scraper independientemente
def run_scraper(headless=True, search_term="seguros colectivos", max_results=5):
    scraper = SuraScraper(headless=headless)
    try:
        scraper.initialize()
        results = scraper.search_by_term(search_term, max_results=max_results)
        scraper.save_results()
        return results
    finally:
        scraper.close()

if __name__ == "__main__":
    # Ejecutar una prueba rápida si se llama directamente
    results = run_scraper(headless=False)
    print(f"Se encontraron {len(results)} resultados de ejemplo")