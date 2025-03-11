import os
import json
import datetime
import threading
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt

from app.scraper import SuraScraper

# Crear aplicación Flask
app = Flask(__name__)
CORS(app)  # Permitir solicitudes cross-origin

# Cache en memoria para almacenar resultados
results_cache = {
    "last_updated": None,
    "data": []
}

# Configuración desde variables de entorno - valores críticos de seguridad
API_SECRET_KEY = os.environ.get('API_SECRET_KEY')
if not API_SECRET_KEY:
    raise ValueError("API_SECRET_KEY must be set as an environment variable")

API_USERNAME = os.environ.get('API_USERNAME')
if not API_USERNAME:
    raise ValueError("API_USERNAME must be set as an environment variable")

API_PASSWORD = os.environ.get('API_PASSWORD')
if not API_PASSWORD:
    raise ValueError("API_PASSWORD must be set as an environment variable")

# Función para validar JWT
def validate_token(token):
    try:
        payload = jwt.decode(token, API_SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        return None

# Decorador para rutas protegidas
def token_required(f):
    def decorated(*args, **kwargs):
        token = None
        # Buscar token en headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
        
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        # Validar token
        payload = validate_token(token)
        if not payload:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    
    # Mantener el nombre de la función
    decorated.__name__ = f.__name__
    return decorated

# Ruta para health check (no requiere autenticación)
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat()
    })

# Ruta para metadatos de la API (no requiere autenticación)
@app.route('/api/info', methods=['GET'])
def get_api_info():
    return jsonify({
        "name": "Sura Scraper API",
        "version": "1.0.0",
        "description": "API para extraer y consultar datos de seguros.sura.cl",
        "endpoints": [
            {"path": "/health", "method": "GET", "description": "Verificar estado del servicio"},
            {"path": "/api/info", "method": "GET", "description": "Obtener información de la API"},
            {"path": "/api/auth/token", "method": "POST", "description": "Obtener token JWT"},
            {"path": "/api/results", "method": "GET", "description": "Obtener resultados de extracción"},
            {"path": "/api/extract", "method": "POST", "description": "Iniciar extracción de datos"},
        ],
        "last_extraction": results_cache["last_updated"]
    })

# Ruta para obtener token JWT
@app.route('/api/auth/token', methods=['POST'])
def get_token():
    auth = request.authorization
    
    # Intentar obtener credenciales del cuerpo JSON si no están en el header
    if not auth:
        data = request.get_json()
        if data and 'username' in data and 'password' in data:
            username = data['username']
            password = data['password']
        else:
            return jsonify({"error": "Authentication credentials required"}), 401
    else:
        username = auth.username
        password = auth.password
    
    # Validar credenciales
    if username != API_USERNAME or password != API_PASSWORD:
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Generar token JWT
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    token = jwt.encode({
        'sub': username,
        'exp': expiration
    }, API_SECRET_KEY, algorithm='HS256')
    
    return jsonify({
        "access_token": token,
        "expires_at": expiration.isoformat()
    })

# Ruta para obtener resultados
@app.route('/api/results', methods=['GET'])
@token_required
def get_results():
    # Parámetros de paginación y filtros
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    search = request.args.get('q', '')
    
    # Cargar resultados si no están en cache
    if not results_cache["data"]:
        load_results_from_file()
    
    data = results_cache["data"]
    
    # Aplicar filtro si hay término de búsqueda
    if search:
        search = search.lower()
        data = [item for item in data if search in json.dumps(item).lower()]
    
    # Calcular total y páginas
    total = len(data)
    pages = (total + limit - 1) // limit if limit > 0 else 1
    
    # Validar página
    if page < 1:
        page = 1
    if page > pages and pages > 0:
        page = pages
    
    # Aplicar paginación
    start = (page - 1) * limit
    end = min(start + limit, total)
    paginated_data = data[start:end]
    
    return jsonify({
        "total": total,
        "page": page,
        "pages": pages,
        "limit": limit,
        "results": paginated_data,
        "last_updated": results_cache["last_updated"]
    })

# Ruta para iniciar extracción
@app.route('/api/extract', methods=['POST'])
@token_required
def start_extraction():
    # Obtener parámetros
    data = request.get_json() or {}
    term = data.get('term', 'seguros colectivos')
    max_results = data.get('max_results', 5)
    headless = data.get('headless', True)
    
    # Iniciar extracción en un hilo separado
    thread = threading.Thread(
        target=run_extraction_thread,
        args=(term, max_results, headless)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "message": "Extraction process started",
        "term": term,
        "max_results": max_results,
        "status": "processing"
    })

# Función para cargar resultados desde el archivo
def load_results_from_file():
    try:
        data_dir = Path("data")
        print(f"Buscando archivos JSON en {data_dir.absolute()}")
        
        # Verificar si el directorio existe
        if not data_dir.exists():
            print(f"Directorio {data_dir.absolute()} no existe, creándolo")
            data_dir.mkdir(parents=True, exist_ok=True)
        
        json_files = list(data_dir.glob("*.json"))
        print(f"Archivos encontrados: {json_files}")
        
        if not json_files:
            print("No se encontraron archivos JSON en el directorio data/")
            results_cache["data"] = []
            return
        
        # Obtener el archivo más reciente
        latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
        print(f"Usando el archivo más reciente: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Contenido leído, tamaño: {len(content)} bytes")
            
            if not content.strip():
                print("El archivo está vacío")
                results_cache["data"] = []
                return
                
            data = json.loads(content)
            print(f"Datos JSON cargados: {type(data)}")
            
        # Actualizar el cache
        if isinstance(data, list):
            results_cache["data"] = data
            print(f"Cargados {len(data)} resultados (formato lista)")
        elif isinstance(data, dict):
            # Si es un diccionario, extraer la lista de resultados
            if "search_results" in data:
                results_cache["data"] = data["search_results"]
                print(f"Cargados {len(data['search_results'])} resultados (de search_results)")
            elif "pages_content" in data:
                results_cache["data"] = data["pages_content"]
                print(f"Cargados {len(data['pages_content'])} resultados (de pages_content)")
            else:
                results_cache["data"] = [data]
                print("Cargado un único resultado (diccionario)")
        
        results_cache["last_updated"] = datetime.datetime.fromtimestamp(
            latest_file.stat().st_mtime
        ).isoformat()
        
        print(f"Cache actualizado con {len(results_cache['data'])} resultados")
        
    except Exception as e:
        import traceback
        print(f"Error detallado al cargar resultados: {str(e)}")
        traceback.print_exc()
        results_cache["data"] = []

# Función para ejecutar en un hilo separado
def run_extraction_thread(term, max_results, headless):
    try:
        scraper = SuraScraper(headless=headless)
        scraper.initialize()
        
        if term == "seguros colectivos":
            # Usar la extracción especializada
            results = scraper.extract_seguros_colectivos(max_pages=max_results)
        else:
            # Usar la búsqueda general
            results = scraper.search_by_term(term, max_results=max_results)
            scraper.save_results()
        
        # Actualizar cache
        load_results_from_file()
        
    except Exception as e:
        print(f"Error en el hilo de extracción: {str(e)}")
    finally:
        if scraper:
            scraper.close()

# Inicializar carga de datos al inicio
load_results_from_file()

# Crear la aplicación
def create_app():
    return app

if __name__ == "__main__":
    app.run(debug=True)