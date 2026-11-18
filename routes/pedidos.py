from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from db import DatabaseError, error_message, execute, query

bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")


@bp.route("/")
def listar():
    q = request.args.get("q", "").strip()

    stats = query("""
        SELECT
            COUNT(DISTINCT p.id_pedido) AS pedidos_hoy,
            COALESCE(SUM(dp.cantidad * dp.precio_unitario), 0) AS ventas_dia,
            COUNT(DISTINCT p.id_cliente) AS clientes_atendidos
        FROM pedidos p
        LEFT JOIN detalle_pedidos dp ON p.id_pedido = dp.id_pedido
        WHERE DATE(p.fecha_compra) = CURRENT_DATE;
    """, one=True)

    sql = """
        SELECT
            p.id_pedido,
            p.fecha_compra,
            c.nombre_cliente,
            c.apellido_cliente,
            v.nombre_vendedor,
            v.apellido_vendedor,
            COALESCE(SUM(dp.cantidad * dp.precio_unitario), 0) AS total
        FROM pedidos p
        JOIN clientes c ON p.id_cliente = c.id_cliente
        JOIN vendedores v ON p.id_vendedor = v.id_vendedor
        LEFT JOIN detalle_pedidos dp ON p.id_pedido = dp.id_pedido
        WHERE (%s = '' OR c.nombre_cliente ILIKE %s OR c.apellido_cliente ILIKE %s OR CAST(p.id_pedido AS TEXT) = %s)
        GROUP BY p.id_pedido, c.nombre_cliente, c.apellido_cliente, v.nombre_vendedor, v.apellido_vendedor
        ORDER BY p.id_pedido DESC;
    """
    like_q = f"%{q}%"
    pedidos = query(sql, (q, like_q, like_q, q))

    return render_template("pedidos/list.html", pedidos=pedidos, stats=stats)


@bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    if request.method == "POST":
        id_cliente = request.form.get("id_cliente")
        id_vendedor = request.form.get("id_vendedor")
        productos_ids = request.form.getlist("producto_id[]")
        cantidades = request.form.getlist("cantidad[]")
        precios = request.form.getlist("precio_unitario[]")

        try:
            nuevo_pedido = query(
                "INSERT INTO pedidos (id_cliente, id_vendedor) VALUES (%s, %s) RETURNING id_pedido;",
                (id_cliente, id_vendedor),
                one=True
            )
            id_pedido = nuevo_pedido["id_pedido"]

            for prod_id, cant, precio in zip(productos_ids, cantidades, precios):
                execute(
                    """INSERT INTO detalle_pedidos (id_pedido, id_producto, cantidad, precio_unitario)
                       VALUES (%s, %s, %s, %s);""",
                    (id_pedido, prod_id, cant, precio)
                )

            flash("Pedido registrado correctamente.", "success")
            return redirect(url_for("pedidos.listar"))

        except DatabaseError as exc:
            flash(error_message(exc), "error")

    clientes = query("SELECT id_cliente, nombre_cliente, apellido_cliente FROM clientes ORDER BY nombre_cliente;")
    vendedores = query("SELECT id_vendedor, nombre_vendedor, apellido_vendedor FROM vendedores ORDER BY nombre_vendedor;")
    productos = query("SELECT id_producto, nombre_producto, precio_venta FROM productos ORDER BY nombre_producto;")

    return render_template("pedidos/form.html", clientes=clientes, vendedores=vendedores, productos=productos)


@bp.route("/<int:id_pedido>")
def detalle(id_pedido):
    pedido = query("SELECT * FROM pedidos WHERE id_pedido = %s;", (id_pedido,), one=True)
    if not pedido:
        abort(404)

    items = query("""
        SELECT pr.nombre_producto, dp.cantidad, dp.precio_unitario, (dp.cantidad * dp.precio_unitario) AS subtotal
        FROM detalle_pedidos dp
        JOIN productos pr ON dp.id_producto = pr.id_producto
        WHERE dp.id_pedido = %s;
    """, (id_pedido,))
    return {"id_pedido": id_pedido, "items": items}