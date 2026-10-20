"""Modelo del proceso de entrega de un pedido.

Representa la guía, transportadora y estado del envío para llevar un control
visual del estado de entrega desde la compra hasta la entrega final.
"""


class Envio:

    def __init__(self, id_envio, transportadora, guia):
        # Identificador del envío y datos del servicio de logística.
        self.__id_envio = id_envio
        self.__transportadora = transportadora
        self.__guia = guia
        # Estado inicial del envío: aún en proceso.
        self.__estado = "En proceso"

    # GETTERS: consultan los datos del envío.
    def get_transportadora(self):
        return self.__transportadora

    def get_estado(self):
        return self.__estado

    def get_guia(self):
        return self.__guia

    def get_id_envio(self):
        return self.__id_envio

    # SETTERS: permiten actualizar la información del envío.
    def set_guia(self, guia):
        self.__guia = guia

    def set_id_envio(self, id_envio):
        self.__id_envio = id_envio

    def set_estado(self, estado):
        self.__estado = estado

    def set_transportadora(self, transportadora):
        self.__transportadora = transportadora

    # MÉTODO: actualiza el estado del envío como entregado.
    def marcar_entregado(self):
        self.__estado = "Entregado"

    # STR: muestra la empresa de envío y su estado actual.
    def __str__(self):
        return f"Envío: {self.__transportadora} - {self.__estado}"