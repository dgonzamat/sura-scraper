import os
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class SuraScraper:
    """Clase para extraer datos del sitio web de Seguros Sura."""
    
    def __init__(self, headless=True, timeout=30):
        """
        Inicializa el scraper.
        
        Args:
            headless (bool): Si True, ejecuta Chrome en modo headless.
            timeout (int): Tiempo máximo de espera en segundos.
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.base_url = "https://seguros.sura.cl"
        self.results = []
        
    def initialize(self):
        """Inicializa el navegador Chrome y configura opciones."""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless")
            
        # Configuraciones adicionales para estabilidad
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # User agent para evitar detección como bot
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        try:
            # En entorno de producción (Docker), Chrome está instalado
            if os.environ.get('DOCKER_ENV'):
                self.driver = webdriver.Chrome(options=options)
            else:
                # En desarrollo, usar ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                
            self.driver.set_page_load_timeout(self.timeout)
            
            return True
        except Exception as e:
            print(f"Error al inicializar el navegador: {str(e)}")
            return False
    
    def close(self):
        """Cierra el navegador y libera recursos."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def search_by_term(self, term, max_results=10):
        """
        Busca contenido por término y extrae los resultados.
        
        Args:
            term (str): Término de búsqueda.
            max_results (int): Número máximo de resultados a extraer.
            
        Returns:
            list: Lista de resultados con título, descripción y URL.
        """
        if not self.driver:
            if not self.initialize():
                return []
        
        try:
            # Navegar a la página principal
            self.driver.get(self.base_url)
            
            # Esperar a que cargue
            time.sleep(2)
            
            # Buscar el campo de búsqueda
            # Nota: Esto depende de la estructura real del sitio web
            try:
                search_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".sfsearchSubmit, button[type='submit']"))
                )
                search_input = self.driver.find_element(By.CSS_SELECTOR, ".sfsearchTxt, input[type='search'], input[name='q']")
                
                # Ingresar término de búsqueda
                search_input.clear()
                search_input.send_keys(term)
                search_button.click()
                
                # Esperar a que carguen los resultados
                time.sleep(3)
                
                # Extraer resultados
                results = []
                result_elements = self.driver.find_elements(By.CSS_SELECTOR, ".searchResults .searchItem, .search-results .result-item")
                
                for element in result_elements[:max_results]:
                    try:
                        # Extraer título y URL (ajustar selectores según la estructura real)
                        title_element = element.find_element(By.CSS_SELECTOR, "h3 a, .result-title a")
                        title = title_element.text.strip()
                        url = title_element.get_attribute("href")
                        
                        # Extraer descripción
                        try:
                            description = element.find_element(By.CSS_SELECTOR, ".searchSnippet, .result-description").text.strip()
                        except NoSuchElementException:
                            description = "No hay descripción disponible"
                        
                        results.append({
                            "title": title,
                            "description": description,
                            "url": url,
                            "extracted_at": datetime.now().isoformat()
                        })
                    except Exception as e:
                        print(f"Error al extraer resultado: {str(e)}")
                
                self.results = results
                return results
                
            except Exception as e:
                print(f"Error al interactuar con el buscador: {str(e)}")
                
                # Plan B: Intentar acceder directamente a la URL de búsqueda
                search_url = f"{self.base_url}/search?q={term}"
                self.driver.get(search_url)
                time.sleep(3)
                
                # Volver a intentar extraer resultados
                # Implementar aquí según se necesite...
                
                return []
                
        except Exception as e:
            print(f"Error durante la búsqueda: {str(e)}")
            return []
    
    def extract_page_content(self, url):
        """
        Extrae el contenido detallado de una página específica.
        
        Args:
            url (str): URL de la página a extraer.
            
        Returns:
            dict: Contenido extraído de la página.
        """
        if not self.driver:
            if not self.initialize():
                return {}
        
        try:
            # Navegar a la URL
            self.driver.get(url)
            
            # Esperar a que cargue
            time.sleep(2)
            
            # Extraer información básica
            title = self.driver.title
            
            # Extraer contenido principal (ajustar selectores según la estructura real)
            try:
                content_element = self.driver.find_element(By.CSS_SELECTOR, ".main-content, article, .content-area")
                content_html = content_element.get_attribute("innerHTML")
                content_text = content_element.text
            except NoSuchElementException:
                content_html = ""
                content_text = ""
            
            # Extraer metadatos (categorías, fechas, etc.)
            categories = []
            try:
                category_elements = self.driver.find_elements(By.CSS_SELECTOR, ".categories a, .breadcrumbs a")
                categories = [element.text.strip() for element in category_elements if element.text.strip()]
            except:
                pass
                
            # Extraer imágenes
            images = []
            try:
                image_elements = self.driver.find_elements(By.CSS_SELECTOR, "img")
                for img in image_elements:
                    src = img.get_attribute("src")
                    alt = img.get_attribute("alt") or ""
                    if src and (self.base_url in src or src.startswith("/")):
                        images.append({"src": src, "alt": alt})
            except:
                pass
            
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
            print(f"Error al extraer contenido de la página {url}: {str(e)}")
            return {"url": url, "error": str(e)}
    
    def save_results(self, filename="sura_results.json"):
        """
        Guarda los resultados extraídos en un archivo JSON.
        
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
        if not self.driver:
            if not self.initialize():
                return {}
        
        results = {
            "search_results": [],
            "pages_content": [],
            "extracted_at": datetime.now().isoformat()
        }
        
        try:
            # Buscar información sobre seguros colectivos
            search_results = self.search_by_term("seguros colectivos", max_results=max_pages)
            results["search_results"] = search_results
            
            # Extraer contenido de las páginas de resultados
            for result in search_results[:max_pages]:
                page_content = self.extract_page_content(result["url"])
                results["pages_content"].append(page_content)
            
            # Intentar acceder directamente a la página de seguros colectivos
            direct_url = f"{self.base_url}/empresas/seguros-colectivos"
            try:
                direct_page_content = self.extract_page_content(direct_url)
                results["direct_page"] = direct_page_content
            except Exception as e:
                results["direct_page"] = {"error": str(e)}
            
            # Guardar los resultados
            self.results = results
            self.save_results("seguros_colectivos.json")
            
            return results
            
        except Exception as e:
            print(f"Error durante la extracción de seguros colectivos: {str(e)}")
            return {"error": str(e)}

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