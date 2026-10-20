import json
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from static.database import conexion as database
from facturacion import calcular_factura, generar_pdf_factura
import routes.routes as routes


class FacturacionTest(unittest.TestCase):
    def setUp(self):
        self.comprador = {
            "nombre_completo": "Ana Compradora",
            "tipo_documento": "CC",
            "documento": "123456789",
            "pais": "Colombia",
            "departamento": "Antioquia",
            "ciudad": "Medellín",
            "direccion": "Calle 10 # 20-30",
            "telefono": "3001234567",
            "email": "ana@example.com",
        }

    def test_calcula_descuento_iva_y_total_desde_las_lineas(self):
        factura = calcular_factura(
            [
                {"id": 7, "nombre": "Sérum", "precio": 10000, "cantidad": 2},
                {"id": 8, "nombre": "Crema", "precio": 5000, "cantidad": 1},
            ],
            self.comprador,
            "efectivo",
            "FACT-000001",
            descuento_porcentaje=Decimal("0.05"),
        )

        self.assertEqual(factura["subtotal"], Decimal("25000.00"))
        self.assertEqual(factura["descuento"], Decimal("1250.00"))
        self.assertEqual(factura["iva"], Decimal("4512.50"))
        self.assertEqual(factura["total_final"], Decimal("28262.50"))
        self.assertEqual(sum((linea["descuento"] for linea in factura["lineas"])), factura["descuento"])
        self.assertEqual(sum((linea["iva"] for linea in factura["lineas"])), factura["total_impuestos"])

    def test_rechaza_compra_sin_items_y_cantidades_invalidas(self):
        with self.assertRaises(ValueError):
            calcular_factura([], self.comprador, "efectivo", "FACT-000001")
        with self.assertRaises(ValueError):
            calcular_factura(
                [{"id": 1, "nombre": "Producto", "precio": 1000, "cantidad": 0}],
                self.comprador,
                "efectivo",
                "FACT-000001",
            )

    def test_pdf_se_genera_con_cabecera_pdf(self):
        factura = calcular_factura(
            [{"id": 1, "nombre": "Producto de prueba", "precio": 1000, "cantidad": 1}],
            self.comprador,
            "transferencia",
            "FACT-000001",
        )

        pdf = generar_pdf_factura(factura).read()

        self.assertTrue(pdf.startswith(b"%PDF-"))

    def test_checkout_genera_factura_web_y_pdf_con_precio_del_catalogo(self):
        producto = {
            "id": 44,
            "nombre": "Serum de prueba",
            "categoria": "skincare",
            "precio": 10000,
            "stock": 4,
            "imagen": "/static/serum.jpg",
            "desc": "Producto para validar el checkout",
        }
        envio = {
            **self.comprador,
            "nombre": "Ana",
            "apellido": "Compradora",
        }

        with tempfile.TemporaryDirectory() as carpeta_temporal:
            pedidos_path = Path(carpeta_temporal) / "pedidos.json"
            productos_path = Path(carpeta_temporal) / "productos.json"
            app = Flask(
                __name__,
                template_folder=str(Path(__file__).resolve().parents[1] / "templates"),
                static_folder=str(Path(__file__).resolve().parents[1] / "static"),
            )
            app.secret_key = "test-factura"
            app.register_blueprint(routes.main_routes)
            cliente = app.test_client()

            with patch.object(routes, "PEDIDOS_DATA_FILE", str(pedidos_path)), \
                    patch.object(routes, "PRODUCTOS_DATA_FILE", str(productos_path)), \
                    patch.object(routes, "obtener_productos", return_value=[producto]), \
                    patch.object(routes, "guardar_pedido_completo_bd", return_value=None), \
                    patch.object(routes, "obtener_factura_por_numero", return_value=None):
                routes._guardar_pedidos_fallback([])
                routes._guardar_productos_fallback([producto])
                with cliente.session_transaction() as session:
                    session["usuario"] = envio["email"]
                    session["envio_data"] = envio

                respuesta = cliente.post(
                    "/procesar",
                    data={
                        "metodo": "efectivo",
                        "items_carrito": json.dumps([
                            {"id": 44, "nombre": "Precio falso", "precio": 1, "cantidad": 2}
                        ]),
                        "total_pedido": "2",
                    },
                    follow_redirects=True,
                )

                self.assertEqual(respuesta.status_code, 200)
                self.assertIn(b"FACT-000001", respuesta.data)
                self.assertIn(b"Serum de prueba", respuesta.data)
                self.assertIn(b"23,800.00", respuesta.data)

                pdf = cliente.get("/factura/FACT-000001/pdf")
                self.assertEqual(pdf.status_code, 200)
                self.assertEqual(pdf.mimetype, "application/pdf")
                self.assertTrue(pdf.data.startswith(b"%PDF-"))

                pedido = routes._leer_pedidos_fallback()[0]
                self.assertEqual(pedido["factura"]["subtotal"], 20000.0)
                self.assertEqual(pedido["factura"]["total_impuestos"], 3800.0)
                self.assertEqual(pedido["factura"]["total_final"], 23800.0)

    def test_mysql_guarda_cabecera_y_detalle_en_la_transaccion(self):
        class FakeCursor:
            def __init__(self):
                self.lastrowid = None
                self.rowcount = 1
                self.resultado = None
                self.filas = []
                self.consultas = []
                self.parametros_factura = None
                self.detalles_guardados = []

            def execute(self, consulta, parametros=None):
                normalizada = " ".join(consulta.lower().split())
                self.consultas.append(normalizada)
                self.resultado = None
                self.filas = []
                if "information_schema.columns" in normalizada:
                    self.filas = []
                elif "information_schema.statistics" in normalizada:
                    self.resultado = (0,)
                elif normalizada.startswith("select id_cliente"):
                    self.resultado = (9,)
                elif normalizada.startswith("select id_factura from facturas"):
                    self.resultado = None
                elif normalizada.startswith("insert into pedidos"):
                    self.lastrowid = 31
                elif normalizada.startswith("insert into facturas"):
                    self.lastrowid = 51
                    self.parametros_factura = parametros
                elif normalizada.startswith("insert into detalle_factura"):
                    self.detalles_guardados.append(parametros)
                elif normalizada.startswith("update productos"):
                    self.rowcount = 1

            def fetchone(self):
                return self.resultado

            def fetchall(self):
                return self.filas

            def close(self):
                pass

        class FakeConnection:
            def __init__(self):
                self.fake_cursor = FakeCursor()
                self.committed = False
                self.rolled_back = False
                self.autocommit = True

            def cursor(self, **kwargs):
                return self.fake_cursor

            def commit(self):
                self.committed = True

            def rollback(self):
                self.rolled_back = True

            def close(self):
                pass

        conexion_falsa = FakeConnection()
        factura = calcular_factura(
            [{"id": 6, "nombre": "Sérum", "precio": 10000, "cantidad": 2}],
            self.comprador,
            "efectivo",
            "FACT-000001",
        )

        with patch.object(database, "get_connection", return_value=conexion_falsa):
            resultado = database.guardar_pedido_completo_bd(
                cliente_info={
                    "nombre": "Ana", "apellido": "Compradora", "email": "ana@example.com",
                    "telefono": "3001234567",
                },
                items_carrito=[{"id": 6, "nombre": "Sérum", "precio": 10000, "cantidad": 2}],
                metodo_pago="efectivo",
                total=float(factura["total_final"]),
                factura_data=factura,
            )

        self.assertEqual(resultado["numero_factura"], "FACT-000001")
        self.assertTrue(conexion_falsa.committed)
        self.assertFalse(conexion_falsa.rolled_back)
        self.assertEqual(len(conexion_falsa.fake_cursor.detalles_guardados), 1)
        self.assertTrue(any(
            consulta.startswith("create table if not exists detalle_factura")
            for consulta in conexion_falsa.fake_cursor.consultas
        ))

    def test_consecutivo_local_no_repite_numeros_en_compras_concurrentes(self):
        with tempfile.TemporaryDirectory() as carpeta_temporal, \
                patch.object(routes, "PEDIDOS_DATA_FILE", str(Path(carpeta_temporal) / "pedidos.json")), \
                patch.object(routes, "_ULTIMO_NUMERO_FACTURA", 0):
            routes._guardar_pedidos_fallback([])
            with ThreadPoolExecutor(max_workers=8) as ejecutor:
                numeros = list(ejecutor.map(lambda _: routes._siguiente_numero_factura(), range(32)))

        self.assertEqual(len(numeros), len(set(numeros)))
        self.assertEqual(set(numeros), {f"FACT-{indice:06d}" for indice in range(1, 33)})


if __name__ == "__main__":
    unittest.main()