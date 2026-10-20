"""Punto de entrada principal de la aplicación Healthy Fast.

Este archivo configura la ruta del proyecto, crea la aplicación Flask con
las carpetas de plantillas y archivos estáticos, carga la clave de sesión
segura y arranca el servidor del sistema.
"""

import os
import sys
from pathlib import Path

# Ajusta la ruta del proyecto para poder importar el paquete app
# sin depender del directorio de ejecución exacto.
BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / 'app'
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from flask import Flask

# Intenta importar el Blueprint desde la estructura del paquete o desde la ruta local.
try:
    from app.routes.routes import main_routes
except ImportError:
    from routes.routes import main_routes

# Crea la instancia principal de Flask con rutas de plantillas y archivos estáticos.
app = Flask(
    __name__,
    template_folder=str(APP_DIR / 'templates'),
    static_folder=str(APP_DIR / 'static')
)

# Carga la clave de sesión desde una variable de entorno.
# Si no existe, usa una clave de desarrollo por seguridad mínima.
_secret_key = os.getenv('SECRET_KEY')
if not _secret_key:
    import warnings
    warnings.warn(
        "⚠️  SECRET_KEY no configurada como variable de entorno. "
        "Se usa la clave de desarrollo — NO usar en producción.",
        stacklevel=2,
    )
    _secret_key = 'healthyfast_arquitectura_segura_2026'
app.secret_key = _secret_key

# Registra todas las rutas definidas en el Blueprint principal.
app.register_blueprint(main_routes)

# Ejecuta la aplicación con un puerto configurable y mensajes de inicio útiles.
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("=" * 60)
    print("  HEALTHY FAST STORE — Servidor Web & Móvil Iniciado")
    print(f"  Acceso Web:     http://localhost:{port}/")
    print(f"  Acceso Móvil:   http://localhost:{port}/app")
    print(f"  Panel Admin:    http://localhost:{port}/admin")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=True)
