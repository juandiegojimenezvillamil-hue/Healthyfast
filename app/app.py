"""Archivo principal de arranque para la aplicación web.

Este módulo crea la instancia de Flask, conecta las rutas del proyecto
con el Blueprint principal y levanta el servidor en modo local para
mostrar la tienda Healthy Fast.
"""

from flask import Flask
from routes.routes import main_routes

# Instancia global de la aplicación Flask.
# Se usa para registrar rutas, manejar sesiones y renderizar plantillas.
app = Flask(__name__)

# Clave secreta de la sesión del usuario.
# Permite guardar datos como login, carrito o datos de envío temporalmente.
app.secret_key = 'healthyfast_arquitectura_segura_2026'

# Se registra el Blueprint principal que contiene todas las rutas del sitio.
app.register_blueprint(main_routes)

# Inicia el servidor cuando se ejecuta este archivo directamente.
if __name__ == '__main__':
    app.run(debug=True)
