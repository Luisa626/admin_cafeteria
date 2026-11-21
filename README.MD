# Administración de cafetería · Flask + PostgreSQL

Aplicación web para consultar, crear, editar y eliminar registros de las ocho tablas de la base de datos `admin_cafeteria_db`: `tipo_documento`, `clientes`, `vendedores`, `categorias`, `productos`, `insumos`, `pedidos` y `detalle_pedidos`.

**Integrantes:** Oscar Andrés Horta Bonilla · María Luisa Rojas Vargas

**Tecnologías:** Python 3.10+, Flask 3, psycopg2, PostgreSQL, python-dotenv, Bootstrap 5 y Bootstrap Icons (desde CDN).

## Tabla de contenido

1. [Tema del proyecto](#tema-del-proyecto)
2. [Modelo entidad-relación (MER)](#modelo-entidad-relación-mer)
3. [Estructura del repositorio](#estructura-del-repositorio)
4. [Instalación](#instalación-en-windows)
5. [Ejecución](#ejecución)
6. [Capturas de la aplicación](#capturas-de-la-aplicación)
7. [Qué hace cada pantalla](#qué-hace-cada-pantalla)
8. [Pruebas automáticas](#pruebas-automáticas)
9. [Detalles de diseño](#detalles-de-diseño)
10. [Alcance y limitaciones](#alcance-y-lmitaciones)

## Tema del proyecto

**Sistema de administración para una cafetería.** Un negocio pequeño de este tipo suele llevar sus ventas, sus clientes y su inventario en cuadernos u hojas de cálculo separadas. Eso dificulta saber cuánto se vendió en el día, qué productos se venden más, cuánto ha vendido cada vendedor o cuándo se está acabando un insumo. Esta aplicación centraliza esa información en una base de datos PostgreSQL y la ofrece en una interfaz web sencilla, pensada para la persona que administra el negocio.

**Qué problemas resuelve**

- Registrar pedidos con sus productos y calcular el total de cada uno de forma automática.
- Conocer las ventas del día, las ventas totales y los productos más vendidos.
- Mantener el directorio de clientes y de vendedores, cada uno con su tipo de documento.
- Saber cuánto ha vendido cada vendedor y quién atiende más pedidos.
- Controlar el stock de los insumos y detectar cuál es el que menos queda.
- Mantener los catálogos del sistema: tipos de documento y categorías de productos.

**Flujo principal de uso:** un vendedor atiende a un cliente, se crea un pedido (cliente + vendedor), se agregan los productos con su cantidad y el sistema toma el precio vigente de cada producto, calcula el total y lo refleja en el panel de inicio.

**Alcance:** es una aplicación de administración interna, con un solo tipo de usuario y sin inicio de sesión. Los insumos se gestionan por separado: no están ligados a recetas ni se descuentan solos cuando se vende un producto.

## Modelo entidad-relación (MER)

![Diagrama de la base de datos](images/db.png)

| Tabla | Descripción | Relaciones |
|---|---|---|
| `tipo_documento` | Catálogo de tipos de documento (CC, CE, TI, PP…) | — |
| `clientes` | Clientes de la cafetería | → `tipo_documento` |
| `vendedores` | Personal que atiende los pedidos | → `tipo_documento` |
| `categorias` | Categorías de productos (nombre único) | — |
| `productos` | Productos a la venta con su precio | → `categorias` |
| `insumos` | Materias primas y su stock actual | — |
| `pedidos` | Cabecera de cada venta (fecha, cliente, vendedor) | → `clientes`, `vendedores` |
| `detalle_pedidos` | Productos, cantidades y precio de cada pedido | → `pedidos`, `productos` |

## Estructura del repositorio

```
admin_cafeteria/
├── app.py                 # Punto de entrada: crea la app, registra los blueprints y el panel de inicio
├── config.py              # Lectura de la configuración (.env)
├── db.py                  # Conexión a PostgreSQL, funciones query / execute y traducción de errores
├── validators.py          # Validaciones de los formularios
├── routes/                # Un blueprint por módulo
│   ├── clientes.py
│   ├── configuracion.py   # tipo_documento y categorias
│   ├── insumos.py
│   ├── pedidos.py         # pedidos y detalle_pedidos
│   ├── productos.py
│   └── vendedores.py
├── templates/             # Plantillas Jinja2
│   ├── base.html          # Plantilla común: menú, mensajes, Bootstrap
│   ├── macros.html        # Botones y encabezados reutilizables
│   ├── index.html         # Panel de inicio
│   ├── 404.html           # Página no encontrada
│   ├── error_db.html      # Error de conexión con la base de datos
│   ├── clientes/          # list.html, form.html
│   ├── configuracion/     # list.html, form.html, categoria_form.html
│   ├── insumos/           # list.html, form.html
│   ├── pedidos/           # list.html, form.html, detalle.html, ver.html
│   ├── productos/         # list.html, form.html
│   └── vendedores/        # list.html, form.html
├── static/                # CSS e imágenes
│   └── css/styles.css
├── db/
│   └── admin_cafeteria_db.sql         # Script de creación de la base de datos
├── docs/                  # MER, diccionario de datos y plan de pruebas
├── images/
│   ├── db.png             # Diagrama de la base de datos
│   ├── arquitectura_admin_cafeteria_cafe.png
│   └── capturas/          # Capturas de la aplicación (ver sección «Capturas»)
├── tests/
│   └── test_crud.py       # Pruebas automáticas
├── pytest.ini
├── requirements.txt       # Librerías de la aplicación
├── requirements-dev.txt   # Librerías de la aplicación + pytest
├── .env.example           # Plantilla de configuración (sin contraseñas)
├── .gitignore             # Excluye venv/, .env y __pycache__/
└── README.md
```

## Instalación en Windows

**Requisitos:** Python 3.10 o superior y PostgreSQL (con pgAdmin).

1. Abre PowerShell en la carpeta del proyecto:
   ```powershell
   cd C:\ruta\a\admin_cafeteria
   ```
2. Crea y activa el entorno virtual, e instala las librerías:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   Si PowerShell bloquea la activación, ejecuta antes:
   `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
3. Crea la base de datos y ejecuta el script de creación. En pgAdmin: crea una base llamada `admin_cafeteria_db`, abre **Query Tool**, carga el archivo `db/admin_cafeteria_db.sql` y ejecútalo.
   O desde la terminal:
   ```powershell
   psql -U postgres -c "CREATE DATABASE admin_cafeteria_db;"
   psql -U postgres -d admin_cafeteria_db -f db/admin_cafeteria_db.sql
   ```
4. Crea tu archivo de configuración a partir de la plantilla y completa tus datos de PostgreSQL (los mismos que usas en pgAdmin):
   ```powershell
   Copy-Item .env.example .env
   ```
   ```
   SECRET_KEY=escribe-una-clave-larga-y-secreta
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=admin_cafeteria_db
   DB_USER=postgres
   DB_PASSWORD=tu_contraseña
   ```
   > El archivo `.env` contiene credenciales y **no se sube a GitHub** (está en `.gitignore`). En el repositorio solo va `.env.example`, sin contraseñas.
5. Si la base quedó sin tipos de documento, agrégalos desde la pantalla **Configuración** o con SQL. Sin ellos no se pueden registrar clientes ni vendedores. tambien estos se pueden editar cambiar o agregar desde la pagina web:
   ```sql
   INSERT INTO tipo_documento (sigla, descripcion) VALUES
     ('CC', 'Cédula de ciudadanía'),
     ('CE', 'Cédula de extranjería'),
     ('TI', 'Tarjeta de identidad'),
     ('PP', 'Pasaporte');
   ```

## Ejecución

```powershell
.\venv\Scripts\Activate.ps1
python app.py
```

Abre **http://127.0.0.1:5000**

> Si el puerto 5000 está ocupado, cambia el valor de `port=` al final de `app.py`.

## Capturas de la aplicación

> Guarda las capturas en `images/capturas/` con los nombres sugeridos. Para mostrar cada una, quita los símbolos `<!--` y `-->` de la línea de la imagen. Mientras tanto, cada sección indica qué conviene capturar.

### 1. Panel de inicio

la página `/` con las tarjetas de ventas del día, ventas totales y pedidos totales, y la tabla de pedidos y productos más vendidos del día.
[Panel de inicio](images/capturas/01-inicio.png)

### 2. Listado de clientes

`/clientes/` con las tarjetas «Nuevos este mes» y «Cliente más frecuente» y la tabla con cliente, documento, telefono .... tambien en la misma tabla los botones de editar y borrar
[Listado de clientes](images/capturas/02-clientes-lista.png)

### 3. Formulario de cliente

`/clientes/nuevo` con la lista desplegable de tipo de documento.
[Formulario de cliente](images/capturas/03-clientes-formulario.png)
[validaciones de formulario de cliente](images/capturas/03-2-validaciones-formulario.png)

### 4. Integridad de los datos

el aviso que aparece al intentar eliminar un cliente que ya tiene pedidos («el registro está relacionado con otros datos…»). Demuestra que la base de datos protege la información.
[Aviso de integridad referencial](images/capturas/04-error-integridad.png)

### 5. Armado de un pedido

la pantalla de detalle de un pedido con varios productos agregados, el subtotal de cada línea y el total.
[Detalle de un pedido](images/capturas/05-pedido-detalle.png)

### 6. Productos

`/productos/` con categoría y precio en pesos de cada producto.
[Listado de productos](images/capturas/06-productos.png)
[Nuevo producto](images/capturas/06-2-nuevo_producto.png)

### 7. Vendedores

`/vendedores/` con las tarjetas de pedidos atendidos hoy y mejor vendedor, y la columna de total vendido.
[Listado de vendedores](images/capturas/07-vendedores.png)

### 8. Insumos

`/insumos/` con el stock de cada insumo y la tarjeta del insumo con menos existencias.
[Listado de insumos](images/capturas/08-insumos.png)

### 10. Configuración

`/configuracion/` con la tabla de tipos de documento (columna «Usado por») y la tabla de categorías (columna «Productos»).
[Configuración](images/capturas/09-configuracion.png)
[categoria](images/capturas/09-2-categoria.png)

### 11. Pruebas automáticas

la terminal después de ejecutar `python -m pytest -v`, con el resumen de pruebas pasadas.
[Pruebas automáticas](images/capturas/10-pytest.png)

## Qué hace cada pantalla

| Módulo | El listado muestra | El formulario pide |
|---|---|---|
| Inicio | Ventas del día, ventas totales, pedidos totales, pedidos de hoy y productos más vendidos hoy | — |
| Pedidos | Fecha, cliente, vendedor y total de cada pedido; tarjetas de pedidos y ventas | Se crea en dos pasos: primero cliente y vendedor; luego se agregan los productos con su cantidad (el precio se toma del producto) |
| Productos | Categoría y precio en pesos | Nombre, categoría (lista desplegable) y precio de venta |
| Clientes | Documento, nombre, teléfono, email, fecha de registro y nº de pedidos; clientes nuevos del mes y cliente más frecuente | Tipo de documento (lista), documento, nombre, apellido, teléfono y email |
| Vendedores | Documento, contacto y total vendido; pedidos atendidos hoy y mejor vendedor | Tipo de documento (lista), documento, nombre, apellido, teléfono y email |
| Insumos | Unidad de medida, stock e insumo con menos stock | Nombre, unidad (lista fija: kg, lb, gramos, ml, litros) y stock |
| Configuración | Tipos de documento (con cuántos clientes los usan) y categorías (con su nº de productos) | Sigla y descripción del tipo de documento; nombre de la categoría |

## Pruebas automáticas

Las pruebas están en `tests/test_crud.py` y recorren el CRUD de cada módulo, las validaciones, los avisos de error y las reglas de integridad. También incluyen pruebas que no necesitan base de datos (validadores, traducción de errores y formato de pesos).

```powershell
pip install -r requirements-dev.txt
python -m pytest -v
```

Para ejecutar solo las que no usan la base de datos:

```powershell
python -m pytest -v -k "validators or error_message or formato_pesos"
```

- **Datos de prueba propios:** cada prueba crea sus registros con el prefijo `ZZ_TEST_` y los elimina al terminar, aunque falle. No dependen de los datos que ya tengas.
- **Base de datos:** por defecto se usa la base configurada en `.env`. Para no tocar tus datos, crea una copia vacía con `database/backup.sql` y apunta las pruebas a ella:
  ```powershell
  $env:TEST_DB_NAME = "admin_cafeteria_test"
  ```

## Detalles de diseño

- **Estructura por capas:** la configuración (`config.py`), el acceso a datos (`db.py`), las validaciones (`validators.py`), las rutas (`routes/`) y las vistas (`templates/`) están separadas. La aplicación se construye con el patrón *application factory* (`create_app`) y cada módulo es un *Blueprint*.
- **Consultas parametrizadas** (`%s` y `%(nombre)s`) en todas las sentencias SQL, para evitar la inyección SQL.
- **Validación en el servidor** de los formularios con `validators.py`, además de los atributos `required` y `maxlength` del navegador.
- **Integridad referencial:** las llaves foráneas usan `ON DELETE RESTRICT`, así que no se puede eliminar, por ejemplo, un cliente con pedidos o una categoría con productos. Solo `detalle_pedidos` se elimina en cascada junto con su pedido.
- **Errores de la base de datos** (duplicados, llaves foráneas, valores fuera de rango) se traducen a mensajes en español en `db.py`.
- **Eliminar siempre usa POST**: un enlace GET nunca borra datos.
- **Post/Redirect/Get:** después de guardar, la aplicación redirige al listado, de modo que recargar la página no duplica registros.
- **Precio histórico:** `detalle_pedidos.precio_unitario` guarda el precio del producto en el momento de la venta, así que un cambio posterior de precio no altera las ventas anteriores.
- **Totales calculados:** el total de cada pedido no se almacena; se calcula con `SUM(cantidad * precio_unitario)`, lo que evita datos inconsistentes.
- **Filtro `pesos`:** muestra los valores como `$ 3.200.000`.
- **Dinero y cantidades con `Decimal`**, no `float`, para evitar errores de redondeo.

## Alcance y limitaciones
i
- La aplicación no tiene inicio de sesión ni roles de usuario.
- Los formularios no incluyen token CSRF.
- Los insumos no están relacionados con los productos ni descuentan stock al vender.
- `app.run(debug=True)` es solo para desarrollo; no debe usarse en producción.

## Integrantes

- Oscar Andrés Horta Bonilla
- María Luisa Rojas Vargas
