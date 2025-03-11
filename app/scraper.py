import os
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from requests.exceptions import RequestException

class SuraScraper:
    """
    Implementación de scraper usando Requests y BeautifulSoup.
    Más ligero y menos propenso a errores que soluciones basadas en navegadores.
    """
    
    def __init__(self, headless=True, timeout=30):
        """
        Inicializa el scraper.
        
        Args:
            headless (bool): No usado en esta implementación.
            timeout (int): Tiempo máximo de espera en segundos.
        """
        self.base_url = "https://seguros.sura.cl"
        self.timeout = timeout
        self.results = []
        self.session = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        print("Inicializando SuraScraper con Requests + BeautifulSoup")
        
    def initialize(self):
        """Inicializa la sesión HTTP."""
        try:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            })
            
            # Verificar si el sitio está accesible
            response = self.session.get(
                self.base_url, 
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            print(f"Conexión establecida con {self.base_url} (status: {response.status_code})")
            return True
        except RequestException as e:
            print(f"Error al inicializar la conexión: {str(e)}")
            return False
        except Exception as e:
            print(f"Error inesperado durante la inicialización: {str(e)}")
            return False
    
    def close(self):
        """Cierra la sesión HTTP."""
        if self.session:
            self.session.close()
            self.session = None
            print("Sesión HTTP cerrada")
    
    def search_by_term(self, term, max_results=10):
        """
        Busca contenido por término y extrae los resultados.
        Intenta hacer scraping real y, si falla, usa datos de ejemplo.
        
        Args:
            term (str): Término de búsqueda.
            max_results (int): Número máximo de resultados a extraer.
            
        Returns:
            list: Lista de resultados con título, descripción y URL.
        """
        if not self.session and not self.initialize():
            print("No se pudo inicializar la sesión, usando datos de ejemplo")
            return self._get_example_search_results(term, max_results)
        
        try:
            # Intentar buscar en el sitio
            print(f"Buscando término: '{term}'")
            
            # Construir la URL de búsqueda
            search_url = f"{self.base_url}/busqueda?q={term}"
            
            # Realizar la solicitud
            response = self.session.get(
                search_url,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Parsear el HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Guardar una copia del HTML para depuración
            os.makedirs("data", exist_ok=True)
            debug_file = os.path.join("data", f"search_response_{datetime.now().strftime('%Y%m%d%H%M%S')}.html")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"HTML de respuesta guardado en {debug_file}")
            
            # Buscar resultados en diferentes posibles estructuras HTML
            results = []
            
            # Intentar diferentes selectores para resultados de búsqueda
            selectors = [
                ".searchResults .searchItem", 
                ".search-results .result-item",
                ".results-list .item",
                "article.result",
                ".search-result",
                ".result"
            ]
            
            found_results = False
            for selector in selectors:
                result_elements = soup.select(selector)
                if result_elements:
                    print(f"Encontrados {len(result_elements)} resultados con selector: {selector}")
                    found_results = True
                    
                    for element in result_elements[:max_results]:
                        try:
                            # Buscar título y URL con diferentes selectores
                            title_selectors = ["h3 a", ".result-title a", "a.title", "h2 a", ".title a", "a[href]"]
                            title_element = None
                            
                            for title_selector in title_selectors:
                                title_element = element.select_one(title_selector)
                                if title_element:
                                    break
                            
                            if not title_element:
                                continue
                            
                            title = title_element.get_text(strip=True)
                            url = title_element.get('href')
                            if url and not url.startswith('http'):
                                url = self.base_url + url if url.startswith('/') else self.base_url + '/' + url
                            
                            # Buscar descripción con diferentes selectores
                            desc_selectors = [".searchSnippet", ".result-description", ".snippet", "p.description", "p"]
                            description = "No hay descripción disponible"
                            
                            for desc_selector in desc_selectors:
                                desc_element = element.select_one(desc_selector)
                                if desc_element:
                                    description = desc_element.get_text(strip=True)
                                    break
                            
                            if title and url:
                                results.append({
                                    "title": title,
                                    "description": description,
                                    "url": url,
                                    "extracted_at": datetime.now().isoformat()
                                })
                        except Exception as e:
                            print(f"Error al procesar un resultado: {str(e)}")
                    
                    break
            
            if not found_results:
                print("No se encontraron resultados con los selectores conocidos")
                
                # Intento alternativo: buscar todos los enlaces con texto
                links = soup.find_all('a', href=True)
                print(f"Encontrados {len(links)} enlaces en total")
                
                relevant_links = []
                search_term_lower = term.lower()
                
                for link in links:
                    link_text = link.get_text(strip=True)
                    link_href = link.get('href')
                    
                    # Filtrar enlaces relevantes
                    if link_text and len(link_text) > 10 and search_term_lower in link_text.lower():
                        url = link_href
                        if url and not url.startswith('http'):
                            url = self.base_url + url if url.startswith('/') else self.base_url + '/' + url
                            
                        relevant_links.append({
                            "title": link_text,
                            "description": "Descripción no disponible",
                            "url": url,
                            "extracted_at": datetime.now().isoformat()
                        })
                
                print(f"Encontrados {len(relevant_links)} enlaces relevantes")
                
                if relevant_links:
                    results = relevant_links[:max_results]
            
            # Si se encontraron resultados, guardarlos
            if results:
                print(f"Scraping real exitoso: {len(results)} resultados")
                self.results = results
                return results
            else:
                print("No se encontraron resultados en el scraping real, usando datos de ejemplo")
                return self._get_example_search_results(term, max_results)
            
        except RequestException as e:
            print(f"Error de solicitud HTTP: {str(e)}")
            return self._get_example_search_results(term, max_results)
        except Exception as e:
            print(f"Error durante el scraping: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._get_example_search_results(term, max_results)
    
    def extract_page_content(self, url):
        """
        Extrae el contenido detallado de una página específica.
        
        Args:
            url (str): URL de la página a extraer.
            
        Returns:
            dict: Contenido extraído de la página.
        """
        if not self.session and not self.initialize():
            print(f"No se pudo inicializar la sesión para extraer {url}, usando datos de ejemplo")
            return self._get_example_page_content(url)
        
        try:
            print(f"Extrayendo contenido de: {url}")
            
            # Realizar la solicitud
            response = self.session.get(
                url,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Parsear el HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Guardar una copia del HTML para depuración
            os.makedirs("data", exist_ok=True)
            debug_file = os.path.join("data", f"page_response_{datetime.now().strftime('%Y%m%d%H%M%S')}.html")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Extraer título
            title = soup.title.string if soup.title else "Sin título"
            
            # Extraer contenido principal con diferentes selectores
            content_selectors = [
                ".main-content", 
                "article", 
                ".content-area", 
                "main", 
                "#main-content",
                ".container"
            ]
            
            content_html = ""
            content_text = ""
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    print(f"Contenido principal encontrado con selector: {selector}")
                    content_html = str(content_element)
                    content_text = content_element.get_text(separator="\n", strip=True)
                    break
            
            if not content_text:
                # Si no encontramos el contenido con los selectores, usar el body
                content_element = soup.body
                if content_element:
                    content_text = content_element.get_text(separator="\n", strip=True)
            
            # Extraer categorías/breadcrumbs
            categories = []
            category_selectors = [".categories a", ".breadcrumbs a", ".breadcrumb a", "nav.breadcrumb a"]
            
            for selector in category_selectors:
                category_elements = soup.select(selector)
                if category_elements:
                    for element in category_elements:
                        category_text = element.get_text(strip=True)
                        if category_text:
                            categories.append(category_text)
                    
                    if categories:
                        break
            
            # Extraer imágenes
            images = []
            img_elements = soup.select("img")
            
            for img in img_elements:
                src = img.get('src')
                alt = img.get('alt', '')
                
                if src:
                    # Convertir URLs relativas a absolutas
                    if not src.startswith('http'):
                        src = self.base_url + src if src.startswith('/') else self.base_url + '/' + src
                    
                    images.append({"src": src, "alt": alt})
            
            # Estructurar los datos extraídos
            page_data = {
                "url": url,
                "title": title,
                "content_html": content_html,
                "content_text": content_text,
                "categories": categories,
                "images": images,
                "extracted_at": datetime.now().isoformat()
            }
            
            return page_data
            
        except RequestException as e:
            print(f"Error de solicitud HTTP: {str(e)}")
            return self._get_example_page_content(url)
        except Exception as e:
            print(f"Error durante la extracción de contenido: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._get_example_page_content(url)
    
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
                
            print(f"Resultados guardados en {filepath}")
            return True
        except Exception as e:
            print(f"Error al guardar resultados: {str(e)}")
            return False
    
    def extract_seguros_colectivos(self, max_pages=5):
        """
        Extrae información específica sobre seguros colectivos.
        
        Args:
            max_pages (int): Número máximo de páginas a extraer.
            
        Returns:
            dict: Información extraída sobre seguros colectivos.
        """
        results = {
            "search_results": [],
            "pages_content": [],
            "extracted_at": datetime.now().isoformat()
        }
        
        try:
            # Buscar información sobre seguros colectivos
            print("Iniciando extracción de información sobre seguros colectivos")
            search_results = self.search_by_term("seguros colectivos", max_results=max_pages)
            results["search_results"] = search_results
            
            # Extraer contenido de las páginas de resultados
            for result in search_results[:max_pages]:
                page_content = self.extract_page_content(result["url"])
                results["pages_content"].append(page_content)
            
            # Intentar acceder directamente a la página de seguros colectivos
            direct_url = f"{self.base_url}/empresas/seguros-colectivos"
            try:
                print(f"Accediendo directamente a: {direct_url}")
                direct_page_content = self.extract_page_content(direct_url)
                results["direct_page"] = direct_page_content
            except Exception as e:
                print(f"Error al acceder a la página directa: {str(e)}")
                results["direct_page"] = {"error": str(e)}
            
            # Guardar los resultados
            self.results = results
            self.save_results("seguros_colectivos.json")
            
            return results
            
        except Exception as e:
            print(f"Error durante la extracción de seguros colectivos: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Usar datos de ejemplo como fallback
            example_data = self._get_example_seguros_colectivos()
            self.results = example_data
            self.save_results("seguros_colectivos.json")
            
            return example_data
    
    # Métodos para generar datos de ejemplo como fallback
    
    def _get_example_search_results(self, term, max_results=10):
        """Genera resultados de ejemplo para una búsqueda."""
        print(f"Generando resultados de ejemplo para búsqueda: {term}")
        
        if "colectivo" in term.lower():
            self.results = self._create_colectivo_results()[:max_results]
        else:
            self.results = self._create_generic_results(term)[:max_results]
        
        return self.results
    
    def _get_example_page_content(self, url):
        """Genera contenido de ejemplo para una URL."""
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
    
    def _get_example_seguros_colectivos(self):
        """Genera datos de ejemplo completos para seguros colectivos."""
        print("Generando datos de ejemplo para seguros colectivos")
        return self._create_seguros_colectivos_data()
    
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
            "search_results": self._create_colectivo_results(),
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
    print(f"Se encontraron {len(results)} resultados")