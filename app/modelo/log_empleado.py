"""Modelo del empleado de la tienda.

Extiende Persona para guardar datos laborales como puesto y salario,
lo que permite manejar la parte administrativa del negocio.
"""

try:
    from modelo.log_persona import Persona
except ImportError:
    try:
        from app.modelo.log_persona import Persona
    except ImportError:
        from log_persona import Persona


class Empleado(Persona):

    def __init__(self, id_persona, nombre, apellido,
                 email, telefono, direccion,
                 puesto, salario):
        # Hereda los datos comunes de Persona y agrega información laboral.
        super().__init__(id_persona, nombre, apellido,
                         email, telefono, direccion)

        self.__puesto = puesto
        self.__salario = salario

    # GETTERS: permiten consultar datos del perfil laboral.
    def get_puesto(self):
        return self.__puesto

    def get_salario(self):
        return self.__salario

    # SETTERS: actualizan puesto o salario del empleado.
    def set_puesto(self, puesto):
        self.__puesto = puesto

    def set_salario(self, salario):
        self.__salario = salario

    # MÉTODO: retorna el salario del empleado.
    def calcular_salario(self):
        return self.__salario

    # STR: representación breve del empleado con su cargo.
    def __str__(self):
        return f"Empleado: {self.get_nombre()} - {self.__puesto}"


