# Diseño Relacional y Justificación de Normalización (1FN, 2FN y 3FN)
**Proyecto:** Sistema de Administración de Cafetería (`admin_cafeteria_db`)  
**Motor de Base de Datos:** PostgreSQL  
**Integrantes:** María Luisa Rojas Vargas y Oscar Andrés Horta Bonilla  
---

## 1. Introducción y Estructura General del Esquema

El modelo de datos de `admin_cafeteria_db` está compuesto por **8 tablas relacionales** diseñadas para garantizar la integridad referencial, eliminar la redundancia de datos y evitar anomalías de inserción, actualización y eliminación en las operaciones diarias de la cafetería (gestión de catálogo, inventario de insumos, clientes, vendedores y facturación de pedidos):

1. **`tipo_documento`** (`id_tipo_documento`, `sigla`, `descripcion`)
2. **`categorias`** (`id_categoria`, `nombre_categoria`)
3. **`clientes`** (`id_cliente`, `id_tipo_documento`, `documento`, `nombre_cliente`, `apellido_cliente`, `telefono`, `email`,`fecha_registro`)
4. **`vendedores`** (`id_vendedor`, `id_tipo_documento`, `documento`, `nombre_vendedor`, `apellido_vendedor`, `telefono`, `email`)
5. **`productos`** (`id_producto`, `id_categoria`, `nombre_producto`, `precio_venta`)
6. **`insumos`** (`id_insumo`, `nombre_insumo`, `unidad_medida`, `stock_actual`)
7. **`pedidos`** (`id_pedido`, `id_cliente`, `id_vendedor`, `fecha_compra`)
8. **`detalle_pedidos`** (`id_detalle`, `id_pedido`, `id_producto`, `cantidad`, `precio_unitario`)

---

## 2. Primera Forma Normal (1FN) — Atomicidad e Identificación Única

### Criterio teórico
Una relación se encuentra en **1FN** si y solo si:
1. Todos sus atributos contienen únicamente **valores atómicos e indivisibles** (no existen listas, arreglos ni valores multivaluados dentro de una misma celda).
2. No existen **grupos repetitivos** de columnas (por ejemplo: `producto_1`, `producto_2`, `cantidad_1`, `cantidad_2`).
3. Cada tabla posee una **llave primaria (`PRIMARY KEY`)** que identifica de manera única cada tupla (registro).

### Justificación en `admin_cafeteria_db`
* **Llaves primarias definidas:** Todas las entidades cuentan con un identificador único autoincremental (`SERIAL` / `IDENTITY`) como llave primaria (`id_tipo_documento`, `id_categoria`, `id_cliente`, `id_vendedor`, `id_producto`, `id_insumo`, `id_pedido`, `id_detalle`), impidiendo tuplas duplicadas.
* **Descomposición de atributos compuestos:** En `clientes` y `vendedores`, los nombres completos se dividieron en atributos atómicos independientes (`nombre_cliente` / `apellido_cliente` y `nombre_vendedor` / `apellido_vendedor`), facilitando búsquedas, ordenamientos y validaciones sin necesidad de parsear cadenas de texto.
* **Eliminación de grupos repetitivos en pedidos:** Un pedido puede incluir múltiples productos en distintas cantidades. En lugar de almacenar listas separadas por comas en `pedidos` o crear columnas fijas (`item_1`, `item_2`), los ítems se extrajeron a la entidad **`detalle_pedidos`**, donde cada fila representa exactamente un producto dentro de un pedido.

---

## 3. Segunda Forma Normal (2FN) — Dependencia Funcional Completa

### Criterio teórico
Una relación se encuentra en **2FN** si:
1. Cumple con todas las reglas de la **1FN**.
2. Todo atributo que no forma parte de la llave primaria depende **funcionalmente de forma completa** de toda la llave primaria (y de cualquier llave candidata), eliminando cualquier **dependencia parcial**.

### Justificación en `admin_cafeteria_db`
* **Tablas con llave primaria simple (`tipo_documento`, `categorias`, `clientes`, `vendedores`, `productos`, `insumos`, `pedidos`):**
  Al contar con una llave primaria compuesta por un único atributo (`id_*`), no es posible que exista dependencia parcial respecto a la llave primaria. Cada columna no clave describe exclusivamente a la instancia identificada por su `id`:
  * En `productos`, `nombre_producto`, `precio_venta` y `id_categoria` dependen únicamente de `id_producto`.
  * En `insumos`, `nombre_insumo`, `unidad_medida` y `stock_actual` dependen únicamente de `id_insumo`.
  * En `pedidos`, `fecha_compra`, `id_cliente` e `id_vendedor` dependen exclusivamente de `id_pedido`.
* **Resolución de relación muchos a muchos (`detalle_pedidos`):**
  La relación lógica entre `pedidos` y `productos` es de muchos a muchos ($N:M$). En `detalle_pedidos`, la combinación `(id_pedido, id_producto)` actúa como llave candidata natural (respaldada por el identificador subrogado `id_detalle`):
  * Los atributos `cantidad`, `precio_unitario` y `subtotal` dependen funcionalmente de la **combinación completa** `(id_pedido, id_producto)`.
  * La `cantidad` no depende solo del producto ni solo del pedido, sino de ese producto específico dentro de ese pedido específico. Asimismo, el nombre del producto o su categoría no se almacenan en `detalle_pedidos` (ya que dependerían parcialmente solo de `id_producto`), sino que permanecen en `productos`.

---

## 4. Tercera Forma Normal (3FN) — Eliminación de Dependencias Transitivas

### Criterio teórico
Una relación se encuentra en **3FN** si:
1. Cumple con todas las reglas de la **2FN**.
2. Ningún atributo no clave depende **transitivamente** de la llave primaria a través de otro atributo no clave ($A \rightarrow B \rightarrow C$, donde $B$ no es llave).

### Justificación en `admin_cafeteria_db`
Para evitar redundancia de datos y anomalías de actualización, toda entidad catálogo o maestra fue aislada en su propia tabla y vinculada mediante llaves foráneas (`FOREIGN KEY`):

1. **Separación de `tipo_documento` respecto a `clientes` y `vendedores`:**
   * *Problema evitado:* Si `sigla` (`CC`, `TI`, `CE`) y `descripcion` (`Cédula de Ciudadanía`, etc.) se guardaran directamente en `clientes` y `vendedores`, existiría la dependencia transitiva `id_cliente → sigla → descripcion`. Modificar la descripción de un tipo de documento obligaría a actualizar cientos de filas y podría generar inconsistencias tipográficas.
   * *Solución aplicada:* Se creó el catálogo **`tipo_documento`** y se referenció mediante la llave foránea `id_tipo_documento` en `clientes` y `vendedores`.

2. **Separación de `categorias` respecto a `productos`:**
   * *Problema evitado:* Almacenar el texto `nombre_categoria` directamente en `productos` generaría repetición constante (ej. `"Bebidas Calientes"` repetido en decenas de productos) y anomalías de borrado (al eliminar el último producto de una categoría, desaparecería la categoría del sistema).
   * *Solución aplicada:* Se extrajo **`categorias`** como tabla independiente y se vinculó en `productos` mediante `id_categoria`.

3. **Desacoplamiento de datos maestros en `pedidos`:**
   * *Problema evitado:* Guardar el nombre, teléfono o documento del cliente o del vendedor dentro de la tabla `pedidos` crearía dependencias transitivas (`id_pedido → id_cliente → nombre_cliente`) y duplicaría información personal en cada compra.
   * *Solución aplicada:* `pedidos` almacena únicamente las llaves foráneas **`id_cliente`** e **`id_vendedor`**, delegando los datos descriptivos a sus respectivas tablas maestras.

4. **Integridad histórica en `detalle_pedidos` (`precio_unitario`):**
   * En `detalle_pedidos` se registra el `precio_unitario` al momento de la venta. Este atributo **no representa una redundancia ni una violación de 3FN**, ya que modela el *precio histórico de la transacción* (que depende de la combinación pedido-producto en el instante de compra) y no el precio vigente del catálogo en `productos`, garantizando que futuras actualizaciones de precios no alteren la contabilidad de pedidos pasados.

---

## 5. Resumen de Cumplimiento por Tabla

| Tabla | Llave Primaria (PK) | Llaves Foráneas (FK) | Nivel Alcanzado | Justificación Principal |
| :--- | :--- | :--- | :---: | :--- |
| **`tipo_documento`** | `id_tipo_documento` | — | **3FN** | Catálogo atómico sin dependencias transitivas. |
| **`categorias`** | `id_categoria` | — | **3FN** | Catálogo independiente para clasificación de productos. |
| **`clientes`** | `id_cliente` | `id_tipo_documento` | **3FN** | Nombres/apellidos atómicos; tipo de documento normalizado. |
| **`vendedores`** | `id_vendedor` | `id_tipo_documento` | **3FN** | Nombres/apellidos atómicos; tipo de documento normalizado. |
| **`productos`** | `id_producto` | `id_categoria` | **3FN** | Atributos propios del producto; categoría extraída a catálogo. |
| **`insumos`** | `id_insumo` | — | **3FN** | Unidad de medida y stock atómicos dependientes solo del insumo. |
| **`pedidos`** | `id_pedido` | `id_cliente`, `id_vendedor` | **3FN** | Sin datos duplicados de cliente/vendedor; ítems delegados a detalle. |
| **`detalle_pedidos`** | `id_detalle` | `id_pedido`, `id_producto` | **3FN** | Resuelve relación $N:M$; `cantidad` y `precio_unitario` dependen de pedido + producto. |