import sys
import unittest

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from routes.routes import normalizar_producto, resolver_imagen_producto, producto_desde_formulario, obtener_datos_producto_por_imagen


class ProductoMappingTest(unittest.TestCase):
    def test_normalizar_producto_usa_campos_de_bd(self):
        producto = normalizar_producto(
            {
                "id_producto": 7,
                "nombre": "Botiquín Premium",
                "stock": 12,
                "precio": 150000,
                "id_categoria": 2,
                "categoria": "emergency",
            },
            "emergency",
        )

        self.assertEqual(producto["id"], 7)
        self.assertEqual(producto["nombre"], "Botiquín Premium")
        self.assertEqual(producto["stock"], 12)
        self.assertEqual(producto["precio"], 150000)
        self.assertEqual(producto["categoria"], "emergency")

    def test_resolver_imagen_producto_usa_url_real_si_existe(self):
        imagen = resolver_imagen_producto("Botiquín Premium", "emergency")
        self.assertIn("botiquin", imagen.lower())

    def test_normalizar_producto_corrige_imagen_local_que_no_coincide(self):
        producto = normalizar_producto({
            "nombre": "serum facial mixto",
            "categoria": "skincare",
            "imagen": "/static/img/categorias/mujer/tonico%20facial.jpeg",
        })

        self.assertIn("/mixto/serum%20facial%20mixto.jpeg", producto["imagen"])

    def test_resolver_prioriza_nombre_exacto_aunque_la_imagen_ya_se_use(self):
        imagen = "/static/img/categorias/mixto/aceite%20de%20coco%20mixto.jpeg"

        resultado = resolver_imagen_producto(
            "aceite de coco mixto", "body", imagenes_excluidas={imagen}
        )

        self.assertEqual(resultado, imagen)

    def test_producto_desde_formulario_genera_datos_validos(self):
        producto = producto_desde_formulario({
            "nombre": "Nuevo producto",
            "categoria": "body",
            "precio": "12000",
            "stock": "7",
            "desc": "Descripción",
            "imagen": "",
        })
        self.assertEqual(producto["nombre"], "Nuevo producto")
        self.assertEqual(producto["categoria"], "body")
        self.assertEqual(producto["stock"], 7)

    def test_producto_desde_formulario_acepta_precio_decimal_sin_cambios(self):
        producto = producto_desde_formulario({
            "nombre": "Producto existente",
            "categoria": "body",
            "precio": "15000.0",
            "stock": "7",
        })

        self.assertEqual(producto["precio"], 15000)

    def test_producto_desde_formulario_preserva_categoria_principal_y_subcategoria(self):
        producto = producto_desde_formulario({
            "nombre": "Nuevo producto",
            "categoria": "body",
            "subcategoria": "mujer",
            "precio": "12000",
            "stock": "7",
            "desc": "Descripción",
            "imagen": "",
        })
        self.assertEqual(producto["categoria"], "body")
        self.assertEqual(producto["subcategoria"], "mujer")

    def test_obtener_datos_producto_por_imagen_genera_datos_basicos_cuando_no_existe(self):
        datos = obtener_datos_producto_por_imagen("/static/img/categorias/mujer/prueba.webp")
        self.assertEqual(datos["nombre"], "Prueba")
        self.assertEqual(datos["categoria"], "body")
        self.assertEqual(datos["subcategoria"], "mujer")


if __name__ == "__main__":
    unittest.main()
