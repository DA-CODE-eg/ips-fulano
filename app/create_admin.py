# create_admin.py
from app import create_app, db
from app.models import Usuario, Rol
from werkzeug.security import generate_password_hash

app = create_app()
app.app_context().push()

# Eliminar cualquier admin existente (opcional)
Usuario.query.filter_by(email='admin@ipsfulano.com').delete()
db.session.commit()

# Obtener rol admin
rol_admin = Rol.query.filter_by(nombre='admin').first()
if not rol_admin:
    print("Error: Rol 'admin' no encontrado. Ejecuta init_db.py primero.")
    exit(1)

# Crear nuevo admin
admin = Usuario(
    nombre='Administrador',
    email='admin@ipsfulano.com',
    password=generate_password_hash('admin123', method='pbkdf2:sha256'),
    rol_id=rol_admin.id,
    activo=True,
    password_cambiada=False
)
db.session.add(admin)
db.session.commit()

print("✅ Usuario admin creado con:")
print("   Email: admin@ipsfulano.com")
print("   Contraseña: admin123")