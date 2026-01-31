from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required, current_user, logout_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, Usuario, Paciente, Cita, Especialidad, HistoriaClinica, HistoriaVersion, HistoriaEntrada, Rol
from .forms import (
    LoginForm,
    CambiarPasswordForm,
    UsuarioForm,
    EspecialidadForm,
    CitaForm,
    PacienteForm,
    RolForm
)
from weasyprint import HTML
from datetime import datetime, timedelta

main = Blueprint('main', __name__)


# --- Rutas principales ---
@main.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        
        if usuario and check_password_hash(usuario.password, form.password.data):
            if not usuario.activo:
                flash('Tu cuenta está inactiva. Contacta al administrador.', 'warning')
                return render_template('login.html', form=form)
            
            login_user(usuario)
            
            # Redirigir a cambiar contraseña si es la primera vez
            if not usuario.password_cambiada:
                flash('Por seguridad, debes cambiar tu contraseña', 'info')
                return redirect(url_for('main.cambiar_password'))
            
            flash(f'Bienvenido {usuario.nombre}', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Correo o contraseña incorrectos', 'error')
    
    return render_template('login.html', form=form)


@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('admin/dashboard.html')


@main.route('/perfil')
@login_required
def perfil():
    return render_template('perfil/perfil.html', user=current_user)


@main.route('/perfil/cambiar-password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    require_current = current_user.password_cambiada
    form = CambiarPasswordForm(require_current=require_current)
    
    if form.validate_on_submit():
        if require_current:
            if not check_password_hash(current_user.password, form.password_actual.data):
                flash('La contraseña actual es incorrecta', 'danger')
                return render_template('perfil/cambiar_password.html', form=form, require_current=require_current)
        
        if check_password_hash(current_user.password, form.password_nueva.data):
            flash('La nueva contraseña debe ser diferente a la actual', 'warning')
            return render_template('perfil/cambiar_password.html', form=form, require_current=require_current)
        
        current_user.password = generate_password_hash(form.password_nueva.data)
        current_user.password_cambiada = True
        db.session.commit()
        flash('Contraseña actualizada exitosamente', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('perfil/cambiar_password.html', form=form, require_current=require_current)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    if request.args.get('inactive') == '1':
        flash('Su sesión se ha cerrado por tiempo de inactividad', 'warning')
    else:
        flash('Has cerrado sesión exitosamente', 'info')
    return redirect(url_for('main.index'))

# ============================================
# PACIENTES
# ============================================
@main.route('/pacientes')
@login_required
def lista_pacientes():
    query = request.args.get('q', '').strip()
    if query:
        pacientes = Paciente.query.filter(
            db.or_(
                Paciente.nombre.contains(query),
                Paciente.identificacion.contains(query)
            )
        ).filter_by(activo=True).all()
    else:
        pacientes = Paciente.query.filter_by(activo=True).all()
    return render_template('paciente/pacientes.html', pacientes=pacientes, query=query)


@main.route('/paciente/nuevo', methods=['GET', 'POST'])
@login_required
def crear_paciente():
    form = PacienteForm()
    if form.validate_on_submit():
        paciente = Paciente(
            nombre=form.nombre.data,
            identificacion=form.identificacion.data,
            sexo=form.sexo.data,
            fecha_nacimiento=form.fecha_nacimiento.data,
            telefono=form.telefono.data,
            email=form.email.data,
            direccion=form.direccion.data,
            activo=True
        )
        db.session.add(paciente)
        db.session.commit()
        flash('Paciente creado exitosamente', 'success')
        return redirect(url_for('main.lista_pacientes'))
    return render_template('paciente/crear.html', form=form)


@main.route('/paciente/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_paciente(id):
    paciente = Paciente.query.get_or_404(id)
    form = PacienteForm(obj=paciente)
    if form.validate_on_submit():
        paciente.nombre = form.nombre.data
        paciente.identificacion = form.identificacion.data
        paciente.sexo = form.sexo.data
        paciente.fecha_nacimiento = form.fecha_nacimiento.data
        paciente.telefono = form.telefono.data
        paciente.email = form.email.data
        paciente.direccion = form.direccion.data
        db.session.commit()
        flash('Paciente actualizado exitosamente', 'success')
        return redirect(url_for('main.lista_pacientes'))
    return render_template('paciente/editar.html', form=form, paciente=paciente)


@main.route('/paciente/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_paciente(id):
    paciente = Paciente.query.get_or_404(id)
    paciente.activo = False
    db.session.commit()
    flash('Paciente eliminado', 'info')
    return redirect(url_for('main.lista_pacientes'))

# ============================================
# USUARIOS (ADMIN)
# ============================================
@main.route('/usuarios', methods=['GET', 'POST'])
@login_required
def lista_usuarios():
    if current_user.rol is None or current_user.rol.nombre != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.dashboard'))

    form = UsuarioForm()
    form.rol_id.choices = [(r.id, r.nombre) for r in Rol.query.all()]

    if form.validate_on_submit():
        if Usuario.query.filter_by(email=form.email.data).first():
            flash('El correo ya está registrado', 'warning')
        else:
            user = Usuario(
                nombre=form.nombre.data,
                email=form.email.data,
                password=generate_password_hash('123456'),
                rol_id=form.rol_id.data,
                activo=True,
                password_cambiada=False
            )
            db.session.add(user)
            db.session.commit()
            flash('Usuario creado. Contraseña temporal: 123456', 'info')
            return redirect(url_for('main.lista_usuarios'))

    # Filter users safely, excluding those with None rol or admin rol
    usuarios = Usuario.query.join(Rol).filter(Rol.nombre != 'admin').all()
    return render_template('admin/usuarios.html', usuarios=usuarios, form=form)


@main.route('/usuario/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    if current_user.rol is None or current_user.rol.nombre != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.dashboard'))

    usuario = Usuario.query.get_or_404(id)
    form = UsuarioForm(obj=usuario)
    form.rol_id.choices = [(r.id, r.nombre) for r in Rol.query.all()]

    if form.validate_on_submit():
        # Verificar si el email ya existe en otro usuario
        existing = Usuario.query.filter_by(email=form.email.data).first()
        if existing and existing.id != usuario.id:
            flash('El correo ya está registrado en otro usuario', 'warning')
        else:
            usuario.nombre = form.nombre.data
            usuario.email = form.email.data
            usuario.rol_id = form.rol_id.data
            db.session.commit()
            flash('Usuario actualizado exitosamente', 'success')
            return redirect(url_for('main.lista_usuarios'))

    return render_template('admin/editar_usuario.html', form=form, usuario=usuario)


@main.route('/usuario/<int:id>/toggle-activo', methods=['POST'])
@login_required
def toggle_usuario_activo(id):
    if current_user.rol is None or current_user.rol.nombre != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.dashboard'))
    usuario = Usuario.query.get_or_404(id)
    usuario.activo = not usuario.activo
    db.session.commit()
    flash(f'Usuario {"activado" if usuario.activo else "inactivado"}', 'info')
    return redirect(url_for('main.lista_usuarios'))


@main.route('/usuario/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_usuario(id):
    if current_user.rol is None or current_user.rol.nombre != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.dashboard'))
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuario eliminado permanentemente', 'info')
    return redirect(url_for('main.lista_usuarios'))


@main.route('/usuario/<int:id>/resetear-password', methods=['POST'])
@login_required
def resetear_password_usuario(id):
    if current_user.rol is None or current_user.rol.nombre != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.dashboard'))

    usuario = Usuario.query.get_or_404(id)
    usuario.password = generate_password_hash('123456')
    usuario.password_cambiada = False
    db.session.commit()
    flash(f'Contraseña de {usuario.nombre} restablecida a: 123456', 'info')
    return redirect(url_for('main.lista_usuarios'))


# ============================================
# ESPECIALIDADES (ADMIN)
# ============================================
@main.route('/especialidades', methods=['GET', 'POST'])
@login_required
def lista_especialidades():
    if current_user.rol is None or current_user.rol.nombre != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.dashboard'))

    form = EspecialidadForm()
    if form.validate_on_submit():
        if Especialidad.query.filter_by(nombre=form.nombre.data).first():
            flash('La especialidad ya existe', 'warning')
        else:
            esp = Especialidad(nombre=form.nombre.data)
            db.session.add(esp)
            db.session.commit()
            flash('Especialidad creada', 'success')
            return redirect(url_for('main.lista_especialidades'))

    especialidades = Especialidad.query.all()
    return render_template('admin/especialidades.html', especialidades=especialidades, form=form)


@main.route('/especialidad/<int:id>/editar', methods=['POST'])
@login_required
def editar_especialidad(id):
    if current_user.rol is None or current_user.rol.nombre != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.dashboard'))

    especialidad = Especialidad.query.get_or_404(id)
    nombre_nuevo = request.form.get('nombre', '').strip()

    if not nombre_nuevo:
        flash('El nombre de la especialidad es requerido', 'danger')
        return redirect(url_for('main.lista_especialidades'))

    # Verificar si el nuevo nombre ya existe en otra especialidad
    existe = Especialidad.query.filter(
        Especialidad.nombre == nombre_nuevo,
        Especialidad.id != id
    ).first()

    if existe:
        flash('Ya existe una especialidad con ese nombre', 'warning')
        return redirect(url_for('main.lista_especialidades'))

    especialidad.nombre = nombre_nuevo
    db.session.commit()
    flash(f'Especialidad actualizada a: {nombre_nuevo}', 'success')
    return redirect(url_for('main.lista_especialidades'))


@main.route('/especialidad/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_especialidad(id):
    if current_user.rol is None or current_user.rol.nombre != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.dashboard'))

    especialidad = Especialidad.query.get_or_404(id)

    # Verificar si tiene citas asociadas
    if especialidad.citas:
        flash(f'No se puede eliminar: La especialidad "{especialidad.nombre}" tiene {len(especialidad.citas)} cita(s) asociada(s)', 'danger')
        return redirect(url_for('main.lista_especialidades'))

    nombre = especialidad.nombre
    db.session.delete(especialidad)
    db.session.commit()
    flash(f'Especialidad "{nombre}" eliminada exitosamente', 'info')
    return redirect(url_for('main.lista_especialidades'))


# ============================================
# ROLES (ADMIN)
# ============================================
@main.route('/roles', methods=['GET', 'POST'])
@login_required
def lista_roles():
    if current_user.rol is None or current_user.rol.nombre != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.dashboard'))

    form = RolForm()
    if form.validate_on_submit():
        if Rol.query.filter_by(nombre=form.nombre.data).first():
            flash('El rol ya existe', 'warning')
        else:
            rol = Rol(nombre=form.nombre.data, descripcion=form.descripcion.data)
            db.session.add(rol)
            db.session.commit()
            flash('Rol creado exitosamente', 'success')
            return redirect(url_for('main.lista_roles'))

    roles = Rol.query.all()
    return render_template('admin/roles.html', roles=roles, form=form)


@main.route('/rol/<int:id>/editar', methods=['POST'])
@login_required
def editar_rol(id):
    if current_user.rol is None or current_user.rol.nombre != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.dashboard'))

    rol = Rol.query.get_or_404(id)
    nombre_nuevo = request.form.get('nombre', '').strip()
    descripcion_nueva = request.form.get('descripcion', '').strip()

    if not nombre_nuevo:
        flash('El nombre del rol es requerido', 'danger')
        return redirect(url_for('main.lista_roles'))

    # Verificar si el nuevo nombre ya existe en otro rol
    existe = Rol.query.filter(
        Rol.nombre == nombre_nuevo,
        Rol.id != id
    ).first()

    if existe:
        flash('Ya existe un rol con ese nombre', 'warning')
        return redirect(url_for('main.lista_roles'))

    rol.nombre = nombre_nuevo
    rol.descripcion = descripcion_nueva
    db.session.commit()
    flash(f'Rol actualizado a: {nombre_nuevo}', 'success')
    return redirect(url_for('main.lista_roles'))


@main.route('/rol/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_rol(id):
    if current_user.rol is None or current_user.rol.nombre != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.dashboard'))

    rol = Rol.query.get_or_404(id)

    # Verificar si tiene usuarios asociados
    if rol.usuarios:
        flash(f'No se puede eliminar: El rol "{rol.nombre}" tiene {len(rol.usuarios)} usuario(s) asociado(s)', 'danger')
        return redirect(url_for('main.lista_roles'))

    nombre = rol.nombre
    db.session.delete(rol)
    db.session.commit()
    flash(f'Rol "{nombre}" eliminado exitosamente', 'info')
    return redirect(url_for('main.lista_roles'))


# ============================================
# CITAS
# ============================================
@main.route('/citas')
@login_required
def lista_citas():
    query = request.args.get('q', '').strip()
    if query:
        citas = Cita.query.join(Paciente).join(Usuario, Cita.medico_id == Usuario.id).join(Especialidad).filter(
            db.or_(
                Paciente.nombre.contains(query),
                Paciente.identificacion.contains(query),
                Usuario.nombre.contains(query),
                Especialidad.nombre.contains(query)
            )
        ).order_by(Cita.fecha.desc()).all()
    else:
        citas = Cita.query.order_by(Cita.fecha.desc()).all()
    return render_template('cita/citas.html', citas=citas)


@main.route('/cita/nueva', methods=['GET', 'POST'])
@login_required
def crear_cita():
    form = CitaForm()
    form.paciente_id.choices = [(p.id, f"{p.nombre} ({p.identificacion})") for p in Paciente.query.filter_by(activo=True).all()]
    form.medico_id.choices = [(u.id, u.nombre) for u in Usuario.query.join(Rol).filter(Rol.nombre == 'medico', Usuario.activo == True).all()]
    form.especialidad_id.choices = [(e.id, e.nombre) for e in Especialidad.query.all()]

    if form.validate_on_submit():
        cita = Cita(
            paciente_id=form.paciente_id.data,
            medico_id=form.medico_id.data,
            especialidad_id=form.especialidad_id.data,
            fecha=form.fecha.data,
            estado='Pendiente'
        )
        db.session.add(cita)
        db.session.commit()
        flash('Cita agendada exitosamente', 'success')
        return redirect(url_for('main.lista_citas'))
    return render_template('cita/crear.html', form=form)


@main.route('/cita/<int:id>/realizada')
@login_required
def marcar_cita_realizada(id):
    cita = Cita.query.get_or_404(id)
    cita.estado = 'Realizada'
    db.session.commit()
    flash('Cita marcada como realizada', 'success')
    return redirect(url_for('main.lista_citas'))


@main.route('/cita/<int:id>/eliminar')
@login_required
def eliminar_cita(id):
    cita = Cita.query.get_or_404(id)
    db.session.delete(cita)
    db.session.commit()
    flash('Cita eliminada', 'info')
    return redirect(url_for('main.lista_citas'))


@main.route('/cita/<int:id>/tiquete')
@login_required
def tiquete_cita(id):
    cita = Cita.query.get_or_404(id)
    return render_template('cita/tiquete.html', cita=cita)


# ============================================
# REPORTES
# ============================================
@main.route('/reporte/pacientes.pdf')
@login_required
def reporte_pacientes_pdf():
    pacientes = Paciente.query.all()
    fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    html = render_template(
        'reporte/pacientes_pdf.html',
        pacientes=pacientes,
        fecha_generacion=fecha_generacion
    )
    
    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=reporte_pacientes.pdf'
    return response


@main.route('/reporte/citas.pdf')
@login_required
def reporte_citas_pdf():
    citas = Cita.query.order_by(Cita.fecha.desc()).all()
    fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    html = render_template(
        'reporte/citas_pdf.html',
        citas=citas,
        fecha_generacion=fecha_generacion
    )
    
    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=reporte_citas.pdf'
    return response


@main.route('/reporte/especialidades.pdf')
@login_required
def reporte_especialidades_pdf():
    if current_user.rol is None or current_user.rol.nombre != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.dashboard'))

    especialidades = Especialidad.query.all()
    fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    html = render_template(
        'reporte/especialidades_pdf.html',
        especialidades=especialidades,
        fecha_generacion=fecha_generacion
    )

    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=reporte_especialidades.pdf'
    return response


@main.route('/reportes')
@login_required
def menu_reportes():
    """Vista principal del menú de reportes"""
    # Obtener estadísticas para mostrar en el dashboard
    stats = {
        'total_pacientes': Paciente.query.filter_by(activo=True).count(),
        'total_citas': Cita.query.count(),
        'total_especialidades': Especialidad.query.count(),
        'citas_pendientes': Cita.query.filter_by(estado='Pendiente').count()
    }
    return render_template('reporte/menu_reportes.html', stats=stats)


# ============================================
# HISTORIAS CLÍNICAS
# ============================================

@main.route('/paciente/<int:id>/historia', methods=['GET', 'POST'])
@login_required
def historia_clinica(id):
    paciente = Paciente.query.get_or_404(id)

    # Obtener o crear historia clínica
    historia = HistoriaClinica.query.filter_by(paciente_id=id).first()
    if not historia:
        historia = HistoriaClinica(paciente_id=id)
        db.session.add(historia)
        db.session.commit()

    if request.method == 'POST':
        contenido_nuevo = request.form.get('contenido', '').strip()

        if not contenido_nuevo:
            flash('El contenido no puede estar vacío', 'danger')
            return redirect(url_for('main.historia_clinica', id=id))

        # Crear nueva entrada
        entrada = HistoriaEntrada(
            historia_id=historia.id,
            autor_id=current_user.id,
            contenido=contenido_nuevo
        )
        db.session.add(entrada)
        db.session.commit()

        flash('Entrada agregada a la historia clínica exitosamente', 'success')
        return redirect(url_for('main.historia_clinica', id=id))

    # Obtener entradas ordenadas por fecha descendente
    entradas = HistoriaEntrada.query.filter_by(historia_id=historia.id).order_by(HistoriaEntrada.fecha.desc()).all()

    return render_template(
        'historia/historia_clinica.html',
        paciente=paciente,
        historia=historia,
        entradas=entradas
    )


@main.route('/paciente/<int:id>/historia/entrada/<int:entrada_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_entrada_historia(id, entrada_id):
    paciente = Paciente.query.get_or_404(id)
    entrada = HistoriaEntrada.query.get_or_404(entrada_id)

    # Verificar que la entrada pertenece a este paciente
    if entrada.historia.paciente_id != id:
        flash('Entrada no encontrada', 'danger')
        return redirect(url_for('main.historia_clinica', id=id))

    # Solo el autor puede editar
    if entrada.autor_id != current_user.id:
        flash('Solo el autor de la entrada puede editarla', 'danger')
        return redirect(url_for('main.historia_clinica', id=id))

    if request.method == 'POST':
        contenido_nuevo = request.form.get('contenido', '').strip()

        if not contenido_nuevo:
            flash('El contenido no puede estar vacío', 'danger')
            return render_template('historia/editar_entrada.html', paciente=paciente, entrada=entrada)

        entrada.contenido = contenido_nuevo
        db.session.commit()

        flash('Entrada actualizada exitosamente', 'success')
        return redirect(url_for('main.historia_clinica', id=id))

    return render_template('historia/editar_entrada.html', paciente=paciente, entrada=entrada)


@main.route('/paciente/<int:id>/historia/entrada/<int:entrada_id>/eliminar', methods=['POST'])
@login_required
def eliminar_entrada_historia(id, entrada_id):
    paciente = Paciente.query.get_or_404(id)
    entrada = HistoriaEntrada.query.get_or_404(entrada_id)

    # Verificar que la entrada pertenece a este paciente
    if entrada.historia.paciente_id != id:
        flash('Entrada no encontrada', 'danger')
        return redirect(url_for('main.historia_clinica', id=id))

    # Solo el autor puede eliminar
    if entrada.autor_id != current_user.id:
        flash('Solo el autor de la entrada puede eliminarla', 'danger')
        return redirect(url_for('main.historia_clinica', id=id))

    # Eliminar la entrada
    db.session.delete(entrada)
    db.session.commit()

    flash('Entrada eliminada exitosamente', 'success')
    return redirect(url_for('main.historia_clinica', id=id))


@main.route('/paciente/<int:id>/historia/imprimir')
@login_required
def imprimir_historia(id):
    """Genera PDF para ver en el navegador"""
    paciente = Paciente.query.get_or_404(id)
    historia = HistoriaClinica.query.filter_by(paciente_id=id).first()

    if not historia:
        historia = HistoriaClinica(paciente_id=id)
        entradas = []
    else:
        # Verificar si solo recientes
        solo_recientes = request.args.get('solo_recientes', '0') == '1'
        if solo_recientes:
            # Entradas de los últimos 30 días
            fecha_limite = datetime.now() - timedelta(days=30)
            entradas = HistoriaEntrada.query.filter(
                HistoriaEntrada.historia_id == historia.id,
                HistoriaEntrada.fecha >= fecha_limite
            ).order_by(HistoriaEntrada.fecha.desc()).all()
        else:
            entradas = HistoriaEntrada.query.filter_by(historia_id=historia.id).order_by(HistoriaEntrada.fecha.desc()).all()

    # Calcular edad si existe fecha de nacimiento
    edad = None
    if paciente.fecha_nacimiento:
        today = datetime.now().date()
        edad = today.year - paciente.fecha_nacimiento.year
        if today.month < paciente.fecha_nacimiento.month or \
           (today.month == paciente.fecha_nacimiento.month and today.day < paciente.fecha_nacimiento.day):
            edad -= 1

    fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    html = render_template(
        'historia/historia_clinica_pdf.html',
        paciente=paciente,
        historia=historia,
        entradas=entradas,
        fecha_generacion=fecha_generacion,
        edad=edad,
        solo_recientes=solo_recientes
    )

    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=historia_clinica_{paciente.identificacion}.pdf'
    return response


@main.route('/paciente/<int:id>/historia/descargar')
@login_required
def descargar_historia(id):
    """Genera PDF para descargar"""
    paciente = Paciente.query.get_or_404(id)
    historia = HistoriaClinica.query.filter_by(paciente_id=id).first()

    if not historia:
        historia = HistoriaClinica(paciente_id=id)
        entradas = []
    else:
        # Verificar si solo recientes
        solo_recientes = request.args.get('solo_recientes', '0') == '1'
        if solo_recientes:
            # Entradas de los últimos 30 días
            fecha_limite = datetime.now() - timedelta(days=30)
            entradas = HistoriaEntrada.query.filter(
                HistoriaEntrada.historia_id == historia.id,
                HistoriaEntrada.fecha >= fecha_limite
            ).order_by(HistoriaEntrada.fecha.desc()).all()
        else:
            entradas = HistoriaEntrada.query.filter_by(historia_id=historia.id).order_by(HistoriaEntrada.fecha.desc()).all()

    # Calcular edad
    edad = None
    if paciente.fecha_nacimiento:
        today = datetime.now().date()
        edad = today.year - paciente.fecha_nacimiento.year
        if today.month < paciente.fecha_nacimiento.month or \
           (today.month == paciente.fecha_nacimiento.month and today.day < paciente.fecha_nacimiento.day):
            edad -= 1

    fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    html = render_template(
        'historia/historia_clinica_pdf.html',
        paciente=paciente,
        historia=historia,
        entradas=entradas,
        fecha_generacion=fecha_generacion,
        edad=edad,
        solo_recientes=solo_recientes
    )

    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=historia_clinica_{paciente.nombre.replace(" ", "_")}_{paciente.identificacion}.pdf'
    return response


@main.route('/paciente/<int:id>/historia/version/<int:version_id>')
@login_required
def ver_version_historia(id, version_id):
    """Ver una versión específica de la historia"""
    paciente = Paciente.query.get_or_404(id)
    version = HistoriaVersion.query.get_or_404(version_id)
    
    # Verificar que la versión pertenece a este paciente
    if version.historia.paciente_id != id:
        flash('Versión no encontrada', 'danger')
        return redirect(url_for('main.historia_clinica', id=id))
    
    return render_template(
        'historia/ver_version.html',
        paciente=paciente,
        version=version
    )