"""Módulo de facturación y detalle del pedido.

Aquí se modela la factura completa de una compra, con los productos pedidos,
los pagos registrados y la información de envío asociado a la transacción.
"""

from datetime import datetime

try:
    from modelo.log_envio import Envio
    from modelo.log_pago import Pago as PagoBase
except ImportError:
    try:
        from app.modelo.log_envio import Envio
        from app.modelo.log_pago import Pago as PagoBase
    except ImportError:
        from log_envio import Envio
        from log_pago import Pago as PagoBase


class FacturaDetalle:
    """Representa un producto dentro de una factura con su cantidad y subtotal."""

    def __init__(self, producto, cantidad):
        # Producto vendido y la cantidad pedida por el cliente.
        self.producto = producto
        self.cantidad = cantidad
        self.precio_unitario = producto.get_precio()
        # Total parcial del detalle: cantidad × precio unitario.
        self.subtotal = self.calcular_subtotal()

    def calcular_subtotal(self):
        return self.cantidad * self.precio_unitario


class Factura:
    """Agrupa todos los datos de una compra y su estado de pago."""

    def __init__(self, id_factura, cliente):
        # Identificador y fecha en la que se genera la factura.
        self.id_factura = id_factura
        self.fecha = datetime.now()
        self.cliente = cliente
        self.estado = "Pendiente"
        # Productos y pagos asociados a la compra.
        self.detalles = []
        self.pagos = []
        self.envio = None
        self.total = 0.0

    def agregar_producto(self, producto, cantidad):
        # Validación de cantidad y disponibilidad del stock.
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a cero.")
        if not producto.hay_stock(cantidad):
            raise ValueError(f"No hay suficiente stock para {producto.get_nombre()}.")

        detalle = FacturaDetalle(producto, cantidad)
        self.detalles.append(detalle)
        producto.descontar_stock(cantidad)
        self.calcular_total()
        return detalle

    def calcular_total(self):
        # Suma todos los subtotales de los productos para obtener el total.
        subtotal_factura = sum(detalle.subtotal for detalle in self.detalles)
        self.total = round(subtotal_factura * 1.19, 2)
        return self.total

    def crear_pago(self, id_pago, metodo):
        # Se genera un pago según el total calculado y se registra como aprobado.
        monto_total = self.calcular_total()
        pago = PagoBase(monto_total)
        pago.id_pago = id_pago
        pago.metodo = metodo
        pago.estado = "Aprobado"
        self.pagos.append(pago)
        self.estado = "Pagada"
        return pago

    def crear_envio(self, id_envio, transportadora, guia):
        # Crea el objeto de envío asociado a la factura.
        self.envio = Envio(id_envio, transportadora, guia)
        return self.envio

    def get_pago(self):
        return self.pagos[-1] if self.pagos else None

    def get_envio(self):
        return self.envio

    def __str__(self):
        nombre_cliente = self.cliente.get_nombre() if self.cliente and hasattr(self.cliente, "get_nombre") else str(self.cliente)
        return f"Factura #{self.id_factura} | Cliente: {nombre_cliente} | Total: ${self.total:.2f} | Estado: {self.estado}"