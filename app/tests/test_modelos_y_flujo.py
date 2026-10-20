import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Asegurar que app/ esté en el sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from flask import Flask
import routes.routes as routes
from routes.routes import main_routes, _leer_pedidos_fallback, _guardar_pedidos_fallback
from modelo import (
    Persona, Cliente, Empleado, Categoria, Producto as ModeloProducto,
    Pago, PagoEfectivo, PagoTarjeta, Envio, Factura, FacturaDetalle
)


class ModelosPOOTest(unittest.TestCase):
    def test_oculta_emergency_del_catalogo_y_del_fallback_de_categorias(self):
        producto_emergency = {'categoria': 'Emergency'}
        self.assertTrue(routes._categoria_excluida('Emergency'))
        self.assertFalse(routes._producto_visible(producto_emergency))

        with patch('routes.routes.get_connection', return_value=None):
            categorias = routes.obtener_categorias_disponibles()

        self.assertNotIn('emergency', [categoria['slug'] for categoria in categorias])

    def test_oculta_frutos_secos_y_proteinas_del_catalogo(self):
        for categoria in ('Frutos Secos', 'Proteínas', 'proteinas'):
            with self.subTest(categoria=categoria):
                self.assertTrue(routes._categoria_excluida(categoria))
                self.assertFalse(routes._producto_visible({'categoria': categoria}))

    def test_herencia_persona_cliente_empleado(self):
        cliente = Cliente(1, "Carlos", "Gómez", "carlos@test.com", "3001234567", "Calle 10 #20")
        self.assertEqual(cliente.get_nombre(), "Carlos")
        self.assertEqual(cliente.get_email(), "carlos@test.com")
        self.assertIn("Carlos", str(cliente))

        empleado = Empleado(2, "Laura", "Pérez", "laura@test.com", "3109876543", "Cra 15 #30", "Administradora", 3500000)
        self.assertEqual(empleado.get_puesto(), "Administradora")
        self.assertEqual(empleado.calcular_salario(), 3500000)
        self.assertIn("Laura", str(empleado))

    def test_producto_stock_y_descuento(self):
        prod = ModeloProducto(10, "Serum Vitamina C", "Antioxidante facial", 85000, 15)
        self.assertTrue(prod.hay_stock(5))
        self.assertFalse(prod.hay_stock(20))
        self.assertTrue(prod.descontar_stock(5))
        self.assertEqual(prod.get_stock(), 10)
        self.assertFalse(prod.descontar_stock(15))

    def test_factura_detalles_total_y_envio(self):
        cliente = Cliente(1, "Ana", "Ruiz", "ana@test.com", "3001112233", "Av 68 #45")
        prod1 = ModeloProducto(101, "Botiquín Tipo A", "Primeros auxilios", 100000, 10)
        prod2 = ModeloProducto(102, "Crema Hidratante", "Cuidado corporal", 50000, 10)

        factura = Factura("HF-TEST-001", cliente)
        factura.agregar_producto(prod1, 1)
        factura.agregar_producto(prod2, 2)

        # Subtotal: 100000 + (50000*2) = 200000. Total con 19% IVA = 238000
        self.assertEqual(factura.calcular_total(), 238000.0)
        self.assertEqual(prod1.get_stock(), 9)
        self.assertEqual(prod2.get_stock(), 8)

        # Agregar pago
        pago = factura.crear_pago("PAG-001", "tarjeta")
        self.assertEqual(pago.estado, "Aprobado")
        self.assertEqual(factura.estado, "Pagada")

        # Agregar envío
        envio = factura.crear_envio("ENV-001", "Healthy Express", "GUIA-999")
        self.assertEqual(envio.get_estado(), "En proceso")
        envio.marcar_entregado()
        self.assertEqual(envio.get_estado(), "Entregado")

    def test_polimorfismo_pagos(self):
        pago_efectivo = PagoEfectivo(monto_a_pagar=50000, billete_entregado=100000)
        self.assertTrue(pago_efectivo.procesar_pago())
        self.assertEqual(pago_efectivo.cambio, 50000.0)
        self.assertEqual(pago_efectivo.estado, "Aprobado")

        pago_efectivo_insuficiente = PagoEfectivo(monto_a_pagar=50000, billete_entregado=20000)
        self.assertFalse(pago_efectivo_insuficiente.procesar_pago())
        self.assertEqual(pago_efectivo_insuficiente.estado, "Rechazado")

        pago_tarjeta = PagoTarjeta(
            monto_a_pagar=120000,
            numero_tarjeta="1234567812345678",
            titular="Carlos Gómez",
            fecha_exp="12/28",
            cvv="123"
        )
        self.assertTrue(pago_tarjeta.procesar_pago())
        self.assertEqual(pago_tarjeta.estado, "Aprobado")


class FlujoCompraRutasTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__, template_folder=str(BASE_DIR / 'templates'), static_folder=str(BASE_DIR / 'static'))
        self.app.secret_key = 'test_secret_key'
        self.app.register_blueprint(main_routes)
        self.client = self.app.test_client()

    def test_rutas_web_principales(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertNotIn(b'>Emergency<', res.data)

        res_prod = self.client.get('/productos')
        self.assertEqual(res_prod.status_code, 200)

        res_cat = self.client.get('/productos?categoria=skincare')
        self.assertEqual(res_cat.status_code, 200)

        res_login = self.client.get('/login')
        self.assertEqual(res_login.status_code, 200)

    def test_productos_con_mixto_aparecen_en_seccion_mixto_web_y_app(self):
        productos = [
            {'id': 1, 'nombre': 'Serum facial mixto', 'categoria': 'skincare', 'precio': 10000, 'stock': 2, 'desc': '', 'imagen': '/static/serum.jpg'},
            {'id': 2, 'nombre': 'Aceite Mixto', 'categoria': 'body', 'precio': 12000, 'stock': 3, 'desc': '', 'imagen': '/static/aceite.jpg'},
            {'id': 3, 'nombre': 'Crema hidratante', 'categoria': 'body', 'precio': 8000, 'stock': 4, 'desc': '', 'imagen': '/static/crema.jpg'},
        ]
        categorias = [
            {'slug': 'skincare', 'nombre': 'Skincare'},
            {'slug': 'body', 'nombre': 'Body Care'},
        ]
        with patch('routes.routes.obtener_productos', return_value=productos), \
                patch('routes.routes.obtener_categorias_disponibles', return_value=categorias):
            respuesta_web = self.client.get('/productos?categoria=mixto')
            respuesta_app = self.client.get('/app/productos?categoria=mixto')

        for respuesta in (respuesta_web, respuesta_app):
            self.assertEqual(respuesta.status_code, 200)
            self.assertIn(b'Serum facial mixto', respuesta.data)
            self.assertIn(b'Aceite Mixto', respuesta.data)
            self.assertNotIn(b'Crema hidratante', respuesta.data)
        self.assertIn(b'/productos/categoria/mixto', respuesta_web.data)
        self.assertIn(b'?categoria=mixto', respuesta_app.data)

    def test_rutas_app_movil(self):
        with self.client.session_transaction() as sess:
            sess['usuario'] = 'estudiante@healthyfast.com'
        res_app = self.client.get('/app')
        self.assertEqual(res_app.status_code, 200)
        self.assertNotIn(b'>Emergency<', res_app.data)

        res_app_prod = self.client.get('/app/productos')
        self.assertEqual(res_app_prod.status_code, 200)

        res_app_cart = self.client.get('/app/carrito')
        self.assertEqual(res_app_cart.status_code, 200)

        res_app_envio = self.client.get('/app/envio')
        self.assertEqual(res_app_envio.status_code, 200)

    def test_rutas_app_productos_sin_categoria_no_falla(self):
        productos = [{
            'id': 1,
            'nombre': 'Producto sin categoria',
            'precio': 25000,
            'stock': 7,
            'desc': 'Descripción de prueba',
            'imagen': '/static/img/categorias/body.png'
        }]
        with patch('routes.routes.obtener_productos', return_value=productos), \
             patch('routes.routes.obtener_categorias_disponibles', return_value=[{'id': 1, 'slug': 'body', 'nombre': 'Body Care'}]):
            res = self.client.get('/app/productos?categoria=body')

        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Producto sin categoria', res.data)

    def test_actualizar_producto_en_bd_crea_categoria_si_falta(self):
        class FakeCursor:
            def __init__(self):
                self.executed = []

            def execute(self, query, params=None):
                self.executed.append((query, params))
                if 'SELECT id_categoria FROM categorias WHERE nombre = %s' in query:
                    return None
                if 'INSERT INTO categorias' in query:
                    return None
                if 'UPDATE productos' in query:
                    return None

            def fetchone(self):
                if len(self.executed) == 1:
                    return (1,)
                return None

            @property
            def rowcount(self):
                return 1

            @property
            def lastrowid(self):
                return 99

        class FakeConnection:
            def cursor(self):
                return FakeCursor()

            def commit(self):
                pass

            def close(self):
                pass

        with patch('routes.routes.get_connection', return_value=FakeConnection()):
            ok = routes.actualizar_producto_en_bd(
                1,
                'Nuevo producto',
                'skincare',
                25000,
                8,
                'descripcion',
                '/static/img/categorias/skincare.jpg',
                subcategoria='mujer',
            )

        self.assertTrue(ok)

    def test_flujo_completo_checkout_y_persistencia(self):
        # 1. Enviar datos de envío
        with self.client.session_transaction() as sess:
            sess['usuario'] = 'estudiante@healthyfast.com'
            sess['envio_data'] = {
                'email': 'comprador@test.com',
                'nombre': 'Estudiante',
                'apellido': 'Prueba',
                'tipo_documento': 'CC',
                'documento': '123456789',
                'pais': 'Colombia',
                'departamento': 'Cundinamarca',
                'telefono': '3009998877',
                'direccion': 'Carrera 7 # 100-20',
                'ciudad': 'Bogotá',
                'cp': '110111'
            }

        # 2. Procesar pago enviando carrito
        items_compra = [
            {"id": 1, "nombre": "Industrial Platinum", "precio": 180000, "cantidad": 1},
            {"id": 2, "nombre": "Glow Serum Avanzado", "precio": 120000, "cantidad": 2}
        ]
        total_esperado = 180000 + (120000 * 2)

        productos_test = [
            {'id': 1, 'nombre': 'Industrial Platinum', 'precio': 180000, 'stock': 5},
            {'id': 2, 'nombre': 'Glow Serum Avanzado', 'precio': 120000, 'stock': 5},
        ]
        with tempfile.TemporaryDirectory() as carpeta_temporal:
            with patch.object(routes, 'PEDIDOS_DATA_FILE', str(Path(carpeta_temporal) / 'pedidos.json')), \
                    patch.object(routes, 'PRODUCTOS_DATA_FILE', str(Path(carpeta_temporal) / 'productos.json')), \
                    patch.object(routes, '_ULTIMO_NUMERO_FACTURA', 0), \
                    patch('routes.routes.obtener_productos', return_value=productos_test), \
                    patch('routes.routes.guardar_pedido_completo_bd', return_value=None), \
                    patch('routes.routes.obtener_factura_por_numero', return_value=None):
                routes._guardar_pedidos_fallback([])
                routes._guardar_productos_fallback(productos_test)
                res_post = self.client.post('/procesar', data={
                    'metodo': 'efectivo',
                    'items_carrito': json.dumps(items_compra),
                    'total_pedido': str(total_esperado)
                }, follow_redirects=True)

        self.assertEqual(res_post.status_code, 200)
        self.assertIn(b'Confirmado', res_post.data)
        self.assertIn(b'Estudiante Prueba', res_post.data)
        self.assertIn(b'FACT-000001', res_post.data)
        self.assertIn(b'499,800.00', res_post.data)

        # 3. Verificar que el pedido aparezca en el Panel Admin
        with self.client.session_transaction() as sess:
            sess['usuario'] = 'admin@healthyfast.com'
            sess['rol'] = 'administrador'

        res_admin = self.client.get('/admin')
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b'Panel de Control', res_admin.data)


if __name__ == '__main__':
    unittest.main()
