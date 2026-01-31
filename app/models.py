from app import db
from flask_login import UserMixin
from datetime import datetime

class Rol(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey('rol.id'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    password_cambiada = db.Column(db.Boolean, default=False)

    rol = db.relationship('Rol', backref='usuarios')

class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    identificacion = db.Column(db.String(20), unique=True, nullable=False)
    telefono = db.Column(db.String(15))
    email = db.Column(db.String(100))
    direccion = db.Column(db.String(200))
    fecha_nacimiento = db.Column(db.Date)
    sexo = db.Column(db.String(20))
    activo = db.Column(db.Boolean, default=True)

class Especialidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)

class HistoriaClinica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    contenido = db.Column(db.Text, default='')
    ultima_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    actualizado_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

    paciente = db.relationship('Paciente', backref='historias')
    actualizado_por = db.relationship('Usuario', foreign_keys=[actualizado_por_id])

class HistoriaEntrada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    historia_id = db.Column(db.Integer, db.ForeignKey('historia_clinica.id'), nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    historia = db.relationship('HistoriaClinica', backref='entradas')
    autor = db.relationship('Usuario', foreign_keys=[autor_id])


class HistoriaVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    historia_id = db.Column(db.Integer, db.ForeignKey('historia_clinica.id'), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    actualizado_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    historia = db.relationship('HistoriaClinica', backref='versiones')
    autor = db.relationship('Usuario', foreign_keys=[actualizado_por_id])

class Cita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    especialidad_id = db.Column(db.Integer, db.ForeignKey('especialidad.id'), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    estado = db.Column(db.String(20), default='Pendiente')  # Pendiente, Realizada, Cancelada

    paciente = db.relationship('Paciente', backref='citas')
    medico = db.relationship('Usuario', foreign_keys=[medico_id])
    especialidad = db.relationship('Especialidad', backref='citas')