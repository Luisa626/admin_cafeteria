import psycopg2
from flask import Flask, render_template

from config import Config
import db
from routes.pedidos import bp as pedidos_bp
from routes.clientes import bp as clientes_bp
from routes.productos import bp as productos_bp
from routes.vendedores import bp as vendedores_bp
from routes.insumos import bp as insumos_bp
from routes.configuracion import bp as configuracion_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    @app.route("/")
    def index():
        fila = db.query("SELECT 1 AS ok", one=True)
        return f"Conexión OK: {fila}"

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)