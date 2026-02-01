"""
Script para inicializar la base de datos en producción
Este script se ejecuta automáticamente durante el deploy en Render
"""
import os
import sys

# Añadir el directorio actual al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Usuario, Rol, Paciente, Especialidad, Cita, HistoriaClinica
from werkzeug.security import generate_password_hash

def init_database():
    # Crear la aplicación con el contexto adecuado
    app = create_app()
    
    with app.app_context():
        print("🔄 Inicializando base de datos...")
        print(f"📊 URI de base de datos: {app.config.get('SQLALCHEMY_DATABASE_URI', 'No configurada')[:50]}...")
        
        try:
            # Crear todas las tablas
            print("📋 Creando tablas...")
            db.create_all()
            print("✅ Tablas creadas")
            
            # Verificar si ya existen roles
            if Rol.query.first() is None:
                print("🔧 Creando roles por defecto...")
                
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
                print("✅ Roles creados exitosamente")
            else:
                print("ℹ️  Los roles ya existen, omitiendo creación")
            
            # Crear usuario administrador por defecto
            admin_email = 'admin@ipsfulano.com'
            if not Usuario.query.filter_by(email=admin_email).first():
                print("👤 Creando usuario administrador...")
                
                rol_admin = Rol.query.filter_by(nombre='admin').first()
                
                if rol_admin:
                    admin = Usuario(
                        nombre='Administrador',
                        email=admin_email,
                        password=generate_password_hash('admin123'),
                        rol_id=rol_admin.id,
                        activo=True,
                        password_cambiada=False
                    )
                    db.session.add(admin)
                    db.session.commit()
                    
                    print("✅ Usuario administrador creado")
                    print("=" * 50)
                    print("📧 Email: admin@ipsfulano.com")
                    print("🔑 Contraseña: admin123")
                    print("=" * 50)
                    print("⚠️  IMPORTANTE: Cambia esta contraseña después del primer ingreso")
                else:
                    print("❌ Error: No se encontró el rol 'admin'")
            else:
                print("ℹ️  El usuario administrador ya existe")
            
            print("✅ Inicialización completada exitosamente")
            
        except Exception as e:
            print(f"❌ Error durante la inicialización: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    init_database()