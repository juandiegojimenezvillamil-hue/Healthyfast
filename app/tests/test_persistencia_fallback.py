import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import routes.routes as routes


class PersistenciaFallbackTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.data_path = Path(self.tmpdir.name) / "productos.json"
        routes.PRODUCTOS_DATA_FILE = str(self.data_path)

    def test_guardar_producto_en_bd_persiste_en_fallback_json(self):
        with patch("routes.routes.get_connection", return_value=None):
            ok = routes.guardar_producto_en_bd(
                "Producto prueba",
                "body",
                10000,
                3,
                "Descripcion",
                "/static/img/categorias/body/test.jpg",
                subcategoria="mujer",
            )

        self.assertTrue(ok)
        self.assertTrue(self.data_path.exists())

        data = json.loads(self.data_path.read_text(encoding="utf-8"))
        self.assertTrue(any(item["nombre"] == "Producto prueba" for item in data))

        guardado = next(item for item in data if item["nombre"] == "Producto prueba")
        self.assertEqual(guardado["subcategoria"], "mujer")

    def test_obtener_datos_producto_por_imagen_devuelve_datos(self):
        productos = [{
            "id": 200,
            "nombre": "Aceite de Coco Hombre",
            "categoria": "hombre",
            "precio": 35000,
            "stock": 11,
            "desc": "Producto para hombre",
            "imagen": "/static/img/categorias/hombre/aceite de coco hombre.jpeg",
            "subcategoria": "hombre",
        }]
        routes._guardar_productos_fallback(productos)

        datos = routes.obtener_datos_producto_por_imagen("/static/img/categorias/hombre/aceite de coco hombre.jpeg")
        self.assertEqual(datos["nombre"], "Aceite de Coco Hombre")
        self.assertEqual(datos["precio"], 35000)

    def test_catalogo_admin_muestra_edicion_y_guarda_sin_panel(self):
        app = Flask(
            __name__,
            template_folder=str(Path(__file__).resolve().parents[1] / "templates"),
            static_folder=str(Path(__file__).resolve().parents[1] / "static"),
        )
        app.secret_key = "test"
        app.register_blueprint(routes.main_routes)
        client = app.test_client()
        producto = {
            "id": 42,
            "nombre": "Producto de prueba",
            "categoria": "body",
            "precio": 12000,
            "stock": 4,
            "desc": "Descripción de prueba",
            "imagen": "/static/test.jpg",
        }

        with patch.object(routes, "obtener_productos", return_value=[producto]), \
                patch.object(routes, "obtener_categorias_disponibles", return_value=[]):
            with client.session_transaction() as session:
                session["rol"] = "administrador"
            respuesta = client.get("/productos?categoria=body")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Editar".encode(), respuesta.data)
        self.assertNotIn("Añadir a la Bolsa".encode(), respuesta.data)

        with client.session_transaction() as session:
            session["rol"] = "administrador"
        with patch.object(routes, "actualizar_producto_en_bd", return_value=True) as actualizar:
            respuesta = client.post(
                "/admin/producto/editar/42",
                data={
                    "nombre": "Producto editado",
                    "categoria": "body",
                    "precio": "13000",
                    "stock": "5",
                    "desc": "Descripción actualizada",
                    "imagen": "/static/test.jpg",
                    "next": "/productos?categoria=body",
                },
            )

        actualizar.assert_called_once()
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.headers["Location"], "/productos?categoria=body")
