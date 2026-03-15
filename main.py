import gspread
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2.service_account import Credentials

# 1. Configuración de acceso a Google Sheets
# Render leerá el archivo 'credenciales.json' que guardaste en la sección Ambiente
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("/etc/secrets/credenciales.json", scopes=scope)
client = gspread.authorize(creds)

# PEGA AQUÍ EL ENLACE DE TU HOJA DE CÁLCULO
URL_DE_TU_HOJA = "https://docs.google.com/spreadsheets/d/1hYyzzcnJkM0pCebcA721EM8x0KBi6810PmqXOmidMnU/edit?usp=sharing"
hoja = client.open_by_url(URL_DE_TU_HOJA).sheet1

app = FastAPI(title="API Tienda ElectroByte")

# Permisos para que tu página web pueda consultar
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/buscar/{termino}")
def buscar_en_inventario(termino: str):
    # Obtenemos todos los datos de la hoja
    datos = hoja.get_all_records()
    resultados = []
    
    termino = termino.lower()
    
    for fila in datos:
        # Buscamos en Nombre, Categoría o Palabras_Clave
        if (termino in str(fila['Nombre']).lower() or 
            termino in str(fila['Categoria']).lower() or 
            termino in str(fila['Palabras_Clave']).lower()):
            
            # Lógica de stock
            disponible = int(fila['Stock']) > 0
            
            resultados.append({
                "sku": fila['SKU'],
                "nombre": fila['Nombre'],
                "precio_original": fila['Precio'],
                "stock": fila['Stock'],
                "categoria": fila['Categoria'],
                "descripcion": fila['Descripcion'],
                "imagen": fila['Imagen_URL'],
                "en stock": "Sí" if disponible else "Agotado"
            })
            
    return {"busqueda": termino, "total": len(resultados), "productos": resultados}

@app.get("/")
def inicio():
    return {"mensaje": "Servidor ElectroByte conectado con Google Sheets"}
