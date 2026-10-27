import logging
import os
from typing import Any, Dict, Optional, cast

import mysql.connector
from mysql.connector import Error

logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST') or '127.0.0.1',
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER') or 'root',
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME') or 'healthdb1',
    'charset': 'utf8mb4',
    'autocommit': True,
}


def get_connection():
    """Conecta a la base configurada; retorna None si MySQL no está disponible."""
    try:
        return mysql.connector.connect(**DB_CONFIG, connection_timeout=5)
    except (Error, OSError, TimeoutError, ValueError) as error:
        logger.error(
            "No se pudo conectar a MySQL en %s:%s, base '%s', usuario '%s': %s",
            DB_CONFIG['host'],
            DB_CONFIG['port'],
            DB_CONFIG['database'],
            DB_CONFIG['user'],
            error,
        )
        return None



def obtener_conexion():
    return get_connection()


def obtener_productos():
    conexion = get_connection()
    if conexion is None:
        return []

    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT 
                p.id_producto AS id, 
                p.nombre, 
                c.nombre AS categoria, 
                p.precio, 
                p.stock
            FROM productos p
            LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
            ORDER BY p.id_producto DESC
        """
        cursor.execute(query)
        productos = cursor.fetchall()
        return productos
    except Exception as e:
        print("Error al obtener productos:", e)
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if conexion:
            conexion.close()


def obtener_factura_por_numero(numero_factura):
    """Lee la factura y sus líneas desde las tablas relacionales de MySQL."""
    conexion = get_connection()
    if conexion is None:
        return None

    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM facturas WHERE numero_factura = %s LIMIT 1",
            (numero_factura,),
        )
        fila = cast(Optional[Dict[str, Any]], cursor.fetchone())
        if not fila:
            return None

        cursor.execute(
            """
            SELECT id_producto, codigo, descripcion AS nombre, unidad, cantidad,
                precio_unitario, descuento, iva_porcentaje, iva, total
            FROM detalle_factura WHERE id_factura = %s ORDER BY id_detalle_factura
            """,
            (fila['id_factura'],),
        )
        lineas = cursor.fetchall() or []
        return {
            'numero_factura': fila.get('numero_factura'),
            'codigo_unico': fila.get('codigo_unico'),
            'fecha_emision': fila.get('fecha'),
            'fecha_vencimiento': fila.get('fecha_vencimiento'),
            'forma_pago': fila.get('forma_pago'),
            'medio_pago': fila.get('medio_pago'),
            'tipo_operacion': fila.get('tipo_operacion'),
            'moneda': 'COP',
            'vendedor': {
                'razon_social': fila.get('vendedor_razon_social'),
                'nit': fila.get('vendedor_nit'),
                'pais': fila.get('vendedor_pais'),
                'departamento': fila.get('vendedor_departamento'),
                'ciudad': fila.get('vendedor_ciudad'),
                'direccion': fila.get('vendedor_direccion'),
                'telefono': fila.get('vendedor_telefono'),
                'email': fila.get('vendedor_email'),
            },
            'comprador': {
                'nombre': fila.get('comprador_nombre'),
                'tipo_documento': fila.get('comprador_tipo_documento'),
                'documento': fila.get('comprador_documento'),
                'pais': fila.get('comprador_pais'),
                'departamento': fila.get('comprador_departamento'),
                'ciudad': fila.get('comprador_ciudad'),
                'direccion': fila.get('comprador_direccion'),
                'telefono': fila.get('comprador_telefono'),
                'email': fila.get('comprador_email'),
            },
            'lineas': lineas,
            'subtotal': fila.get('subtotal') or 0,
            'descuento': fila.get('descuento') or 0,
            'total_bruto': fila.get('total_bruto') or 0,
            'iva_porcentaje': fila.get('iva_porcentaje') or 19,
            'iva': fila.get('total_impuestos') or 0,
            'total_impuestos': fila.get('total_impuestos') or 0,
            'total_neto': fila.get('total_neto') or fila.get('total') or 0,
            'total_final': fila.get('total_neto') or fila.get('total') or 0,
        }
    except Error as error:
        print("Error al consultar la factura en MySQL:", error)
        return None
    finally:
        if cursor is not None:
            cursor.close()
        conexion.close()


def obtener_usuarios():
    conexion = get_connection()
    if conexion is None:
        return []

    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT 
                u.id_usuario,
                u.correo AS correo, 
                u.nombre AS nombre, 
                COALESCE(r.nombre, 'cliente') AS rol
            FROM usuarios u
            LEFT JOIN roles r ON u.id_rol = r.id_rol
            ORDER BY u.id_usuario ASC
        """
        cursor.execute(query)
        usuarios = cursor.fetchall()
        return usuarios
    except Exception as e:
        print("Error al obtener usuarios:", e)
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if conexion:
            conexion.close()


def obtener_pedidos():
    conexion = get_connection()
    if conexion is None:
        return []

    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        query = """
            SELECT 
                CONCAT('HF-', f.id_factura) AS id, 
                f.id_factura,
                COALESCE(c.nombre, 'Cliente Registrado') AS cliente, 
                f.total, 
                'Pendiente' AS estado,
                f.fecha
            FROM facturas f
            LEFT JOIN pedidos p ON f.id_pedido = p.id_pedido
            LEFT JOIN clientes c ON p.id_cliente = c.id_cliente
            ORDER BY f.id_factura DESC
        """
        cursor.execute(query)
        pedidos = cursor.fetchall()
        return pedidos
    except Exception as e:
        print("Error al obtener pedidos:", e)
        return []
    finally:
        if cursor is not None:
            cursor.close()
        if conexion:
            conexion.close()


def _asegurar_esquema_facturacion(cursor):
    """Migra facturas antiguas y crea el detalle fiscal sin repetir cambios."""
    cursor.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = DATABASE() AND table_name = 'facturas'
        """
    )
    columnas = {fila[0] for fila in cursor.fetchall()}
    definiciones = {
        'numero_factura': 'VARCHAR(30) NULL',
        'codigo_unico': 'CHAR(36) NULL',
        'fecha_vencimiento': 'DATE NULL',
        'forma_pago': 'VARCHAR(50) NULL',
        'medio_pago': 'VARCHAR(80) NULL',
        'tipo_operacion': 'VARCHAR(80) NULL',
        'subtotal': 'DECIMAL(12,2) NULL',
        'descuento': 'DECIMAL(12,2) NULL',
        'total_bruto': 'DECIMAL(12,2) NULL',
        'iva_porcentaje': 'DECIMAL(5,2) NULL',
        'total_impuestos': 'DECIMAL(12,2) NULL',
        'total_neto': 'DECIMAL(12,2) NULL',
        'comprador_nombre': 'VARCHAR(200) NULL',
        'comprador_tipo_documento': 'VARCHAR(30) NULL',
        'comprador_documento': 'VARCHAR(60) NULL',
        'comprador_pais': 'VARCHAR(80) NULL',
        'comprador_departamento': 'VARCHAR(100) NULL',
        'comprador_ciudad': 'VARCHAR(100) NULL',
        'comprador_direccion': 'VARCHAR(255) NULL',
        'comprador_telefono': 'VARCHAR(30) NULL',
        'comprador_email': 'VARCHAR(150) NULL',
        'vendedor_razon_social': 'VARCHAR(200) NULL',
        'vendedor_nit': 'VARCHAR(60) NULL',
        'vendedor_pais': 'VARCHAR(80) NULL',
        'vendedor_departamento': 'VARCHAR(100) NULL',
        'vendedor_ciudad': 'VARCHAR(100) NULL',
        'vendedor_direccion': 'VARCHAR(255) NULL',
        'vendedor_telefono': 'VARCHAR(30) NULL',
        'vendedor_email': 'VARCHAR(150) NULL',
    }
    for columna, definicion in definiciones.items():
        if columna not in columnas:
            cursor.execute(f"ALTER TABLE facturas ADD COLUMN {columna} {definicion}")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS detalle_factura (
            id_detalle_factura INT NOT NULL AUTO_INCREMENT,
            id_factura INT NOT NULL,
            id_producto INT NULL,
            codigo VARCHAR(80) NOT NULL,
            descripcion VARCHAR(255) NOT NULL,
            unidad VARCHAR(20) NOT NULL,
            cantidad DECIMAL(12,2) NOT NULL,
            precio_unitario DECIMAL(12,2) NOT NULL,
            descuento DECIMAL(12,2) NOT NULL DEFAULT 0,
            iva_porcentaje DECIMAL(5,2) NOT NULL DEFAULT 19,
            iva DECIMAL(12,2) NOT NULL DEFAULT 0,
            total DECIMAL(12,2) NOT NULL,
            PRIMARY KEY (id_detalle_factura),
            KEY idx_detalle_factura_factura (id_factura),
            CONSTRAINT fk_detalle_factura_factura
                FOREIGN KEY (id_factura) REFERENCES facturas (id_factura)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.statistics
        WHERE table_schema = DATABASE() AND table_name = 'facturas'
            AND index_name = 'uq_facturas_numero_factura'
        """
    )
    indice = cursor.fetchone()
    if not indice or not indice[0]:
        cursor.execute(
            "CREATE UNIQUE INDEX uq_facturas_numero_factura ON facturas (numero_factura)"
        )


def _numero_factura_disponible(cursor, numero_factura):
    """Evita reutilizar un número que ya exista en MySQL."""
    numero = str(numero_factura or 'FACT-000001')
    while True:
        cursor.execute(
            "SELECT id_factura FROM facturas WHERE numero_factura = %s LIMIT 1",
            (numero,),
        )
        if cursor.fetchone() is None:
            return numero
        try:
            consecutivo = int(numero.removeprefix('FACT-')) + 1
        except ValueError:
            consecutivo = 1
        numero = f"FACT-{consecutivo:06d}"


def guardar_pedido_completo_bd(cliente_info, items_carrito, metodo_pago, total, factura_data=None):
    """
    Registra la transacción completa en MySQL:
    1. Clientes
    2. Pedidos
    3. Detalle_pedido
    4. Facturas
    5. Pagos
    6. Descuenta stock de productos
    """
    conexion = get_connection()
    if conexion is None:
        return None

    cursor = None
    try:
        cursor = conexion.cursor()
        _asegurar_esquema_facturacion(cursor)
        conexion.start_transaction()

        # 1. Obtener o crear cliente
        nombre_completo = f"{cliente_info.get('nombre', '')} {cliente_info.get('apellido', '')}".strip() or "Cliente"
        correo = cliente_info.get('email', '') or 'cliente@healthyfast.com'
        telefono = cliente_info.get('telefono', '')

        cursor.execute("SELECT id_cliente FROM clientes WHERE correo = %s LIMIT 1", (correo,))
        cliente_row = cursor.fetchone()
        if cliente_row is not None and isinstance(cliente_row, (tuple, list)):
            cliente_id_raw = cliente_row[0]
            id_cliente = int(str(cliente_id_raw)) if cliente_id_raw is not None else 0
            cursor.execute(
                "UPDATE clientes SET nombre = %s, telefono = %s WHERE id_cliente = %s",
                (nombre_completo, telefono, id_cliente)
            )
        else:
            cursor.execute(
                "INSERT INTO clientes (nombre, telefono, correo) VALUES (%s, %s, %s)",
                (nombre_completo, telefono, correo)
            )
            last_id = cursor.lastrowid
            if last_id is None:
                raise ValueError("No se pudo obtener el id del cliente insertado.")
            id_cliente = int(str(last_id))

        # 2. Insertar pedido
        cursor.execute(
            "INSERT INTO pedidos (fecha, id_cliente) VALUES (CURDATE(), %s)",
            (id_cliente,)
        )
        pedido_id = cursor.lastrowid
        if pedido_id is None:
            raise ValueError("No se pudo obtener el id del pedido.")
        id_pedido = int(str(pedido_id))

        # 3. Insertar detalles de pedido y actualizar stock
        for item in items_carrito:
            id_prod = item.get('id')
            cant = int(item.get('cantidad', 1) or 1)
            precio_unit = float(item.get('precio', 0) or 0)

            # Verificar si existe id numérico en productos
            if str(id_prod).isdigit():
                cursor.execute(
                    """
                    INSERT INTO detalle_pedido (id_pedido, id_producto, cantidad, precio)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (id_pedido, int(id_prod), cant, precio_unit)
                )
                # Descontar stock
                cursor.execute(
                    "UPDATE productos SET stock = stock - %s WHERE id_producto = %s AND stock >= %s",
                    (cant, int(id_prod), cant)
                )
                if cursor.rowcount != 1:
                    raise ValueError(f"Stock insuficiente para el producto {id_prod}.")

        # 4. Insertar factura y conservar los datos usados al emitirla.
        factura_data = factura_data or {}
        comprador = factura_data.get('comprador', {})
        vendedor = factura_data.get('vendedor', {})
        numero_factura = _numero_factura_disponible(
            cursor, factura_data.get('numero_factura')
        )
        factura_data['numero_factura'] = numero_factura
        cursor.execute(
            """
            INSERT INTO facturas (
                id_pedido, fecha, total, numero_factura, codigo_unico, fecha_vencimiento,
                forma_pago, medio_pago, tipo_operacion, subtotal, descuento, total_bruto,
                iva_porcentaje, total_impuestos, total_neto, comprador_nombre,
                comprador_tipo_documento, comprador_documento, comprador_pais,
                comprador_departamento, comprador_ciudad, comprador_direccion,
                comprador_telefono, comprador_email, vendedor_razon_social, vendedor_nit,
                vendedor_pais, vendedor_departamento, vendedor_ciudad, vendedor_direccion,
                vendedor_telefono, vendedor_email
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                id_pedido,
                factura_data.get('fecha_emision'),
                float(factura_data.get('total_final', total)),
                numero_factura,
                factura_data.get('codigo_unico'),
                factura_data.get('fecha_vencimiento'),
                factura_data.get('forma_pago'),
                factura_data.get('medio_pago'),
                factura_data.get('tipo_operacion'),
                factura_data.get('subtotal'),
                factura_data.get('descuento'),
                factura_data.get('total_bruto'),
                factura_data.get('iva_porcentaje'),
                factura_data.get('total_impuestos'),
                factura_data.get('total_neto'),
                comprador.get('nombre'),
                comprador.get('tipo_documento'),
                comprador.get('documento'),
                comprador.get('pais'),
                comprador.get('departamento'),
                comprador.get('ciudad'),
                comprador.get('direccion'),
                comprador.get('telefono'),
                comprador.get('email'),
                vendedor.get('razon_social'),
                vendedor.get('nit'),
                vendedor.get('pais'),
                vendedor.get('departamento'),
                vendedor.get('ciudad'),
                vendedor.get('direccion'),
                vendedor.get('telefono'),
                vendedor.get('email'),
            ),
        )
        id_factura = cursor.lastrowid

        for linea in factura_data.get('lineas', []):
            cursor.execute(
                """
                INSERT INTO detalle_factura (
                    id_factura, id_producto, codigo, descripcion, unidad, cantidad,
                    precio_unitario, descuento, iva_porcentaje, iva, total
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    id_factura,
                    int(linea['id_producto']) if str(linea.get('id_producto', '')).isdigit() else None,
                    linea.get('codigo', 'N/A'),
                    linea.get('nombre', 'Producto'),
                    linea.get('unidad', 'UND'),
                    linea.get('cantidad', 0),
                    linea.get('precio_unitario', 0),
                    linea.get('descuento', 0),
                    linea.get('iva_porcentaje', 19),
                    linea.get('iva', 0),
                    linea.get('total', 0),
                ),
            )

        # 5. Insertar pago
        cursor.execute(
            """
            INSERT INTO pagos (id_factura, monto, fecha)
            VALUES (%s, %s, CURDATE())
            """,
            (id_factura, float(total))
        )

        conexion.commit()
        return {
            'id_factura': id_factura,
            'id_pedido': id_pedido,
            'numero_factura': numero_factura,
            'numero_orden': f"HF-{id_factura}",
            'total': float(total),
            'estado': 'Pagada' if metodo_pago == 'tarjeta' else 'Pendiente'
        }

    except Error as e:
        print("Error al guardar pedido completo en MySQL:", e)
        if conexion:
            conexion.rollback()
        return False
    except (ValueError, TypeError) as e:
        print("Error al validar el pedido en MySQL:", e)
        if conexion:
            conexion.rollback()
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conexion:
            conexion.close()