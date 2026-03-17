-- ============================================================
--  BASE DE DATOS - SCHEMA COMPLETO
--  Motor: MySQL 8.0+
--  Charset: utf8mb4 | Collation: utf8mb4_unicode_ci
-- ============================================================

CREATE DATABASE IF NOT EXISTS LokalMarket
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE LokalMarket;

-- ============================================================
-- 1. USUARIOS (clientes, administradores, socios)
-- ============================================================
CREATE TABLE usuarios (
    id              INT             NOT NULL AUTO_INCREMENT,
    nombre          VARCHAR(120)    NOT NULL,
    correo          VARCHAR(180)    NOT NULL,
    contrasena_hash VARCHAR(255)    NOT NULL,
    -- Array de direcciones: [{ calle, ciudad, estado, cp, referencia }]
    direcciones     JSON            DEFAULT NULL,
    foto_url        VARCHAR(500)    DEFAULT NULL,
    rol             ENUM(
                        'cliente',
                        'administrador',
                        'socio'
                    )               NOT NULL DEFAULT 'cliente',
    activo          TINYINT(1)      NOT NULL DEFAULT 1,
    creado_en       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                    ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE  KEY uq_usuarios_correo (correo),
    INDEX   idx_usuarios_nombre    (nombre),
    INDEX   idx_usuarios_rol       (rol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 2. EMPRESA
-- ============================================================
CREATE TABLE empresa (
    id              INT             NOT NULL AUTO_INCREMENT,
    nombre          VARCHAR(150)    NOT NULL,
    direccion       TEXT            NOT NULL,
    -- Ej: ["efectivo","tarjeta","transferencia","QR"]
    metodo_pago     JSON            DEFAULT NULL,
    -- Ej: {"lunes":"9:00-18:00","sabado":"9:00-14:00","domingo":"cerrado"}
    horario         JSON            DEFAULT NULL,
    latitud         DECIMAL(9,6)    DEFAULT NULL,
    longitud        DECIMAL(9,6)    DEFAULT NULL,
    telefono        VARCHAR(20)     DEFAULT NULL,
    -- Campo indexado para el botón filtrar por tipo de producto
    tipo_producto   ENUM(
                        'alimentos',
                        'ropa',
                        'tecnologia',
                        'farmacia',
                        'servicios',
                        'otro'
                    )               NOT NULL DEFAULT 'otro',
    activo          TINYINT(1)      NOT NULL DEFAULT 1,
    creado_en       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                    ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    INDEX   idx_empresa_nombre        (nombre),
    INDEX   idx_empresa_tipo_producto (tipo_producto)   -- usado por el filtro
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 3. PRODUCTOS
-- ============================================================
CREATE TABLE productos (
    id                  INT             NOT NULL AUTO_INCREMENT,
    empresa_id          INT             NOT NULL,
    nombre              VARCHAR(200)    NOT NULL,
    precio              DECIMAL(10,2)   NOT NULL,
    categoria           VARCHAR(80)     NOT NULL,
    imagen_url          VARCHAR(500)    DEFAULT NULL,
    cantidad_stock      INT             NOT NULL DEFAULT 0,
    cantidad_vendidos   INT             NOT NULL DEFAULT 0,
    activo              TINYINT(1)      NOT NULL DEFAULT 1,
    creado_en           TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    INDEX   idx_productos_empresa_id  (empresa_id),
    INDEX   idx_productos_categoria   (categoria),
    INDEX   idx_productos_precio      (precio),
    FULLTEXT idx_productos_nombre     (nombre),

    CONSTRAINT fk_productos_empresa
        FOREIGN KEY (empresa_id)
        REFERENCES empresa (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 4. PEDIDOS
-- ============================================================
CREATE TABLE pedidos (
    id                  INT             NOT NULL AUTO_INCREMENT,
    usuario_id          INT             NOT NULL,
    fecha               TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total               DECIMAL(10,2)   NOT NULL,
    estado              ENUM(
                            'pendiente',
                            'en_camino',
                            'entregado',
                            'cambio_solicitado',
                            'cancelado'
                        )               NOT NULL DEFAULT 'pendiente',
    -- Snapshot de la dirección en el momento del pedido
    direccion_entrega   JSON            NOT NULL,
    notas               TEXT            DEFAULT NULL,
    actualizado_en      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    INDEX   idx_pedidos_usuario_id  (usuario_id),
    INDEX   idx_pedidos_estado      (estado),
    INDEX   idx_pedidos_fecha       (fecha),

    CONSTRAINT fk_pedidos_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 5. PEDIDO_ITEMS  (relación N:M  pedidos <-> productos)
-- ============================================================
CREATE TABLE pedido_items (
    pedido_id       INT             NOT NULL,
    producto_id     INT             NOT NULL,
    cantidad        INT             NOT NULL DEFAULT 1,
    -- Precio al momento de la compra (snapshot)
    precio_unitario DECIMAL(10,2)   NOT NULL,

    PRIMARY KEY (pedido_id, producto_id),

    CONSTRAINT fk_items_pedido
        FOREIGN KEY (pedido_id)
        REFERENCES pedidos (id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_items_producto
        FOREIGN KEY (producto_id)
        REFERENCES productos (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 6. CARRITO TEMPORAL (NUEVA TABLA - AGREGADA SIN MODIFICAR NADA)
-- ============================================================
CREATE TABLE carrito_temp (
    id              INT             NOT NULL AUTO_INCREMENT,
    usuario_id      INT             NULL,  -- NULL si el usuario no ha iniciado sesión
    session_id      VARCHAR(255)    NOT NULL, -- Para identificar usuarios sin cuenta
    producto_id     INT             NOT NULL,
    cantidad        INT             NOT NULL DEFAULT 1,
    creado_en       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en  TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP 
                                        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    INDEX idx_carrito_usuario (usuario_id),
    INDEX idx_carrito_sesion (session_id),
    INDEX idx_carrito_producto (producto_id),

    CONSTRAINT fk_carrito_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios (id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_carrito_producto
        FOREIGN KEY (producto_id)
        REFERENCES productos (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- DATOS DE PRUEBA (SIN CAMBIOS)
-- ============================================================

-- Usuarios
INSERT INTO usuarios (nombre, correo, contrasena_hash, rol) VALUES
('Ana García',     'ana@example.com',   '$2b$12$hash_ejemplo_1', 'cliente'),
('Luis Pérez',     'luis@example.com',  '$2b$12$hash_ejemplo_2', 'administrador'),
('María Socio',    'maria@example.com', '$2b$12$hash_ejemplo_3', 'socio');

-- Empresa
INSERT INTO empresa (nombre, direccion, telefono, tipo_producto, latitud, longitud) VALUES
('TechStore MTY',  'Av. Constitución 100, Monterrey, NL', '8112345678', 'tecnologia', 25.686614, -100.316113),
('Ropa Fina SA',   'Calle Morelos 55, CDMX',              '5512345678', 'ropa',       19.432608, -99.133209);

-- Productos
INSERT INTO productos (empresa_id, nombre, precio, categoria, cantidad_stock) VALUES
(1, 'Audífonos Bluetooth Pro', 899.00, 'Audio',    50),
(1, 'Teclado Mecánico RGB',    1299.00, 'Periféricos', 30),
(2, 'Playera Algodón Premium', 349.00, 'Camisetas', 100);

-- Pedido
INSERT INTO pedidos (usuario_id, total, estado, direccion_entrega) VALUES
(1, 1198.00, 'en_camino',
 '{"calle":"Hidalgo 22","ciudad":"Minatitlán","estado":"Veracruz","cp":"96700"}');

-- Items del pedido
INSERT INTO pedido_items (pedido_id, producto_id, cantidad, precio_unitario) VALUES
(1, 1, 1, 899.00),
(1, 2, 1, 1299.00);

-- ============================================================
-- DATOS DE PRUEBA PARA CARRITO (OPCIONAL)
-- ============================================================
-- Ejemplo de carrito para usuario 1 (Ana)
INSERT INTO carrito_temp (usuario_id, session_id, producto_id, cantidad) VALUES
(1, 'session_abc123', 1, 2),
(1, 'session_abc123', 3, 1);

-- Ejemplo de carrito para usuario sin sesión
INSERT INTO carrito_temp (session_id, producto_id, cantidad) VALUES
('session_guest_xyz789', 2, 1);