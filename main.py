import gspread
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2.service_account import Credentials
import unicodedata # Librería nativa para eliminar tildes

# 1. Configuración de credenciales seguras
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("/etc/secrets/credenciales.json", scopes=scope)
client = gspread.authorize(creds)

URL_DE_TU_HOJA = "https://docs.google.com/spreadsheets/d/1hYyzzcnJkM0pCebcA721EM8x0KBi6810PmqXOmidMnU/edit"
hoja = client.open_by_url(URL_DE_TU_HOJA).sheet1

app = FastAPI(title="API Conecta FIMEE")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ESCUDOS DE PROTECCIÓN Y SANEAMIENTO DE DATOS ---

def normalizar_texto(texto):
    """Filtro 1: Elimina mayúsculas, espacios extra y tildes. 
    Así 'Árduíno ' se vuelve 'arduino' y las búsquedas nunca fallan."""
    if not texto: return ""
    texto = str(texto).lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

def sanear_numero(valor):
    """Filtro 2: Convierte textos humanos en variables matemáticas puras.
    Si en Excel escriben ' S/ 15,50 ', lo limpia y lo convierte a 15.50"""
    if isinstance(valor, (int, float)): return float(valor)
    if not valor: return 0.0
    try:
        limpio = str(valor).replace('S/', '').replace('s/', '').replace(' ', '').replace(',', '.')
        return float(limpio)
    except ValueError:
        return 0.0 # Si escriben pura letra por error, devuelve 0 para no colapsar

# --- RUTAS DE LA API ---

@app.get("/buscar/{termino}")
def buscar_en_inventario(termino: str):
    try:
        datos = hoja.get_all_records()
        resultados = []
        termino_limpio = normalizar_texto(termino)
        
        for fila in datos:
            # 1. Filtro de Integridad: Si no hay SKU o Nombre, saltar
            if not fila.get('SKU') or not fila.get('Nombre'):
                continue
                
            # 2. Filtro de Visibilidad: Si dice "No", "Falso" o está vacío, saltar
            visible = str(fila.get('Visible_Web', '')).strip().lower()
            if visible in ['no', 'falso', 'false', '0', '']:
                continue 
            
            # Normalizamos los campos de búsqueda
            nombre = normalizar_texto(fila.get('Nombre', ''))
            categoria = normalizar_texto(fila.get('Categoria', ''))
            tags = normalizar_texto(fila.get('Palabras_Clave', ''))
            
            if termino_limpio in nombre or termino_limpio in categoria or termino_limpio in tags:
                
                # Empaquetamos SOLO los datos públicos y seguros
                resultados.append({
                    "sku": str(fila.get('SKU', '')).strip(),
                    "nombre": str(fila.get('Nombre', '')).strip(),
                    "precio": sanear_numero(fila.get('Precio', 0)),
                    "precio_oferta": sanear_numero(fila.get('Precio_Oferta', 0)),
                    "descuento": sanear_numero(fila.get('Descuento_%', 0)),
                    "stock": sanear_numero(fila.get('Stock', 0)),
                    "categoria": str(fila.get('Categoria', '')).strip(),
                    "descripcion": str(fila.get('Descripcion', '')).strip(),
                    "imagen": str(fila.get('Imagen_URL', '')).strip(),
                    "datasheet": str(fila.get('Enlace_Datasheet', '')).strip(),
                    "opciones_potencia": str(fila.get('Opciones_Potencia', '')).strip(),
                    "opciones_valor": str(fila.get('Opciones_Valor', '')).strip()
                    # Nota de Seguridad: Costo_Compra, Ubicacion_Fisica y Proveedor 
                    # NUNCA se agregan aquí para proteger el negocio.
                })
                
        return {"total": len(resultados), "productos": resultados}
        
    except Exception as e:
        return {"error_critico": "Falla de conexión", "detalle": str(e)}
