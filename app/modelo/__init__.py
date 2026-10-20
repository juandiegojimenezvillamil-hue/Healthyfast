"""Paquete que exporta los modelos de dominio del sistema.

Aquí se reúnen las clases principales del negocio: personas, clientes,
empleados, productos, categorías, pagos, envíos y facturas.
"""

# Healthy Fast - Paquete de Modelos Lógicos POO
# Importa las clases del dominio para reutilizarse en toda la aplicación.
try:
    from modelo.log_persona import Persona
    from modelo.log_cliente import Cliente
    from modelo.log_empleado import Empleado
    from modelo.log_categoria import Categoria
    from modelo.log_produc import Producto
    from modelo.log_pago import Pago, PagoEfectivo, PagoTarjeta
    from modelo.log_envio import Envio
    from modelo.log_factura import Factura, FacturaDetalle
except ImportError:
    from app.modelo.log_persona import Persona
    from app.modelo.log_cliente import Cliente
    from app.modelo.log_empleado import Empleado
    from app.modelo.log_categoria import Categoria
    from app.modelo.log_produc import Producto
    from app.modelo.log_pago import Pago, PagoEfectivo, PagoTarjeta
    from app.modelo.log_envio import Envio
    from app.modelo.log_factura import Factura, FacturaDetalle

# Exporta los nombres para usarse con importaciones tipo from app.modelo import ...
__all__ = [
    'Persona',
    'Cliente',
    'Empleado',
    'Categoria',
    'Producto',
    'Pago',
    'PagoEfectivo',
    'PagoTarjeta',
    'Envio',
    'Factura',
    'FacturaDetalle',
]
