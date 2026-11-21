-- ============================================================================
-- SCRIPT DE CARGA INICIAL (SEED) — admin_cafeteria_db
-- Mínimo 10 registros por tabla respetando integridad referencial
-- ============================================================================

BEGIN;

-- 1. TIPO_DOCUMENTO (10 registros)
INSERT INTO tipo_documento (sigla, descripcion) VALUES
('CC',    'Cédula de Ciudadanía'),
('TI',    'Tarjeta de Identidad'),
('CE',    'Cédula de Extranjería'),
('NIT',   'Número de Identificación Tributaria'),
('PA',    'Pasaporte'),
('PPT',   'Permiso por Protección Temporal'),
('PEP',   'Permiso Especial de Permanencia'),
('RC',    'Registro Civil de Nacimiento'),
('DIE',   'Documento de Identificación Extranjero'),
('NUIP',  'Número Único de Identificación Personal');

-- 2. CATEGORIAS (10 registros)
INSERT INTO categorias (nombre_categoria) VALUES
('Bebidas Calientes'),
('Bebidas Frías'),
('Panadería'),
('Repostería y Pastelería'),
('Sándwiches y Wraps'),
('Desayunos'),
('Postres Fríos'),
('Jugos y Batidos'),
('Snacks y Mecato'),
('Café en Grano y Molido');

-- 3. INSUMOS (10 registros)
INSERT INTO insumos (nombre_insumo, unidad_medida, stock_actual) VALUES
('Café excelso molido',      'kg',  25.50),
('Leche entera',             'L',   40.00),
('Leche deslactosada',       'L',   30.00),
('Azúcar refinada',          'kg',  20.00),
('Panela pulverizada',       'kg',  15.00),
('Chocolate de mesa',        'kg',  12.50),
('Harina de trigo',          'kg',  35.00),
('Queso campesino',          'kg',  10.00),
('Vasos desechables 9 oz',   'und', 500.00),
('Servilletas de papel',     'und', 1000.00);

-- 4. CLIENTES (10 registros)
INSERT INTO clientes (id_tipo_documento, documento, nombre_cliente, apellido_cliente, telefono, email) VALUES
(1, 107521001, 'Carlos',    'Ramírez',   '3102001001', 'carlos.ramirez@correo.com'),
(1, 107521002, 'Laura',     'Gómez',     '3112001002', 'laura.gomez@correo.com'),
(1, 107521003, 'Andrés',    'Martínez',  '3122001003', 'andres.martinez@correo.com'),
(2, 107521004, 'Sofía',     'Hernández', '3132001004', 'sofia.hernandez@correo.com'),
(1, 107521005, 'Diego',     'López',     '3142001005', 'diego.lopez@correo.com'),
(3, 107521006, 'Valentina', 'Torres',    '3152001006', 'valentina.torres@correo.com'),
(1, 107521007, 'Mateo',     'Vargas',    '3162001007', 'mateo.vargas@correo.com'),
(4, 900123456, 'Inversiones Huila SAS', 'Comercial', '6088701008', 'compras@invhuila.com'),
(1, 107521009, 'Camila',    'Rojas',     '3182001009', 'camila.rojas@correo.com'),
(5, 107521010, 'Sebastián', 'Morales',   '3202001010', 'sebastian.morales@correo.com');

-- 5. VENDEDORES (10 registros)
INSERT INTO vendedores (id_tipo_documento, documento, nombre_vendedor, apellido_vendedor, telefono, email) VALUES
(1, 108110001, 'María',     'Rojas',     '3003002001', 'maria.rojas@miaucafe.com'),
(1, 108110002, 'Oscar',     'Horta',     '3003002002', 'oscar.horta@miaucafe.com'),
(1, 108110003, 'Daniela',   'Castro',    '3003002003', 'daniela.castro@miaucafe.com'),
(1, 108110004, 'Julián',    'Mendoza',   '3003002004', 'julian.mendoza@miaucafe.com'),
(1, 108110005, 'Paula',     'Ortiz',     '3003002005', 'paula.ortiz@miaucafe.com'),
(1, 108110006, 'Felipe',    'Suárez',    '3003002006', 'felipe.suarez@miaucafe.com'),
(1, 108110007, 'Natalia',   'Paredes',   '3003002007', 'natalia.paredes@miaucafe.com'),
(3, 108110008, 'Alejandro', 'Silva',     '3003002008', 'alejandro.silva@miaucafe.com'),
(1, 108110009, 'Tatiana',   'Ríos',      '3003002009', 'tatiana.rios@miaucafe.com'),
(1, 108110010, 'Cristian',  'Peña',      '3003002010', 'cristian.pena@miaucafe.com');

-- 6. PRODUCTOS (10 registros)
INSERT INTO productos (nombre_producto, precio_venta, id_categoria) VALUES
('Café Americano',          4500.00,  1),
('Capuchino Tradicional',   6500.00,  1),
('Latte Vainilla Frío',     7500.00,  2),
('Croissant de Mantequilla',5000.00,  3),
('Torta de Zanahoria',      7000.00,  4),
('Sándwich Jamón y Queso',  9500.00,  5),
('Huevos al Gusto con Pan', 11000.00, 6),
('Cheesecake de Maracuyá',  8500.00,  7),
('Jugo Natural en Leche',   6000.00,  8),
('Bolsa Café Origen 500g',  28000.00, 10);

-- 7. PEDIDOS (10 registros)
INSERT INTO pedidos (id_cliente, id_vendedor, fecha_compra) VALUES
(1,  1, '2026-11-10 08:15:00'),
(2,  2, '2026-11-10 09:30:00'),
(3,  3, '2026-11-11 10:05:00'),
(4,  1, '2026-11-11 15:20:00'),
(5,  4, '2026-11-12 08:45:00'),
(6,  2, '2026-11-12 16:10:00'),
(7,  5, '2026-11-13 11:00:00'),
(8,  6, '2026-11-14 09:15:00'),
(9,  7, '2026-11-15 17:30:00'),
(10, 8, '2026-11-16 14:40:00');

-- 8. DETALLE_PEDIDOS (12 registros vinculados a los 10 pedidos y 10 productos)
INSERT INTO detalle_pedidos (id_pedido, id_producto, cantidad, precio_unitario) VALUES
(1,  1, 2, 4500.00),
(1,  4, 1, 5000.00),
(2,  2, 1, 6500.00),
(3,  6, 2, 9500.00),
(4,  3, 1, 7500.00),
(4,  5, 1, 7000.00),
(5,  7, 2, 11000.00),
(6,  8, 1, 8500.00),
(7,  9, 2, 6000.00),
(8, 10, 3, 28000.00),
(9,  2, 2, 6500.00),
(10, 1, 1, 4500.00);

COMMIT;