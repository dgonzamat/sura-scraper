import os
import time
import json
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class SuraScraper:
    """Clase para extraer datos del sitio web de Seguros Sura con manejo robusto de navegador."""
    
    def __init__(self, headless=True, timeout=30, max_retries=3):
        """
        Inicializa el scraper con configuraciones avanzadas.
        
        Args:
            headless (bool): Si True, ejecuta Chrome en modo headless.
            timeout (int): Tiempo máximo de espera en segundos.
            max_retries (int): Número máximo de reintentos para operaciones.
        """
        self.headless = headless
        self.timeout = timeout
        self.max_retries = max_retries
        self.driver = None
        self.base_url = "https://seguros.sura.cl"
        self.results = []
        
    def _configure_chrome_options(self):
        """Configura opciones de Chrome con medidas de seguridad y estabilidad."""
        options = Options()
        
        # Configuraciones de seguridad y estabilidad
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Modo headless
        if self.headless:
            options.add_argument("--headless")
        
        # User agent para evitar detección como bot
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Deshabilitar extensiones y notificaciones
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        
        # Configuraciones adicionales para rendimiento y estabilidad
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-software-rasterizer")
        
        return options
    
    def _get_chromedriver_path(self):
        """
        Obtiene la ruta del ChromeDriver de manera inteligente.
        
        Returns:
            str: Ruta del ChromeDriver
        """
        # Lista de ubicaciones posibles de ChromeDriver
        possible_paths = [
            '/usr/local/bin/chromedriver',  # Ruta en Docker
            '/usr/bin/chromedriver',        # Otra ruta común
            os.path.expanduser('~/chromedriver')  # Ruta en home
        ]
        
        # Primero busca en rutas predefinidas
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"ChromeDriver encontrado en {path}")
                return path
        
        # Si no encuentra, usa ChromeDriverManager
        try:
            driver_path = ChromeDriverManager().install()
            logger.info(f"ChromeDriver instalado mediante ChromeDriverManager: {driver_path}")
            return driver_path
        except Exception as e:
            logger.error(f"Error crítico al obtener ChromeDriver: {e}")
            raise RuntimeError("No se pudo encontrar ni instalar ChromeDriver")
    
    def initialize(self):
        """
        Inicializa el navegador Chrome con manejo de errores avanzado.
        
        Returns:
            bool: True si la inicialización es exitosa, False en caso contrario.
        """
        for attempt in range(self.max_retries):
            try:
                # Configurar opciones de Chrome
                chrome_options = self._configure_chrome_options()
                
                # Obtener ruta de ChromeDriver
                driver_path = self._get_chromedriver_path()
                
                # Crear servicio de ChromeDriver
                service = Service(driver_path)
                
                # Inicializar WebDriver
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # Configurar timeouts
                self.driver.set_page_load_timeout(self.timeout)
                self.driver.implicitly_wait(10)  # Espera implícita para elementos
                
                logger.info(f"Navegador inicializado correctamente (Intento {attempt + 1})")
                return True
            
            except WebDriverException as e:
                logger.warning(f"Error de WebDriver en intento {attempt + 1}: {e}")
                
                # Limpiar recursos si hay un driver parcialmente inicializado
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                
                # Si es el último intento, registrar error crítico
                if attempt == self.max_retries - 1:
                    logger.error("No se pudo inicializar el navegador después de múltiples intentos")
                    return False
                
                # Pequeña pausa entre intentos
                time.sleep(2)
        
        return False
    
    def close(self):
        """Cierra el navegador y libera recursos."""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Navegador cerrado correctamente")
        except Exception as e:
            logger.error(f"Error al cerrar el navegador: {e}")
        finally:
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
                logger.error("No se pudo inicializar el navegador para búsqueda")
                return []
        
        results = []
        try:
            # Navegar a la página principal
            self.driver.get(self.base_url)
            
            # Esperar y encontrar campo de búsqueda
            try:
                search_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search'], .search-input"))
                )
                search_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'], .search-button"))
                )
                
                # Limpiar e ingresar término
                search_input.clear()
                search_input.send_keys(term)
                search_button.click()
                
                # Esperar resultados
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".search-result, .result-item"))
                )
                
            except TimeoutException:
                logger.warning("Timeout al buscar elementos de búsqueda")
                return []
            
            # Extraer resultados
            result_elements = self.driver.find_elements(By.CSS_SELECTOR, ".search-result, .result-item")
            
            for element in result_elements[:max_results]:
                try:
                    # Extraer título
                    title_element = element.find_element(By.CSS_SELECTOR, "h3 a, .result-title")
                    title = title_element.text.strip()
                    url = title_element.get_attribute("href") or ""
                    
                    # Extraer descripción
                    try:
                        description_element = element.find_element(By.CSS_SELECTOR, ".search-description, .result-snippet")
                        description = description_element.text.strip()
                    except NoSuchElementException:
                        description = "Sin descripción disponible"
                    
                    # Agregar resultado
                    results.append({
                        "title": title,
                        "description": description,
                        "url": url,
                        "extracted_at": datetime.now().isoformat()
                    })
                    
                except Exception as item_error:
                    logger.warning(f"Error al extraer resultado individual: {item_error}")
            
            logger.info(f"Búsqueda completada. Resultados encontrados: {len(results)}")
            self.results = results
            return results
        
        except Exception as e:
            logger.error(f"Error crítico durante la búsqueda: {e}")
            return []
    
    def save_results(self, filename=None):
        """
        Guarda los resultados extraídos en un archivo JSON.
        
        Args:
            filename (str, opcional): Nombre del archivo. Si no se proporciona, 
                                      se genera uno basado en la fecha y hora.
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        try:
            # Crear directorio de datos si no existe
            os.makedirs("data", exist_ok=True)
            
            # Generar nombre de archivo si no se proporciona
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"sura_results_{timestamp}.json"
            
            # Ruta completa del archivo
            filepath = os.path.join("data", filename)
            
            # Guardar resultados
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Resultados guardados en {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"Error al guardar resultados: {e}")
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
            search_results = self.search_by_term("seguros colectivos", max_results=max_pages)
            results["search_results"] = search_results
            
            # Extraer contenido de páginas
            for result in search_results[:max_pages]:
                try:
                    self.driver.get(result["url"])
                    time.sleep(2)  # Esperar carga de página
                    
                    # Extraer contenido principal
                    content_element = self.driver.find_element(By.CSS_SELECTOR, "body")
                    page_content = {
                        "url": result["url"],
                        "title": result["title"],
                        "content": content_element.text,
                        "html": content_element.get_attribute("innerHTML")
                    }
                    
                    results["pages_content"].append(page_content)
                except Exception as page_error:
                    logger.warning(f"Error al extraer página {result['url']}: {page_error}")
            
            # Guardar resultados
            self.results = results
            self.save_results("seguros_colectivos.json")
            
            return results
        
        except Exception as e:
            logger.error(f"Error durante extracción de seguros colectivos: {e}")
            return {"error": str(e)}

def run_scraper(headless=True, search_term="seguros colectivos", max_results=5):
    """
    Función de utilidad para ejecutar el scraper de manera simple.
    
    Args:
        headless (bool): Modo headless del navegador.
        search_term (str): Término de búsqueda.
        max_results (int): Número máximo de resultados.
        
    Returns:
        list: Resultados de la búsqueda.
    """
    scraper = SuraScraper(headless=headless)
    try:
        scraper.initialize()
        results = scraper.search_by_term(search_term, max_results=max_results)
        scraper.save_results()
        return results
    except Exception as e:
        logger.error(f"Error en ejecución del scraper: {e}")
        return []
    finally:
        scraper.close()

if __name__ == "__main__":
    # Punto de entrada para ejecución directa
    results = run_scraper(headless=False)
    print(f"Resultados extraídos: {len(results)}")