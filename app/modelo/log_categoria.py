"""Modelo de una categoría de productos.

Cada categoría agrupa varios productos, por ejemplo skincare, body o emergency.
Esto ayuda a organizar el catálogo y a clasificar la información del negocio.
"""


class Categoria:

    def __init__(self, id_categoria, nombre):
        # Identificador de la categoría y nombre visible que se mostrará en la app.
        self.__id_categoria = id_categoria
        self.__nombre = nombre
        # Lista de productos asociados a esta categoría.
        self.__productos = []

    # GETTERS: permiten acceder a los atributos internos de la categoría.
    def get_id_categoria(self):
        return self.__id_categoria

    def get_nombre(self):
        return self.__nombre

    def get_productos(self):
        return self.__productos

    # SETTERS: actualizan la categoría si se cambia su nombre o identificador.
    def set_id_categoria(self, id_categoria):
        self.__id_categoria = id_categoria

    def set_nombre(self, nombre):
        self.__nombre = nombre

    # MÉTODO: agrega un producto dentro de la categoría.
    def agregar_producto(self, producto):
        self.__productos.append(producto)

    # STR: representación legible de la categoría.
    def __str__(self):
        return f"Categoría: {self.__nombre}"