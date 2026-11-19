import psycopg2
from flask import Flask, app, render_template

from config import Config
import db
from routes.pedidos import bp as pedidos_bp
from routes.clientes import bp as clientes_bp
from routes.productos import bp as productos_bp
from routes.vendedores import bp as vendedores_bp
from routes.insumos import bp as insumos_bp
from routes.configuracion import bp as configuracion_bp


def formato_pesos(valor):
    """Filtro Jinja: 3200000 -> $ 3.200.000"""
    if valor is None:
        return ""
    return "$ " + f"{float(valor):,.0f}".replace(",", ".")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    app.add_template_filter(formato_pesos, "pesos")

    for bp in (pedidos_bp, clientes_bp, productos_bp, vendedores_bp, insumos_bp, configuracion_bp):
        app.register_blueprint(bp)

    @app.route("/")
    def inicio():
        resumen = db.query("""
             SELECT (SELECT COUNT(*) FROM pedidos) AS pedidos_totales,
                    (SELECT COALESCE(SUM(cantidad * precio_unitario), 0)
                        FROM detalle_pedidos) AS total_ventas,
                    (SELECT COALESCE(SUM(d.cantidad * d.precio_unitario), 0)
                        FROM pedidos p
                        JOIN detalle_pedidos d ON d.id_pedido = p.id_pedido
                        WHERE p.fecha_compra >= CURRENT_DATE
                        AND p.fecha_compra <  CURRENT_DATE + 1) AS ventas_del_dia
        """, one=True)

        
        pedidos_recientes = db.query("""
            SELECT p.id_pedido AS pedido, p.id_cliente, p.id_vendedor, COALESCE(SUM(d.cantidad * 
                    d.precio_unitario), 0) AS total
                    FROM pedidos p
                    JOIN detalle_pedidos d ON d.id_pedido = p.id_pedido
                    WHERE p.fecha_compra >= CURRENT_DATE
                    AND p.fecha_compra <  CURRENT_DATE + 1
                    GROUP BY p.id_pedido, p.id_cliente, p.id_vendedor
                    ORDER BY p.id_pedido DESC
        """)

        top_productos = db.query("""
            SELECT pr.nombre_producto, SUM(d.cantidad) AS unidades_vendidas
                FROM pedidos p
                JOIN detalle_pedidos d ON d.id_pedido = p.id_pedido
                JOIN productos pr      ON pr.id_producto = d.id_producto
                GROUP BY pr.id_producto, pr.nombre_producto
                ORDER BY unidades_vendidas DESC
                LIMIT 3
        """)

        stats_clientes = db.query("""
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
        return render_template("index.html", r=resumen, pedidos=pedidos_recientes, top=top_productos, sc=stats_clientes)

    @app.errorhandler(psycopg2.OperationalError)
    def error_conexion(exc):
        return render_template("error_db.html", error=str(exc)), 500

    @app.errorhandler(404)
    def no_encontrado(exc):
        return render_template("404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)