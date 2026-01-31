from app import create_app, db
from app.models import Usuario
from werkzeug.security import generate_password_hash

app = create_app()
app.app_context().push()

# Ver usuarios
usuarios = Usuario.query.all()
print("Usuarios en la base de datos:")
for u in usuarios:
    print(f"ID: {u.id}, Nombre: {u.nombre}, Email: {u.email}, Rol: {u.rol}")

# Si no existe el admin, créalo
if not Usuario.query.filter_by(email='admin@ipsfulano.com').first():
    print("\nCreando usuario admin...")
    admin = Usuario(
        nombre='Administrador',
        email='admin@ipsfulano.com',
        password=generate_password_hash('admin123', method='pbkdf2:sha256'),
        rol='admin',
        activo=True
    )
    db.session.add(admin)
    db.session.commit()
    print("✅ Admin creado.")
else:
    print("\n✅ El usuario admin ya existe.")