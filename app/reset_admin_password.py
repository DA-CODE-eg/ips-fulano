# reset_admin_password.py
from app import create_app, db
from app.models import Usuario
from werkzeug.security import generate_password_hash

app = create_app()
app.app_context().push()

admin = Usuario.query.filter_by(email='admin@ipsfulano.com').first()

if admin:
    admin.password = generate_password_hash('admin123', method='pbkdf2:sha256')
    db.session.commit()
    print("✅ Contraseña del admin restablecida a 'admin123'")
else:
    print("❌ No se encontró el usuario admin. Ejecuta init_db.py primero.")
