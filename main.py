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
    """Filtro 1: Elimina mayúsculas, espacios extra y tildes."""
    if not texto: return ""
    texto = str(texto).lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

def sanear_numero(valor):
    """Filtro 2: Convierte textos humanos en variables matemáticas puras."""
    if isinstance(valor, (int, float)): return float(valor)
    if not valor: return 0.0
    try:
        limpio = str(valor).replace('S/', '').replace('s/', '').replace(' ', '').replace(',', '.')
        return float(limpio)
    except ValueError:
        return 0.0 

# --- RUTAS DE LA API ---

@app.get("/")
def inicio():
    return {"mensaje": "Servidor Conecta FIMEE Operativo y Seguro", "estado": "Online"}

@app.get("/buscar/{termino}")
def buscar_en_inventario(termino: str):
    try:
        datos = hoja.get_all_records()
        resultados = []
        
        # --- MEJORA 1: TOKENIZACIÓN ---
        # Cortamos lo que el usuario escribe en palabras sueltas
        # Ej: "fisica serway" se convierte en ["fisica", "serway"]
        termino_limpio = normalizar_texto(termino)
        palabras_busqueda = termino_limpio.split() 
        
        # Si la búsqueda está vacía, no hacemos nada
        if not palabras_busqueda:
            return {"total": 0, "productos": []}
        
        for fila in datos:
            sku = str(fila.get('SKU', '')).strip().upper()
            
            # 1. Filtro de Integridad: Si no hay SKU o Nombre, saltar
            if not sku or not fila.get('Nombre'):
                continue
                
            # 2. Filtro de Visibilidad: Si dice "No", "Falso" o está vacío, saltar
            visible = str(fila.get('Visible_Web', '')).strip().lower()
            if visible in ['no', 'falso', 'false', '0', '']:
                continue 
            
            # 3. Normalizamos TODAS las columnas de texto
            nombre = normalizar_texto(fila.get('Nombre', ''))
            categoria = normalizar_texto(fila.get('Categoria', ''))
            tags = normalizar_texto(fila.get('Palabras_Clave', ''))
            descripcion = normalizar_texto(fila.get('Descripcion', ''))
            
            # --- MEJORA 2: LA MEGACADENA ---
            # Unimos toda la información en un solo bloque gigante de texto.
            # Si es un libro (LIB-), la descripción es fundamental para encontrar al autor o el tema.
            if sku.startswith("LIB-"):
                texto_busqueda = f"{nombre} {categoria} {tags} {descripcion}"
            else:
                # Para componentes también lo unimos, así si buscan "sensor ultrasonido" 
                # y "ultrasonido" está en la descripción, igual lo encuentra.
                texto_busqueda = f"{nombre} {categoria} {tags} {descripcion}"
            
            # --- MEJORA 3: MATCH INTELIGENTE ---
            # Verifica que TODAS las palabras que el usuario escribió existan en la megacadena, 
            # sin importar el orden en el que las haya escrito.
            coincidencia = all(palabra in texto_busqueda for palabra in palabras_busqueda)
            
            if coincidencia:
                # Empaquetamos SOLO los datos públicos y seguros
                resultados.append({
                    "sku": sku,
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
                })
                
        return {"total": len(resultados), "productos": resultados}
        
    except Exception as e:
        return {"error_critico": "Falla de conexión", "detalle": str(e)}
