-- ============================================================
--  BASE DE DATOS - PostgreSQL (EXACTAMENTE TU MISMA ESTRUCTURA)
--  Con ENUM, roles, igual que tu MySQL
-- ============================================================

-- Eliminar tablas si existen
DROP TABLE IF EXISTS carrito_temp CASCADE;
DROP TABLE IF EXISTS pedido_items CASCADE;
DROP TABLE IF EXISTS pedidos CASCADE;
DROP TABLE IF EXISTS productos CASCADE;
DROP TABLE IF EXISTS solicitudes_empresa CASCADE;
DROP TABLE IF EXISTS empresa CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

-- ============================================================
-- 1. USUARIOS (con ENUM igual a tu MySQL)
-- ============================================================
CREATE TABLE usuarios (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(120) NOT NULL,
    correo          VARCHAR(180) NOT NULL UNIQUE,
    contrasena_hash VARCHAR(255) NOT NULL,
    direcciones     JSONB DEFAULT NULL,
    foto_url        VARCHAR(500) DEFAULT NULL,
    telefono        VARCHAR(20) DEFAULT NULL,
    -- ENUM exactamente como en tu MySQL
    rol             VARCHAR(20) NOT NULL CHECK (rol IN ('cliente', 'administrador', 'socio')) DEFAULT 'cliente',
    empresa_id      INTEGER DEFAULT NULL,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. EMPRESA (con ENUM igual a tu MySQL)
-- ============================================================
CREATE TABLE empresa (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(150) NOT NULL,
    direccion       TEXT NOT NULL,
    -- JSON para metodo_pago igual que en MySQL
    metodo_pago     JSONB DEFAULT NULL,
    -- JSON para horario igual que en MySQL
    horario         JSONB DEFAULT NULL,
    latitud         DECIMAL(9,6) DEFAULT NULL,
    longitud        DECIMAL(9,6) DEFAULT NULL,
    telefono        VARCHAR(20) DEFAULT NULL,
    -- ENUM exactamente como en tu MySQL
    tipo_producto   VARCHAR(20) NOT NULL CHECK (tipo_producto IN ('alimentos', 'ropa', 'tecnologia', 'farmacia', 'servicios', 'otro')) DEFAULT 'otro',
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3. PRODUCTOS (igual a tu estructura)
-- ============================================================
CREATE TABLE productos (
    id                  SERIAL PRIMARY KEY,
    empresa_id          INTEGER NOT NULL,
    nombre              VARCHAR(200) NOT NULL,
    precio              DECIMAL(10,2) NOT NULL,
    categoria           VARCHAR(80) NOT NULL,
    imagen_url          VARCHAR(500) DEFAULT NULL,
    cantidad_stock      INTEGER NOT NULL DEFAULT 0,
    cantidad_vendidos   INTEGER NOT NULL DEFAULT 0,
    activo              BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_productos_empresa 
        FOREIGN KEY (empresa_id) 
        REFERENCES empresa(id) 
        ON DELETE RESTRICT
);

-- ============================================================
-- 4. SOLICITUDES_EMPRESA (igual a tu estructura)
-- ============================================================
CREATE TABLE solicitudes_empresa (
    id              SERIAL PRIMARY KEY,
    nombre_negocio  VARCHAR(150) NOT NULL,
    propietario     VARCHAR(120) NOT NULL,
    email           VARCHAR(180) NOT NULL,
    telefono        VARCHAR(20) NOT NULL,
    ciudad          VARCHAR(100) NOT NULL,
    direccion       TEXT,
    descripcion     TEXT,
    categorias      JSONB DEFAULT NULL,
    -- ENUM para estado igual que en MySQL
    estado          VARCHAR(20) NOT NULL CHECK (estado IN ('pendiente', 'aprobada', 'rechazada')) DEFAULT 'pendiente',
    creado_en       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 5. PEDIDOS (con ENUM igual a tu MySQL)
-- ============================================================
CREATE TABLE pedidos (
    id                  SERIAL PRIMARY KEY,
    usuario_id          INTEGER NOT NULL,
    fecha               TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total               DECIMAL(10,2) NOT NULL,
    -- ENUM exactamente como en tu MySQL
    estado              VARCHAR(20) NOT NULL CHECK (estado IN ('pendiente', 'en_camino', 'entregado', 'cambio_solicitado', 'cancelado')) DEFAULT 'pendiente',
    direccion_entrega   JSONB NOT NULL,
    notas               TEXT DEFAULT NULL,
    actualizado_en      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_pedidos_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE RESTRICT
);

-- ============================================================
-- 6. PEDIDO_ITEMS (igual a tu estructura)
-- ============================================================
CREATE TABLE pedido_items (
    pedido_id       INTEGER NOT NULL,
    producto_id     INTEGER NOT NULL,
    cantidad        INTEGER NOT NULL DEFAULT 1,
    precio_unitario DECIMAL(10,2) NOT NULL,
    
    PRIMARY KEY (pedido_id, producto_id),
    
    CONSTRAINT fk_items_pedido
        FOREIGN KEY (pedido_id)
        REFERENCES pedidos(id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_items_producto
        FOREIGN KEY (producto_id)
        REFERENCES productos(id)
        ON DELETE RESTRICT
);

-- ============================================================
-- 7. CARRITO_TEMP (igual a tu estructura)
-- ============================================================
CREATE TABLE carrito_temp (
    id              SERIAL PRIMARY KEY,
    usuario_id      INTEGER DEFAULT NULL,
    session_id      VARCHAR(255) NOT NULL,
    producto_id     INTEGER NOT NULL,
    cantidad        INTEGER NOT NULL DEFAULT 1,
    creado_en       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_carrito_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_carrito_producto
        FOREIGN KEY (producto_id)
        REFERENCES productos(id)
        ON DELETE RESTRICT
);

-- ============================================================
-- ÍNDICES (para rendimiento)
-- ============================================================
CREATE INDEX idx_usuarios_correo ON usuarios(correo);
CREATE INDEX idx_usuarios_rol ON usuarios(rol);
CREATE INDEX idx_empresa_nombre ON empresa(nombre);
CREATE INDEX idx_empresa_tipo_producto ON empresa(tipo_producto);
CREATE INDEX idx_productos_empresa ON productos(empresa_id);
CREATE INDEX idx_productos_categoria ON productos(categoria);
CREATE INDEX idx_productos_precio ON productos(precio);
CREATE INDEX idx_pedidos_usuario ON pedidos(usuario_id);
CREATE INDEX idx_pedidos_estado ON pedidos(estado);
CREATE INDEX idx_pedidos_fecha ON pedidos(fecha);
CREATE INDEX idx_carrito_sesion ON carrito_temp(session_id);
CREATE INDEX idx_carrito_usuario ON carrito_temp(usuario_id);
CREATE INDEX idx_carrito_producto ON carrito_temp(producto_id);

-- ============================================================
-- DATOS DE PRUEBA (SOLO 1 ADMIN, 1 EMPRESA)
-- ============================================================

-- 1. UN SOLO ADMINISTRADOR (contraseña: admin123)
-- Hash SHA256 de 'admin123' = 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9
INSERT INTO usuarios (nombre, correo, contrasena_hash, rol) VALUES
('Jennifer Vannesa', 'balamvannesa72@gmail.com', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'administrador');

-- 2. SOCIO PROPIETARIO (contraseña: socio123)
INSERT INTO usuarios (nombre, correo, contrasena_hash, rol, empresa_id) VALUES
('Carlos López', 'socio@gmail.com', '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824', 'socio', 1);

-- 3. UNA SOLA EMPRESA - TECNOLÓGICA
INSERT INTO empresa (nombre, direccion, telefono, tipo_producto, latitud, longitud) VALUES
('TechStore', 'Av. Tecnológico 456, Ciudad de México', '5512345678', 'tecnologia', 19.432608, -99.133209);

-- 4. PRODUCTOS TECNOLÓGICOS
INSERT INTO productos (empresa_id, nombre, precio, categoria, imagen_url, cantidad_stock) VALUES
(1, 'Audífonos Bluetooth Pro', 899.00, 'Audio', 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop', 50),
(1, 'Teclado Mecánico RGB', 1299.00, 'Periféricos', 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400&h=400&fit=crop', 30),
(1, 'Mouse Gamer Pro', 599.00, 'Periféricos', 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400&h=400&fit=crop', 45),
(1, 'Laptop HP Pavilion', 15999.00, 'Computadoras', 'https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=400&h=400&fit=crop', 15),
(1, 'Monitor Samsung 24"', 3899.00, 'Monitores', 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=400&h=400&fit=crop', 20),
(1, 'Tablet Samsung Galaxy', 5299.00, 'Tablets', 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400&h=400&fit=crop', 25);