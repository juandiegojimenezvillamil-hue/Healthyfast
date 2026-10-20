"""Modelo del producto que se vende en la tienda.

Representa el artículo comercial con nombre, descripción, precio y cantidad
actual disponible. Sirve como base para la lógica de compra y stock.
"""


class Producto:

    def __init__(self, id_producto, nombre,
                 descripcion, precio, stock):
        # Atributos principales del producto en el negocio.
        self.__id_producto = id_producto
        self.__nombre = nombre
        self.__descripcion = descripcion
        self.__precio = precio
        self.__stock = stock

    # GETTERS: permiten consultar la información del producto.
    def get_nombre(self):
        return self.__nombre

    def get_precio(self):
        return self.__precio

    def get_stock(self):
        return self.__stock

    def get_descripcion(self):
        return self.__descripcion

    def get_id_producto(self):
        return self.__id_producto

    # SETTERS: permiten actualizar el producto si cambian sus datos.
    def set_nombre(self, nombre):
        self.__nombre = nombre

    def set_precio(self, precio):
        self.__precio = precio

    def set_stock(self, stock):
        self.__stock = stock

    def set_descripcion(self, descripcion):
        self.__descripcion = descripcion

    def set_id_producto(self, id_produc):
        self.__id_producto = id_produc

    # MÉTODOS DE NEGOCIO: validan y actualizan el inventario.
    def hay_stock(self, cantidad):
        return self.__stock >= cantidad

    def descontar_stock(self, cantidad):
        if not self.hay_stock(cantidad):
            return False
        self.__stock -= cantidad
        return True

    # STR: presentación legible del producto para depuración o impresión.
    def __str__(self):
        return f"{self.__nombre} - ${self.__precio}"