from fastapi import FastAPI

# Inicializamos el motor del servidor
app = FastAPI(title="Buscador de Componentes FIMEE")

# Ruta principal para comprobar que el servidor despertó correctamente
@app.get("/")
def verificar_estado():
    return {
        "mensaje": "¡El servidor de Tienda ElectroByte está funcionando perfectamente!",
        "estado": "Activo"
    }

# Estructura base donde conectaremos la inteligencia artificial luego
@app.get("/buscar/{palabra_clave}")
def procesar_busqueda(palabra_clave: str):
    # Por ahora solo nos devuelve la palabra que escriba el cliente
    return {
        "cliente_busca": palabra_clave, 
        "respuesta": "Pronto conectaremos esto con los paquetes del inventario."
    }