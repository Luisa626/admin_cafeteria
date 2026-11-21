# Diccionario de datos — Cafetería

**Asignatura:** Programación Web  
**Integrantes:** María Luisa Rojas Vargas y Oscar Andrés Horta Bonilla  
**Base de datos:** `admin_cafeteria_db`  
**Motor:** PostgreSQL  

En este diccionario explicamos qué guarda cada tabla de la cafetería, para qué sirve cada campo y qué reglas debe cumplir.

## Significado de las restricciones

| Restricción | Significado |
|---|---|
| PK | Identifica cada registro. No se repite ni puede quedar nula. |
| FK | Relaciona un registro con otra tabla. |
| NOT NULL | El campo es obligatorio. |
| UNIQUE | El valor no se puede repetir. |
| CHECK | El dato debe cumplir una condición. |
| DEFAULT | Valor que se usa si no se indica otro. |

La columna «Tipo declarado» muestra cómo definimos los campos en el script de creación de tablas. Usamos `SERIAL` para el ID propio de cada tabla, que se genera automáticamente. Las llaves foráneas son `INTEGER` porque guardan el ID de un registro que ya existe en otra tabla.

En PostgreSQL, `SERIAL` crea un campo entero con una secuencia. Por eso en el archivo de respaldo (`admin_cafeteria_db_backup.sql`) aparece como `INTEGER` junto con su secuencia; corresponde al mismo campo.

Los precios están en pesos colombianos. Los campos `NUMERIC(10,2)` permiten guardar valores con dos decimales.

## 1. Tabla `tipo_documento`

Guarda los tipos de documento de identidad que pueden tener los clientes y vendedores.

| Campo | Tipo declarado | Restricciones | Descripción |
|---|---|---|---|
| `id_tipo_documento` | SERIAL | PK, NOT NULL | Identificador del tipo de documento. Se genera automáticamente. |
| `sigla` | VARCHAR(5) | NOT NULL, UNIQUE | Abreviatura del documento, por ejemplo CC o NIT. |
| `descripcion` | VARCHAR(50) | NOT NULL, UNIQUE | Nombre completo del tipo de documento. |

Valores registrados actualmente:

| Sigla | Descripción |
|---|---|
| CC | Cédula de ciudadanía |
| CE | Cédula de Extranjería |
| NIT | Número de Identificación Tributaria |
| TI | Tarjeta de Identidad |

## 2. Tabla `clientes`

Guarda la identificación y los datos de contacto de los clientes.

| Campo | Tipo declarado | Restricciones | Descripción |
|---|---|---|---|
| `id_cliente` | SERIAL | PK, NOT NULL | Identificador interno del cliente. Se genera automáticamente. |
| `id_tipo_documento` | INTEGER | NOT NULL, FK a `tipo_documento.id_tipo_documento` | Tipo de documento del cliente. |
| `documento` | BIGINT | NOT NULL, UNIQUE | Número de documento del cliente. No puede repetirse. |
| `nombre_cliente` | VARCHAR(50) | NOT NULL | Nombre del cliente. |
| `apellido_cliente` | VARCHAR(50) | NOT NULL | Apellido del cliente. |
| `telefono` | VARCHAR(15) | Permite NULL | Teléfono de contacto. Es opcional. |
| `email` | VARCHAR(100) | UNIQUE, permite NULL | Correo opcional. Los valores registrados no pueden repetirse. |
| `fecha_registro` | TIMESTAMP WITHOUT TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Fecha y hora en que se registró el cliente. |

`id_cliente` es el número interno del registro; `documento` corresponde al documento de identidad del cliente.

## 3. Tabla `vendedores`

Guarda la identificación y los datos de contacto de los vendedores.

| Campo | Tipo declarado | Restricciones | Descripción |
|---|---|---|---|
| `id_vendedor` | SERIAL | PK, NOT NULL | Identificador interno del vendedor. Se genera automáticamente. |
| `id_tipo_documento` | INTEGER | NOT NULL, FK a `tipo_documento.id_tipo_documento` | Tipo de documento del vendedor. |
| `documento` | BIGINT | NOT NULL, UNIQUE | Número de documento del vendedor. No puede repetirse. |
| `nombre_vendedor` | VARCHAR(50) | NOT NULL | Nombre del vendedor. |
| `apellido_vendedor` | VARCHAR(50) | NOT NULL | Apellido del vendedor. |
| `telefono` | VARCHAR(15) | Permite NULL | Teléfono de contacto. Es opcional. |
| `email` | VARCHAR(100) | UNIQUE, permite NULL | Correo opcional. Los valores registrados no pueden repetirse. |

## 4. Tabla `categorias`

Guarda las categorías en las que se clasifican los productos.

| Campo | Tipo declarado | Restricciones | Descripción |
|---|---|---|---|
| `id_categoria` | SERIAL | PK, NOT NULL | Identificador de la categoría. Se genera automáticamente. |
| `nombre_categoria` | VARCHAR(50) | NOT NULL, UNIQUE | Nombre de la categoría. No puede repetirse. |

## 5. Tabla `productos`

Guarda los productos que se venden, con su precio y su categoría.

| Campo | Tipo declarado | Restricciones | Descripción |
|---|---|---|---|
| `id_producto` | SERIAL | PK, NOT NULL | Identificador del producto. Se genera automáticamente. |
| `nombre_producto` | VARCHAR(100) | NOT NULL, UNIQUE | Nombre del producto. No puede repetirse. |
| `precio_venta` | NUMERIC(10,2) | NOT NULL | Precio de venta del producto, en pesos colombianos. |
| `id_categoria` | INTEGER | NOT NULL, FK a `categorias.id_categoria` | Categoría a la que pertenece el producto. |

## 6. Tabla `insumos`

Guarda los materiales que se usan en la cafetería (por ejemplo, ingredientes o suministros) y sus existencias. Es un inventario aparte del de productos: no está relacionada con `productos` ni con `pedidos`.

| Campo | Tipo declarado | Restricciones | Descripción |
|---|---|---|---|
| `id_insumo` | SERIAL | PK, NOT NULL | Identificador del insumo. Se genera automáticamente. |
| `nombre_insumo` | VARCHAR(100) | NOT NULL, UNIQUE | Nombre del insumo. No puede repetirse. |
| `unidad_medida` | VARCHAR(20) | NOT NULL | Unidad en que se mide el insumo, por ejemplo kg, litros o unidades. |
| `stock_actual` | NUMERIC(10,2) | NOT NULL, DEFAULT 0.00 | Existencias actuales del insumo, en su unidad de medida. |

El stock se actualiza desde la aplicación; no hay triggers en la base de datos.

## 7. Tabla `pedidos`

Guarda el número, la fecha, el cliente y el vendedor de cada pedido. Los artículos del pedido se guardan en `detalle_pedidos`.

| Campo | Tipo declarado | Restricciones | Descripción |
|---|---|---|---|
| `id_pedido` | SERIAL | PK, NOT NULL | Identificador del pedido. Se genera automáticamente. |
| `fecha_compra` | TIMESTAMP WITHOUT TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Fecha y hora en que se registra el pedido. |
| `id_cliente` | INTEGER | NOT NULL, FK a `clientes.id_cliente` | Cliente que hace el pedido. |
| `id_vendedor` | INTEGER | NOT NULL, FK a `vendedores.id_vendedor` | Vendedor que atiende el pedido. |

No se puede generar un pedido sin cliente ni sin vendedor. El total del pedido se calcula sumando `cantidad × precio_unitario` de sus artículos.

## 8. Tabla `detalle_pedidos`

Guarda cada artículo de un pedido, con su cantidad y su precio.

| Campo | Tipo declarado | Restricciones | Descripción |
|---|---|---|---|
| `id_detalle` | SERIAL | PK, NOT NULL | Identificador del artículo dentro del pedido. Se genera automáticamente. |
| `id_pedido` | INTEGER | NOT NULL, FK a `pedidos.id_pedido` | Pedido al que pertenece el artículo. |
| `id_producto` | INTEGER | NOT NULL, FK a `productos.id_producto` | Producto pedido. |
| `cantidad` | INTEGER | NOT NULL, CHECK: mayor que 0 | Cantidad de unidades pedidas. |
| `precio_unitario` | NUMERIC(10,2) | NOT NULL | Precio de cada unidad en este pedido, en pesos colombianos. |

## Relaciones

| Tabla principal | Tabla relacionada | Relación |
|---|---|---|
| `tipo_documento` | `clientes` | Un tipo de documento puede usarse en varios clientes; cada cliente tiene un tipo de documento. |
| `tipo_documento` | `vendedores` | Un tipo de documento puede usarse en varios vendedores; cada vendedor tiene un tipo de documento. |
| `categorias` | `productos` | Una categoría puede tener varios productos; cada producto pertenece a una categoría. |
| `clientes` | `pedidos` | Un cliente puede tener varios pedidos; cada pedido pertenece a un cliente. |
| `vendedores` | `pedidos` | Un vendedor puede atender varios pedidos; cada pedido tiene un vendedor. |
| `pedidos` | `detalle_pedidos` | Un pedido puede tener varios artículos; cada detalle pertenece a un pedido. |
| `productos` | `detalle_pedidos` | Un producto puede aparecer en varios detalles de pedidos. |

Al borrar un registro, la base de datos actúa así:

- **`ON DELETE RESTRICT`:** no se puede borrar un registro si otros dependen de él. Por ejemplo, un cliente con pedidos, una categoría con productos o un tipo de documento en uso no se pueden eliminar.
- **`ON DELETE CASCADE`:** al borrar un pedido se borran también sus artículos en `detalle_pedidos`.

## Reglas que comprobamos desde la aplicación

Además de las restricciones de PostgreSQL, el archivo `validators.py` comprueba que los datos del formulario sean válidos antes de guardarlos:

| Validación | Qué comprueba |
|---|---|
| `texto` | Que el campo no esté vacío (si es obligatorio) y que no supere la longitud máxima. |
| `entero` | Que el valor sea un número entero y esté dentro del mínimo y máximo permitidos. |
| `decimal` | Que el valor sea un número (acepta coma o punto como separador decimal) y cumpla el mínimo, el máximo o sea mayor que un valor dado. |
| `fecha` | Que el valor sea una fecha válida en formato ISO (`AAAA-MM-DD`). |
| `email` | Que el correo tenga `@` y un punto después de ella. El correo es opcional: si se deja vacío no se valida. |

Como la base de datos solo tiene un `CHECK` (`cantidad > 0` en `detalle_pedidos`), estas validaciones son la principal protección contra datos inválidos, como precios negativos o stock negativo.

El stock de `insumos` se actualiza desde la aplicación (Python). No usamos triggers.
