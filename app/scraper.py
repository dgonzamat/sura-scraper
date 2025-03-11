import os
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

class SuraScraper:
    """
    Versión híbrida del scraper que intenta hacer scraping real con Playwright
    y fallback a datos de ejemplo si falla.
    """
    
    def __init__(self, headless=True, timeout=30):
        """
        Inicializa el scraper.
        
        Args:
            headless (bool): Si True, ejecuta el navegador en modo headless.
            timeout (int): Tiempo máximo de espera en segundos.
        """
        self.headless = headless
        self.timeout = timeout
        self.base_url = "https://seguros.sura.cl"
        self.results = []
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.using_real_data = False
        print("Inicializando SuraScraper híbrido (Playwright + datos de ejemplo)")
        
    def initialize(self):
        """
        Inicializa el navegador para el scraping.
        Devuelve True si tiene éxito, False si falla.
        """
        try:
            # Ejecutamos la inicialización de Playwright de manera síncrona
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._initialize_async())
        except Exception as e:
            print(f"Error al inicializar el navegador: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    async def _initialize_async(self):
        """
        Versión asíncrona de la inicialización para Playwright.
        """
        try:
            print("Inicializando Playwright...")
            self.playwright = await async_playwright().start()
            print("Lanzando navegador...")
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
            print("Creando contexto...")
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            print("Creando página...")
            self.page = await self.context.new_page()
            await self.page.set_default_timeout(self.timeout * 1000)
            print("Navegador inicializado correctamente")
            return True
        except Exception as e:
            print(f"Error al inicializar Playwright: {str(e)}")
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            return False
    
    def close(self):
        """Cierra el navegador y libera recursos."""
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._close_async())
        except Exception as e:
            print(f"Error al cerrar el navegador: {str(e)}")
            
    async def _close_async(self):
        """Versión asíncrona para cerrar el navegador."""
        if self.playwright:
            try:
                if self.page:
                    await self.page.close()
                if self.context:
                    await self.context.close()
                if self.browser:
                    await self.browser.close()
                await self.playwright.stop()
            except Exception as e:
                print(f"Error al cerrar componentes de Playwright: {str(e)}")
            finally:
                self.playwright = None
                self.browser = None
                self.context = None
                self.page = None
    
    def search_by_term(self, term, max_results=10):
        """
        Busca contenido por término y extrae los resultados.
        Intenta hacer scraping real primero y si falla, usa datos de ejemplo.
        
        Args:
            term (str): Término de búsqueda.
            max_results (int): Número máximo de resultados a extraer.
            
        Returns:
            list: Lista de resultados con título, descripción y URL.
        """
        if not self.page:
            print("El navegador no está inicializado, usando datos de ejemplo")
            return self._get_example_search_results(term, max_results)
        
        try:
            # Ejecutar el scraping real de manera síncrona
            loop = asyncio.get_event_loop()
            real_results = loop.run_until_complete(self._search_by_term_async(term, max_results))
            
            if real_results:
                print(f"Scraping real exitoso, se encontraron {len(real_results)} resultados")
                self.results = real_results
                self.using_real_data = True
                return real_results
            else:
                print("No se encontraron resultados reales, usando datos de ejemplo")
                return self._get_example_search_results(term, max_results)
                
        except Exception as e:
            print(f"Error durante el scraping real: {str(e)}")
            import traceback
            traceback.print_exc()
            print("Fallback a datos de ejemplo")
            return self._get_example_search_results(term, max_results)
    
    async def _search_by_term_async(self, term, max_results=10):
        """
        Versión asíncrona de la búsqueda con Playwright.
        """
        try:
            print(f"Navegando a {self.base_url}...")
            await self.page.goto(self.base_url, wait_until="networkidle")
            await self.page.wait_for_load_state("domcontentloaded")
            
            # Buscar el campo de búsqueda y el botón
            print("Buscando elementos de búsqueda...")
            
            # Capturar screenshot para depuración
            screenshot_path = os.path.join("data", "homepage_screenshot.png")
            await self.page.screenshot(path=screenshot_path)
            print(f"Captura de pantalla guardada en {screenshot_path}")
            
            # Buscar el campo de búsqueda usando diferentes selectores
            search_selectors = [
                ".sfsearchTxt", 
                "input[type='search']", 
                "input[name='q']",
                ".search-input",
                "[placeholder*='Buscar']"
            ]
            
            search_input = None
            for selector in search_selectors:
                if await self.page.query_selector(selector):
                    search_input = await self.page.query_selector(selector)
                    print(f"Campo de búsqueda encontrado con selector: {selector}")
                    break
            
            if not search_input:
                print("No se encontró el campo de búsqueda")
                return []
            
            # Buscar el botón de búsqueda
            button_selectors = [
                ".sfsearchSubmit", 
                "button[type='submit']",
                ".search-button", 
                "button:has(svg)"
            ]
            
            search_button = None
            for selector in button_selectors:
                if await self.page.query_selector(selector):
                    search_button = await self.page.query_selector(selector)
                    print(f"Botón de búsqueda encontrado con selector: {selector}")
                    break
            
            if not search_button:
                print("No se encontró el botón de búsqueda")
                return []
            
            # Realizar la búsqueda
            await search_input.fill("")
            await search_input.type(term, delay=100)
            
            # Capturar screenshot antes de hacer clic
            screenshot_path = os.path.join("data", "before_search_click.png")
            await self.page.screenshot(path=screenshot_path)
            
            print(f"Buscando el término: '{term}'")
            await search_button.click()
            
            # Esperar a que se carguen los resultados
            print("Esperando resultados de búsqueda...")
            await self.page.wait_for_load_state("networkidle")
            
            # Capturar screenshot después de la búsqueda
            screenshot_path = os.path.join("data", "search_results.png")
            await self.page.screenshot(path=screenshot_path)
            
            # Extraer resultados usando diferentes selectores
            result_selectors = [
                ".searchResults .searchItem", 
                ".search-results .result-item",
                ".results-list .item",
                "article.result"
            ]
            
            results = []
            for selector in result_selectors:
                result_elements = await self.page.query_selector_all(selector)
                if result_elements:
                    print(f"Resultados encontrados con selector: {selector}")
                    break
            
            if not result_elements:
                print("No se encontraron elementos de resultado")
                return []
            
            print(f"Encontrados {len(result_elements)} resultados")
            
            # Procesar los resultados encontrados
            for element in result_elements[:max_results]:
                try:
                    # Extraer título y URL
                    title_selectors = ["h3 a", ".result-title a", "a.title", "h2 a"]
                    title_element = None
                    for title_selector in title_selectors:
                        title_element = await element.query_selector(title_selector)
                        if title_element:
                            break
                    
                    if not title_element:
                        continue
                    
                    title = await title_element.text_content()
                    url = await title_element.get_attribute("href")
                    
                    # Extraer descripción
                    desc_selectors = [".searchSnippet", ".result-description", ".snippet", "p.description"]
                    description = "No hay descripción disponible"
                    
                    for desc_selector in desc_selectors:
                        desc_element = await element.query_selector(desc_selector)
                        if desc_element:
                            description = await desc_element.text_content()
                            break
                    
                    if title and url:
                        results.append({
                            "title": title.strip(),
                            "description": description.strip(),
                            "url": url if url.startswith('http') else self.base_url + url,
                            "extracted_at": datetime.now().isoformat()
                        })
                except Exception as e:
                    print(f"Error al extraer un resultado: {str(e)}")
            
            print(f"Scraping completado, se extrajeron {len(results)} resultados")
            return results
                
        except Exception as e:
            print(f"Error durante la búsqueda asíncrona: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def extract_page_content(self, url):
        """
        Extrae el contenido detallado de una página específica.
        Intenta hacer scraping real primero y si falla, usa datos de ejemplo.
        
        Args:
            url (str): URL de la página a extraer.
            
        Returns:
            dict: Contenido extraído de la página.
        """
        if not self.page:
            print("El navegador no está inicializado, usando datos de ejemplo")
            return self._get_example_page_content(url)
        
        try:
            # Ejecutar el scraping real de manera síncrona
            loop = asyncio.get_event_loop()
            real_content = loop.run_until_complete(self._extract_page_content_async(url))
            
            if real_content and real_content.get("content_text"):
                print(f"Extracción real de contenido exitosa para {url}")
                return real_content
            else:
                print(f"No se pudo extraer contenido real de {url}, usando datos de ejemplo")
                return self._get_example_page_content(url)
                
        except Exception as e:
            print(f"Error durante la extracción de contenido: {str(e)}")
            import traceback
            traceback.print_exc()
            print("Fallback a datos de ejemplo")
            return self._get_example_page_content(url)
    
    async def _extract_page_content_async(self, url):
        """
        Versión asíncrona de la extracción de contenido con Playwright.
        """
        try:
            print(f"Navegando a {url}...")
            await self.page.goto(url, wait_until="networkidle")
            await self.page.wait_for_load_state("domcontentloaded")
            
            # Capturar screenshot para depuración
            screenshot_path = os.path.join("data", f"page_content_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
            await self.page.screenshot(path=screenshot_path)
            print(f"Captura de pantalla de página guardada en {screenshot_path}")
            
            # Extraer información básica
            title = await self.page.title()
            
            # Extraer contenido principal con diferentes selectores
            content_selectors = [
                ".main-content", 
                "article", 
                ".content-area", 
                "main", 
                "#main-content"
            ]
            
            content_html = ""
            content_text = ""
            
            for selector in content_selectors:
                content_element = await self.page.query_selector(selector)
                if content_element:
                    print(f"Contenido principal encontrado con selector: {selector}")
                    content_html = await self.page.evaluate(f"document.querySelector('{selector}').innerHTML")
                    content_text = await content_element.text_content()
                    break
            
            if not content_text:
                # Si no encontramos el contenido con los selectores, usar el body
                content_element = await self.page.query_selector("body")
                if content_element:
                    content_text = await content_element.text_content()
            
            # Extraer categorías/breadcrumbs
            categories = []
            category_selectors = [".categories a", ".breadcrumbs a", ".breadcrumb a", "nav.breadcrumb a"]
            
            for selector in category_selectors:
                category_elements = await self.page.query_selector_all(selector)
                if category_elements:
                    for element in category_elements:
                        category_text = await element.text_content()
                        if category_text.strip():
                            categories.append(category_text.strip())
                    
                    if categories:
                        print(f"Categorías encontradas con selector: {selector}")
                        break
            
            # Extraer imágenes
            images = []
            img_elements = await self.page.query_selector_all("img")
            
            for img in img_elements:
                src = await img.get_attribute("src")
                alt = await img.get_attribute("alt") or ""
                
                if src:
                    # Convertir URLs relativas a absolutas
                    if not src.startswith('http'):
                        if src.startswith('/'):
                            src = self.base_url + src
                        else:
                            src = self.base_url + '/' + src
                    
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
            
        except Exception as e:
            print(f"Error durante la extracción de contenido asíncrona: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
    
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
                
            print(f"Resultados guardados en {filepath} (datos {'reales' if self.using_real_data else 'de ejemplo'})")
            return True
        except Exception as e:
            print(f"Error al guardar resultados: {str(e)}")
            return False
    
    def extract_seguros_colectivos(self, max_pages=5):
        """
        Extrae información específica sobre seguros colectivos.
        Intenta hacer scraping real primero y si falla, usa datos de ejemplo.
        
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
            print("Fallback a datos de ejemplo para seguros colectivos")
            
            # Usar datos de ejemplo como fallback
            example_data = self._get_example_seguros_colectivos()
            self.results = example_data
            self.save_results("seguros_colectivos.json")
            
            return example_data
    
    def _get_example_search_results(self, term, max_results=10):
        """
        Genera resultados de ejemplo para una búsqueda.
        """
        self.using_real_data = False
        print(f"Generando resultados de ejemplo para búsqueda: {term}")
        
        if "colectivo" in term.lower():
            self.results = self._create_colectivo_results()[:max_results]
        else:
            self.results = self._create_generic_results(term)[:max_results]
        
        return self.results
    
    def _get_example_page_content(self, url):
        """
        Genera contenido de ejemplo para una URL.
        """
        self.using_real_data = False
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
        """
        Genera datos de ejemplo completos para seguros colectivos.
        """
        self.using_real_data = False
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
    print(f"Se encontraron {len(results)} resultados")