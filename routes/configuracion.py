"""Configuración: catálogos tipo_documento y categorias (agregar y editar en el mismo panel)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

import validators as v
from db import DatabaseError, error_message, execute, query

bp = Blueprint("configuracion", __name__, url_prefix="/configuracion")


def _mostrar_errores(errores):
    for e in errores:
        flash(e, "danger")


# ======================================================================
# PÁGINA PRINCIPAL
# ======================================================================
@bp.route("/")
def index():
    # Tipos de documento + cuántos clientes y vendedores los usan
    tipos = query("""
        SELECT td.*,
               (SELECT COUNT(*) FROM clientes c   WHERE c.id_tipo_documento = td.id_tipo_documento)
             + (SELECT COUNT(*) FROM vendedores v WHERE v.id_tipo_documento = td.id_tipo_documento)
               AS en_uso
          FROM tipo_documento td
         ORDER BY td.id_tipo_documento
    """)

    # Categorías + cuántos productos tiene cada una
    categorias = query("""
        SELECT ca.*, COUNT(p.id_producto) AS num_productos
          FROM categorias ca
          LEFT JOIN productos p ON p.id_categoria = ca.id_categoria
         GROUP BY ca.id_categoria
         ORDER BY ca.id_categoria
    """)

    # ¿Hay algún registro en modo edición? (?editar_tipo=3 / ?editar_categoria=2)
    tipo_editar = None
    id_tipo = request.args.get("editar_tipo", type=int)
    if id_tipo:
        tipo_editar = query("SELECT * FROM tipo_documento WHERE id_tipo_documento = %s",
                            (id_tipo,), one=True)

    categoria_editar = None
    id_cat = request.args.get("editar_categoria", type=int)
    if id_cat:
        categoria_editar = query("SELECT * FROM categorias WHERE id_categoria = %s",
                                 (id_cat,), one=True)

    return render_template("configuracion/index.html",
                           tipos=tipos, categorias=categorias,
                           tipo_editar=tipo_editar, categoria_editar=categoria_editar)


# ======================================================================
# TIPOS DE DOCUMENTO
# ======================================================================
def _leer_tipo(form):
    errores = []
    datos = {
        "sigla": v.texto(form, "sigla", "Sigla", errores, max_len=5),
        "descripcion": v.texto(form, "descripcion", "Descripción", errores, max_len=50),
    }
    return datos, errores


@bp.route("/tipos/nuevo", methods=["POST"])
def tipo_crear():
    datos, errores = _leer_tipo(request.form)
    if not errores:
        try:
            execute("""INSERT INTO tipo_documento (sigla, descripcion)
                       VALUES (%(sigla)s, %(descripcion)s)""", datos)
            flash("Tipo de documento creado.", "success")
        except DatabaseError as exc:
            errores.append(error_message(exc))
    _mostrar_errores(errores)
    return redirect(url_for(".index", _anchor="tipos"))


@bp.route("/tipos/<int:id>/editar", methods=["POST"])
def tipo_actualizar(id):
    datos, errores = _leer_tipo(request.form)
    if not errores:
        try:
            if execute("""UPDATE tipo_documento
                             SET sigla = %(sigla)s, descripcion = %(descripcion)s
                           WHERE id_tipo_documento = %(id)s""",
                       {**datos, "id": id}):
                flash("Tipo de documento actualizado.", "success")
            else:
                flash("El tipo de documento no existe.", "warning")
            return redirect(url_for(".index", _anchor="tipos"))   # sale del modo edición
        except DatabaseError as exc:
            errores.append(error_message(exc))
    _mostrar_errores(errores)
    # Hubo errores: se queda en modo edición
    return redirect(url_for(".index", editar_tipo=id, _anchor="tipos"))


@bp.route("/tipos/<int:id>/eliminar", methods=["POST"])
def tipo_eliminar(id):
    try:
        if execute("DELETE FROM tipo_documento WHERE id_tipo_documento = %s", (id,)):
            flash("Tipo de documento eliminado.", "success")
        else:
            flash("El tipo de documento no existe.", "warning")
    except DatabaseError as exc:
        flash(error_message(exc), "danger")
    return redirect(url_for(".index", _anchor="tipos"))


# ======================================================================
# CATEGORÍAS
# ======================================================================
def _leer_categoria(form):
    errores = []
    datos = {
        "nombre_categoria": v.texto(form, "nombre_categoria", "Categoría", errores, max_len=50),
    }
    return datos, errores


@bp.route("/categorias/nueva", methods=["POST"])
def categoria_crear():
    datos, errores = _leer_categoria(request.form)
    if not errores:
        try:
            execute("""INSERT INTO categorias (nombre_categoria)
                       VALUES (%(nombre_categoria)s)""", datos)
            flash("Categoría creada.", "success")
        except DatabaseError as exc:
            errores.append(error_message(exc))
    _mostrar_errores(errores)
    return redirect(url_for(".index", _anchor="categorias"))


@bp.route("/categorias/<int:id>/editar", methods=["POST"])
def categoria_actualizar(id):
    datos, errores = _leer_categoria(request.form)
    if not errores:
        try:
            if execute("""UPDATE categorias
                             SET nombre_categoria = %(nombre_categoria)s
                           WHERE id_categoria = %(id)s""",
                       {**datos, "id": id}):
                flash("Categoría actualizada.", "success")
            else:
                flash("La categoría no existe.", "warning")
            return redirect(url_for(".index", _anchor="categorias"))
        except DatabaseError as exc:
            errores.append(error_message(exc))
    _mostrar_errores(errores)
    return redirect(url_for(".index", editar_categoria=id, _anchor="categorias"))


@bp.route("/categorias/<int:id>/eliminar", methods=["POST"])
def categoria_eliminar(id):
    try:
        if execute("DELETE FROM categorias WHERE id_categoria = %s", (id,)):
            flash("Categoría eliminada.", "success")
        else:
            flash("La categoría no existe.", "warning")
    except DatabaseError as exc:
        flash(error_message(exc), "danger")
    return redirect(url_for(".index", _anchor="categorias"))
