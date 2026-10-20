"""Modelo del cliente.

Un cliente hereda la información de Persona y agrega un historial de compras,
lo que permite guardar facturas o transacciones asociadas a un usuario.
"""

try:
    from modelo.log_persona import Persona
except ImportError:
    try:
        from app.modelo.log_persona import Persona
    except ImportError:
        from log_persona import Persona


class Cliente(Persona):

    def __init__(self, id_persona, nombre, apellido,
                 email, telefono, direccion):
        # Inicializa la información común y agrega el historial del cliente.
        super().__init__(id_persona, nombre, apellido,
                         email, telefono, direccion)

        # Guarda las facturas o compras realizadas por este cliente.
        self.__historial = []

    # GETTERS: devuelve el historial de compras del cliente.
    def get_historial(self):
        return self.__historial

    # SETTERS: reemplaza el historial completo por otro listado.
    def set_historial(self, historial):
        self.__historial = historial

    # MÉTODO: agrega una factura nueva al historial del cliente.
    def agregar_factura(self, factura):
        self.__historial.append(factura)

    # STR: representación breve del cliente.
    def __str__(self):
        return f"Cliente: {self.get_nombre()}"
