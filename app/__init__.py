from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuración
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ips-fulano-secreto-cambiar-en-produccion')
    
    # Base de datos - PostgreSQL en producción, SQLite en desarrollo
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        # Render usa postgres:// pero SQLAlchemy necesita postgresql://
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    else:
        # SQLite para desarrollo local
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/database.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.index'  # Cambiado de 'main.login' a 'main.index'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'

    # Importar modelos
    from .models import Usuario, Rol

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Registrar el blueprint
    from .routes import main
    app.register_blueprint(main)

    with app.app_context():
        # Crear directorio instance solo si usamos SQLite
        if not app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql'):
            os.makedirs(os.path.join(app.instance_path), exist_ok=True)
        
        # Crear todas las tablas
        db.create_all()
        
        # Crear roles por defecto si no existen
        if not Rol.query.first():
            roles_por_defecto = [
                {'nombre': 'admin', 'descripcion': 'Administrador del sistema'},
                {'nombre': 'medico', 'descripcion': 'Profesional médico'},
                {'nombre': 'enfermeria', 'descripcion': 'Personal de enfermería'},
                {'nombre': 'recepcionista', 'descripcion': 'Personal de recepción'}
            ]
            for rol_data in roles_por_defecto:
                rol = Rol(nombre=rol_data['nombre'], descripcion=rol_data['descripcion'])
                db.session.add(rol)
            db.session.commit()
            print("✅ Roles por defecto creados")

        # Crear admin por defecto si no existe
        from werkzeug.security import generate_password_hash
        if not Usuario.query.filter_by(email='admin@ipsfulano.com').first():
            rol_admin = Rol.query.filter_by(nombre='admin').first()
            if rol_admin:
                admin = Usuario(
                    nombre='Administrador',
                    email='admin@ipsfulano.com',
                    password=generate_password_hash('admin123'),
                    rol_id=rol_admin.id,
                    activo=True,
                    password_cambiada=False
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Usuario admin creado")
                print("   Email: admin@ipsfulano.com")
                print("   Contraseña: admin123")

    return app