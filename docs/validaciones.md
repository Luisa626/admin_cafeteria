## Validación en el servidor y manejo de errores de BD

La aplicación implementa una estrategia de validación en dos niveles: validación preventiva de formularios en el servidor mediante el módulo `validators.py` antes de ejecutar cualquier sentencia SQL[cite: 10], y captura controlada de excepciones de PostgreSQL en `db.py` para garantizar la integridad transaccional y presentar mensajes comprensibles al usuario[cite: 11].

---

### 1. Funciones de validación disponibles (`validators.py`)

El módulo `validators.py` centraliza la sanitización (`.strip()`) y verificación de tipos, rangos y longitudes, acumulando los mensajes de error en una lista `errores`[cite: 10]:

| Función | Parámetros principales | Comportamiento y mensajes generados |
| :--- | :--- | :--- |
| **`texto`** | `obligatorio=True`, `max_len=None` | Verifica que el campo no esté vacío (`"El campo «{etiqueta}» es obligatorio."`) y que no exceda el límite de caracteres (`"«{etiqueta}» admite máximo {max_len} caracteres."`). Devuelve `None` si está vacío[cite: 10]. |
| **`entero`** | `minimo=None`, `maximo=None` | Valida presencia obligatoria, conversión a `int` (`"«{etiqueta}» debe ser un número entero."`) y límites inferior/superior (`minimo` / `maximo`)[cite: 10]. |
| **`decimal`** | `minimo=None`, `maximo=None`, `mayor_que=None` | Normaliza comas a puntos decimales, convierte a `Decimal` (`"«{etiqueta}» debe ser un número."`) y evalúa desigualdad estricta (`mayor_que`) o límites inclusivos (`minimo`, `maximo`)[cite: 10]. |
| **`fecha`** | `form`, `campo`, `etiqueta`, `errores` | Exige presencia y valida el formato estándar ISO `AAAA-MM-DD` mediante `date.fromisoformat()` (`"«{etiqueta}» debe ser una fecha válida."`)[cite: 10]. |
| **`email`** | `form`, `campo`, `etiqueta`, `errores` | Campo opcional; si contiene texto, verifica la presencia de `@` y de al menos un `.` en el dominio posterior (`"«{etiqueta}» no tiene un formato válido."`)[cite: 10]. |

---

### 2. Reglas de validación aplicadas por módulo

Cada ruta valida los datos entrantes contra las restricciones definidas en el esquema de `admin_cafeteria_db`[cite: 8, 10]:

| Módulo / Tabla | Campo | Validador aplicado | Regla y límite en el servidor |
| :--- | :--- | :--- | :--- |
| **`tipo_documento`** | `sigla` | `v.texto`[cite: 4, 10] | Obligatorio, máximo **5** caracteres (se normaliza a mayúsculas)[cite: 4, 8, 10]. |
| **`tipo_documento`** | `descripcion` | `v.texto`[cite: 4, 10] | Obligatorio, máximo **50** caracteres[cite: 4, 8, 10]. |
| **`categorias`** | `nombre_categoria` | `v.texto`[cite: 4, 10] | Obligatorio, máximo **50** caracteres[cite: 8, 10]. |
| **`clientes`** | `id_tipo_documento` | `v.entero`[cite: 10] | Obligatorio, entero positivo (`minimo=1`)[cite: 8, 10]. |
| **`clientes`** | `documento` | `v.entero`[cite: 10] | Obligatorio, entero positivo (`minimo=1`)[cite: 8, 10]. |
| **`clientes`** | `nombre_cliente` | `v.texto`[cite: 10] | Obligatorio, máximo **50** caracteres[cite: 8, 10]. |
| **`clientes`** | `apellido_cliente` | `v.texto`[cite: 10] | Obligatorio, máximo **50** caracteres[cite: 8, 10]. |
| **`clientes`** | `telefono` | `v.texto`[cite: 10] | Opcional (`obligatorio=False`), máximo **15** caracteres[cite: 8, 10]. |
| **`clientes`** | `email` | `v.texto` + `v.email`[cite: 10] | Opcional (`obligatorio=False`), máximo **100** caracteres y formato de correo válido[cite: 8, 10]. |
| **`vendedores`** | `id_tipo_documento` | `v.entero`[cite: 10] | Obligatorio, entero positivo (`minimo=1`)[cite: 8, 10]. |
| **`vendedores`** | `documento` | `v.entero`[cite: 10] | Obligatorio, entero positivo (`minimo=1`)[cite: 8, 10]. |
| **`vendedores`** | `nombre_vendedor` | `v.texto`[cite: 10] | Obligatorio, máximo **50** caracteres[cite: 8, 10]. |
| **`vendedores`** | `apellido_vendedor` | `v.texto`[cite: 10] | Obligatorio, máximo **50** caracteres[cite: 8, 10]. |
| **`vendedores`** | `telefono` | `v.texto`[cite: 10] | Opcional (`obligatorio=False`), máximo **15** caracteres[cite: 8, 10]. |
| **`vendedores`** | `email` | `v.texto` + `v.email`[cite: 10] | Opcional (`obligatorio=False`), máximo **100** caracteres y formato de correo válido[cite: 8, 10]. |
| **`productos`** | `nombre_producto` | `v.texto`[cite: 10] | Obligatorio, máximo **100** caracteres[cite: 8, 10]. |
| **`productos`** | `precio_venta` | `v.decimal`[cite: 10] | Obligatorio, valor numérico estrictamente mayor que cero (`mayor_que=0`)[cite: 8, 10]. |
| **`productos`** | `id_categoria` | `v.entero`[cite: 10] | Obligatorio, entero positivo (`minimo=1`)[cite: 8, 10]. |
| **`insumos`** | `nombre_insumo` | `v.texto`[cite: 10] | Obligatorio, máximo **100** caracteres[cite: 8, 10]. |
| **`insumos`** | `unidad_medida` | `v.texto`[cite: 10] | Obligatorio, máximo **20** caracteres[cite: 8, 10]. |
| **`insumos`** | `stock_actual` | `v.decimal`[cite: 10] | Obligatorio, valor numérico mayor o igual a cero (`minimo=0`)[cite: 8, 10]. |
| **`pedidos`** | `id_cliente` | `v.entero`[cite: 10] | Obligatorio, entero positivo (`minimo=1`)[cite: 8, 10]. |
| **`pedidos`** | `id_vendedor` | `v.entero`[cite: 10] | Obligatorio, entero positivo (`minimo=1`)[cite: 8, 10]. |
| **`pedidos`** | `fecha_compra` | `v.fecha`[cite: 10] | Fecha válida en formato ISO (`AAAA-MM-DD`)[cite: 8, 10]. |
| **`detalle_pedidos`** | `id_producto` | `v.entero`[cite: 10] | Obligatorio, entero positivo (`minimo=1`)[cite: 8, 10]. |
| **`detalle_pedidos`** | `cantidad` | `v.entero`[cite: 10] | Obligatorio, entero mayor o igual a `1` (`minimo=1`)[cite: 8, 10]. |

---

### 3. Gestión de transacciones y manejo de errores de BD (`db.py`)

El módulo `db.py` administra una conexión por petición HTTP mediante el contexto `g` de Flask (`get_db` / `close_db`) y protege la integridad de la base de datos ante fallos[cite: 11]:

1. **Rollback automático en `query()` y `execute()`:**
   Tanto las consultas de lectura (`query`) como las operaciones de escritura (`execute`) envuelven la ejecución del cursor en bloques `try ... except psycopg2.Error:`[cite: 11]. Si ocurre una excepción en PostgreSQL, se ejecuta inmediatamente `conn.rollback()` antes de relanzar el error (`DatabaseError`), evitando que la conexión quede bloqueada en estado de transacción abortada (`InFailedSqlTransaction`)[cite: 11].

2. **Traducción de códigos `SQLSTATE` mediante `error_message(exc)`:**
   Las rutas capturan `DatabaseError` y traducen el código `pgcode` y el detalle de la restricción en mensajes claros mostrados mediante `flash()`[cite: 3, 11]:

| Código `SQLSTATE` | Error de PostgreSQL | Restricción / Condición detectada | Mensaje presentado al usuario |
| :--- | :--- | :--- | :--- |
| **`23503`** | `ForeignKeyViolation` | Eliminación de registro con dependencias (`ON DELETE RESTRICT`) o FK inexistente[cite: 8, 11]. | *"No se puede completar la operación: el registro está relacionado con otros datos (por ejemplo, tiene ventas o productos asociados)."*[cite: 11] |
| **`23505`** | `UniqueViolation` | `clientes_documento_key`[cite: 11] | *"Ya existe un cliente registrado con ese número de documento."*[cite: 11] |
| **`23505`** | `UniqueViolation` | `vendedores_documento_key`[cite: 11] | *"Ya existe un vendedor registrado con ese número de documento."*[cite: 11] |
| **`23505`** | `UniqueViolation` | `tipos_documento_sigla_key` / `descripcion_key`[cite: 11] | *"Ya existe un tipo de documento con esa sigla / descripción."*[cite: 11] |
| **`23505`** | `UniqueViolation` | Otras llaves únicas (`email`, `nombre_categoria`, `nombre_producto`, `nombre_insumo`)[cite: 8, 11]. | *"Ya existe un registro con esos datos."*[cite: 11] |
| **`22003`** | `NumericValueOutOfRange` | Desbordamiento de entero de 32 bits (`INTEGER`)[cite: 11]. | *"El valor ingresado es demasiado grande (debe ser menor o igual a 2147483647)."*[cite: 11] |
| **`23514`** | `CheckViolation` | Incumplimiento de cláusula `CHECK` (ej. `cantidad > 0` en `detalle_pedidos`)[cite: 8, 11]. | *"Algún valor está fuera del rango permitido por la base de datos."*[cite: 11] |
| **`23502`** | `NotNullViolation` | Inserción de `NULL` en columna definida como `NOT NULL`[cite: 8, 11]. | *"Falta un campo obligatorio."*[cite: 11] |