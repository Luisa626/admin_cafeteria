-- ===========================================
-- Base de datos: admin_cafeteria_db
-- script creacion de tablas
-- ===========================================

CREATE DATABASE admin_cafeteria_db;

-- \c admin_cafeteria_db

DROP TABLE IF EXISTS detalle_pedidos CASCADE; 
DROP TABLE IF EXISTS pedidos CASCADE;
DROP TABLE IF EXISTS productos CASCADE;
DROP TABLE IF EXISTS categorias CASCADE;
DROP TABLE IF EXISTS insumos CASCADE;
DROP TABLE IF EXISTS clientes CASCADE;
DROP TABLE IF EXISTS vendedores CASCADE;
DROP TABLE IF EXISTS tipo_documento CASCADE;

-- ====================================
-- TABLAS
-- ====================================

-- 1. Tabla Tipo de Documento
CREATE TABLE IF NOT EXISTS public.tipo_documento (
    id_tipo_documento serial NOT NULL,
    sigla character varying(5) NOT NULL,
    descripcion character varying(50) NOT NULL,
    CONSTRAINT tipo_documento_pkey PRIMARY KEY (id_tipo_documento),
    CONSTRAINT tipo_documento_descripcion_key UNIQUE (descripcion),
    CONSTRAINT tipo_documento_sigla_key UNIQUE (sigla)
);

-- 2. Tabla Clientes
CREATE TABLE IF NOT EXISTS public.clientes (
    id_cliente serial NOT NULL,
    id_tipo_documento integer NOT NULL,
    documento bigint NOT NULL,
    nombre_cliente character varying(50) NOT NULL,
    apellido_cliente character varying(50) NOT NULL,
    telefono character varying(15),
    email character varying(100),
    fecha_registro timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT clientes_pkey PRIMARY KEY (id_cliente),
    CONSTRAINT clientes_documento_key UNIQUE (documento),
    CONSTRAINT clientes_email_key UNIQUE (email)
);

-- 3. Tabla Vendedores
CREATE TABLE IF NOT EXISTS public.vendedores (
    id_vendedor serial NOT NULL,
    id_tipo_documento integer NOT NULL,
    documento bigint NOT NULL,
    nombre_vendedor character varying(50) NOT NULL,
    apellido_vendedor character varying(50) NOT NULL,
    telefono character varying(15),
    email character varying(100),
    CONSTRAINT vendedores_pkey PRIMARY KEY (id_vendedor),
    CONSTRAINT vendedores_documento_key UNIQUE (documento),
    CONSTRAINT vendedores_email_key UNIQUE (email)
);

-- 4. Tabla Categorias
CREATE TABLE IF NOT EXISTS public.categorias (
    id_categoria serial NOT NULL,
    nombre_categoria character varying(50) NOT NULL,
    CONSTRAINT categorias_pkey PRIMARY KEY (id_categoria),
    CONSTRAINT categorias_nombre_categoria_key UNIQUE (nombre_categoria)
);

-- 5. Tabla Productos
CREATE TABLE IF NOT EXISTS public.productos (
    id_producto serial NOT NULL,
    nombre_producto character varying(100) NOT NULL,
    precio_venta numeric(10, 2) NOT NULL,
    id_categoria integer NOT NULL,
    CONSTRAINT productos_pkey PRIMARY KEY (id_producto),
    CONSTRAINT productos_nombre_producto_key UNIQUE (nombre_producto)
);

-- 6. Tabla Insumos
CREATE TABLE IF NOT EXISTS public.insumos (
    id_insumo serial NOT NULL,
    nombre_insumo character varying(100) NOT NULL,
    unidad_medida character varying(20) NOT NULL,
    stock_actual numeric(10, 2) NOT NULL DEFAULT 0.00,
    CONSTRAINT insumos_pkey PRIMARY KEY (id_insumo),
    CONSTRAINT insumos_nombre_insumo_key UNIQUE (nombre_insumo)
);

-- 7. Tabla Pedidos
CREATE TABLE IF NOT EXISTS public.pedidos (
    id_pedido serial NOT NULL,
    fecha_compra timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_cliente integer NOT NULL,
    id_vendedor integer NOT NULL,
    CONSTRAINT pedidos_pkey PRIMARY KEY (id_pedido)
);

-- 8. Tabla Detalle de Pedidos
CREATE TABLE IF NOT EXISTS public.detalle_pedidos (
    id_detalle serial NOT NULL,
    id_pedido integer NOT NULL,
    id_producto integer NOT NULL,
    cantidad integer NOT NULL,
    precio_unitario numeric(10, 2) NOT NULL,
    CONSTRAINT detalle_pedidos_pkey PRIMARY KEY (id_detalle)
);

ALTER TABLE IF EXISTS public.clientes
    ADD CONSTRAINT fk_clientes_tipo_doc FOREIGN KEY (id_tipo_documento)
    REFERENCES public.tipo_documento (id_tipo_documento) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE RESTRICT;


ALTER TABLE IF EXISTS public.detalle_pedidos
    ADD CONSTRAINT fk_detalle_pedidos_pedido FOREIGN KEY (id_pedido)
    REFERENCES public.pedidos (id_pedido) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;


ALTER TABLE IF EXISTS public.detalle_pedidos
    ADD CONSTRAINT fk_detalle_pedidos_producto FOREIGN KEY (id_producto)
    REFERENCES public.productos (id_producto) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE RESTRICT;


ALTER TABLE IF EXISTS public.pedidos
    ADD CONSTRAINT fk_pedidos_clientes FOREIGN KEY (id_cliente)
    REFERENCES public.clientes (id_cliente) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE RESTRICT;


ALTER TABLE IF EXISTS public.pedidos
    ADD CONSTRAINT fk_pedidos_vendedores FOREIGN KEY (id_vendedor)
    REFERENCES public.vendedores (id_vendedor) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE RESTRICT;


ALTER TABLE IF EXISTS public.productos
    ADD CONSTRAINT fk_productos_categoria FOREIGN KEY (id_categoria)
    REFERENCES public.categorias (id_categoria) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE RESTRICT;


ALTER TABLE IF EXISTS public.vendedores
    ADD CONSTRAINT fk_vendedores_tipo_doc FOREIGN KEY (id_tipo_documento)
    REFERENCES public.tipo_documento (id_tipo_documento) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE RESTRICT;

-- Relacion clientes-vendedroes -> tipo_documento
CREATE INDEX IF NOT EXISTS idx_clientes_tipo_doc ON public.clientes (id_tipo_documento);
CREATE INDEX IF NOT EXISTS idx_vendedores_tipo_doc ON public.vendedores (id_tipo_documento);
-- Relacion productos -> categorias
CREATE INDEX IF NOT EXISTS idx_productos_categoria ON public.productos (id_categoria);
-- Relaciones de la cabecera de pedidos
CREATE INDEX IF NOT EXISTS idx_pedidos_cliente ON public.pedidos (id_cliente);
CREATE INDEX IF NOT EXISTS idx_pedidos_vendedor ON public.pedidos (id_vendedor);
-- Relaciones del detalle de pedidos
CREATE INDEX IF NOT EXISTS idx_detalle_pedidos_pedido ON public.detalle_pedidos (id_pedido);
CREATE INDEX IF NOT EXISTS idx_detalle_pedidos_producto ON public.detalle_pedidos (id_producto);
-- Filtrar o consultar ventas por fecha/rango de fechas
CREATE INDEX IF NOT EXISTS idx_pedidos_fecha ON public.pedidos (fecha_compra);
