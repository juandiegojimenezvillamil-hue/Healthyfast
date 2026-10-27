"""Archivo central de rutas, lógica de negocio y flujo comercial de Healthy Fast.

Este módulo reúne el manejo de usuarios, productos, categorías, login,
carrito, pago y administración. Es la capa principal que conecta la vista
(HTML) con la base de datos y los modelos de dominio del proyecto.
"""

import json
import os
import secrets
import threading
import unicodedata
import zlib
from datetime import datetime
from decimal import Decimal
from functools import wraps
from typing import Any, cast
from urllib.parse import quote, unquote
from mysql.connector import Error
from flask import Blueprint, abort, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash

# Importa funciones de conexión para consultar y guardar datos en la BD.
try:
    from static.database.conexion import (
        get_connection,
        obtener_productos as db_obtener_productos,
        obtener_usuarios as db_obtener_usuarios,
        obtener_pedidos as db_obtener_pedidos,
        guardar_pedido_completo_bd,
        obtener_factura_por_numero,
    )
except ImportError:
    from app.static.database.conexion import (
        get_connection,
        obtener_productos as db_obtener_productos,
        obtener_usuarios as db_obtener_usuarios,
        obtener_pedidos as db_obtener_pedidos,
        guardar_pedido_completo_bd,
        obtener_factura_por_numero,
    )

# Importa los modelos orientados a objetos del dominio del negocio.
try:
    from modelo import (
        Cliente, Empleado, Categoria, Producto as ModeloProducto,
        Pago, PagoEfectivo, PagoTarjeta, Envio, Factura, FacturaDetalle
    )
except ImportError:
    from app.modelo import (
        Cliente, Empleado, Categoria, Producto as ModeloProducto,
        Pago, PagoEfectivo, PagoTarjeta, Envio, Factura, FacturaDetalle
    )

try:
    from facturacion import calcular_factura, generar_pdf_factura
except ImportError:
    from app.facturacion import calcular_factura, generar_pdf_factura

# Blueprint principal del sitio que agrupa todas las rutas del proyecto.
main_routes = Blueprint('main', __name__)


# Decorador que restringe el acceso solo a administradores.
def admin_required(func):
    """Permite ejecutar una ruta únicamente a usuarios con rol administrador."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Se revisa el rol guardado en la sesión antes de ejecutar la función protegida.
        rol_actual = str(session.get('rol') or '').strip().lower()
        if rol_actual != 'administrador':
            # El usuario no autorizado recibe un mensaje y vuelve al formulario de login.
            flash('Acceso denegado. Debes iniciar sesión como administrador.', 'danger')
            return redirect(url_for('main.login'))
        # Si el rol es correcto, se ejecuta la ruta original sin modificar sus argumentos.
        return func(*args, **kwargs)
    return wrapper


# Decorador que exige que el usuario haya iniciado sesión para comprar.
def usuario_required(func):
    """Protege las rutas de compra para usuarios que ya iniciaron sesión."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Guarda la URL actual para regresar allí después de iniciar sesión.
        if not session.get('usuario'):
            session['despues_login'] = request.full_path.rstrip('?')
            flash('Debes iniciar sesión para continuar con la compra.', 'warning')
            return redirect(url_for('main.login'))
        # El usuario autenticado puede continuar con el proceso solicitado.
        return func(*args, **kwargs)
    return wrapper


# Datos iniciales del catálogo para uso en modo demo y fallback local.
# Sirven como respaldo cuando la base de datos no está disponible.
PRODUCTOS_BD = [
    {"id": 1, "nombre": "Botiquín Industrial Platinum", "categoria": "emergency", "precio": 185000, "imagen": "https://images.unsplash.com/photo-1607613009820-a29f7bb81c04?auto=format&fit=crop&w=500", "badge": "Más Vendido", "desc": "Botiquín de primera respuesta con 85 implementos certificados: gasas, vendas, alcohol, guantes, analgésicos y tijeras de paramédico. Ideal para empresas, hogares y vehículos en Colombia.", "stock": 15},
    {"id": 2, "nombre": "Glow Serum Vitamina C", "categoria": "skincare", "precio": 125000, "imagen": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=500", "badge": "Premium", "desc": "Sérum facial con ácido hialurónico al 2% y vitamina C estabilizada. Hidrata en profundidad, reduce manchas y aporta luminosidad visible desde la primera semana de uso.", "stock": 24},
    {"id": 3, "nombre": "Aceite Corporal Relajante", "categoria": "body", "precio": 79000, "imagen": "https://images.unsplash.com/photo-1617897903246-719242758050?auto=format&fit=crop&w=500", "badge": "Wellness", "desc": "Aceite 100% natural de lavanda y almendras dulces. Hidrata y suaviza la piel seca, alivia tensiones musculares y activa la circulación. Perfecto para masajes y rutina nocturna.", "stock": 10},
    {"id": 4, "nombre": "Kit Patitas Sanas", "categoria": "pets", "precio": 48000, "imagen": "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?auto=format&fit=crop&w=500", "badge": "Mascotas", "desc": "Bálsamo veterinario para cojinetes de perros y gatos. Protege de superficies calientes y frías, hidrata grietas y previene infecciones. Formulado con cera de abeja e ingredientes naturales seguros.", "stock": 30}
]

# Usuarios demo para pruebas rápidas y acceso al panel admin sin BD.
# Mantener las credenciales compatibles con los datos semilla de la base de datos
# (admin@healthyfast.com / hector009 y estudiante@healthyfast.com / cliente123).
USUARIOS_BD = [
    {"correo": "admin@healthyfast.com", "nombre": "Profesor Evaluador", "rol": "administrador", "password": "hector009"},
    {"correo": "estudiante@healthyfast.com", "nombre": "Samuel Vega", "rol": "cliente", "password": "cliente123"},
    {"correo": "cliente@healthyfast.com", "nombre": "Laura Cliente", "rol": "cliente", "password": "roro6"},
]

CREDENCIALES_DEMO = {
    "admin@healthyfast.com": {"hector009", "admin123"},
    "estudiante@healthyfast.com": {"cliente123"},
    "cliente@healthyfast.com": {"cliente123", "roro6"},
    "sofia.admin@healthyfast.com": {"hector010"},
}


def _credenciales_demo_validas(correo: str, password: str) -> bool:
    """Acepta los accesos demo y los aliases usados en la documentación y la BD."""
    correo_normalizado = (correo or '').strip().lower()
    if not correo_normalizado or not password:
        return False

    aliases = {correo_normalizado}
    if correo_normalizado in {'cliente@healthyfast.com', 'estudiante@healthyfast.com'}:
        aliases.update({'cliente@healthyfast.com', 'estudiante@healthyfast.com'})

    for alias in aliases:
        if password in CREDENCIALES_DEMO.get(alias, set()):
            return True
    return False

# Datos de pedidos de ejemplo para mostrar estadísticas y fallback local.
PEDIDOS_BD = [
    {"id": "HF-9482", "cliente": "Samuel Vega", "total": 258000, "estado": "Completado"},
    {"id": "HF-9483", "cliente": "Andrea Gómez", "total": 78000, "estado": "Pendiente"},
    {"id": "HF-9484", "cliente": "jose santana", "total": 78000, "estado": "Pendiente"}
]

# Listado de categorías que se muestran al usuario en la tienda.
CATEGORIAS_DISPONIBLES = [
    {"slug": "skincare", "nombre": "Skincare"},
    {"slug": "body", "nombre": "Body Care"},
    {"slug": "emergency", "nombre": "Emergency"},
    {"slug": "pets", "nombre": "Pets"},
]

CATEGORIAS_EXCLUIDAS = {
    'bebidas saludables', 'snacks orgánicos', 'bebidas', 'snacks',
    'suplementos', 'suplemento', 'frutos secos', 'proteínas', 'proteinas',
    'emergency',
}
DESCRIPCIONES_CATEGORIA = {
    'skincare': 'Cuidado facial para hidratar, proteger y mejorar la apariencia de la piel.',
    'body': 'Cuidado corporal para hidratar, relajar y mantener la piel saludable.',
    'emergency': 'Elementos esenciales para atender primeros auxilios en casa, trabajo o vehículo.',
    'pets': 'Cuidado e higiene para mantener saludables y protegidas a tus mascotas.',
}

PRODUCTOS_DATA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'database', 'productos_persistidos.json'))
PEDIDOS_DATA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'database', 'pedidos_persistidos.json'))
_FACTURA_SEQUENCE_LOCK = threading.Lock()
_ULTIMO_NUMERO_FACTURA = 0


def _leer_pedidos_fallback():
    """Lee los pedidos guardados en JSON y crea el archivo si aún no existe."""
    # La carpeta se crea automáticamente para que el modo local funcione desde cero.
    if not os.path.exists(PEDIDOS_DATA_FILE):
        os.makedirs(os.path.dirname(PEDIDOS_DATA_FILE), exist_ok=True)
        with open(PEDIDOS_DATA_FILE, 'w', encoding='utf-8') as archivo:
            json.dump([dict(p) for p in PEDIDOS_BD], archivo, ensure_ascii=False, indent=2)
        return [dict(p) for p in PEDIDOS_BD]

    try:
        # Intenta recuperar la lista persistida en el archivo de respaldo.
        with open(PEDIDOS_DATA_FILE, 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)
            if isinstance(datos, list):
                return datos
    except (json.JSONDecodeError, OSError):
        # Si el archivo está dañado o no puede leerse, se usan los pedidos demo.
        pass

    return [dict(p) for p in PEDIDOS_BD]


def _guardar_pedidos_fallback(pedidos):
    """Escribe la lista de pedidos en el archivo JSON local."""
    # Garantiza que exista la carpeta antes de abrir el archivo en modo escritura.
    os.makedirs(os.path.dirname(PEDIDOS_DATA_FILE), exist_ok=True)
    with open(PEDIDOS_DATA_FILE, 'w', encoding='utf-8') as archivo:
        json.dump(pedidos, archivo, ensure_ascii=False, indent=2)
    return True


def _categoria_excluida(categoria):
    """Indica si una categoría debe ocultarse del catálogo público."""
    # Se normalizan acentos y guiones para comparar nombres con distintos formatos.
    categoria_normalizada = _normalizar_texto(categoria).replace('-', ' ')
    return categoria_normalizada in {_normalizar_texto(item) for item in CATEGORIAS_EXCLUIDAS}


def _producto_visible(producto):
    """Devuelve True cuando el producto pertenece a una categoría permitida."""
    return not _categoria_excluida(producto.get('categoria', ''))


def _productos_fallback_visibles():
    """Obtiene del JSON únicamente los productos que pueden mostrarse al cliente."""
    return [p for p in _leer_productos_fallback() if _producto_visible(p)]


def guardar_pedido_fallback(pedido):
    """Añade un pedido al inicio de la colección persistida localmente."""
    # El pedido más reciente queda primero para facilitar su visualización en el panel.
    pedidos = _leer_pedidos_fallback()
    pedidos.insert(0, pedido)
    _guardar_pedidos_fallback(pedidos)
    return True


def obtener_ultimo_envio_usuario(correo):
    """Recupera la última dirección usada por un cliente desde los pedidos locales."""
    # Se normaliza el correo para que las mayúsculas no impidan encontrar coincidencias.
    correo_normalizado = (correo or '').strip().lower()
    if not correo_normalizado:
        return None

    # Recorre los pedidos desde el más reciente hasta encontrar una dirección válida.
    for pedido in _leer_pedidos_fallback():
        if str(pedido.get('email') or '').strip().lower() != correo_normalizado:
            continue
        if not pedido.get('direccion'):
            continue
        # Se separa el nombre completo para rellenar nombre y apellido del formulario.
        cliente = str(pedido.get('cliente') or '')
        return {
            'email': correo_normalizado,
            'nombre': cliente.split(' ', 1)[0],
            'apellido': cliente.split(' ', 1)[1] if ' ' in cliente else '',
            'telefono': pedido.get('telefono', ''),
            'tipo_documento': pedido.get('tipo_documento', ''),
            'documento': pedido.get('documento', ''),
            'pais': pedido.get('pais', 'Colombia'),
            'departamento': pedido.get('departamento', ''),
            'direccion': pedido.get('direccion', ''),
            'referencia': pedido.get('referencia', ''),
            'ciudad': pedido.get('ciudad', ''),
            'cp': pedido.get('cp', ''),
        }
    return None


def obtener_pedidos_totales():
    """Obtiene pedidos desde MySQL y usa JSON cuando la consulta no devuelve datos."""
    # La base de datos es la fuente principal cuando está disponible.
    pedidos_db = db_obtener_pedidos()
    if pedidos_db:
        return pedidos_db
    return _leer_pedidos_fallback()



def slug_categoria(categoria):
    """Convierte el nombre de una categoría a un identificador URL estable."""
    if not categoria:
        # Valor usado cuando el producto no tiene categoría.
        return "sin-categoria"
    texto = str(categoria).strip().lower()
    mapa = {
        "skincare": "skincare",
        "body": "body",
        "body care": "body",
        "emergency": "emergency",
        "pets": "pets",
        "pets care": "pets",
    }
    # Para categorías conocidas se usa el slug oficial; las demás se vuelven compatibles con URL.
    return mapa.get(texto, texto.replace(' ', '-'))


def categoria_slug_de_producto(producto):
    """Obtiene el slug de categoría de un producto normalizado o proveniente de BD."""
    if not producto:
        return "sin-categoria"
    # Se prueban las posibles claves porque el producto puede venir de MySQL, JSON o formulario.
    valor = producto.get('categoria') or producto.get('categoria_visual') or producto.get('subcategoria')
    if valor in (None, ''):
        return "sin-categoria"
    return slug_categoria(valor)


def _producto_nombre_contiene_mixto(producto):
    """Indica si el nombre del producto incluye la palabra completa "mixto"."""
    nombre = _normalizar_texto(producto.get('nombre') or '')
    return 'mixto' in nombre.split()


def _producto_pertenece_a_categoria(producto, categoria_slug):
    """Incluye en Mixto los productos marcados así en el nombre, sin cambiar su categoría."""
    return (
        categoria_slug_de_producto(producto) == categoria_slug
        or (categoria_slug == 'mixto' and _producto_nombre_contiene_mixto(producto))
    )


def _agregar_categoria_mixto(categorias, productos):
    """Añade el filtro Mixto a la tienda si hay productos que lo indican en el nombre."""
    if (
        any(_producto_nombre_contiene_mixto(producto) for producto in productos)
        and not any(slug_categoria(categoria.get('slug') or categoria.get('nombre')) == 'mixto'
                    for categoria in categorias)
    ):
        return [*categorias, {'slug': 'mixto', 'nombre': 'Mixto'}]
    return categorias


def obtener_categorias_disponibles():
    """Carga las categorías públicas desde MySQL o devuelve las categorías estáticas."""
    # Se intenta consultar la BD para mostrar también categorías creadas por administración.
    conexion = get_connection()
    categorias = []
    if conexion is not None:
        try:
            cursor = conexion.cursor()
            cursor.execute("SELECT id_categoria, nombre FROM categorias ORDER BY nombre ASC")
            # Convierte cada fila de la consulta al formato que esperan las plantillas.
            for row in cursor.fetchall():
                row_data = cast(tuple[Any, Any], row)
                id_cat = row_data[0]
                nombre = row_data[1]
                if _categoria_excluida(nombre):
                    continue
                categorias.append({"id": int(id_cat), "slug": slug_categoria(nombre), "nombre": nombre})
            # Si la BD está vacía, conserva las categorías iniciales del proyecto.
            return categorias if categorias else [
                categoria for categoria in CATEGORIAS_DISPONIBLES
                if not _categoria_excluida(categoria['nombre'])
            ]
        except Exception:
            # Cualquier problema de conexión activa el retorno de categorías estáticas.
            pass
        finally:
            try:
                conexion.close()
            except Exception:
                pass

    # Fallback a la lista estática si no hay conexión
    return [
        {"id": None, "slug": c["slug"], "nombre": c["nombre"]}
        for c in CATEGORIAS_DISPONIBLES
        if not _categoria_excluida(c['nombre'])
    ]


def nombre_categoria(slug):
    """Devuelve el nombre visible de una categoría a partir de su slug."""
    if not slug:
        return 'Todos'
    for categoria in CATEGORIAS_DISPONIBLES:
        if categoria['slug'] == slug:
            return categoria['nombre']
    return slug.replace('-', ' ').title()


def productos_destacados_por_categoria(productos):
    """Selecciona un producto destacado para cada categoría disponible."""
    destacados = []
    categorias = obtener_categorias_disponibles()
    # Busca primero por ID, que es la relación más exacta en la base de datos.
    for categoria in categorias:
        # Priorizar match por id_categoria si el producto lo contiene
        producto = None
        if categoria.get('id') is not None:
            producto = next((p for p in productos if p.get('id_categoria') == categoria['id']), None)
        # Si no hay ID, intenta encontrarlo mediante el slug de categoría.
        if not producto:
            producto = next((p for p in productos if p.get('categoria') == categoria['slug']), None)
        if producto:
            destacados.append(producto)
    return destacados


def _normalizar_texto(texto):
    """Quita acentos y convierte un texto a minúsculas para comparaciones."""
    # NFKD + encode('ascii') ya elimina todos los acentos; los .replace eran código muerto (bug #6)
    return unicodedata.normalize('NFKD', str(texto)).encode('ascii', 'ignore').decode('ascii').lower()


# Palabras muy comunes que no aportan a distinguir un producto de otro
# (evita falsos empates como "para", "de", "con" coincidiendo con cualquier
# archivo que también las contenga).
_PALABRAS_VACIAS = {
    'para', 'con', 'sin', 'del', 'las', 'los', 'una', 'uno', 'que',
    'por', 'esta', 'este', 'sus', 'tus',
}


def resolver_imagen_producto(nombre, categoria=None, imagenes_excluidas=None):
    """Encuentra la imagen apropiada buscando primero en carpetas locales y luego en URLs de respaldo."""
    # Todas las imágenes del catálogo se encuentran dentro de esta carpeta raíz.
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'img', 'categorias'))
    if not os.path.isdir(base_dir):
        return "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=500"

    # Relaciona los slugs públicos con los nombres reales de las carpetas.
    alias_categoria = {
        'emergency': 'botiquin',
        'pets': 'mascotas',
        'body': 'mixto',
        'skincare': 'mujer',
    }

    # Subcarpetas reales en disco (las que existen)
    subcarpetas_disponibles = sorted(
        d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))
    )

    nombre_limpio = _normalizar_texto(nombre or '')

    # ── Detectar subcarpeta por palabras clave en el nombre del producto ──
    # Ejemplo: "serum facial hombre" → carpeta "hombre"
    #          "balsamo mixto"       → carpeta "mixto"
    #          "aceite para perros"  → carpeta "mascotas"
    _PALABRAS_SUBCARPETA = {
        'hombre':   'hombre',
        'mujer':    'mujer',
        'mixto':    'mixto',
        'mascotas': 'mascotas',
        'botiquin': 'botiquin',
        'perro':    'mascotas',
        'perros':   'mascotas',
        'gato':     'mascotas',
        'gatos':    'mascotas',
    }
    # Detecta una carpeta concreta cuando el nombre contiene una palabra clave.
    carpeta_por_nombre = None
    for palabra, subcarpeta in _PALABRAS_SUBCARPETA.items():
        if palabra in nombre_limpio and os.path.isdir(os.path.join(base_dir, subcarpeta)):
            carpeta_por_nombre = subcarpeta
            break

    carpeta = None
    if carpeta_por_nombre:
        # El nombre indica directamente la subcarpeta → buscar ahí primero
        carpeta = carpeta_por_nombre
    elif categoria:
        categoria_norm = slug_categoria(categoria)
        categoria_dir = os.path.join(base_dir, categoria_norm)
        if os.path.isdir(categoria_dir):
            carpeta = categoria_norm
        else:
            carpeta = alias_categoria.get(categoria_norm, categoria_norm)
            if not os.path.isdir(os.path.join(base_dir, carpeta)):
                carpeta = None

    # Busca en todas las carpetas para tolerar categorías generales o nombres
    # abreviados, pero conserva prioridad para la carpeta más probable.
    carpetas_a_buscar = ([carpeta] if carpeta else []) + [
        subcarpeta for subcarpeta in subcarpetas_disponibles if subcarpeta != carpeta
    ]

    # Evita reutilizar imágenes ya asignadas a otros productos de la consulta.
    imagenes_excluidas = set(imagenes_excluidas or ())
    palabras = [palabra for palabra in nombre_limpio.split() if len(palabra) > 2 and palabra not in _PALABRAS_VACIAS]
    candidatos = []


    # Recorre imágenes y calcula un puntaje según la similitud de nombres.
    prioridad_carpeta = {nombre: indice for indice, nombre in enumerate(carpetas_a_buscar)}
    for subcarpeta in carpetas_a_buscar:
        carpeta_abs = os.path.join(base_dir, subcarpeta)
        for root, _, files in os.walk(carpeta_abs):
            for archivo in sorted(files):  # orden determinístico dentro de la carpeta
                if not archivo.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                    continue
                ruta = os.path.join(root, archivo)
                nombre_archivo = _normalizar_texto(os.path.splitext(archivo)[0])
                if not nombre_limpio:
                    continue
                if nombre_limpio == nombre_archivo:
                    puntaje = 1000
                elif nombre_limpio in nombre_archivo or nombre_archivo in nombre_limpio:
                    puntaje = 500
                else:
                    coincidencias = sum(1 for palabra in palabras if palabra in nombre_archivo)
                    puntaje = coincidencias
                if puntaje >= 1:
                    # Desempate: menor diferencia de longitud = nombre de archivo más cercano al producto
                    diferencia_longitud = abs(len(nombre_archivo) - len(nombre_limpio))
                    candidatos.append((puntaje, prioridad_carpeta[subcarpeta], diferencia_longitud, ruta))

    if candidatos:
        # Prioriza similitud, luego categoría y finalmente longitud del nombre.
        candidatos.sort(key=lambda item: (-item[0], item[1], item[2], item[3]))
        for puntaje, _, _, mejor_ruta in candidatos:
            ruta_relativa = os.path.relpath(mejor_ruta, os.path.join(os.path.dirname(__file__), '..'))
            ruta_web = '/' + ruta_relativa.replace('\\', '/').replace(' ', '%20')
            if ruta_web not in imagenes_excluidas or puntaje == 1000:
                return ruta_web


    # Si no hay coincidencia por nombre, repartir las imágenes locales de forma
    # determinística para que productos distintos no reciban siempre la primera.
    # Sin coincidencia textual, reparte las imágenes de forma estable usando CRC32.
    carpeta_fallback = None
    if categoria:
        categoria_norm = slug_categoria(categoria)
        carpeta_fallback = alias_categoria.get(categoria_norm, categoria_norm)
        carpeta_fallback_dir = os.path.join(base_dir, carpeta_fallback)
        if os.path.isdir(carpeta_fallback_dir):
            imagenes_fallback = []
            for root, _, files in os.walk(carpeta_fallback_dir):
                for archivo in files:
                    if archivo.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                        ruta = os.path.join(root, archivo)
                        imagenes_fallback.append(ruta)
            if imagenes_fallback:
                imagenes_fallback.sort()
                indice = zlib.crc32(nombre_limpio.encode('utf-8')) % len(imagenes_fallback)
                imagenes_ordenadas = imagenes_fallback[indice:] + imagenes_fallback[:indice]
                for ruta in imagenes_ordenadas:
                    ruta_relativa = os.path.relpath(ruta, os.path.join(os.path.dirname(__file__), '..'))
                    ruta_web = '/' + ruta_relativa.replace('\\', '/').replace(' ', '%20')
                    if ruta_web not in imagenes_excluidas:
                        return ruta_web

            imagenes_fallback = []
            for subcarpeta in sorted(os.listdir(base_dir)):
                carpeta_abs = os.path.join(base_dir, subcarpeta)
                if not os.path.isdir(carpeta_abs):
                    continue
                for root, _, files in os.walk(carpeta_abs):
                    for archivo in files:
                        if archivo.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                            imagenes_fallback.append(os.path.join(root, archivo))
            imagenes_fallback.sort()
            if imagenes_fallback:
                indice = zlib.crc32(nombre_limpio.encode('utf-8')) % len(imagenes_fallback)
                imagenes_ordenadas = imagenes_fallback[indice:] + imagenes_fallback[:indice]
                for ruta in imagenes_ordenadas:
                    ruta_relativa = os.path.relpath(ruta, os.path.join(os.path.dirname(__file__), '..'))
                    ruta_web = '/' + ruta_relativa.replace('\\', '/').replace(' ', '%20')
                    if ruta_web not in imagenes_excluidas:
                        return ruta_web


    # Sin coincidencia local: usar imagen de Unsplash específica por categoría
    # para que cada tipo de producto tenga una imagen distinta y representativa,
    # en lugar de repetir siempre el mismo genérico.
    _FALLBACK_POR_CATEGORIA = {
        'emergency': 'https://images.unsplash.com/photo-1607613009820-a29f7bb81c04?auto=format&fit=crop&w=500',
        'botiquin':  'https://images.unsplash.com/photo-1607613009820-a29f7bb81c04?auto=format&fit=crop&w=500',
        'skincare':  'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=500',
        'mujer':     'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=500',
        'hombre':    'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=500',
        'body':      'https://images.unsplash.com/photo-1617897903246-719242758050?auto=format&fit=crop&w=500',
        'mixto':     'https://images.unsplash.com/photo-1556228578-8c89e6adf883?auto=format&fit=crop&w=500',
        'pets':      'https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?auto=format&fit=crop&w=500',
        'mascotas':  'https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?auto=format&fit=crop&w=500',
    }
    clave_fallback = carpeta or slug_categoria(categoria or '')
    # Usar la imagen de Unsplash específica para la categoría del producto
    imagen_categoria = _FALLBACK_POR_CATEGORIA.get(clave_fallback)
    if imagen_categoria and imagen_categoria not in imagenes_excluidas:
        return imagen_categoria
    # Si la de su categoría ya está excluida, intentar con las demás
    for imagen_fallback in _FALLBACK_POR_CATEGORIA.values():
        if imagen_fallback not in imagenes_excluidas:
            return imagen_fallback

    return "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=500"


def _imagen_coincide_con_nombre_producto(nombre, imagen):
    """Indica si el archivo contiene todas las palabras distintivas del producto."""
    ruta = unquote(str(imagen or '').split('?', 1)[0])
    nombre_archivo = _normalizar_texto(os.path.splitext(os.path.basename(ruta))[0])
    palabras_producto = [
        palabra for palabra in _normalizar_texto(nombre or '').split()
        if len(palabra) > 2 and palabra not in _PALABRAS_VACIAS
    ]
    palabras_archivo = nombre_archivo.split()
    return bool(palabras_producto) and all(
        any(palabra in palabra_archivo_item or palabra_archivo_item in palabra
            for palabra_archivo_item in palabras_archivo)
        for palabra in palabras_producto
    )


def listar_imagenes_disponibles():
    """Construye la lista de imágenes locales que puede elegir el administrador."""
    # La carpeta se calcula respecto al módulo para que funcione desde cualquier directorio.
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'img', 'categorias'))
    if not os.path.isdir(base_dir):
        return []

    imagenes = []
    # Recorre subcarpetas y filtra únicamente extensiones reconocidas como imágenes.
    for root, _, files in os.walk(base_dir):
        for archivo in files:
            if not archivo.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                continue

            # Convierte la ruta física de Windows en una ruta que pueda usar el navegador.
            ruta_abs = os.path.join(root, archivo)
            ruta_relativa = os.path.relpath(ruta_abs, os.path.join(os.path.dirname(__file__), '..'))
            ruta_web = '/' + ruta_relativa.replace('\\', '/').replace(' ', '%20')
            carpeta = os.path.relpath(root, base_dir)
            nombre_archivo = os.path.splitext(archivo)[0].replace('_', ' ').replace('-', ' ').title()
            etiqueta = f"{nombre_archivo} ({carpeta if carpeta != '.' else 'general'})"
            imagenes.append({"valor": ruta_web, "nombre": etiqueta})

    imagenes.sort(key=lambda item: item["nombre"].lower())
    return imagenes


def producto_desde_formulario(form_data):
    """Convierte los campos del formulario administrativo a un diccionario de producto."""
    # Limpia texto y asigna valores predeterminados para evitar campos vacíos inesperados.
    nombre = (form_data.get("nombre") or "").strip()
    categoria = (form_data.get("categoria") or "body").strip().lower()
    subcategoria = (form_data.get("subcategoria") or "").strip().lower()
    precio = Decimal(str(form_data.get("precio", 0) or 0))
    stock = int(form_data.get("stock", 0) or 0)
    descripcion = (form_data.get("desc") or "").strip()
    imagen = (form_data.get("imagen") or "").strip()

    # La categoría principal se conserva separada de la subcategoría visual.
    categoria_principal = slug_categoria(categoria) if categoria else "body"
    categoria_final = categoria_principal
    if subcategoria:
        categoria_final = subcategoria

    # Si el administrador no eligió imagen, se busca una automáticamente.
    return {
        "nombre": nombre,
        "categoria": categoria_principal,
        "precio": precio,
        "stock": stock,
        "desc": descripcion,
        "imagen": imagen or resolver_imagen_producto(nombre, categoria_final),
        "subcategoria": subcategoria,
        "categoria_visual": categoria_final,
    }


def normalizar_producto(row, categoria=None):
    """Unifica el formato de un producto proveniente de BD, JSON o memoria."""
    # Convierte el precio a Decimal antes de transformarlo para evitar errores de precisión.
    precio = row.get("precio") or 0
    if isinstance(precio, str):
        precio = Decimal(precio)
    elif not isinstance(precio, Decimal):
        precio = Decimal(str(precio))
    # Los precios menores a 1000 se interpretan como valores expresados en miles.
    if 0 < precio < 1000:
        precio *= 1000

    # Si la fila contiene id_categoria, úsalo; de lo contrario, derivar slug desde el nombre
    # Usa la categoría recibida explícitamente o la incluida en la fila.
    id_categoria = row.get("id_categoria")  # bug #1: antes se repetía la misma clave dos veces
    categoria_nombre = slug_categoria(categoria or row.get("categoria") or "sin-categoria")
    stock = row.get("stock") or 0
    nombre = row.get("nombre") or "Producto sin nombre"
    imagen = row.get("imagen") or resolver_imagen_producto(nombre, categoria_nombre)
    if imagen and '/static/img/categorias/' in unquote(str(imagen)).lower():
        imagen_sugerida = resolver_imagen_producto(nombre, categoria_nombre)
        if (
            imagen_sugerida != imagen
            and _imagen_coincide_con_nombre_producto(nombre, imagen_sugerida)
            and not _imagen_coincide_con_nombre_producto(nombre, imagen)
        ):
            imagen = imagen_sugerida

    # Devuelve siempre las mismas claves para que las plantillas no dependan del origen.
    return {
        "id": row.get("id") or row.get("id_producto"),
        "nombre": nombre,
        "categoria": categoria_nombre,
        "id_categoria": int(id_categoria) if id_categoria is not None and str(id_categoria).isdigit() else None,
        "precio": float(precio),
        "imagen": imagen,
        "badge": row.get("badge") or ("Nuevo" if int(stock) > 0 else "Sin stock"),
        "desc": row.get("descripcion") or row.get("desc") or DESCRIPCIONES_CATEGORIA.get(categoria_nombre, "Producto de cuidado y bienestar para uso diario."),
        "stock": int(stock),
    }


def _leer_productos_fallback():
    """Lee el catálogo JSON y lo inicializa con productos demo cuando falta."""
    # Crea el archivo inicial para que las operaciones locales tengan un almacenamiento real.
    if not os.path.exists(PRODUCTOS_DATA_FILE):
        os.makedirs(os.path.dirname(PRODUCTOS_DATA_FILE), exist_ok=True)
        with open(PRODUCTOS_DATA_FILE, 'w', encoding='utf-8') as archivo:
            json.dump([dict(p) for p in PRODUCTOS_BD], archivo, ensure_ascii=False, indent=2)
        return [dict(p) for p in PRODUCTOS_BD]

    try:
        # Carga el JSON y confirma que su estructura principal sea una lista.
        with open(PRODUCTOS_DATA_FILE, 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)
            if isinstance(datos, list):
                return datos
    except (json.JSONDecodeError, OSError):
        # Si el archivo no es válido, se devuelve el catálogo inicial en memoria.
        pass

    return [dict(p) for p in PRODUCTOS_BD]


def _guardar_productos_fallback(productos):
    """Persiste el catálogo completo en el archivo JSON local."""
    # Crea la carpeta de base de datos antes de escribir el archivo.
    os.makedirs(os.path.dirname(PRODUCTOS_DATA_FILE), exist_ok=True)
    with open(PRODUCTOS_DATA_FILE, 'w', encoding='utf-8') as archivo:
        json.dump(productos, archivo, ensure_ascii=False, indent=2)
    return True


def obtener_datos_producto_por_imagen(imagen):
    """Busca los datos de un producto a partir de la ruta de su imagen."""
    if not imagen:
        return {}

    # Normaliza la URL para comparar rutas codificadas y no codificadas.
    imagen_limpia = str(imagen).strip()
    imagen_limpia = unquote(imagen_limpia)
    nombre_archivo = os.path.splitext(os.path.basename(imagen_limpia.split('?')[0]))[0]
    categoria_detectada = "body"
    subcategoria_detectada = ""

    # Deduce una categoría inicial observando la carpeta de la imagen.
    if "/mujer/" in imagen_limpia.lower():
        categoria_detectada = "body"
        subcategoria_detectada = "mujer"
    elif "/hombre/" in imagen_limpia.lower():
        categoria_detectada = "body"
        subcategoria_detectada = "hombre"
    elif "/mixto/" in imagen_limpia.lower():
        categoria_detectada = "body"
        subcategoria_detectada = "mixto"
    elif "/botiquin/" in imagen_limpia.lower():
        categoria_detectada = "emergency"
        subcategoria_detectada = "botiquin"
    elif "/mascotas/" in imagen_limpia.lower():
        categoria_detectada = "pets"
        subcategoria_detectada = "mascotas"

    # Primero intenta localizar el producto en MySQL.
    conexion = get_connection()
    if conexion is not None:
        try:
            cursor = conexion.cursor(dictionary=True)
            ruta_limpia = imagen_limpia.split('?')[0]
            ruta_limpia_codificada = quote(ruta_limpia, safe='/:')
            nombre_archivo_con_ext = os.path.basename(ruta_limpia)
            nombre_archivo = os.path.splitext(nombre_archivo_con_ext)[0]
            # Esta consulta sirve como comprobación de coincidencia exacta cuando se dispone de una ruta almacenada.
            cursor.execute(
                """
                SELECT p.id_producto AS id, p.nombre, p.stock, p.precio,
                      c.nombre AS categoria, '' AS imagen
                FROM productos p
                LEFT JOIN categorias c ON c.id_categoria = p.id_categoria
                WHERE 1 = 0
                ORDER BY p.id_producto DESC
                LIMIT 1
                  """
            )

            row = cursor.fetchone()
            if row:
                producto = normalizar_producto(row)
                return {
                    "nombre": producto.get("nombre", ""),
                    "categoria": producto.get("categoria", ""),
                    "subcategoria": "",
                    "precio": producto.get("precio", 0),
                    "stock": producto.get("stock", 0),
                    "desc": producto.get("desc", ""),
                    "imagen": producto.get("imagen", ""),
                }
            # Si no encontró coincidencia exacta, trae todos los productos para comparar variantes de ruta.
            # y hacer comparaciones más permisivas (basename, sin /static, decodificados)
            cursor.execute(
                """
                SELECT p.id_producto AS id, p.nombre, p.stock, p.precio,
                       c.nombre AS categoria, '' AS imagen
                FROM productos p
                LEFT JOIN categorias c ON c.id_categoria = p.id_categoria
                ORDER BY p.id_producto DESC
                """
            )
            productos_bd = cursor.fetchall() or []
            buscado_basename = os.path.basename(ruta_limpia).lower()
            buscado_sin_static = ruta_limpia.lstrip('/').replace('static/', '')
            buscado_decod = unquote(ruta_limpia).lower()
            for p in productos_bd:
                producto_data = cast(dict[str, Any], p)
                img_val = str(producto_data.get('imagen') or '').strip()
                img_norm = unquote(img_val).lower()
                img_basename = os.path.basename(img_norm)
                # Compara rutas completas, nombres de archivo y versiones sin /static.
                if img_norm == buscado_decod or img_basename == buscado_basename or img_norm.endswith(buscado_basename) or buscado_basename in img_norm or img_norm.endswith(buscado_sin_static) or img_norm.endswith(buscado_sin_static.split('/')[-1]):
                    producto = normalizar_producto(producto_data)
                    return {
                        "nombre": producto.get("nombre", ""),
                        "categoria": producto.get("categoria", ""),
                        "subcategoria": "",
                        "precio": producto.get("precio", 0),
                        "stock": producto.get("stock", 0),
                        "desc": producto.get("desc", ""),
                        "imagen": producto.get("imagen", ""),
                    }
        except Error as e:
            print("Error al buscar producto en MySQL:", e)
        finally:
            try:
                conexion.close()
            except Exception:
                pass

    # Si MySQL no resolvió la imagen, intenta encontrarla en el catálogo JSON.
    productos = _leer_productos_fallback()
    imagen_normalizada = unquote(imagen_limpia)
    # Primera comparación: prueba todas las variantes completas de la ruta.
    for producto in productos:
        imagen_producto = str(producto.get("imagen", "")).strip()
        # comparar versiones decodificadas y variantes sin prefijos
        imagen_prod_dec = unquote(imagen_producto)
        variantes_input = [imagen_normalizada, imagen_normalizada.lstrip('/'), imagen_normalizada.replace('/static/', ''), os.path.basename(imagen_normalizada)]
        variantes_prod = [imagen_prod_dec, imagen_prod_dec.lstrip('/'), imagen_prod_dec.replace('/static/', ''), os.path.basename(imagen_prod_dec)]
        if any(vp == vi for vp in variantes_prod for vi in variantes_input):
            return {
                "nombre": producto.get("nombre", nombre_archivo.replace('_', ' ').replace('-', ' ').title()),
                "categoria": producto.get("categoria", categoria_detectada),
                "subcategoria": producto.get("subcategoria", subcategoria_detectada),
                "precio": producto.get("precio", 0),
                "stock": producto.get("stock", 0),
                "desc": producto.get("desc", ""),
                "imagen": producto.get("imagen", imagen_limpia),
            }

    # Segunda comparación: permite que coincida solo el nombre del archivo.
    for producto in productos:
        imagen_producto = str(producto.get("imagen", "")).strip()
        if unquote(imagen_producto).endswith(unquote(imagen_normalizada).split('/')[-1]):
            return {
                "nombre": producto.get("nombre", nombre_archivo.replace('_', ' ').replace('-', ' ').title()),
                "categoria": producto.get("categoria", categoria_detectada),
                "subcategoria": producto.get("subcategoria", subcategoria_detectada),
                "precio": producto.get("precio", 0),
                "stock": producto.get("stock", 0),
                "desc": producto.get("desc", ""),
                "imagen": producto.get("imagen", imagen_limpia),
            }

    # Si no existe producto asociado, devuelve datos mínimos inferidos desde el archivo.
    return {
        "nombre": nombre_archivo.replace('_', ' ').replace('-', ' ').title(),
        "categoria": categoria_detectada,
        "subcategoria": subcategoria_detectada,
        "precio": 0,
        "stock": 0,
        "desc": "",
        "imagen": imagen_limpia,
    }


def obtener_productos():
    """Obtiene y normaliza el catálogo desde MySQL o desde el fallback JSON."""
    # La conexión determina cuál será la fuente de datos principal.
    conexion = get_connection()
    if conexion is None:
        return [normalizar_producto(p) for p in _productos_fallback_visibles()]

    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = 'productos'
                AND column_name IN ('imagen', 'descripcion')
            """
        )
        columnas_producto = {
            str(fila.get('column_name'))
            for fila in (cursor.fetchall() or [])
            if isinstance(fila, dict)
        }
        if 'imagen' not in columnas_producto:
            cursor.execute("ALTER TABLE productos ADD COLUMN imagen VARCHAR(255) NULL")
        if 'descripcion' not in columnas_producto:
            cursor.execute("ALTER TABLE productos ADD COLUMN descripcion TEXT NULL")
        if len(columnas_producto) < 2:
            conexion.commit()

        # La consulta une productos con categorías para entregar información completa a la interfaz.
        cursor.execute(
            """
             SELECT p.id_producto AS id, p.nombre, p.stock, p.precio,
                 p.descripcion, c.nombre AS categoria, p.id_categoria AS id_categoria, p.imagen
            FROM productos p
            LEFT JOIN categorias c ON c.id_categoria = p.id_categoria
            ORDER BY p.id_producto DESC
            """
        )
        filas = cursor.fetchall()
        if filas:
            productos = []
            imagenes_usadas = set()
            # Normaliza cada fila y asigna imágenes distintas cuando la BD no tiene una guardada.
            for fila in filas:
                fila_data = cast(dict[str, Any], fila)
                producto = normalizar_producto(fila_data)
                if not fila_data.get('imagen'):
                    producto['imagen'] = resolver_imagen_producto(
                        producto['nombre'], producto['categoria'], imagenes_usadas
                    )
                productos.append(producto)
                imagenes_usadas.add(producto['imagen'])
            return [producto for producto in productos if _producto_visible(producto)]
    except Error as e:
        print("Error al leer productos desde MySQL:", e)
    finally:
        try:
            conexion.close()
        except Exception:
            pass

    # Último respaldo: devuelve los productos visibles almacenados en JSON.
    return [normalizar_producto(p) for p in _productos_fallback_visibles()]


def guardar_producto_en_bd(nombre, categoria, precio, stock, descripcion="", imagen="", subcategoria=None):
    """Guarda un producto nuevo en MySQL o, si no hay conexión, en el JSON de respaldo.

    Este método también valida columnas auxiliares como imagen y descripcion para
    que la base de datos pueda aceptar productos con contenido multimedia y texto.
    """
    conexion = get_connection()
    if conexion is None:
        # Fallback de emergencia: crea el producto en el archivo JSON local.
        productos = _leer_productos_fallback()
        nuevo_id = max((int(p.get("id", 0)) for p in productos if str(p.get("id", "")).isdigit()), default=0) + 1
        producto = {
            "id": nuevo_id,
            "nombre": nombre,
            "categoria": subcategoria or categoria,
            "precio": float(precio),
            "stock": int(stock),
            "desc": descripcion,
            "imagen": imagen or resolver_imagen_producto(nombre, subcategoria or categoria),
            "badge": "Nuevo",
            "subcategoria": subcategoria or "",
        }
        productos.append(producto)
        return _guardar_productos_fallback(productos)

    try:
        cursor = conexion.cursor()
        # Si la tabla no tiene columnas de imagen o descripcion, las crea para soportar la carga de productos.
        cursor.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'productos' AND column_name = 'imagen'")
        count_row = cursor.fetchone()
        count_data = cast(tuple[Any, ...], count_row) if count_row is not None else None
        if count_data is not None and count_data[0] == 0:
            cursor.execute("ALTER TABLE productos ADD COLUMN imagen VARCHAR(255) NULL")
            conexion.commit()
        cursor.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'productos' AND column_name = 'descripcion'")
        descripcion_row = cursor.fetchone()
        descripcion_data = cast(tuple[Any, ...], descripcion_row) if descripcion_row is not None else None
        if descripcion_data is not None and descripcion_data[0] == 0:
            cursor.execute("ALTER TABLE productos ADD COLUMN descripcion TEXT NULL")
            conexion.commit()

        # Busca si ya existe la categoría del producto; si no, la crea.
        cursor.execute("SELECT id_categoria FROM categorias WHERE nombre = %s", (categoria,))
        categoria_row = cursor.fetchone()

        if categoria_row:
            categoria_data = cast(tuple[Any, ...], categoria_row)
            id_categoria = categoria_data[0]
        else:
            cursor.execute("INSERT INTO categorias (nombre) VALUES (%s)", (categoria,))
            conexion.commit()
            id_categoria = cursor.lastrowid

        # Inserta el producto principal en la tabla productos.
        cursor.execute(
            """
            INSERT INTO productos (nombre, stock, precio, descripcion, id_categoria, imagen)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (nombre, stock, precio, descripcion or None, id_categoria, imagen or None),
        )
        conexion.commit()
        return True
    except Error as e:
        print("Error al insertar producto en MySQL:", e)
        return False
    finally:
        try:
            conexion.close()
        except Exception:
            pass


def actualizar_producto_en_bd(producto_id, nombre, categoria, precio, stock, descripcion="", imagen="", subcategoria=None):
    """Actualiza un producto existente en la base de datos o en el backup local.

    Esta función se usa desde el panel administrativo cuando se edita un producto
    y necesita conservar su información principal y su imagen asociada.
    """
    conexion = get_connection()
    if conexion is None:
        # Fallback local: busca el producto por id y reemplaza sus datos.
        productos = _leer_productos_fallback()
        for producto in productos:
            if str(producto.get("id")) == str(producto_id):
                producto["nombre"] = nombre
                producto["categoria"] = subcategoria or categoria
                producto["precio"] = float(precio)
                producto["stock"] = int(stock)
                producto["desc"] = descripcion
                producto["imagen"] = imagen or producto.get("imagen") or resolver_imagen_producto(nombre, subcategoria or categoria)
                producto["subcategoria"] = subcategoria or ""
                return _guardar_productos_fallback(productos)
        return False

    try:
        cursor = conexion.cursor()
        # Asegura que la tabla soporte imágenes y descripción en caso de bases antiguas.
        cursor.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'productos' AND column_name = 'imagen'")
        count_row = cursor.fetchone()
        count_data = cast(tuple[Any, ...], count_row) if count_row is not None else None
        if count_data is not None and count_data[0] == 0:
            cursor.execute("ALTER TABLE productos ADD COLUMN imagen VARCHAR(255) NULL")
            conexion.commit()
        cursor.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'productos' AND column_name = 'descripcion'")
        descripcion_row = cursor.fetchone()
        descripcion_data = cast(tuple[Any, ...], descripcion_row) if descripcion_row is not None else None
        if descripcion_data is not None and descripcion_data[0] == 0:
            cursor.execute("ALTER TABLE productos ADD COLUMN descripcion TEXT NULL")
            conexion.commit()

        categoria_destino = (subcategoria or categoria or "body").strip()
        cursor.execute("SELECT id_categoria FROM categorias WHERE nombre = %s", (categoria_destino,))
        categoria_row = cursor.fetchone()

        if categoria_row:
            categoria_data = cast(tuple[Any, ...], categoria_row)
            id_categoria = categoria_data[0]
        else:
            cursor.execute("INSERT INTO categorias (nombre) VALUES (%s)", (categoria_destino,))
            conexion.commit()
            id_categoria = cursor.lastrowid

        # Actualiza los campos del producto para reflejar los cambios del editor.
        cursor.execute(
            """
            UPDATE productos
            SET nombre = %s, stock = %s, precio = %s, descripcion = %s, id_categoria = %s, imagen = %s
            WHERE id_producto = %s
            """,
            (nombre, stock, precio, descripcion or None, id_categoria, imagen or None, producto_id),
        )
        conexion.commit()
        return cursor.rowcount > 0
    except Error as e:
        print("Error al actualizar producto en MySQL:", e)
        return False
    finally:
        try:
            conexion.close()
        except Exception:
            pass


def eliminar_producto_en_bd(producto_id):
    """Elimina un producto de la base de datos o del archivo local de respaldo."""
    conexion = get_connection()
    if conexion is None:
        productos = _leer_productos_fallback()
        productos = [p for p in productos if str(p.get("id")) != str(producto_id)]
        return _guardar_productos_fallback(productos)

    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM productos WHERE id_producto = %s", (producto_id,))
        conexion.commit()
        return cursor.rowcount > 0
    except Error as e:
        print("Error al eliminar producto en MySQL:", e)
        return False
    finally:
        try:
            conexion.close()
        except Exception:
            pass


@main_routes.route('/')
def index():
    """Muestra la página principal con los primeros productos del catálogo."""
    # Limita la consulta para mostrar una selección breve en la portada.
    productos = obtener_productos()[:3]
    return render_template('web/index.html', productos=productos)


@main_routes.route('/productos')
def productos():
    """Muestra el catálogo completo o filtrado por una categoría."""
    # Carga productos y categorías para construir los filtros de la tienda.
    productos = obtener_productos()
    categorias = _agregar_categoria_mixto(obtener_categorias_disponibles(), productos)
    cat = request.args.get('categoria')
    if cat:
        # Cuando llega una categoría, solo se muestran productos de ese grupo.
        cat_slug = slug_categoria(cat)
        filtrados = [p for p in productos if _producto_pertenece_a_categoria(p, cat_slug)]
        return render_template(
            'web/products.html',
            productos=filtrados,
            categoria_activa=cat_slug,
            categorias=categorias,
            categoria_nombre=nombre_categoria(cat_slug),
            mostrar_destacados=False,
        )

    # Sin filtro, separa un producto destacado por categoría del resto del catálogo.
    featured_products = productos_destacados_por_categoria(productos)
    featured_references = {id(producto) for producto in featured_products}
    productos_restantes = [
        producto for producto in productos if id(producto) not in featured_references
    ]

    return render_template(
        'web/products.html',
        productos=productos_restantes,
        featured_products=featured_products,
        categoria_activa='todos',
        categoria_nombre='Todos',
        categorias=categorias,
        mostrar_destacados=True,
    )


@main_routes.route('/productos/categoria/<string:categoria>')
def productos_por_categoria(categoria):
    """Filtra productos mediante un slug de categoría o un ID numérico."""
    productos = obtener_productos()
    categorias = _agregar_categoria_mixto(obtener_categorias_disponibles(), productos)
    # Permitir recibir tanto slug como id numérico
    filtrados = []
    if str(categoria).isdigit():
        # Los enlaces antiguos pueden enviar directamente el identificador de MySQL.
        cat_id = int(categoria)
        filtrados = [p for p in productos if p.get('id_categoria') == cat_id]
        categoria_slug = next((c['slug'] for c in categorias if c.get('id') == cat_id), slug_categoria(categoria))
    else:
        # La forma pública habitual utiliza el slug de la categoría.
        categoria_slug = slug_categoria(categoria)
        filtrados = [p for p in productos if _producto_pertenece_a_categoria(p, categoria_slug)]
    return render_template(
        'web/products.html',
        productos=filtrados,
        categoria_activa=categoria_slug,
        categoria_nombre=nombre_categoria(categoria_slug),
        categorias=categorias,
        mostrar_destacados=False,
    )


@main_routes.route('/login', methods=['GET', 'POST'])
def login():
    """Autentica clientes y administradores usando MySQL o usuarios demo."""
    if request.method == 'POST':
        # Normaliza las credenciales recibidas desde el formulario.
        correo = (request.form.get('correo') or '').strip().lower()
        password = (request.form.get('password') or '').strip()
        if not correo or not password:
            # Evita consultar la base de datos cuando faltan campos obligatorios.
            flash('Por favor ingresa tu correo y contraseña.', 'danger')
            return render_template('web/login.html')

        rol = None
        nombre = None
        password_hash_bd = None
        # La primera fuente de autenticación es la tabla de usuarios de MySQL.
        conexion = get_connection()
        if conexion is not None:
            try:
                cursor = conexion.cursor(dictionary=True)
                cursor.execute(
                    """
                    SELECT u.nombre, COALESCE(r.nombre, 'cliente') AS rol, u.password
                    FROM usuarios u
                    LEFT JOIN roles r ON u.id_rol = r.id_rol
                    WHERE LOWER(u.correo) = %s
                    LIMIT 1
                    """,
                    (correo,)
                )
                fila = cursor.fetchone()
                if isinstance(fila, dict):
                    password_hash_bd = str(fila.get('password') or '')
                    # Soportar contraseñas hasheadas (werkzeug) y texto plano (datos legacy)
                    if password_hash_bd.startswith('pbkdf2:') or password_hash_bd.startswith('scrypt:'):
                        # Verifica de forma segura las contraseñas creadas con Werkzeug.
                        if check_password_hash(password_hash_bd, password):
                            rol = _normalizar_texto(fila.get('rol') or 'cliente')
                            nombre = str(fila.get('nombre') or '')
                    elif password_hash_bd == password:
                        # Mantiene compatibilidad con registros antiguos en texto plano.
                        # Contraseña en texto plano (datos semilla de BD)
                        rol = _normalizar_texto(fila.get('rol') or 'cliente')
                        nombre = str(fila.get('nombre') or '')
            except Exception:
                pass
            finally:
                try:
                    conexion.close()
                except Exception:
                    pass

        # Fallback: buscar en la lista estática para permitir el modo demo sin BD.
        if rol is None:
            for u in USUARIOS_BD:
                if u['correo'].lower() != correo:
                    continue
                password_guardada = str(u.get('password') or '')
                credenciales_validas = False
                if password_guardada:
                    if password_guardada.startswith(('pbkdf2:', 'scrypt:')):
                        credenciales_validas = check_password_hash(password_guardada, password)
                    else:
                        credenciales_validas = password_guardada == password
                        if not credenciales_validas:
                            credenciales_validas = _credenciales_demo_validas(u.get('correo') or correo, password)
                else:
                    credenciales_validas = _credenciales_demo_validas(u.get('correo') or correo, password)
                if credenciales_validas:
                    rol = u['rol']
                    nombre = u['nombre']
                    break

        if rol is None:
            # No se crea sesión cuando las credenciales no coinciden.
            flash('Correo o contraseña incorrectos. Verifica tus datos.', 'danger')
            return render_template('web/login.html')

        # Guarda en sesión la identidad mínima que necesitan las rutas protegidas.
        session['usuario'] = correo
        session['rol'] = rol
        session['nombre'] = nombre or correo

        # Personaliza el mensaje y decide el texto según el rol obtenido.
        primer_nombre = (nombre or correo).split(' ')[0]
        if rol == 'administrador':
            flash(f'¡Bienvenido/a de nuevo, {primer_nombre}! Sesión iniciada como administrador.', 'success')
        else:
            flash(f'¡Hola, {primer_nombre}! 👋 Qué gusto verte de nuevo. Disfruta tu experiencia de compra en Healthy Fast 🛍️', 'success')
        # Si el usuario llegó desde una ruta protegida, vuelve a esa ruta después del login.
        destino = session.pop('despues_login', None)
        if isinstance(destino, str) and destino.startswith('/') and not destino.startswith('//'):
            return redirect(destino)
        return redirect(url_for('main.index'))
    return render_template('web/login.html')


@main_routes.route('/envio', methods=['GET', 'POST'])
@usuario_required
def envio():
    """Recibe y almacena los datos de entrega antes de mostrar el pago."""
    if request.method == 'POST':
        # Guarda temporalmente la dirección porque todavía no se ha creado el pedido.
        session['envio_data'] = {
            'email': request.form.get('email'),
            'nombre': request.form.get('nombre'),
            'apellido': request.form.get('apellido'),
            'tipo_documento': request.form.get('tipo_documento'),
            'documento': request.form.get('documento'),
            'pais': request.form.get('pais') or request.form.get('estado') or 'Colombia',
            'departamento': request.form.get('departamento'),
            'telefono': request.form.get('telefono'),
            'direccion': request.form.get('direccion'),
            'referencia': request.form.get('referencia'),
            'ciudad': request.form.get('ciudad'),
            'cp': request.form.get('cp')
        }
        # Informa al usuario y avanza al siguiente paso del checkout.
        flash('Dirección registrada correctamente. Continúa con el método de pago.', 'success')
        return redirect(url_for('main.pago'))
    # En una nueva visita, intenta precargar la última dirección conocida.
    return render_template(
        'web/envio.html',
        datos_envio_previo=obtener_ultimo_envio_usuario(session.get('usuario')),
    )


@main_routes.route('/pago')
@usuario_required
def pago():
    """Muestra la pantalla de selección y confirmación del método de pago."""
    return render_template(
        'web/pago.html', aplicar_descuento=bool(session.get('beneficio_primera_compra'))
    )


@main_routes.route('/logout')
def logout():
    """Cierra la sesión eliminando todos los datos temporales del usuario."""
    # Limpiar toda la sesión evita conservar rol, usuario o datos de checkout.
    session.clear()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('main.index'))


# --- PANEL DE ADMINISTRACIÓN (CRUD, ANALYTICS, PEDIDOS, USUARIOS) ---
@main_routes.route('/admin')
@admin_required

def admin_dashboard():
    """Carga estadísticas, usuarios, pedidos y productos para el panel administrativo."""
    # Cada fuente intenta obtener información real y tiene un respaldo demo o local.
    usuarios_db = db_obtener_usuarios()
    usuarios = usuarios_db if usuarios_db else USUARIOS_BD

    # Convierte los pedidos a diccionarios para facilitar su uso en la plantilla.
    pedidos = [cast(dict[str, Any], pedido) for pedido in obtener_pedidos_totales()]
    # Calcula las métricas principales que aparecen en las tarjetas del panel.
    total_ventas = sum(float(p.get('total', 0) or 0) for p in pedidos if p.get('total') is not None)
    productos = obtener_productos()
    total_stock = sum(int(p.get('stock', 0) or 0) for p in productos)

    return render_template(
        'web/admin.html',
        productos=productos,
        usuarios=usuarios,
        pedidos=pedidos,
        total_ventas=total_ventas,
        total_stock=total_stock,
        imagenes_disponibles=listar_imagenes_disponibles(),
    )


@main_routes.route('/admin/producto/auto', methods=['GET'])
@admin_required
def auto_producto():
    """Devuelve información sugerida al seleccionar una imagen en el administrador."""
    # El frontend envía la ruta de imagen como parámetro de consulta.
    imagen = request.args.get('imagen', '')
    datos = obtener_datos_producto_por_imagen(imagen)
    return {
        "ok": True,
        "datos": datos,
    }


@main_routes.route('/admin/producto/agregar', methods=['POST'])
@admin_required
def agregar_producto():
    """Crea un producto nuevo con los datos enviados desde el panel."""
    # Primero transforma y valida los campos del formulario al formato interno.
    datos = producto_desde_formulario(request.form)
    guardado = guardar_producto_en_bd(
        datos["nombre"],
        datos["categoria"],
        datos["precio"],
        datos["stock"],
        datos["desc"],
        datos["imagen"],
        subcategoria=datos.get("subcategoria"),
    )
    # Informa visualmente si la operación terminó bien o falló.
    if guardado:
        flash('Producto agregado correctamente.', 'success')
    else:
        flash('No se pudo guardar el producto en la base de datos.', 'danger')
    return redirect(url_for('main.admin_dashboard'))


@main_routes.route('/admin/producto/editar/<int:id>', methods=['POST'])
@admin_required
def editar_producto(id):
    """Actualiza un producto existente identificado por su ID."""
    datos = producto_desde_formulario(request.form)
    actualizado = actualizar_producto_en_bd(
        id,
        datos["nombre"],
        datos["categoria"],
        datos["precio"],
        datos["stock"],
        datos["desc"],
        datos["imagen"],
        subcategoria=datos.get("subcategoria"),
    )
    # Muestra el resultado y vuelve al listado administrativo.
    if actualizado:
        flash('Producto actualizado.', 'success')
    else:
        flash('No se pudo actualizar el producto.', 'danger')
    destino = request.form.get('next', '')
    if destino.startswith('/') and not destino.startswith('//'):
        return redirect(destino)
    return redirect(url_for('main.admin_dashboard'))


# bug #3: cambiado de GET a POST para evitar que un link/bot elimine productos accidentalmente
@main_routes.route('/admin/producto/eliminar/<int:id>', methods=['POST'])
@admin_required
def eliminar_producto(id):
    """Elimina un producto después de recibir una solicitud POST protegida."""
    # La ruta usa POST para impedir eliminaciones accidentales mediante enlaces GET.
    eliminado = eliminar_producto_en_bd(id)
    if eliminado:
        flash('Producto eliminado de la base de datos.', 'warning')
    else:
        flash('No se pudo eliminar el producto.', 'danger')
    return redirect(url_for('main.admin_dashboard'))


@main_routes.route('/registro', methods=['GET', 'POST'])
def registro():
    """Registro de nuevos clientes con contraseña hasheada."""
    if request.method == 'POST':
        # Limpia los campos recibidos antes de validarlos.
        nombre = (request.form.get('nombre') or '').strip()
        apellido = (request.form.get('apellido') or '').strip()
        correo = (request.form.get('correo') or '').strip().lower()
        password = (request.form.get('password') or '').strip()
        password2 = (request.form.get('password2') or '').strip()

        if not all([nombre, correo, password, password2]):
            # Impide registrar cuentas incompletas.
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('web/login.html', mostrar_registro=True)
        if password != password2:
            # Comprueba que la confirmación de contraseña coincida.
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('web/login.html', mostrar_registro=True)
        if len(password) < 6:
            # Aplica la longitud mínima definida por la aplicación.
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
            return render_template('web/login.html', mostrar_registro=True)

        nombre_completo = f"{nombre} {apellido}".strip()
        # Nunca se guarda la contraseña original cuando se crea una cuenta nueva.
        password_hash = generate_password_hash(password)

        # Intenta registrar al usuario en MySQL si existe una conexión activa.
        conexion = get_connection()
        if conexion is not None:
            try:
                cursor = conexion.cursor()
                # Verifica que el correo no esté ocupado por otra cuenta.
                cursor.execute("SELECT id_usuario FROM usuarios WHERE LOWER(correo) = %s", (correo,))
                if cursor.fetchone():
                    flash('Este correo ya está registrado. Inicia sesión.', 'warning')
                    return render_template('web/login.html', mostrar_registro=False)
                # Busca el ID de rol cliente para relacionarlo con el nuevo usuario.
                cursor.execute("SELECT id_rol FROM roles WHERE LOWER(nombre) LIKE '%cliente%' LIMIT 1")
                rol_row = cursor.fetchone()
                id_rol_value: Any = rol_row[0] if isinstance(rol_row, (tuple, list)) else None
                id_rol: int | None = cast(int | None, id_rol_value)
                cursor.execute(
                    "INSERT INTO usuarios (nombre, correo, password, id_rol) VALUES (%s, %s, %s, %s)",
                    (nombre_completo, correo, password_hash, id_rol)
                )
                conexion.commit()
                # Marca el beneficio que se aplicará en el primer pedido.
                session['beneficio_primera_compra'] = True
                flash(f'¡Bienvenido/a {nombre}! Tu cuenta fue creada exitosamente. Ya puedes iniciar sesión. 🎉', 'success')
                return redirect(url_for('main.login'))
            except Exception as e:
                print('Error al registrar usuario:', e)
                flash('Ocurrió un error al registrar. Intenta de nuevo.', 'danger')
            finally:
                try:
                    conexion.close()
                except Exception:
                    pass
        else:
            # Sin BD, registra el usuario en la lista de memoria usada por el modo demo.
            if any(u['correo'] == correo for u in USUARIOS_BD):
                flash('Este correo ya está registrado. Inicia sesión.', 'warning')
                return render_template('web/login.html', mostrar_registro=False)
            USUARIOS_BD.append({
                'correo': correo,
                'nombre': nombre_completo,
                'rol': 'cliente',
                'password': password_hash,
            })
            # El descuento también queda disponible para el flujo local.
            session['beneficio_primera_compra'] = True
            flash(f'¡Bienvenido/a {nombre}! Tu cuenta fue creada exitosamente. Tienes 5% de descuento en tu primera compra.', 'success')
            return redirect(url_for('main.login'))

    # En GET solo se muestra el formulario de registro.
    return render_template('web/login.html', mostrar_registro=True)


def _preparar_items_compra(items_carrito):
    """Valida los artículos del carrito antes de procesar la compra.

    Esta función revisa que cada producto exista, que tenga stock suficiente y que
    la cantidad pedida sea válida. Si algo falla, retorna None para cancelar la compra.
    """
    if not isinstance(items_carrito, list):
        return None

    cantidades = {}
    articulos = {}
    for item in items_carrito:
        if not isinstance(item, dict) or item.get('id') in (None, ''):
            return None
        try:
            cantidad_decimal = Decimal(str(item.get('cantidad', 0)))
            if not cantidad_decimal.is_finite() or cantidad_decimal != cantidad_decimal.to_integral_value():
                return None
            cantidad = int(cantidad_decimal)
        except (ArithmeticError, TypeError, ValueError):
            return None
        cantidades[str(item['id'])] = cantidades.get(str(item['id']), 0) + cantidad
        articulos[str(item['id'])] = item

    productos = {str(item.get('id')): item for item in obtener_productos()}
    items_validos = []
    for id_producto, cantidad in cantidades.items():
        item = articulos[id_producto]
        producto = productos.get(id_producto)
        try:
            precio = Decimal(str(producto.get('precio'))) if producto else Decimal("0")
            stock = int(producto.get('stock', 0) or 0) if producto else 0
        except (ArithmeticError, TypeError, ValueError):
            return None
        if producto is None or cantidad < 1 or cantidad > stock or precio <= 0:
            return None
        items_validos.append({
            **item,
            'nombre': producto['nombre'],
            'precio': float(precio),
            'cantidad': cantidad,
        })
    return items_validos


def _descontar_stock_fallback(items_carrito):
    """Actualiza el stock en el JSON local cuando la base de datos no está disponible."""
    productos = _leer_productos_fallback()
    por_id = {str(item.get('id')): item for item in productos}
    for item in items_carrito:
        producto = por_id.get(str(item.get('id')))
        if producto is not None:
            producto['stock'] = max(0, int(producto.get('stock', 0) or 0) - int(item.get('cantidad', 1) or 1))
    _guardar_productos_fallback(productos)


def _siguiente_numero_factura():
    """Obtiene el siguiente consecutivo a partir de las facturas ya respaldadas."""
    global _ULTIMO_NUMERO_FACTURA
    maximo = 0
    for pedido in _leer_pedidos_fallback():
        datos_factura = pedido.get('factura') or {}
        numero = pedido.get('numero_factura') or datos_factura.get('numero_factura') or ''
        if str(numero).startswith('FACT-'):
            try:
                maximo = max(maximo, int(str(numero)[5:]))
            except ValueError:
                continue
    with _FACTURA_SEQUENCE_LOCK:
        _ULTIMO_NUMERO_FACTURA = max(_ULTIMO_NUMERO_FACTURA, maximo) + 1
        return f"FACT-{_ULTIMO_NUMERO_FACTURA:06d}"


def _normalizar_factura_json(valor):
    """Convierte decimales y fechas a valores compatibles con JSON."""
    if isinstance(valor, Decimal):
        return float(valor)
    if hasattr(valor, 'isoformat') and not isinstance(valor, str):
        return valor.isoformat()
    if isinstance(valor, dict):
        return {clave: _normalizar_factura_json(dato) for clave, dato in valor.items()}
    if isinstance(valor, list):
        return [_normalizar_factura_json(dato) for dato in valor]
    return valor


def _buscar_factura(numero_factura):
    """Busca primero el registro relacional y luego el respaldo JSON del pedido."""
    factura = obtener_factura_por_numero(numero_factura)
    if factura:
        return factura
    for pedido in _leer_pedidos_fallback():
        if pedido.get('numero_factura') == numero_factura:
            return pedido.get('factura')
        factura_fallback = pedido.get('factura') or {}
        if factura_fallback.get('numero_factura') == numero_factura:
            return factura_fallback
    return None


def _usuario_puede_ver_factura(numero_factura, factura):
    """Restringe la factura al comprador de la sesión o a un administrador."""
    if str(session.get('rol') or '').strip().lower() == 'administrador':
        return True
    autorizadas = session.get('facturas_autorizadas', [])
    if numero_factura in autorizadas:
        return True
    correo_usuario = str(session.get('usuario') or '').strip().lower()
    correo_comprador = str((factura.get('comprador') or {}).get('email') or '').strip().lower()
    return bool(correo_usuario and correo_usuario == correo_comprador)


@main_routes.route('/procesar', methods=['POST'])
@usuario_required
def procesar_pago():
    """Procesa el checkout final: valida carrito, arma la factura, registra el pago y guarda la orden.

    Este bloque es el núcleo del flujo de compra: reúne la información del cliente,
    genera la factura, calcula el total con descuento, hace el cobro y persiste la venta.
    """
    metodo = (request.form.get('metodo') or 'efectivo').strip().lower()
    if metodo not in {'efectivo', 'transferencia'}:
        metodo = 'efectivo'
    titular = ''
    numero_tarjeta = ''
    fecha_exp = ''
    cvv = ''

    # Lee los datos del carrito enviados desde la vista y los convierte en una lista Python.
    items_raw = request.form.get('items_carrito', '[]')
    try:
        items_carrito = json.loads(items_raw) if items_raw else []
    except Exception:
        items_carrito = []

    # Verifica que el carrito sea válido y que cada producto tenga stock suficiente.
    items_carrito = _preparar_items_compra(items_carrito)
    if items_carrito is None or not items_carrito:
        flash('Uno o más productos no tienen existencias suficientes.', 'warning')
        return redirect(url_for('main.productos'))

    # Recupera la información de envío almacenada en sesión.
    envio_data = session.get('envio_data') or {}
    campos_facturacion_requeridos = (
        'email', 'nombre', 'apellido', 'tipo_documento', 'documento',
        'departamento', 'ciudad', 'direccion', 'telefono',
    )
    if any(not str(envio_data.get(campo) or '').strip() for campo in campos_facturacion_requeridos):
        flash('Completa los datos de identificación y envío antes de confirmar la compra.', 'warning')
        return redirect(url_for('main.envio'))

    # 1. Instanciar clases de dominio POO para simular el negocio.
    nombre_c = envio_data.get('nombre', 'Cliente')
    apellido_c = envio_data.get('apellido', '')
    email_c = envio_data.get('email', 'cliente@healthyfast.com')
    tel_c = envio_data.get('telefono', '')
    dir_c = envio_data.get('direccion', '')

    cliente_obj = Cliente(
        id_persona=None,
        nombre=nombre_c,
        apellido=apellido_c,
        email=email_c,
        telefono=tel_c,
        direccion=dir_c,
    )

    # Genera identificadores independientes para la orden y la factura.
    numero_orden_temp = f"HF-{secrets.token_hex(4).upper()}"
    numero_factura_temp = _siguiente_numero_factura()
    factura_obj = Factura(id_factura=numero_orden_temp, cliente=cliente_obj)

    # Añade los artículos comprados a la factura como detalles de venta.
    for it in items_carrito:
        p_obj = ModeloProducto(
            id_producto=it.get('id'),
            nombre=it.get('nombre', 'Producto'),
            descripcion='',
            precio=float(it.get('precio', 0) or 0),
            stock=999,
        )
        factura_obj.detalles.append(FacturaDetalle(p_obj, int(it.get('cantidad', 1) or 1)))

    # Los precios y cantidades llegan de los productos recuperados en el servidor.
    aplicar_descuento = bool(session.pop('beneficio_primera_compra', False))
    factura_data = calcular_factura(
        items_carrito,
        {
            **envio_data,
            'nombre_completo': f"{nombre_c} {apellido_c}".strip(),
        },
        metodo,
        numero_factura_temp,
        descuento_porcentaje=Decimal('0.05') if aplicar_descuento else Decimal('0'),
    )
    total_calculado = float(factura_data['total_final'])

    factura_obj.total = total_calculado

    # El proyecto simula la confirmación del pago; no integra una pasarela bancaria.
    pago_obj = PagoEfectivo(
        monto_a_pagar=total_calculado,
        billete_entregado=total_calculado,
    )
    pago_obj.procesar_pago()
    factura_obj.pagos.append(pago_obj)
    factura_obj.estado = "Pendiente"

    # Crea el objeto de envío asociado a la factura y a la orden de compra.
    envio_obj = factura_obj.crear_envio(
        id_envio=f"ENV-{numero_orden_temp}",
        transportadora="Healthy Express Colombia",
        guia=f"GUIA-{int(datetime.now().timestamp()) % 1000000}",
    )

    # 2. Persiste la compra en MySQL o en el fallback local si la BD está apagada.
    res_bd = guardar_pedido_completo_bd(
        cliente_info=envio_data,
        items_carrito=items_carrito,
        metodo_pago=metodo,
        total=total_calculado,
        factura_data=factura_data,
    )
    if res_bd is False:
        flash('No se pudo registrar la compra. Verifica el inventario e inténtalo de nuevo.', 'danger')
        return redirect(url_for('main.productos'))

    numero_final = res_bd['numero_orden'] if res_bd else numero_orden_temp
    numero_factura_final = res_bd.get('numero_factura', numero_factura_temp) if res_bd else numero_factura_temp
    factura_data['numero_factura'] = numero_factura_final

    # Guarda una copía del pedido en JSON para que el panel administrativo siempre tenga datos.
    pedido_fallback = {
        'id': numero_final,
        'cliente': f"{nombre_c} {apellido_c}".strip() or "Cliente",
        'email': email_c,
        'total': total_calculado,
        'estado': factura_obj.estado,
        'metodo': metodo,
        'direccion': dir_c,
        'ciudad': envio_data.get('ciudad', ''),
        'telefono': tel_c,
        'tipo_documento': envio_data.get('tipo_documento', ''),
        'documento': envio_data.get('documento', ''),
        'pais': envio_data.get('pais', 'Colombia'),
        'departamento': envio_data.get('departamento', ''),
        'referencia': envio_data.get('referencia', ''),
        'cp': envio_data.get('cp', ''),
        'fecha': datetime.now().strftime('%Y-%m-%d'),
        'numero_factura': numero_factura_final,
        'factura': _normalizar_factura_json(factura_data),
        'items': items_carrito,
    }
    guardar_pedido_fallback(pedido_fallback)
    _descontar_stock_fallback(items_carrito)

    # 3. Guarda el resumen del pedido en sesión para la vista final de confirmación.
    session['pedido_confirmado'] = {
        'numero_orden': numero_final,
        'numero_factura': numero_factura_final,
        'metodo': metodo,
        'nombre_cliente': f"{nombre_c} {apellido_c}".strip() or "Cliente",
        'ciudad': envio_data.get('ciudad', ''),
        'direccion': dir_c,
        'email': email_c,
        'total': total_calculado,
        'items': items_carrito,
        'transportadora': envio_obj.get_transportadora(),
        'guia': envio_obj.get_guia(),
        'estado_factura': factura_obj.estado,
    }
    session['facturas_autorizadas'] = [numero_factura_final]

    # Limpia los datos temporales para no dejar información de la compra en sesión.
    session.pop('envio_data', None)

    return redirect(url_for('main.ver_factura', numero_factura=numero_factura_final))


@main_routes.route('/factura/<string:numero_factura>')
@usuario_required
def ver_factura(numero_factura):
    """Muestra la factura guardada para la compra confirmada."""
    factura = _buscar_factura(numero_factura)
    if not factura:
        abort(404)
    if not _usuario_puede_ver_factura(numero_factura, factura):
        abort(403)
    return render_template('web/factura.html', factura=factura)


@main_routes.route('/factura/<string:numero_factura>/pdf')
@usuario_required
def descargar_factura(numero_factura):
    """Genera y descarga el PDF desde los datos persistidos de la factura."""
    factura = _buscar_factura(numero_factura)
    if not factura:
        abort(404)
    if not _usuario_puede_ver_factura(numero_factura, factura):
        abort(403)
    archivo = generar_pdf_factura(factura)
    return send_file(
        archivo,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{numero_factura}.pdf",
    )


@main_routes.route('/confirmacion')
def confirmacion():
    """Muestra la página final de pedido confirmado al usuario.

    Recoge el resumen guardado en sesión, lo elimina de la memoria para evitar
    duplicados y renderiza la vista de confirmación con la información de compra.
    """
    pedido = session.pop('pedido_confirmado', None)
    if not pedido:
        flash('No hay un pedido activo. Continúa comprando.', 'info')
        return redirect(url_for('main.index'))
    return render_template('web/confirmacion.html', pedido=pedido)



# --- RUTAS DE LA APLICACIÓN MÓVIL ---

@main_routes.route('/app')
def app_index():
    """Home de la app móvil con algunos productos destacados y categorías."""
    todos_productos = obtener_productos()
    productos = todos_productos[:6]
    categorias = _agregar_categoria_mixto(obtener_categorias_disponibles(), todos_productos)
    return render_template('aplicacion/index_app.html', productos=productos, categorias=categorias)


@main_routes.route('/app/productos')
def app_productos():
    """Catálogo móvil que permite filtrar productos por categoría."""
    productos = obtener_productos()
    categorias = _agregar_categoria_mixto(obtener_categorias_disponibles(), productos)
    cat = request.args.get('categoria')
    if cat:
        cat_slug = slug_categoria(cat)
        filtrados = [p for p in productos if _producto_pertenece_a_categoria(p, cat_slug)]
        return render_template(
            'aplicacion/products_app.html',
            productos=filtrados,
            categoria_activa=cat_slug,
            categoria_nombre=nombre_categoria(cat_slug),
            categorias=categorias,
        )
    return render_template(
        'aplicacion/products_app.html',
        productos=productos,
        categoria_activa='todos',
        categoria_nombre='Todos',
        categorias=categorias,
    )


@main_routes.route('/app/carrito')
def app_carrito():
    """Vista del carrito en la app móvil para revisar los productos antes de pagar."""
    return render_template('aplicacion/cart_app.html')


@main_routes.route('/app/envio', methods=['GET', 'POST'])
@usuario_required
def app_envio():
    """Formulario de envío en la versión móvil de la plataforma."""
    if request.method == 'POST':
        session['envio_data'] = {
            'email': request.form.get('email'),
            'nombre': request.form.get('nombre'),
            'apellido': request.form.get('apellido'),
            'tipo_documento': request.form.get('tipo_documento'),
            'documento': request.form.get('documento'),
            'pais': request.form.get('pais') or 'Colombia',
            'departamento': request.form.get('departamento'),
            'telefono': request.form.get('telefono'),
            'direccion': request.form.get('direccion'),
            'referencia': request.form.get('referencia'),
            'ciudad': request.form.get('ciudad'),
            'cp': request.form.get('cp'),
        }
        return redirect(url_for('main.app_pago'))
    datos_envio_previo = obtener_ultimo_envio_usuario(session.get('usuario'))
    return render_template('aplicacion/envio_app.html', datos_envio_previo=datos_envio_previo)


@main_routes.route('/app/pago')
@usuario_required
def app_pago():
    """Pantalla de pago para la interfaz móvil."""
    return render_template(
        'aplicacion/pago_app.html', aplicar_descuento=bool(session.get('beneficio_primera_compra'))
    )


@main_routes.app_errorhandler(404)
def pagina_no_encontrada(e):
    """Manejador personalizado para mostrar una página 404 amigable."""
    return render_template('web/404.html'), 404
