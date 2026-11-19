from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

import validators as v
from db import DatabaseError, error_message, execute, query

bp = Blueprint("configuracion", __name__, url_prefix="/configuracion")


# 1. LISTAR
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


# --- RUTAS PARA CATEGORÍA (/configuracion/categoria/...) ---

@bp.route("/categoria/", methods=["GET", "POST"])
@bp.route("/categoria/crear", methods=["GET", "POST"])
def categoria_crear():
    if request.method == "POST":
        nombre = request.form.get("nombre_categoria", "").strip()

        if not nombre:
            flash("El nombre de la categoría es obligatorio.", "warning")
            return render_template("configuracion/categoria_form.html", item=request.form)

        try:
            execute(
                "INSERT INTO categorias (nombre_categoria) VALUES (%s)",
                (nombre,),
            )
            flash("Categoría creada correctamente.", "success")
            return redirect(url_for("configuracion.listar"))
        except DatabaseError as e:
            flash(error_message(e), "danger")
            return render_template("configuracion/categoria_form.html", item=request.form)

    return render_template("configuracion/categoria_form.html", item=None)


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
        nombre = request.form.get("nombre_categoria", "").strip()

        if not nombre:
            flash("El nombre de la categoría es obligatorio.", "warning")
            return render_template("configuracion/categoria_form.html", item=item)

        try:
            execute(
                "UPDATE categorias SET nombre_categoria = %s WHERE id_categoria = %s",
                (nombre, id),
            )
            flash("Categoría actualizada correctamente.", "success")
            return redirect(url_for("configuracion.listar"))
        except DatabaseError as e:
            flash(error_message(e), "danger")

    return render_template("configuracion/categoria_form.html", item=item)


@bp.route("/categoria/eliminar/<int:id>", methods=["POST"])
def categoria_eliminar(id):
    try:
        execute("DELETE FROM categorias WHERE id_categoria = %s", (id,))
        flash("Categoría eliminada.", "success")
    except DatabaseError as e:
        flash(error_message(e), "danger")

    return redirect(url_for("configuracion.listar"))


# 2. CREAR
@bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    if request.method == "POST":
        sigla = request.form.get("sigla", "").strip().upper()
        descripcion = request.form.get("descripcion", "").strip()

        if not sigla or not descripcion:
            flash("La sigla y la descripción son obligatorias.", "warning")
            return render_template("configuracion/form.html", item=request.form)

        if len(sigla) > 5:
            flash("La sigla no puede tener más de 5 caracteres.", "warning")
            return render_template("configuracion/form.html", item=request.form)

        if len(descripcion) > 50:
            flash("La descripción no puede tener más de 50 caracteres.", "warning")
            return render_template("configuracion/form.html", item=request.form)

        try:
            execute(
                "INSERT INTO tipo_documento (sigla, descripcion) VALUES (%s, %s)",
                (sigla, descripcion),
            )
            flash("Tipo de documento creado correctamente.", "success")
            return redirect(url_for("configuracion.listar"))
        except DatabaseError as e:
            flash(error_message(e), "danger")
            return render_template("configuracion/form.html", item=request.form)

    return render_template("configuracion/form.html", item=None)


# 3. EDITAR
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
        sigla = request.form.get("sigla", "").strip().upper()
        descripcion = request.form.get("descripcion", "").strip()

        if not sigla or not descripcion:
            flash("La sigla y la descripción son obligatorias.", "warning")
            return render_template("configuracion/form.html", item=item)

        if len(sigla) > 5 or len(descripcion) > 50:
            flash("La sigla (máx. 5) o descripción (máx. 50) excede el límite.", "warning")
            return render_template("configuracion/form.html", item=item)

        try:
            execute(
                "UPDATE tipo_documento SET sigla = %s, descripcion = %s WHERE id_tipo_documento = %s",
                (sigla, descripcion, id),
            )
            flash("Tipo de documento actualizado correctamente.", "success")
            return redirect(url_for("configuracion.listar"))
        except DatabaseError as e:
            flash(error_message(e), "danger")

    return render_template("configuracion/form.html", item=item)


# 4. ELIMINAR
@bp.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    try:
        execute("DELETE FROM tipo_documento WHERE id_tipo_documento = %s", (id,))
        flash("Tipo de documento eliminado.", "success")
    except DatabaseError as e:
        flash(error_message(e), "danger")

    return redirect(url_for("configuracion.listar"))