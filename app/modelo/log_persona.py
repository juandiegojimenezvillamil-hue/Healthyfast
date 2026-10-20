"""Modelo base para toda persona del sistema.

Representa la información común de clientes y empleados, como nombre,
correo, teléfono y dirección. La idea es reutilizar esta clase para no
duplicar atributos en cada tipo de usuario.
"""


class Persona:

    def __init__(self, id_persona, nombre, apellido,
                 email, telefono, direccion):
        # Identificador único de la persona en la base de datos o en memoria.
        self.__id_persona = id_persona
        # Datos básicos de contacto y ubicación de la persona.
        self.__nombre = nombre
        self.__apellido = apellido
        self.__email = email
        self.__telefono = telefono
        self.__direccion = direccion

    # GETTERS: métodos para consultar los datos almacenados.
    def get_id_persona(self):
        return self.__id_persona

    def get_nombre(self):
        return self.__nombre

    def get_apellido(self):
        return self.__apellido

    def get_email(self):
        return self.__email

    def get_telefono(self):
        return self.__telefono

    def get_direccion(self):
        return self.__direccion

    # SETTERS: permiten actualizar la información de la persona.
    def set_nombre(self, nombre):
        self.__nombre = nombre

    def set_apellido(self, apellido):
        self.__apellido = apellido

    def set_email(self, email):
        self.__email = email

    def set_telefono(self, telefono):
        self.__telefono = telefono

    def set_direccion(self, direccion):
        self.__direccion = direccion

    # STR: devuelve una representación legible del nombre completo.
    def __str__(self):
        return f"{self.__nombre} {self.__apellido}"