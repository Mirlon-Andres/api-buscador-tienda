from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Buscador de Componentes FIMEE")

# --- ESTO ES EL PERMISO (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Esto permite que cualquier página lea tus datos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------------

@app.get("/")
def verificar_estado():
    return {
        "mensaje": "¡El servidor de Tienda ElectroByte está funcionando perfectamente!",
        "estado": "Activo"
    }

@app.get("/buscar/{palabra_clave}")
def procesar_busqueda(palabra_clave: str):
    return {
        "cliente_busca": palabra_clave, 
        "respuesta": f"Buscando en el inventario el mejor paquete para: {palabra_clave}"
    }
