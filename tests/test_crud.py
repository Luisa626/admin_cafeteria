"""Pruebas del CRUD de admin_cafeteria contra PostgreSQL.

Cada prueba crea sus propios registros (con el prefijo ZZ_TEST_) y los elimina al
terminar, aunque la prueba falle, así que los datos que ya tengas no se modifican.
Las pruebas NO dependen de que existan datos previos: crean sus propios tipos de
documento, categorías, clientes, vendedores y productos.

Ejecutar todo:            python -m pytest -v
Solo pruebas sin base:    python -m pytest -v -k "validators or error_message or formato_pesos"

Algunas pruebas describen cómo DEBERÍA comportarse la aplicación y pueden fallar mientras el
código tenga errores pendientes: cada fallo apunta a algo por corregir.

Opcional: para no tocar tu base real, crea una copia vacía con el script
db/admin_cafeteria_db.sql y apunta las pruebas a ella:
    $env:TEST_DB_NAME = "admin_cafeteria_test"      (PowerShell)
"""
import os
import re
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import psycopg2
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import validators as v
from app import create_app, formato_pesos
from config import Config
from db import error_message

PREFIJO = "ZZ_TEST_"
DB_NAME = os.getenv("TEST_DB_NAME", Config.DB_NAME)


# ====================================================================== ayudas

def sql(consulta, params=()):
    """Ejecuta SQL directo (con commit) y devuelve la primera fila, si hay."""
    conn = psycopg2.connect(host=Config.DB_HOST, port=Config.DB_PORT, dbname=DB_NAME,
                            user=Config.DB_USER, password=Config.DB_PASSWORD)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(consulta, params)
            return cur.fetchone() if cur.description else None
    finally:
        conn.close()


def contar(tabla):
    return sql(f"SELECT COUNT(*) FROM {tabla}")[0]


def html(respuesta):
    return respuesta.get_data(as_text=True)


def _limpiar():
    """Borra todo lo que empiece por ZZ_TEST_ respetando el orden de las llaves foráneas."""
    patron = PREFIJO.replace("_", r"\_") + "%"
    sql("""DELETE FROM pedidos
            WHERE id_cliente  IN (SELECT id_cliente  FROM clientes   WHERE nombre_cliente  LIKE %s)
               OR id_vendedor IN (SELECT id_vendedor FROM vendedores WHERE nombre_vendedor LIKE %s)""",
        (patron, patron))                                   # detalle_pedidos se borra en cascada
    sql("DELETE FROM productos  WHERE nombre_producto  LIKE %s", (patron,))
    sql("DELETE FROM clientes   WHERE nombre_cliente   LIKE %s", (patron,))
    sql("DELETE FROM vendedores WHERE nombre_vendedor  LIKE %s", (patron,))
    sql("DELETE FROM insumos    WHERE nombre_insumo    LIKE %s", (patron,))
    sql("DELETE FROM categorias WHERE nombre_categoria LIKE %s", (patron,))
    sql("DELETE FROM tipo_documento WHERE descripcion  LIKE %s", (patron,))


# Creación de registros por SQL (para preparar escenarios sin pasar por la aplicación)

def crear_cliente(tipo, nombre="Cli", documento=900000001):
    return sql("""INSERT INTO clientes (id_tipo_documento, documento, nombre_cliente, apellido_cliente)
                  VALUES (%s, %s, %s, 'Prueba') RETURNING id_cliente""",
               (tipo, documento, PREFIJO + nombre))[0]


def crear_vendedor(tipo, nombre="Ven", documento=900000002):
    return sql("""INSERT INTO vendedores (id_tipo_documento, documento, nombre_vendedor, apellido_vendedor)
                  VALUES (%s, %s, %s, 'Prueba') RETURNING id_vendedor""",
               (tipo, documento, PREFIJO + nombre))[0]


def crear_producto(categoria, nombre="Prod", precio=10000):
    return sql("""INSERT INTO productos (nombre_producto, precio_venta, id_categoria)
                  VALUES (%s, %s, %s) RETURNING id_producto""",
               (PREFIJO + nombre, precio, categoria))[0]


def crear_pedido_vacio(id_cliente, id_vendedor):
    return sql("""INSERT INTO pedidos (id_cliente, id_vendedor)
                  VALUES (%s, %s) RETURNING id_pedido""", (id_cliente, id_vendedor))[0]


def crear_pedido(id_cliente, id_vendedor, id_producto, cantidad=3, precio=10000):
    id_pedido = crear_pedido_vacio(id_cliente, id_vendedor)
    sql("""INSERT INTO detalle_pedidos (id_pedido, id_producto, cantidad, precio_unitario)
           VALUES (%s, %s, %s, %s)""", (id_pedido, id_producto, cantidad, precio))
    return id_pedido


# ===================================================================== fixtures

@pytest.fixture()
def limpio():
    _limpiar()
    yield
    _limpiar()


@pytest.fixture()
def client(limpio):
    app = create_app()
    app.config["TESTING"] = True
    app.config["DB_NAME"] = DB_NAME
    with app.test_client() as c:
        yield c


@pytest.fixture()
def tipo_doc(limpio):
    """Un tipo de documento propio de la prueba."""
    return sql("""INSERT INTO tipo_documento (sigla, descripcion)
                  VALUES ('ZZT', %s) RETURNING id_tipo_documento""", (PREFIJO + "Tipo",))[0]


@pytest.fixture()
def categoria(limpio):
    """Una categoría propia de la prueba."""
    return sql("""INSERT INTO categorias (nombre_categoria)
                  VALUES (%s) RETURNING id_categoria""", (PREFIJO + "Cat",))[0]


@pytest.fixture()
def escenario(tipo_doc, categoria):
    """Un cliente, un vendedor y un producto (de 10.000) listos para armar pedidos."""
    return SimpleNamespace(cliente=crear_cliente(tipo_doc),
                           vendedor=crear_vendedor(tipo_doc),
                           producto=crear_producto(categoria, precio=10000))


# ===================================================================== páginas

@pytest.mark.parametrize("ruta", ["/", "/clientes/", "/clientes/nuevo", "/productos/",
                                  "/productos/nuevo", "/vendedores/", "/vendedores/nuevo",
                                  "/insumos/", "/insumos/nuevo", "/pedidos/", "/pedidos/nuevo",
                                  "/configuracion/", "/configuracion/nuevo",
                                  "/configuracion/categoria/crear"])
def test_paginas_cargan(client, ruta):
    assert client.get(ruta).status_code == 200


def test_ruta_inexistente_da_404(client):
    assert client.get("/no-existe").status_code == 404


@pytest.mark.parametrize("ruta", ["/clientes/999999/editar", "/productos/999999/editar",
                                  "/vendedores/999999/editar", "/insumos/999999/editar",
                                  "/pedidos/999999/editar", "/pedidos/999999",
                                  "/pedidos/999999/ver", "/configuracion/editar/999999",
                                  "/configuracion/categoria/editar/999999"])
def test_registro_inexistente_da_404(client, ruta):
    assert client.get(ruta).status_code == 404


@pytest.mark.parametrize("ruta", ["/clientes/1/eliminar", "/productos/1/eliminar",
                                  "/vendedores/1/eliminar", "/insumos/1/eliminar",
                                  "/configuracion/eliminar/1",
                                  "/configuracion/categoria/eliminar/1",
                                  "/pedidos/1/eliminar", "/pedidos/1/agregar",
                                  "/pedidos/1/quitar/1"])
def test_eliminar_no_acepta_get(client, ruta):
    """Eliminar solo funciona por POST: un enlace GET nunca debe borrar datos."""
    assert client.get(ruta).status_code == 405


def test_error_de_conexion_muestra_pagina_de_error():
    app = create_app()
    app.config["TESTING"] = True
    app.config["DB_PORT"] = 1          # puerto donde no escucha PostgreSQL
    with app.test_client() as c:
        assert c.get("/clientes/").status_code == 500


# ===================================================================== clientes

def datos_cliente(tipo, **cambios):
    return {"id_tipo_documento": str(tipo), "documento": "900000001",
            "nombre_cliente": PREFIJO + "Cli", "apellido_cliente": "Prueba",
            "telefono": "3001112233", "email": "zz_test@ejemplo.co", **cambios}


def test_crud_clientes(client, tipo_doc):
    antes = contar("clientes")
    datos = datos_cliente(tipo_doc)

    r = client.post("/clientes/nuevo", data=datos, follow_redirects=True)
    assert "Cliente creado correctamente" in html(r)
    id_, documento, telefono, email, registro = sql(
        """SELECT id_cliente, documento, telefono, email, fecha_registro
             FROM clientes WHERE nombre_cliente=%s""", (PREFIJO + "Cli",))
    assert (documento, telefono, email) == (900000001, "3001112233", "zz_test@ejemplo.co")
    assert registro is not None                       # la fecha de registro se asigna sola

    assert PREFIJO + "Cli" in html(client.get(f"/clientes/{id_}/editar"))

    r = client.post(f"/clientes/{id_}/editar", data={**datos, "telefono": "", "email": ""},
                    follow_redirects=True)
    assert "Cliente actualizado correctamente" in html(r)
    assert sql("SELECT telefono, email FROM clientes WHERE id_cliente=%s", (id_,)) == (None, None)

    r = client.post(f"/clientes/{id_}/eliminar", follow_redirects=True)
    assert "Cliente eliminado" in html(r)
    assert contar("clientes") == antes


def test_cliente_valores_invalidos(client):
    r = client.post("/clientes/nuevo", data={
        "id_tipo_documento": "999999", "documento": "abc", "nombre_cliente": "",
        "apellido_cliente": "X", "telefono": "1" * 16, "email": "malo"})
    texto = html(r)
    assert "Tipo de documento no válido" in texto
    assert "«Documento» debe ser un número entero" in texto
    assert "«Nombre» es obligatorio" in texto
    assert "«Teléfono» admite máximo 15 caracteres" in texto
    assert "«Email» no tiene un formato válido" in texto


def test_cliente_documento_fuera_de_rango(client, tipo_doc):
    """Un documento mayor que un INTEGER de PostgreSQL se rechaza con un mensaje claro."""
    r = client.post("/clientes/nuevo", data=datos_cliente(tipo_doc, documento="9999999999"))
    assert "menor o igual a 2147483647" in html(r)
    assert sql("SELECT COUNT(*) FROM clientes WHERE nombre_cliente=%s", (PREFIJO + "Cli",))[0] == 0


def test_no_elimina_cliente_con_pedidos(client, tipo_doc, categoria):
    id_cli = crear_cliente(tipo_doc)
    crear_pedido(id_cli, crear_vendedor(tipo_doc), crear_producto(categoria))
    r = client.post(f"/clientes/{id_cli}/eliminar", follow_redirects=True)
    assert "relacionado" in html(r)
    assert sql("SELECT COUNT(*) FROM clientes WHERE id_cliente=%s", (id_cli,))[0] == 1


def test_listado_clientes(client, tipo_doc):
    crear_cliente(tipo_doc)
    texto = html(client.get("/clientes/"))
    assert PREFIJO + "Cli" in texto and "Prueba" in texto
    assert "Nuevos este mes" in texto and "Cliente más frecuente" in texto


# ==================================================================== productos

def datos_producto(categoria, **cambios):
    return {"nombre_producto": PREFIJO + "Prod", "id_categoria": str(categoria),
            "precio_venta": "12345.50", **cambios}


def test_crud_productos(client, categoria):
    datos = datos_producto(categoria)

    r = client.post("/productos/nuevo", data=datos, follow_redirects=True)
    assert "Producto creado correctamente" in html(r)
    id_, precio = sql("SELECT id_producto, precio_venta FROM productos WHERE nombre_producto=%s",
                      ((PREFIJO + "Prod").upper(),))
    assert float(precio) == 12345.50

    r = client.post(f"/productos/{id_}/editar", data={**datos, "precio_venta": "999"},
                    follow_redirects=True)
    assert "Producto actualizado correctamente" in html(r)
    assert float(sql("SELECT precio_venta FROM productos WHERE id_producto=%s", (id_,))[0]) == 999

    r = client.post(f"/productos/{id_}/eliminar", follow_redirects=True)
    assert "Producto eliminado" in html(r)
    assert sql("SELECT COUNT(*) FROM productos WHERE id_producto=%s", (id_,))[0] == 0


def test_producto_valores_invalidos(client):
    r = client.post("/productos/nuevo", data={"nombre_producto": "", "id_categoria": "",
                                              "precio_venta": "-5"})
    texto = html(r)
    assert "«Nombre del producto» es obligatorio" in texto
    assert "«Categoría» es obligatorio" in texto
    assert "mayor que 0" in texto


def test_producto_precio_no_numerico(client, categoria):
    r = client.post("/productos/nuevo", data=datos_producto(categoria, precio_venta="abc"))
    assert "debe ser un número" in html(r)


def test_producto_precio_fuera_de_rango(client, categoria):
    """La columna es NUMERIC(10,2): el máximo es 99999999.99."""
    r = client.post("/productos/nuevo", data=datos_producto(categoria, precio_venta="100000000"))
    assert "menor o igual a" in html(r)
    assert sql("SELECT COUNT(*) FROM productos WHERE nombre_producto=%s", (PREFIJO + "Prod",))[0] == 0


def test_producto_con_categoria_inexistente(client):
    r = client.post("/productos/nuevo", data=datos_producto(999999))
    assert "relacionado" in html(r)


def test_no_elimina_producto_con_pedidos(client, tipo_doc, categoria):
    id_prod = crear_producto(categoria)
    crear_pedido(crear_cliente(tipo_doc), crear_vendedor(tipo_doc), id_prod)
    r = client.post(f"/productos/{id_prod}/eliminar", follow_redirects=True)
    assert "relacionado" in html(r)
    assert sql("SELECT COUNT(*) FROM productos WHERE id_producto=%s", (id_prod,))[0] == 1


def test_listado_productos(client, categoria):
    crear_producto(categoria, precio=12000)
    texto = html(client.get("/productos/"))
    assert PREFIJO + "Prod" in texto and PREFIJO + "Cat" in texto
    assert "$ 12.000" in texto


# =================================================================== vendedores

def datos_vendedor(tipo, **cambios):
    return {"id_tipo_documento": str(tipo), "documento": "900000002",
            "nombre_vendedor": PREFIJO + "Ven", "apellido_vendedor": "Prueba",
            "telefono": "3002223344", "email": "zz_ven@ejemplo.co", **cambios}


def test_crud_vendedores(client, tipo_doc):
    datos = datos_vendedor(tipo_doc)

    r = client.post("/vendedores/nuevo", data=datos, follow_redirects=True)
    assert "Vendedor creado correctamente" in html(r)
    id_, documento, email = sql("""SELECT id_vendedor, documento, email
                                     FROM vendedores WHERE nombre_vendedor=%s""", (PREFIJO + "Ven",))
    assert (documento, email) == (900000002, "zz_ven@ejemplo.co")

    r = client.post(f"/vendedores/{id_}/editar", data={**datos, "apellido_vendedor": "Nuevo"},
                    follow_redirects=True)
    assert "Vendedor actualizado correctamente" in html(r)
    assert sql("SELECT apellido_vendedor FROM vendedores WHERE id_vendedor=%s", (id_,))[0] == "Nuevo"

    r = client.post(f"/vendedores/{id_}/eliminar", follow_redirects=True)
    assert "Vendedor eliminado" in html(r)
    assert sql("SELECT COUNT(*) FROM vendedores WHERE id_vendedor=%s", (id_,))[0] == 0


def test_vendedor_valores_invalidos(client, tipo_doc):
    r = client.post("/vendedores/nuevo", data=datos_vendedor(
        tipo_doc, documento="", nombre_vendedor="N" * 51, email="malo"))
    texto = html(r)
    assert "El campo «Documento» es obligatorio." in texto
    assert "«Nombre» admite máximo 50 caracteres." in texto
    assert "«Email» no tiene un formato válido." in texto


def test_vendedor_documento_fuera_de_rango(client, tipo_doc):
    r = client.post("/vendedores/nuevo", data=datos_vendedor(tipo_doc, documento="9999999999"))
    assert "menor o igual a 2147483647" in html(r)
    assert sql("SELECT COUNT(*) FROM vendedores WHERE nombre_vendedor=%s", (PREFIJO + "Ven",))[0] == 0


def test_vendedor_sin_nombre(client, tipo_doc):
    r = client.post("/vendedores/nuevo", data=datos_vendedor(tipo_doc, nombre_vendedor=""))
    assert "«Nombre» es obligatorio." in html(r)


def test_no_elimina_vendedor_con_pedidos(client, tipo_doc, categoria):
    id_ven = crear_vendedor(tipo_doc)
    crear_pedido(crear_cliente(tipo_doc), id_ven, crear_producto(categoria))
    r = client.post(f"/vendedores/{id_ven}/eliminar", follow_redirects=True)
    assert "relacionado" in html(r)
    assert sql("SELECT COUNT(*) FROM vendedores WHERE id_vendedor=%s", (id_ven,))[0] == 1


def test_listado_vendedores_muestra_total_vendido(client, tipo_doc, categoria):
    """3 unidades a $ 10.000 = $ 30.000 vendidos."""
    crear_pedido(crear_cliente(tipo_doc), crear_vendedor(tipo_doc),
                 crear_producto(categoria), cantidad=3, precio=10000)
    texto = html(client.get("/vendedores/"))
    assert PREFIJO + "Ven" in texto
    assert "$ 30.000" in texto


# ===================================================================== insumos

def datos_insumo(**cambios):
    return {"nombre_insumo": PREFIJO + "Ins", "unidad_medida": "kg", "stock_actual": "12.5",
            **cambios}


def test_crud_insumos(client):
    datos = datos_insumo()

    r = client.post("/insumos/nuevo", data=datos, follow_redirects=True)
    assert "Insumo creado correctamente" in html(r)
    id_, unidad, stock = sql("""SELECT id_insumo, unidad_medida, stock_actual
                                  FROM insumos WHERE nombre_insumo=%s""", ((PREFIJO + "Ins").upper(),))
    assert unidad == "kg" and float(stock) == 12.5

    # el formulario de edición deja marcada la unidad guardada
    assert re.search(r'value="kg"\s+selected', html(client.get(f"/insumos/{id_}/editar")))

    r = client.post(f"/insumos/{id_}/editar", data={**datos, "unidad_medida": "L",
                                                    "stock_actual": "0"}, follow_redirects=True)
    assert "Insumo actualizado correctamente" in html(r)
    unidad, stock = sql("SELECT unidad_medida, stock_actual FROM insumos WHERE id_insumo=%s", (id_,))
    assert unidad == "L" and float(stock) == 0

    r = client.post(f"/insumos/{id_}/eliminar", follow_redirects=True)
    assert "Insumo eliminado" in html(r)
    assert sql("SELECT COUNT(*) FROM insumos WHERE id_insumo=%s", (id_,))[0] == 0


def test_insumo_valores_invalidos(client):
    r = client.post("/insumos/nuevo", data={"nombre_insumo": "", "unidad_medida": "toneladas",
                                            "stock_actual": "-1"})
    texto = html(r)
    assert "«Nombre del insumo» es obligatorio" in texto
    assert "Unidad de medida no válida" in texto
    assert "mayor o igual a 0" in texto


def test_insumo_stock_no_numerico_ni_fuera_de_rango(client):
    r = client.post("/insumos/nuevo", data=datos_insumo(stock_actual="abc"))
    assert "debe ser un número" in html(r)
    r = client.post("/insumos/nuevo", data=datos_insumo(stock_actual="100000000"))
    assert "menor o igual a 99999999.99" in html(r)
    assert sql("SELECT COUNT(*) FROM insumos WHERE nombre_insumo=%s", (PREFIJO + "Ins",))[0] == 0


def test_insumo_acepta_coma_decimal(client):
    client.post("/insumos/nuevo", data=datos_insumo(stock_actual="2,5"), follow_redirects=True)
    stock = sql("SELECT stock_actual FROM insumos WHERE nombre_insumo=%s", ((PREFIJO + "Ins").upper(),))[0]
    assert float(stock) == 2.5


def test_listado_insumos(client):
    client.post("/insumos/nuevo", data=datos_insumo(nombre_insumo=PREFIJO + "Ins_A"))
    client.post("/insumos/nuevo", data=datos_insumo(nombre_insumo=PREFIJO + "Ins_B"))
    texto = html(client.get("/insumos/"))
    assert (PREFIJO + "Ins_A").upper() in texto and (PREFIJO + "Ins_B").upper() in texto


# ================================================================== pedidos

def test_flujo_completo_de_un_pedido(client, escenario):
    # 1. Crear el pedido (cliente + vendedor): redirige a la pantalla de detalle
    r = client.post("/pedidos/nuevo", data={"id_cliente": str(escenario.cliente),
                                            "id_vendedor": str(escenario.vendedor)},
                    follow_redirects=True)
    id_, fecha = sql("SELECT id_pedido, fecha_compra FROM pedidos WHERE id_cliente=%s",
                     (escenario.cliente,))
    assert fecha is not None
    texto = html(r)
    assert f"Pedido #{id_}" in texto and PREFIJO + "Cli" in texto
    assert "Aún no hay productos" in texto and "Cancelar pedido" in texto

    # 2. Agregar un producto: el precio sale de la base de datos, no del formulario
    r = client.post(f"/pedidos/{id_}/agregar",
                    data={"id_producto": str(escenario.producto), "cantidad": "3"},
                    follow_redirects=True)
    texto = html(r)
    assert "$ 30.000" in texto and "Terminar pedido" in texto
    id_detalle, cantidad, precio = sql(
        "SELECT id_detalle, cantidad, precio_unitario FROM detalle_pedidos WHERE id_pedido=%s", (id_,))
    assert cantidad == 3 and float(precio) == 10000

    # 3. El precio queda guardado: si el producto sube de precio, el pedido no cambia
    sql("UPDATE productos SET precio_venta = 99999 WHERE id_producto=%s", (escenario.producto,))
    assert "$ 30.000" in html(client.get(f"/pedidos/{id_}"))
    assert float(sql("SELECT precio_unitario FROM detalle_pedidos WHERE id_detalle=%s",
                     (id_detalle,))[0]) == 10000

    # 4. Quitar la línea
    r = client.post(f"/pedidos/{id_}/quitar/{id_detalle}", follow_redirects=True)
    assert "Aún no hay productos" in html(r)
    assert sql("SELECT COUNT(*) FROM detalle_pedidos WHERE id_pedido=%s", (id_,))[0] == 0

    # 5. Eliminar el pedido
    r = client.post(f"/pedidos/{id_}/eliminar", follow_redirects=True)
    assert "Pedido eliminado" in html(r)
    assert sql("SELECT COUNT(*) FROM pedidos WHERE id_pedido=%s", (id_,))[0] == 0


def test_total_suma_todas_las_lineas(client, escenario):
    id_ = crear_pedido_vacio(escenario.cliente, escenario.vendedor)
    for cantidad in ("3", "2"):
        client.post(f"/pedidos/{id_}/agregar",
                    data={"id_producto": str(escenario.producto), "cantidad": cantidad})
    assert "$ 50.000" in html(client.get(f"/pedidos/{id_}"))      # 5 unidades x 10.000


def test_editar_pedido_cambia_el_vendedor(client, escenario, tipo_doc):
    id_ = crear_pedido_vacio(escenario.cliente, escenario.vendedor)
    otro = crear_vendedor(tipo_doc, nombre="Ven2", documento=900000003)
    assert PREFIJO + "Cli" in html(client.get(f"/pedidos/{id_}/editar"))

    r = client.post(f"/pedidos/{id_}/editar",
                    data={"id_cliente": str(escenario.cliente), "id_vendedor": str(otro)},
                    follow_redirects=True)
    assert "Pedido actualizado correctamente" in html(r)
    assert sql("SELECT id_vendedor FROM pedidos WHERE id_pedido=%s", (id_,))[0] == otro


def test_pedido_sin_cliente_ni_vendedor(client):
    antes = contar("pedidos")
    r = client.post("/pedidos/nuevo", data={"id_cliente": "", "id_vendedor": ""})
    texto = html(r)
    assert "«Cliente» es obligatorio" in texto and "«Vendedor» es obligatorio" in texto
    assert contar("pedidos") == antes


def test_pedido_con_cliente_inexistente(client, escenario):
    """Debe responder con un mensaje claro, sin romperse (error 500)."""
    antes = contar("pedidos")
    r = client.post("/pedidos/nuevo", data={"id_cliente": "999999",
                                            "id_vendedor": str(escenario.vendedor)})
    assert "relacionado" in html(r)
    assert contar("pedidos") == antes


def test_agregar_producto_con_datos_invalidos(client, escenario):
    id_ = crear_pedido_vacio(escenario.cliente, escenario.vendedor)
    producto = str(escenario.producto)
    for datos in ({"id_producto": "", "cantidad": "1"},
                  {"id_producto": producto, "cantidad": "0"},
                  {"id_producto": producto, "cantidad": "-2"},
                  {"id_producto": producto, "cantidad": "abc"}):
        r = client.post(f"/pedidos/{id_}/agregar", data=datos, follow_redirects=True)
        assert "cantidad válida" in html(r), datos
    assert sql("SELECT COUNT(*) FROM detalle_pedidos WHERE id_pedido=%s", (id_,))[0] == 0


def test_agregar_producto_inexistente_no_crea_linea(client, escenario):
    id_ = crear_pedido_vacio(escenario.cliente, escenario.vendedor)
    client.post(f"/pedidos/{id_}/agregar", data={"id_producto": "999999", "cantidad": "1"})
    assert sql("SELECT COUNT(*) FROM detalle_pedidos WHERE id_pedido=%s", (id_,))[0] == 0


def test_agregar_a_pedido_inexistente(client, escenario):
    r = client.post("/pedidos/999999/agregar",
                    data={"id_producto": str(escenario.producto), "cantidad": "1"},
                    follow_redirects=True)
    assert r.status_code == 404
    assert sql("SELECT COUNT(*) FROM detalle_pedidos WHERE id_pedido=999999")[0] == 0


def test_detalle_muestra_el_boton_segun_haya_lineas(client, escenario):
    id_ = crear_pedido_vacio(escenario.cliente, escenario.vendedor)
    texto = html(client.get(f"/pedidos/{id_}"))
    assert "Cancelar pedido" in texto and "Terminar pedido" not in texto

    client.post(f"/pedidos/{id_}/agregar",
                data={"id_producto": str(escenario.producto), "cantidad": "1"})
    texto = html(client.get(f"/pedidos/{id_}"))
    assert "Terminar pedido" in texto and "Cancelar pedido" not in texto


def test_ver_pedido_es_de_solo_lectura(client, escenario):
    id_ = crear_pedido(escenario.cliente, escenario.vendedor, escenario.producto)
    r = client.get(f"/pedidos/{id_}/ver")
    texto = html(r)
    assert r.status_code == 200
    assert PREFIJO + "Prod" in texto and "$ 30.000" in texto
    assert "Quitar" not in texto


def test_listado_pedidos(client, escenario):
    crear_pedido(escenario.cliente, escenario.vendedor, escenario.producto)
    texto = html(client.get("/pedidos/"))
    assert PREFIJO + "Cli" in texto and PREFIJO + "Ven" in texto
    assert "$ 30.000" in texto
    assert "Pedidos de hoy" in texto and "Ventas del día" in texto and "Ventas totales" in texto


def test_eliminar_pedido_borra_sus_lineas(client, escenario):
    id_ = crear_pedido(escenario.cliente, escenario.vendedor, escenario.producto)
    r = client.post(f"/pedidos/{id_}/eliminar", follow_redirects=True)
    assert "Pedido eliminado" in html(r)
    assert sql("SELECT COUNT(*) FROM detalle_pedidos WHERE id_pedido=%s", (id_,))[0] == 0


def test_eliminar_pedido_inexistente(client):
    r = client.post("/pedidos/999999/eliminar", follow_redirects=True)
    assert "no existe" in html(r)


# ================================================================= configuración
# Tipos de documento: /configuracion/nuevo, /editar/<id>, /eliminar/<id>
# Categorías:         /configuracion/categoria/crear, /editar/<id>, /eliminar/<id>

def test_configuracion_crud_tipo_documento(client):
    r = client.post("/configuracion/nuevo",
                    data={"sigla": "zzx", "descripcion": PREFIJO + "TipoX"}, follow_redirects=True)
    assert "Tipo de documento creado correctamente" in html(r)
    id_, sigla = sql("SELECT id_tipo_documento, sigla FROM tipo_documento WHERE descripcion=%s",
                     (PREFIJO + "TipoX",))
    assert sigla == "ZZX"                                  # la sigla se guarda en mayúsculas

    assert PREFIJO + "TipoX" in html(client.get(f"/configuracion/editar/{id_}"))

    r = client.post(f"/configuracion/editar/{id_}",
                    data={"sigla": "zzy", "descripcion": PREFIJO + "TipoY"}, follow_redirects=True)
    assert "Tipo de documento actualizado correctamente" in html(r)
    assert sql("SELECT sigla, descripcion FROM tipo_documento WHERE id_tipo_documento=%s",
               (id_,)) == ("ZZY", PREFIJO + "TipoY")

    r = client.post(f"/configuracion/eliminar/{id_}", follow_redirects=True)
    assert "Tipo de documento eliminado" in html(r)
    assert sql("SELECT COUNT(*) FROM tipo_documento WHERE id_tipo_documento=%s", (id_,))[0] == 0


@pytest.mark.parametrize("datos,esperado", [
    ({"sigla": "", "descripcion": ""}, "es obligatorio."),
    ({"sigla": "ABCDEF", "descripcion": "Válida"}, "«Sigla» admite máximo 5 caracteres."),
    ({"sigla": "OK", "descripcion": "D" * 51}, "«Descripción» admite máximo 50 caracteres."),
])
def test_configuracion_tipo_valores_invalidos(client, datos, esperado):
    r = client.post("/configuracion/nuevo", data=datos)
    assert esperado in html(r)


def test_configuracion_no_elimina_tipo_en_uso(client, tipo_doc):
    crear_cliente(tipo_doc)
    r = client.post(f"/configuracion/eliminar/{tipo_doc}", follow_redirects=True)
    assert "relacionado" in html(r)
    assert sql("SELECT COUNT(*) FROM tipo_documento WHERE id_tipo_documento=%s", (tipo_doc,))[0] == 1


def test_configuracion_usado_por_cuenta_clientes_y_vendedores(client, tipo_doc):
    """«Usado por» debe sumar clientes y vendedores: ambos impiden eliminar el tipo."""
    crear_cliente(tipo_doc)
    crear_vendedor(tipo_doc)
    texto = html(client.get("/configuracion/"))
    fila = re.search(r"ZZT</td>\s*<td>" + re.escape(PREFIJO + "Tipo") + r"</td>.*?<td[^>]*>\s*(\d+)\s*</td>",texto,
    re.DOTALL,)
    assert fila, "no se encontró la fila del tipo de prueba en la tabla"
    assert int(fila.group(1)) == 2


def test_configuracion_crud_categoria(client):
    r = client.post("/configuracion/categoria/crear",
                    data={"nombre_categoria": PREFIJO + "CatX"}, follow_redirects=True)
    assert "Categoría creada correctamente" in html(r)
    id_ = sql("SELECT id_categoria FROM categorias WHERE nombre_categoria=%s", ((PREFIJO + "CatX").upper(),))[0]

    assert (PREFIJO + "CatX").upper() in html(client.get(f"/configuracion/categoria/editar/{id_}"))

    r = client.post(f"/configuracion/categoria/editar/{id_}",
                    data={"nombre_categoria": PREFIJO + "CatY"}, follow_redirects=True)
    assert "Categoría actualizada correctamente" in html(r)
    assert sql("SELECT nombre_categoria FROM categorias WHERE id_categoria=%s",
               (id_,))[0] == (PREFIJO + "CatY").upper()

    r = client.post(f"/configuracion/categoria/eliminar/{id_}", follow_redirects=True)
    assert "Categoría eliminada" in html(r)
    assert sql("SELECT COUNT(*) FROM categorias WHERE id_categoria=%s", (id_,))[0] == 0


def test_configuracion_categoria_duplicada_y_vacia(client):
    client.post("/configuracion/categoria/crear", data={"nombre_categoria": PREFIJO + "Cat"}, follow_redirects=True)
    r = client.post("/configuracion/categoria/crear", data={"nombre_categoria": PREFIJO + "Cat"}, follow_redirects=True)
    assert "Ya existe un registro" in html(r)
    r = client.post("/configuracion/categoria/crear", data={"nombre_categoria": "   "}, follow_redirects=True)
    assert "El campo «Nombre de la categoría» es obligatorio." in html(r)


def test_configuracion_categoria_nombre_muy_largo(client):
    r = client.post("/configuracion/categoria/crear", data={"nombre_categoria": "C" * 51})
    assert "50 caracteres" in html(r)


def test_configuracion_no_elimina_categoria_con_productos(client, categoria):
    crear_producto(categoria)
    r = client.post(f"/configuracion/categoria/eliminar/{categoria}", follow_redirects=True)
    assert "relacionado" in html(r)
    assert sql("SELECT COUNT(*) FROM categorias WHERE id_categoria=%s", (categoria,))[0] == 1


@pytest.mark.parametrize("ruta", ["/configuracion/eliminar/999999",
                                  "/configuracion/categoria/eliminar/999999"])
def test_configuracion_eliminar_inexistente_avisa(client, ruta):
    """No debe decir «eliminado» cuando no se borró nada."""
    assert "no existe" in html(client.post(ruta, follow_redirects=True))


# ============================================ pruebas sin base de datos (unitarias)

def test_validators_texto():
    errores = []
    assert v.texto({"x": "  hola  "}, "x", "X", errores, max_len=10) == "hola"
    assert errores == []

    assert v.texto({"x": "   "}, "x", "X", errores) is None
    assert "«X» es obligatorio" in errores[-1]

    errores = []
    assert v.texto({"x": ""}, "x", "X", errores, obligatorio=False) is None   # opcional vacío -> NULL
    assert errores == []

    v.texto({"x": "abcdef"}, "x", "X", errores, max_len=3)
    assert "máximo 3" in errores[0]


def test_validators_entero():
    errores = []
    assert v.entero({"n": " 5 "}, "n", "N", errores) == 5 and errores == []

    assert v.entero({"n": "abc"}, "n", "N", errores) is None
    assert "número entero" in errores[-1]

    assert v.entero({"n": ""}, "n", "N", errores) is None
    assert "obligatorio" in errores[-1]

    errores = []
    v.entero({"n": "0"}, "n", "N", errores, minimo=1)
    assert "mayor o igual a 1" in errores[0]

    errores = []
    v.entero({"n": "11"}, "n", "N", errores, maximo=10)
    assert "menor o igual a 10" in errores[0]


def test_validators_decimal():
    errores = []
    assert v.decimal({"d": "2,5"}, "d", "D", errores) == Decimal("2.5")     # coma decimal
    assert errores == []

    assert v.decimal({"d": "x"}, "d", "D", errores) is None
    assert "debe ser un número" in errores[-1]

    errores = []
    v.decimal({"d": "0"}, "d", "D", errores, mayor_que=0)
    assert "mayor que 0" in errores[0]

    errores = []
    v.decimal({"d": "-1"}, "d", "D", errores, minimo=0)
    assert "mayor o igual a 0" in errores[0]

    errores = []
    v.decimal({"d": "101"}, "d", "D", errores, maximo=Decimal("100"))
    assert "menor o igual a 100" in errores[0]


def test_validators_fecha():
    errores = []
    assert v.fecha({"f": "2026-10-23"}, "f", "F", errores) == date(2026, 10, 23)
    assert errores == []

    assert v.fecha({"f": "23/10/2026"}, "f", "F", errores) is None
    assert "fecha válida" in errores[-1]

    assert v.fecha({"f": ""}, "f", "F", errores) is None
    assert "obligatorio" in errores[-1]


def test_validators_email():
    errores = []
    assert v.email({"e": "a@b.co"}, "e", "E", errores) == "a@b.co" and errores == []
    assert v.email({"e": ""}, "e", "E", errores) is None and errores == []   # el email es opcional

    for malo in ("malo", "a@b", "@"):
        errores = []
        v.email({"e": malo}, "e", "E", errores)
        assert "formato válido" in errores[0], malo


@pytest.mark.parametrize("codigo, fragmento", [
    ("23503", "relacionado"),            # llave foránea
    ("23505", "Ya existe un registro"),  # único duplicado
    ("23514", "fuera del rango"),        # CHECK
    ("23502", "campo obligatorio"),      # NOT NULL
])
def test_error_message_traduce_codigos_conocidos(codigo, fragmento):
    assert fragmento in error_message(SimpleNamespace(pgcode=codigo))


def test_error_message_codigo_desconocido():
    exc = SimpleNamespace(pgcode="99999", pgerror="boom")
    assert error_message(exc) == "Error de base de datos: boom"


def test_formato_pesos():
    assert formato_pesos(3200000) == "$ 3.200.000"
    assert formato_pesos(Decimal("1500.00")) == "$ 1.500"
    assert formato_pesos(0) == "$ 0"
    assert formato_pesos(None) == ""
