from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

import validators as v
from db import DatabaseError, error_message, execute, query

bp = Blueprint("configuracion", __name__, url_prefix="/configuracion")


def _leer_formulario_categoria(form):
    errores = []
    
    nombre = v.texto(form, "nombre_categoria", "Nombre de la categoría", errores, max_len=100)
    
    datos = {
        "nombre_categoria": nombre.upper() if nombre else nombre
    }
    
    return datos, errores

def _leer_formulario_tipo_doc(form):
    errores = []
    
    sigla = v.texto(form, "sigla", "Sigla", errores, max_len=5)
    descripcion = v.texto(form, "descripcion", "Descripción", errores, max_len=50)
    
    datos = {
        "sigla": sigla.upper() if sigla else sigla,
        "descripcion": descripcion
    }
    
    return datos, errores

def _render_form_categorias(item, titulo):
    return render_template("configuracion/categoria_form.html", item=item, titulo=titulo)

def _render_form_tipo_doc(item, titulo):
    return render_template("configuracion/form.html", item=item, titulo=titulo)  
      
@bp.route("/")
def listar():
    items = query("""
        SELECT td.id_tipo_documento AS id_configuracion,
               td.sigla,
               td.descripcion,
               COUNT(c.id_cliente) AS usado_por
        FROM tipo_documento td
        LEFT JOIN clientes c ON c.id_tipo_documento = td.id_tipo_documento
        GROUP BY td.id_tipo_documento, td.sigla, td.descripcion
        ORDER BY td.sigla
    """)

    categorias = query("""
        SELECT ct.id_categoria,
               ct.nombre_categoria,
               COUNT(p.id_producto) AS num_productos
        FROM categorias ct
        LEFT JOIN productos p ON p.id_categoria = ct.id_categoria
        GROUP BY ct.id_categoria, ct.nombre_categoria
        ORDER BY ct.nombre_categoria
    """)

    return render_template("configuracion/list.html", items=items, categorias=categorias)

@bp.route("/categoria/", methods=["GET", "POST"])
@bp.route("/categoria/crear", methods=["GET", "POST"])
def categoria_crear():
    item = {}
    if request.method == "POST":
        item = request.form.to_dict()
        datos, errores = _leer_formulario_categoria(request.form)

        if not errores:
            try:
                execute(
                    "INSERT INTO categorias (nombre_categoria) VALUES (%(nombre_categoria)s)",
                    datos,
                )
                flash("Categoría creada correctamente.", "success")
                return redirect(url_for("configuracion.listar"))
            except DatabaseError as e:
                errores.append(error_message(e))
                
        for e in errores:
            flash(e, "danger")

    return _render_form_categorias(item, "Nueva categoría")


@bp.route("/categoria/editar/<int:id>", methods=["GET", "POST"])
def categoria_editar(id):
    rows = query(
        "SELECT id_categoria, nombre_categoria FROM categorias WHERE id_categoria = %s",
        (id,),
    )
    if not rows:
        abort(404)
    item = rows[0]

    if request.method == "POST":
        item = {**item, **request.form.to_dict()}
        datos, errores = _leer_formulario_categoria(request.form)

        if not errores:
            try:
                execute(
                    "UPDATE categorias SET nombre_categoria = %(nombre_categoria)s WHERE id_categoria = %(id)s",
                    {**datos, "id": id},
                )
                flash("Categoría actualizada correctamente.", "success")
                return redirect(url_for("configuracion.listar"))
            except DatabaseError as e:
                errores.append(error_message(e))
                
        for e in errores:
            flash(e, "danger")

    return _render_form_categorias(item, "Editar Categoría")


@bp.route("/categoria/eliminar/<int:id>", methods=["POST"])
def categoria_eliminar(id):
    try:
        execute("DELETE FROM categorias WHERE id_categoria = %s", (id,))
        flash("Categoría eliminada.", "success")
    except DatabaseError as e:
        flash(error_message(e), "danger")

    return redirect(url_for("configuracion.listar"))

@bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    item = {}
    if request.method == "POST":
        item = request.form.to_dict()
        datos, errores = _leer_formulario_tipo_doc(request.form)

        if not errores:
            try:
                execute(
                    "INSERT INTO tipo_documento (sigla, descripcion) VALUES (%(sigla)s, %(descripcion)s)",
                    datos,
                )
                flash("Tipo de documento creado correctamente.", "success")
                return redirect(url_for("configuracion.listar"))
            except DatabaseError as e:
                errores.append(error_message(e))
                
        for e in errores:
            flash(e, "danger")

    return _render_form_tipo_doc(item, "Nuevo Tipo de documento")


@bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    rows = query(
        """
        SELECT id_tipo_documento AS id_configuracion, sigla, descripcion
        FROM tipo_documento
        WHERE id_tipo_documento = %s
        """,
        (id,),
    )
    if not rows:
        abort(404)
    item = rows[0]

    if request.method == "POST":
        item = {**item, **request.form.to_dict()}
        datos, errores = _leer_formulario_tipo_doc(request.form)

        if not errores:
            try:
                execute(
                    "UPDATE tipo_documento SET sigla = %(sigla)s, descripcion = %(descripcion)s WHERE id_tipo_documento = %(id)s",
                    {**datos, "id": id},
                )
                flash("Tipo de documento actualizado correctamente.", "success")
                return redirect(url_for("configuracion.listar"))
            except DatabaseError as e:
                errores.append(error_message(e))

        for e in errores:
            flash(e, "danger")

    return _render_form_tipo_doc(item, "Editar Tipo de documento")


@bp.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    try:
        execute("DELETE FROM tipo_documento WHERE id_tipo_documento = %s", (id,))
        flash("Tipo de documento eliminado.", "success")
    except DatabaseError as e:
        flash(error_message(e), "danger")

    return redirect(url_for("configuracion.listar"))