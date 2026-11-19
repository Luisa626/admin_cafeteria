from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

import validators as v
from db import DatabaseError, error_message, execute, query

bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")


def _leer_formulario(form):
    errores = []
    datos = {
        "id_cliente": v.entero(form, "id_cliente", "Cliente", errores, minimo=1),
        "id_vendedor": v.entero(form, "id_vendedor", "Vendedor", errores, minimo=1),
    }
    return datos, errores


def _clientes():
    return query("""SELECT id_cliente,
                           CONCAT(nombre_cliente, ' ', apellido_cliente) AS nombre_cliente
                      FROM clientes ORDER BY nombre_cliente, apellido_cliente""")


def _vendedores():
    return query("""SELECT id_vendedor,
                           CONCAT(nombre_vendedor, ' ', apellido_vendedor) AS nombre_vendedor
                      FROM vendedores ORDER BY nombre_vendedor, apellido_vendedor""")


def _render_form(item, titulo):
    return render_template("pedidos/form.html", item=item, titulo=titulo,
                           clientes=_clientes(), vendedores=_vendedores())


# ---------- LISTA (pantalla por defecto) ----------
@bp.route("/")
def listar():
    pedidos = query("""
        SELECT p.id_pedido, p.fecha_compra,
               CONCAT(c.nombre_cliente, ' ', c.apellido_cliente) AS cliente,
               CONCAT(v.nombre_vendedor, ' ', v.apellido_vendedor) AS vendedor,
               COALESCE(SUM(d.cantidad * d.precio_unitario), 0) AS total
          FROM pedidos p
          JOIN clientes c   ON c.id_cliente = p.id_cliente
          JOIN vendedores v ON v.id_vendedor = p.id_vendedor
          LEFT JOIN detalle_pedidos d ON d.id_pedido = p.id_pedido
         GROUP BY p.id_pedido, c.id_cliente, v.id_vendedor
         ORDER BY p.id_pedido DESC
    """)
    pedidos_recientes = query("""
        SELECT COUNT(*) AS total_pedidos
          FROM pedidos
         WHERE fecha_compra >= CURRENT_DATE AND fecha_compra < CURRENT_DATE + 1
    """, one=True)
    ventas_del_dia = query("""
        SELECT COALESCE(SUM(d.cantidad * d.precio_unitario), 0) AS ventas_del_dia
          FROM pedidos p
          JOIN detalle_pedidos d ON d.id_pedido = p.id_pedido
         WHERE p.fecha_compra >= CURRENT_DATE AND p.fecha_compra < CURRENT_DATE + 1
    """, one=True)
    ventas_totales = query("""
        SELECT COALESCE(SUM(cantidad * precio_unitario), 0) AS ventas_totales
          FROM detalle_pedidos
    """, one=True)
    return render_template("pedidos/list.html", items=pedidos,
                           pedidos_recientes=pedidos_recientes,
                           ventas_del_dia=ventas_del_dia,
                           ventas_totales=ventas_totales)

@bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    item = {}
    if request.method == "POST":
        item = request.form.to_dict()
        datos, errores = _leer_formulario(request.form)
        if not errores:
            try:
                fila = query(
                    """INSERT INTO pedidos (id_cliente, id_vendedor, fecha_compra)
                       VALUES (%(id_cliente)s, %(id_vendedor)s, NOW())
                       RETURNING id_pedido""",
                    datos, one=True)
                return redirect(url_for("pedidos.detalle", id_pedido=fila["id_pedido"]))
            except DatabaseError as exc:
                errores.append(error_message(exc))
        for e in errores:
            flash(e, "danger")
    return _render_form(item, "Nuevo pedido")

@bp.route("/<int:id_pedido>")
def detalle(id_pedido):
    pedido = query("""
        SELECT p.id_pedido, p.fecha_compra,
               CONCAT(c.nombre_cliente, ' ', c.apellido_cliente) AS cliente,
               CONCAT(v.nombre_vendedor, ' ', v.apellido_vendedor) AS vendedor
          FROM pedidos p
          JOIN clientes c   ON c.id_cliente = p.id_cliente
          JOIN vendedores v ON v.id_vendedor = p.id_vendedor
         WHERE p.id_pedido = %s
    """, (id_pedido,), one=True)
    if pedido is None:
        abort(404)

    lineas = query("""
        SELECT d.id_detalle, pr.nombre_producto, d.cantidad, d.precio_unitario,
               d.cantidad * d.precio_unitario AS subtotal
          FROM detalle_pedidos d
          JOIN productos pr ON pr.id_producto = d.id_producto
         WHERE d.id_pedido = %s
         ORDER BY d.id_detalle
    """, (id_pedido,))
    total = sum(l["subtotal"] for l in lineas)
    productos = query("""SELECT id_producto, nombre_producto, precio_venta
                           FROM productos ORDER BY nombre_producto""")
    return render_template("pedidos/detalle.html", titulo=f"Pedido #{id_pedido}",
                           pedido=pedido, lineas=lineas, total=total,
                           productos=productos)


@bp.route("/<int:id_pedido>/agregar", methods=["POST"])
def agregar(id_pedido):
    id_producto = request.form.get("id_producto", "")
    cantidad = request.form.get("cantidad", "")
    if not id_producto or not cantidad.isdigit() or int(cantidad) < 1:
        flash("Elige un producto y una cantidad válida (mínimo 1).", "danger")
        return redirect(url_for("pedidos.detalle", id_pedido=id_pedido))
    try:
        # El precio se toma de la base de datos, no del formulario
        execute("""INSERT INTO detalle_pedidos (id_pedido, id_producto, cantidad, precio_unitario)
                   SELECT %s, id_producto, %s, precio_venta
                     FROM productos WHERE id_producto = %s""",
                (id_pedido, int(cantidad), id_producto))
    except DatabaseError as exc:
        flash(error_message(exc), "danger")
    return redirect(url_for("pedidos.detalle", id_pedido=id_pedido))


@bp.route("/<int:id_pedido>/quitar/<int:id_detalle>", methods=["POST"])
def quitar(id_pedido, id_detalle):
    try:
        execute("DELETE FROM detalle_pedidos WHERE id_detalle = %s AND id_pedido = %s",
                (id_detalle, id_pedido))
    except DatabaseError as exc:
        flash(error_message(exc), "danger")
    return redirect(url_for("pedidos.detalle", id_pedido=id_pedido))


# ---------- editar cliente/vendedor y eliminar ----------
@bp.route("/<int:id>/editar", methods=["GET", "POST"])
def editar(id):
    item = query("SELECT * FROM pedidos WHERE id_pedido = %s", (id,), one=True)
    if item is None:
        abort(404)
    if request.method == "POST":
        item = {**item, **request.form.to_dict()}
        datos, errores = _leer_formulario(request.form)
        if not errores:
            try:
                execute("""UPDATE pedidos
                              SET id_cliente = %(id_cliente)s,
                                  id_vendedor = %(id_vendedor)s
                            WHERE id_pedido = %(id)s""",
                        {**datos, "id": id})
                flash("Pedido actualizado correctamente.", "success")
                return redirect(url_for(".listar"))
            except DatabaseError as exc:
                errores.append(error_message(exc))
        for e in errores:
            flash(e, "danger")
    return _render_form(item, "Editar pedido")


@bp.route("/<int:id>/eliminar", methods=["POST"])
def eliminar(id):
    try:
        # Primero los detalles, luego el pedido
        execute("DELETE FROM detalle_pedidos WHERE id_pedido = %s", (id,))
        if execute("DELETE FROM pedidos WHERE id_pedido = %s", (id,)):
            flash("Pedido eliminado.", "success")
        else:
            flash("El pedido no existe.", "warning")
    except DatabaseError as exc:
        flash(error_message(exc), "danger")
    return redirect(url_for(".listar"))

@bp.route("/<int:id_pedido>/ver")
def ver(id_pedido):
    pedido = query("""
        SELECT p.id_pedido, p.fecha_compra,
               CONCAT(c.nombre_cliente, ' ', c.apellido_cliente) AS cliente,
               CONCAT(v.nombre_vendedor, ' ', v.apellido_vendedor) AS vendedor
          FROM pedidos p
          JOIN clientes c   ON c.id_cliente = p.id_cliente
          JOIN vendedores v ON v.id_vendedor = p.id_vendedor
         WHERE p.id_pedido = %s
    """, (id_pedido,), one=True)
    if pedido is None:
        abort(404)

    lineas = query("""
        SELECT d.id_detalle, pr.nombre_producto, d.cantidad, d.precio_unitario,
               d.cantidad * d.precio_unitario AS subtotal
          FROM detalle_pedidos d
          JOIN productos pr ON pr.id_producto = d.id_producto
         WHERE d.id_pedido = %s
         ORDER BY d.id_detalle
    """, (id_pedido,))
    total = sum(l["subtotal"] for l in lineas)
    productos = query("""SELECT id_producto, nombre_producto, precio_venta
                           FROM productos ORDER BY nombre_producto""")
    return render_template("pedidos/ver.html", titulo=f"Pedido #{id_pedido}",
                           pedido=pedido, lineas=lineas, total=total,
                           productos=productos)



