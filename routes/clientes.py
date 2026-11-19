"""CRUD de la tabla clientes."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

import validators as v
from db import DatabaseError, error_message, execute, query


bp = Blueprint("clientes", __name__, url_prefix="/clientes")

INT_MAX = 2147483647  


def _tipos_documento():
    return query("""SELECT id_tipo_documento, sigla, descripcion
                      FROM tipo_documento
                     ORDER BY id_tipo_documento""")

def _leer_formulario(form, tipos):
    errores = []
    datos = {
        "id_tipo_documento": v.entero(form, "id_tipo_documento", "Tipo de documento",
                                      errores, minimo=1),
        "documento": v.entero(form, "documento", "Documento",
                              errores, minimo=1, maximo=INT_MAX),
        "nombre_cliente": v.texto(form, "nombre_cliente", "Nombre", errores, max_len=50),
        "apellido_cliente": v.texto(form, "apellido_cliente", "Apellido", errores, max_len=50),
        "telefono": v.texto(form, "telefono", "Teléfono", errores,
                            obligatorio=False, max_len=15),
        "email": v.email(form, "email", "Email", errores),
    }

    ids_validos = {t["id_tipo_documento"] for t in tipos}
    if datos["id_tipo_documento"] is not None and datos["id_tipo_documento"] not in ids_validos:
        errores.append("Tipo de documento no válido.")
    return datos, errores

def _render_form(item, titulo, tipos):
    return render_template("clientes/form.html", item=item, titulo=titulo,
                           tipos_documento=tipos)


@bp.route("/")
def listar():
    items = query("""
        SELECT cl.*, td.sigla, COUNT(p.id_pedido) AS num_pedidos
          FROM clientes cl
          JOIN tipo_documento td ON td.id_tipo_documento = cl.id_tipo_documento
          LEFT JOIN pedidos p ON p.id_cliente = cl.id_cliente
         GROUP BY cl.id_cliente, td.sigla
         ORDER BY cl.id_cliente
    """)

    stats = query("""
        SELECT (SELECT COUNT(*) FROM clientes
                 WHERE date_trunc('month', fecha_registro)
                     = date_trunc('month', CURRENT_DATE)) AS nuevos_mes,
               (SELECT cl.nombre_cliente || ' ' || cl.apellido_cliente
                  FROM pedidos p
                  JOIN clientes cl ON cl.id_cliente = p.id_cliente
                 GROUP BY cl.id_cliente
                 ORDER BY COUNT(*) DESC, cl.id_cliente
                 LIMIT 1) AS cliente_frecuente
    """, one=True)

    return render_template("clientes/list.html", items=items, sc=stats)


@bp.route("/nuevo", methods=["GET", "POST"])
def crear():
    item = {}
    tipos = _tipos_documento()
    if request.method == "POST":
        item = request.form.to_dict()
        datos, errores = _leer_formulario(request.form, tipos)
        if not errores:
            try:
                execute("""INSERT INTO clientes
                               (id_tipo_documento, documento, nombre_cliente,
                                apellido_cliente, telefono, email, fecha_registro)
                           VALUES (%(id_tipo_documento)s, %(documento)s, %(nombre_cliente)s,
                                   %(apellido_cliente)s, %(telefono)s, %(email)s, NOW())""",
                        datos)
                flash("Cliente creado correctamente.", "success")
                return redirect(url_for(".listar"))
            except DatabaseError as exc:
                errores.append(error_message(exc))
        for e in errores:
            flash(e, "danger")
    return _render_form(item, "Nuevo cliente", tipos)


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
def editar(id):
    item = query("SELECT * FROM clientes WHERE id_cliente = %s", (id,), one=True)
    if item is None:
        abort(404)
    tipos = _tipos_documento()
    if request.method == "POST":
        item = {**item, **request.form.to_dict()}
        datos, errores = _leer_formulario(request.form, tipos)
        if not errores:
            try:
                execute("""UPDATE clientes
                              SET id_tipo_documento = %(id_tipo_documento)s,
                                  documento         = %(documento)s,
                                  nombre_cliente    = %(nombre_cliente)s,
                                  apellido_cliente  = %(apellido_cliente)s,
                                  telefono          = %(telefono)s,
                                  email             = %(email)s
                            WHERE id_cliente = %(id)s""",
                        {**datos, "id": id})
                flash("Cliente actualizado correctamente.", "success")
                return redirect(url_for(".listar"))
            except DatabaseError as exc:
                errores.append(error_message(exc))
        for e in errores:
            flash(e, "danger")
    return _render_form(item, "Editar cliente", tipos)


@bp.route("/<int:id>/eliminar", methods=["POST"])
def eliminar(id):
    try:
        if execute("DELETE FROM clientes WHERE id_cliente = %s", (id,)):
            flash("Cliente eliminado.", "success")
        else:
            flash("El cliente no existe.", "warning")
    except DatabaseError as exc:
        flash(error_message(exc), "danger")
    return redirect(url_for(".listar"))

