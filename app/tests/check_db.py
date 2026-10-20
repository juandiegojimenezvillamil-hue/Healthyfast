"""Script de diagnóstico para verificar la conexión a MySQL.

Su función es chequear si la base de datos está disponible, mostrar la
configuración activa y confirmar que existen las tablas principales del
sistema antes de ejecutar operaciones de venta o administración.
"""

import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / 'app'))


# Auxiliar para extraer un valor de una fila de resultados de MySQL.
def first_value(row: Any) -> Any:
    if row is None:
        return None
    if isinstance(row, Mapping):
        return next(iter(row.values()), None)
    if isinstance(row, (tuple, list)):
        return row[0] if row else None
    return None

# Importa la conexión de la base de datos usando la ruta del proyecto.
try:
    from app.static.database.conexion import get_connection, DB_CONFIG
except ImportError:
    from static.database.conexion import get_connection, DB_CONFIG

# Muestra la configuración de conexión actual para diagnóstico rápido.
print("--- Diagnostico de Conexion MySQL Healthy Fast ---")
print(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']} | Usuario: {DB_CONFIG['user']}")
print(f"Base de datos configurada: {DB_CONFIG['database']}")

# Intenta conectarse y consulta información útil de la base de datos.
conn = get_connection()
if conn:
    print("[OK] Conexion exitosa a MySQL.")
    try:
        cur = conn.cursor()
        cur.execute("SELECT DATABASE()")
        print(f"Base de datos activa: {first_value(cur.fetchone())}")
        cur.execute("SHOW TABLES")
        tablas = [str(first_value(table)) for table in cur.fetchall()]
        print(f"Tablas encontradas ({len(tablas)}):", ", ".join(tablas))
        if 'productos' in tablas:
            cur.execute("SELECT COUNT(*) FROM productos")
            print(f"Total productos en BD: {first_value(cur.fetchone())}")
        if 'usuarios' in tablas:
            cur.execute("SELECT COUNT(*) FROM usuarios")
            print(f"Total usuarios en BD: {first_value(cur.fetchone())}")
        if 'pedidos' in tablas:
            cur.execute("SELECT COUNT(*) FROM pedidos")
            print(f"Total pedidos en BD: {first_value(cur.fetchone())}")
        cur.close()
    except Exception as e:
        print("Error consultando tablas:", e)
    finally:
        conn.close()
else:
    print("[AVISO] No hay conexion activa a MySQL. La aplicacion utilizara el fallback local.")
