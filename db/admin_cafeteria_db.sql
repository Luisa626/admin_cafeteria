-- ===========================================
-- Base de datos: cafeteria_db
-- script creacion de tablas
-- ===========================================

-- CREATE DATABSE admin_cafeteria_db;
-- \c admin_cafeteria_db

DROP TABLE IF EXISTS detalle_pedidos;
DROP TABLE IF EXISTS pedidos;
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS categorias;
DROP TABLE IF EXISTS insumos;
DROP TABLE IF EXISTS clientes;
DROP TABLE IF EXISTS vendedores;
DROP TABLE IF EXISTS tipo_documento;

-- ====================================
-- TABLAS
-- ====================================

-- 1. Tabla Tipo de Documento
CREATE TABLE public.tipo_documento (
    id_tipo_documento SERIAL PRIMARY KEY,
    sigla CHARACTER VARYING(5) NOT NULL,
    descripcion CHARACTER VARYING(50) NOT NULL
);

-- 2. Tabla Clientes
CREATE TABLE public.clientes (
    id_cliente SERIAL PRIMARY KEY,
    id_tipo_documento INTEGER NOT NULL,
    documento INTEGER NOT NULL,
    nombre_cliente CHARACTER VARYING(50) NOT NULL,
    apellido_cliente CHARACTER VARYING(50) NOT NULL,
    telefono CHARACTER VARYING(15),
    email CHARACTER VARYING(100),
    fecha_registro TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_clientes_tipo_doc FOREIGN KEY (id_tipo_documento)
        REFERENCES public.tipo_documento (id_tipo_documento) ON DELETE RESTRICT
);

-- 3. Tabla Vendedores
CREATE TABLE public.vendedores (
    id_vendedor SERIAL PRIMARY KEY,
    id_tipo_documento INTEGER NOT NULL,
    documento INTEGER NOT NULL,
    nombre_vendedor CHARACTER VARYING(50) NOT NULL,
    apellido_vendedor CHARACTER VARYING(50) NOT NULL,
    telefono CHARACTER VARYING(15),
    email CHARACTER VARYING(100),
    CONSTRAINT fk_vendedores_tipo_doc FOREIGN KEY (id_tipo_documento)
        REFERENCES public.tipo_documento (id_tipo_documento) ON DELETE RESTRICT
);

-- 4. Tabla Categorias
CREATE TABLE public.categorias (
    id_categoria SERIAL PRIMARY KEY,
    nombre_categoria CHARACTER VARYING(50) NOT NULL UNIQUE
);

-- 5. Tabla Productos
CREATE TABLE public.productos (
    id_producto SERIAL PRIMARY KEY,
    nombre_producto CHARACTER VARYING(100) NOT NULL,
    precio_venta NUMERIC(10,2) NOT NULL,
    id_categoria INTEGER NOT NULL,
    CONSTRAINT fk_productos_categoria FOREIGN KEY (id_categoria)
        REFERENCES public.categorias (id_categoria) ON DELETE RESTRICT
);

-- 6. Tabla Insumos
CREATE TABLE public.insumos (
    id_insumo SERIAL PRIMARY KEY,
    nombre_insumo CHARACTER VARYING(100) NOT NULL,
    unidad_medida CHARACTER VARYING(20) NOT NULL,
    stock_actual NUMERIC(10,2) NOT NULL DEFAULT 0.00
);

-- 7. Tabla Pedidos
CREATE TABLE public.pedidos (
    id_pedido SERIAL PRIMARY KEY,
    fecha_compra TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    id_cliente INTEGER NOT NULL,
    id_vendedor INTEGER NOT NULL,
    CONSTRAINT fk_pedidos_clientes FOREIGN KEY (id_cliente)
        REFERENCES public.clientes (id_cliente) ON DELETE RESTRICT,
    CONSTRAINT fk_pedidos_vendedores FOREIGN KEY (id_vendedor)
        REFERENCES public.vendedores (id_vendedor) ON DELETE RESTRICT
);

-- 8. Tabla Detalle de Pedidos
CREATE TABLE public.detalle_pedidos (
    id_detalle SERIAL PRIMARY KEY,
    id_pedido INTEGER NOT NULL,
    id_producto INTEGER NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10,2) NOT NULL,
    CONSTRAINT fk_detalle_pedidos_pedido FOREIGN KEY (id_pedido)
        REFERENCES public.pedidos (id_pedido) ON DELETE CASCADE,
    CONSTRAINT fk_detalle_pedidos_producto FOREIGN KEY (id_producto)
        REFERENCES public.productos (id_producto) ON DELETE RESTRICT
);


-- Relacion clientes-vendedroes -> tipo_documento
CREATE INDEX idx_clientes_tipo_doc ON public.clientes (id_tipo_documento);
CREATE INDEX idx_vendedores_tipo_doc ON public.vendedores (id_tipo_documento);
-- Relacion productos -> categorias
CREATE INDEX idx_productos_categoria ON public.productos (id_categorias);
-- Relaciones de la cabecera de pedidos
CREATE INDEX idx_pedidos_cliente ON public.pedidos (id_cliente);
CREATE INDEX idx_pedidos_vendedor ON public.pedidos (id_vendedor);
-- Relaciones del detalle de pedidos
CREATE INDEX idx_detalle_pedidos_pedido ON public.detalle_pedidos (id_pedido);
CREATE INDEX idx_detalle_pedidos_producto ON public.detalle_pedidos (id_productos);
-- Filtrar o consultar ventas por fecha/rango de fechas
CREATE INDEX idx_pedidos_fecha ON public.pedidos (fecha_compra);
-- Buscar clientes o vendedores por su numero de documento en el sistema
CREATE INDEX idx_clientes_documento ON public.clientes (documento);
CREATE INDEX idx_vendedores_documento ON public.vendedores (documento);