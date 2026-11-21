"""CRUD de la tabla insumos."""
from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

import validators as v
from db import DatabaseError, error_message, execute, query

bp = Blueprint("insumos", __name__, url_prefix="/insumos")

STOCK_MAX = Decimal("99999999.99")  

UNIDADES = ["kg", "lb", "g", "mL", "L", "und"]

def _leer_formulario(form):
    errores = []
    nombre = v.texto(form, "nombre_insumo", "Nombre del insumo", errores, max_len=100)
    datos = {
        "nombre_insumo": nombre.upper() if nombre else nombre,
        "unidad_medida": v.texto(form, "unidad_medida", "Unidad de medida", errores, max_len=20),
        "stock_actual": v.decimal(form, "stock_actual", "Stock", errores,
                                  minimo=0, maximo=STOCK_MAX),
    }
    if datos["unidad_medida"] and datos["unidad_medida"] not in UNIDADES:
        errores.append("Unidad de medida no válida.")

    return datos, errores

def _render_form(item, titulo):
    return render_template("insumos/form.html", item=item, titulo=titulo,
                           unidades=UNIDADES)


@bp.route("/")
def listar():
    items = query("SELECT * FROM insumos ORDER BY id_insumo")
    bajo = query("""
        SELECT nombre_insumo, unidad_medida, stock_actual
          FROM insumos
         ORDER BY stock_actual ASC, id_insumo
         LIMIT 1
    """, one=True)
    return render_template("insumos/list.html", items=items, bajo=bajo)


@bp.route("/nuevo", methods=["GET", "POST"])
def crear():
    item = {}
    if request.method == "POST":
        item = request.form.to_dict()
        datos, errores = _leer_formulario(request.form)
        if not errores:
            try:
                execute("""INSERT INTO insumos (nombre_insumo, unidad_medida, stock_actual)
                           VALUES (%(nombre_insumo)s, %(unidad_medida)s, %(stock_actual)s)""",
                        datos)
                flash("Insumo creado correctamente.", "success")
                return redirect(url_for(".listar"))
            except DatabaseError as exc:
                errores.append(error_message(exc))
        for e in errores:
            flash(e, "danger")
    return _render_form(item, "Nuevo insumo")


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
def editar(id):
    item = query("SELECT * FROM insumos WHERE id_insumo = %s", (id,), one=True)
    if item is None:
        abort(404)
    if request.method == "POST":
        item = {**item, **request.form.to_dict()}
        datos, errores = _leer_formulario(request.form)
        if not errores:
            try:
                execute("""UPDATE insumos
                              SET nombre_insumo = %(nombre_insumo)s,
                                  unidad_medida = %(unidad_medida)s,
                                  stock_actual  = %(stock_actual)s
                            WHERE id_insumo = %(id)s""",
                        {**datos, "id": id})
                flash("Insumo actualizado correctamente.", "success")
                return redirect(url_for(".listar"))
            except DatabaseError as exc:
                errores.append(error_message(exc))
        for e in errores:
            flash(e, "danger")
    return _render_form(item, "Editar insumo")


@bp.route("/<int:id>/eliminar", methods=["POST"])
def eliminar(id):
    try:
        if execute("DELETE FROM insumos WHERE id_insumo = %s", (id,)):
            flash("Insumo eliminado.", "success")
        else:
            flash("El insumo no existe.", "warning")
    except DatabaseError as exc:
        flash(error_message(exc), "danger")
    return redirect(url_for(".listar"))
