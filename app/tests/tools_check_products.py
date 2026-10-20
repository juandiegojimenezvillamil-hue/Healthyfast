"""Script de validación rápida del catálogo de productos.

Se usa para comprobar que la aplicación pueda leer correctamente los
productos y las categorías desde la lógica principal antes de abrir la
interfaz o ejecutar pruebas más complejas.
"""

import sys
import os

# Agrega la raíz del proyecto para poder importar el módulo routes.
sys.path.insert(0, os.getcwd())
from routes import routes

# Verifica cuántos productos trae la lógica actual y muestra las categorías disponibles.
print('PRODUCTOS_COUNT:', len(routes.obtener_productos()))
print('CATEGORIAS_LEIDAS:')
for c in routes.obtener_categorias_disponibles():
    print(' -', c)
