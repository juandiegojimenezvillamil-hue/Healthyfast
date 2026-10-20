"""Módulo de pagos y métodos de cobro del sistema.

Define la base para cualquier pago y dos variantes: efectivo y tarjeta.
Esto permite modelar el proceso de cobro con polimorfismo y reutilizar la
lógica general en todas las formas de pago.
"""

from datetime import datetime

# CLASE PADRE (Base genérica): representa cualquier transacción de pago.
class Pago:
    def __init__(self, monto):
        # Cada pago recibe un identificador único, fecha y monto total.
        self.id_pago = f"PAG-{int(datetime.now().timestamp())}"
        self.fecha = datetime.now()
        self.monto = monto
        self.estado = "Pendiente"
        self.metodo = None

    def procesar_pago(self) -> bool:
        # Este método sirve como plantilla para que las clases hijas lo redefinan.
        return False

# CLASE HIJA 1: modela el pago con efectivo.
class PagoEfectivo(Pago):
    def __init__(self, monto_a_pagar, billete_entregado):
        # La clase hija reutiliza el constructor principal y añade datos del efectivo.
        super().__init__(monto_a_pagar)
        self.billete_entregado = billete_entregado
        self.cambio = 0.0

    def procesar_pago(self) -> bool:
        print("\n--- Procesando Pago en Efectivo ---")
        if self.billete_entregado >= self.monto:
            self.cambio = self.billete_entregado - self.monto
            self.estado = "Aprobado"
            print(f"[OK] Pago exitoso. Total: ${self.monto} | Entrego: ${self.billete_entregado}")
            print(f"[INFO] Cambio a devolver: ${self.cambio:.2f}")
            return True
        else:
            self.estado = "Rechazado"
            print(f"[ERROR] El monto entregado (${self.billete_entregado}) no alcanza para pagar (${self.monto}).")
            return False

# CLASE HIJA 2: modela el pago con tarjeta.
class PagoTarjeta(Pago):
    def __init__(self, monto_a_pagar, numero_tarjeta, titular, fecha_exp, cvv):
        # Reutiliza la lógica general del pago y agrega datos de la tarjeta.
        super().__init__(monto_a_pagar)
        self.numero_tarjeta = numero_tarjeta
        self.titular = titular
        self.fecha_exp = fecha_exp
        self.cvv = cvv

    def procesar_pago(self) -> bool:
        print("\n--- Procesando Pago con Tarjeta ---")
        # Simula la validación del banco con una comprobación simple de longitud.
        if len(self.numero_tarjeta) == 16 and len(str(self.cvv)) in [3, 4]:
            self.estado = "Aprobado"
            # Ocultamos los dígitos para evitar exponer información sensible.
            tarjeta_oculta = f"**** **** **** {self.numero_tarjeta[-4:]}"
            print(f"[OK] Transaccion aprobada para {self.titular}.")
            print(f"[INFO] Tarjeta: {tarjeta_oculta}")
            return True
        else:
            self.estado = "Rechazado"
            print("[ERROR] Datos de tarjeta invalidos. Revise el numero o CVV.")
            return False
