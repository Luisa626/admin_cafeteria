from flask import Flask
from config import Config
import db

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