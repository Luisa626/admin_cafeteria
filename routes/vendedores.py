from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

import validators as v
from db import DatabaseError, error_message, execute, query

bp = Blueprint("vendedores", __name__, url_prefix="/vendedores")

INT_MAX = 2147483647  # límite de un INTEGER en PostgreSQL

def _leer_formulario(form):
    errores = []
    datos = {
        "id_tipo_documento": v.entero(form, "id_tipo_documento", "Tipo de documento", errores, minimo=1),
        "documento": v.texto(form, "documento", "Documento", errores, max_len=20),
        "nombre_vendedor": v.texto(form, "nombre_vendedor", "Nombre", errores, max_len=100),
        "apellido_vendedor": v.texto(form, "apellido_vendedor", "Apellido", errores, max_len=100),
        "telefono": v.texto(form, "telefono", "Teléfono", errores, max_len=15),
        "email": v.texto(form, "email", "Email", errores, max_len=100),
    }
    return datos, errores

def _tipo_documento():
    return query("SELECT id_tipo_documento, sigla FROM tipo_documento ORDER BY sigla")

def _render_form(item, titulo):
    return render_template("vendedores/form.html", item=item, titulo=titulo,
                           tipo_documento=_tipo_documento())

@bp.route("/")
def listar():
    items = query("""
        SELECT 
            v.id_vendedor,
            CONCAT(v.nombre_vendedor, ' ', v.apellido_vendedor) AS vendedor,
            CONCAT(td.sigla, ' ', v.documento) AS documento_completo,
            v.telefono,
            v.email AS correo,
            COALESCE(SUM(dp.cantidad * dp.precio_unitario), 0) AS total_vendido
        FROM vendedores v
        JOIN tipo_documento td 
            ON v.id_tipo_documento = td.id_tipo_documento
        LEFT JOIN pedidos p 
            ON v.id_vendedor = p.id_vendedor
        LEFT JOIN detalle_pedidos dp 
            ON p.id_pedido = dp.id_pedido
        GROUP BY 
            v.id_vendedor, 
            v.nombre_vendedor, 
            v.apellido_vendedor, 
            td.sigla, 
            v.documento, 
            v.telefono, 
            v.email
        ORDER BY v.nombre_vendedor;
    """)
    pedidos_hoy = query("""
            SELECT COUNT(*) AS pedidos_hoy
            FROM pedidos
            WHERE fecha_compra >= CURRENT_DATE
            AND fecha_compra <  CURRENT_DATE + 1
    """, one=True)
    pedidos_atendidos = query("""
            SELECT CONCAT(v.nombre_vendedor, ' ', v.apellido_vendedor) AS vendedor_top
            FROM vendedores v
            JOIN pedidos p ON v.id_vendedor = p.id_vendedor
            WHERE p.fecha_compra >= CURRENT_DATE
            AND p.fecha_compra <  CURRENT_DATE + 1
            GROUP BY v.id_vendedor, v.nombre_vendedor, v.apellido_vendedor
            ORDER BY COUNT(p.id_pedido) DESC
            LIMIT 1;
    """, one=True)

    return render_template("vendedores/list.html", items=items, pedidos_hoy=pedidos_hoy, pedidos_atendidos=pedidos_atendidos)

@bp.route("/nuevo", methods=["GET", "POST"])
def crear():
    item = {}
    if request.method == "POST":
        item = request.form.to_dict()
        datos, errores = _leer_formulario(request.form)
        if not errores:
            try:
                execute("""INSERT INTO vendedores (id_tipo_documento, nombre_vendedor, apellido_vendedor, telefono, email)
                           VALUES (%(id_tipo_documento)s, %(nombre_vendedor)s, %(apellido_vendedor)s, %(telefono)s, %(email)s)""",
                        datos)
                flash("Vendedor creado correctamente.", "success")
                return redirect(url_for(".listar"))
            except DatabaseError as exc:
                errores.append(error_message(exc))
        for e in errores:
            flash(e, "danger")
    return _render_form(item, "Nuevo vendedor")

@bp.route("/<int:id>/editar", methods=["GET", "POST"])
def editar(id):
    item = query("SELECT * FROM vendedores WHERE id_vendedor = %s", (id,), one=True)
    if item is None:
        abort(404)
    if request.method == "POST":
        item = {**item, **request.form.to_dict()}
        datos, errores = _leer_formulario(request.form)
        if not errores:
            try:
                execute("""UPDATE vendedores
                              SET id_tipo_documento = %(id_tipo_documento)s,
                                  documento = %(documento)s,
                                  nombre_vendedor = %(nombre_vendedor)s,
                                  apellido_vendedor = %(apellido_vendedor)s,
                                  telefono = %(telefono)s,
                                  email = %(email)s
                            WHERE id_vendedor = %(id)s""",
                        {**datos, "id": id})
                flash("Vendedor actualizado correctamente.", "success")
                return redirect(url_for(".listar"))
            except DatabaseError as exc:
                errores.append(error_message(exc))
        for e in errores:
            flash(e, "danger")
    return _render_form(item, "Editar vendedor")

@bp.route("/<int:id>/eliminar", methods=["POST"])
def eliminar(id):
    try:
        if execute("DELETE FROM vendedores WHERE id_vendedor = %s", (id,)):
            flash("Vendedor eliminado.", "success")
        else:
            flash("El vendedor no existe.", "warning")
    except DatabaseError as exc:
        flash(error_message(exc), "danger")
    return redirect(url_for(".listar"))