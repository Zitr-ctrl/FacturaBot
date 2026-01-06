-- Schema de Base de Datos para FacturaBot
-- PostgreSQL 12+

-- Eliminar tablas si existen (para desarrollo)
DROP TABLE IF EXISTS detalles_factura CASCADE;
DROP TABLE IF EXISTS facturas CASCADE;
DROP TABLE IF EXISTS proveedores CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

-- Tabla de usuarios del sistema
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    ruc VARCHAR(13),
    empresa VARCHAR(300),
    plan VARCHAR(50) DEFAULT 'basico',
    activo BOOLEAN DEFAULT true,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_conexion TIMESTAMP
);

-- Tabla de proveedores (emisores de facturas)
CREATE TABLE proveedores (
    id SERIAL PRIMARY KEY,
    ruc VARCHAR(13) UNIQUE NOT NULL,
    razon_social VARCHAR(300) NOT NULL,
    nombre_comercial VARCHAR(300),
    direccion TEXT,
    telefono VARCHAR(50),
    email VARCHAR(200),
    categoria VARCHAR(100),
    notas TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para búsquedas rápidas por RUC
CREATE INDEX idx_proveedores_ruc ON proveedores(ruc);

-- Tabla principal de facturas
CREATE TABLE facturas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    proveedor_id INTEGER REFERENCES proveedores(id),
    
    -- Información del comprador
    ruc_comprador VARCHAR(13) NOT NULL,
    razon_social_comprador VARCHAR(300) NOT NULL,
    
    -- Datos de la factura
    numero_autorizacion VARCHAR(49) NOT NULL UNIQUE,
    numero_factura VARCHAR(17) NOT NULL,
    clave_acceso VARCHAR(49) NOT NULL,
    fecha_emision DATE NOT NULL,
    fecha_autorizacion TIMESTAMP,
    
    -- Totales financieros
    subtotal_sin_impuestos DECIMAL(12, 2) NOT NULL,
    subtotal_iva_0 DECIMAL(12, 2) DEFAULT 0,
    subtotal_iva_12 DECIMAL(12, 2) DEFAULT 0,
    iva DECIMAL(12, 2) NOT NULL,
    propina DECIMAL(12, 2) DEFAULT 0,
    total DECIMAL(12, 2) NOT NULL,
    
    -- Metadata
    ambiente VARCHAR(20),  -- PRODUCCION, PRUEBAS
    tipo_emision VARCHAR(20),  -- NORMAL, CONTINGENCIA
    
    -- Categorización y procesamiento
    categoria VARCHAR(100),  -- servicios, suministros, inventario, etc.
    subcategoria VARCHAR(100),
    mes_contable INTEGER,  -- 1-12
    anio_contable INTEGER,
    estado VARCHAR(50) DEFAULT 'pendiente',  -- pendiente, revisado, exportado
    
    -- Control
    ruta_archivo VARCHAR(500),
    procesada_automaticamente BOOLEAN DEFAULT true,
    fecha_procesamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_revision TIMESTAMP,
    revisado_por INTEGER REFERENCES usuarios(id),
    
    -- Auditoría
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_totales CHECK (total >= 0),
    CONSTRAINT chk_iva CHECK (iva >= 0),
    CONSTRAINT chk_fecha_emision CHECK (fecha_emision <= CURRENT_DATE)
);

-- Índices para optimizar consultas comunes
CREATE INDEX idx_facturas_usuario ON facturas(usuario_id);
CREATE INDEX idx_facturas_proveedor ON facturas(proveedor_id);
CREATE INDEX idx_facturas_fecha ON facturas(fecha_emision);
CREATE INDEX idx_facturas_periodo ON facturas(anio_contable, mes_contable);
CREATE INDEX idx_facturas_clave ON facturas(clave_acceso);
CREATE INDEX idx_facturas_estado ON facturas(estado);
CREATE INDEX idx_facturas_categoria ON facturas(categoria);

-- Tabla de detalles de factura (items/productos)
CREATE TABLE detalles_factura (
    id SERIAL PRIMARY KEY,
    factura_id INTEGER REFERENCES facturas(id) ON DELETE CASCADE,
    codigo_producto VARCHAR(50),
    descripcion TEXT NOT NULL,
    cantidad DECIMAL(10, 2) NOT NULL,
    precio_unitario DECIMAL(12, 4) NOT NULL,
    descuento DECIMAL(12, 2) DEFAULT 0,
    precio_total DECIMAL(12, 2) NOT NULL,
    
    CONSTRAINT chk_cantidad CHECK (cantidad > 0),
    CONSTRAINT chk_precio CHECK (precio_unitario >= 0)
);

-- Índice para consultas de detalles por factura
CREATE INDEX idx_detalles_factura ON detalles_factura(factura_id);

-- Vista para reportes mensuales
CREATE OR REPLACE VIEW reporte_mensual AS
SELECT 
    f.anio_contable,
    f.mes_contable,
    f.usuario_id,
    COUNT(*) as total_facturas,
    SUM(f.subtotal_sin_impuestos) as total_subtotal,
    SUM(f.iva) as total_iva,
    SUM(f.total) as total_general,
    f.categoria,
    COUNT(DISTINCT f.proveedor_id) as total_proveedores
FROM facturas f
GROUP BY 
    f.anio_contable, 
    f.mes_contable, 
    f.usuario_id,
    f.categoria;

-- Vista para análisis por proveedor
CREATE OR REPLACE VIEW analisis_proveedores AS
SELECT 
    p.id,
    p.ruc,
    p.razon_social,
    p.categoria,
    COUNT(f.id) as total_facturas,
    SUM(f.total) as monto_total,
    AVG(f.total) as promedio_factura,
    MAX(f.fecha_emision) as ultima_factura,
    MIN(f.fecha_emision) as primera_factura
FROM proveedores p
LEFT JOIN facturas f ON p.id = f.proveedor_id
GROUP BY p.id, p.ruc, p.razon_social, p.categoria;

-- Función para actualizar timestamp de actualización
CREATE OR REPLACE FUNCTION actualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para auto-actualizar timestamps
CREATE TRIGGER trigger_actualizar_facturas
BEFORE UPDATE ON facturas
FOR EACH ROW
EXECUTE FUNCTION actualizar_timestamp();

CREATE TRIGGER trigger_actualizar_proveedores
BEFORE UPDATE ON proveedores
FOR EACH ROW
EXECUTE FUNCTION actualizar_timestamp();

-- Función para auto-categorizar mes y año
CREATE OR REPLACE FUNCTION set_periodo_contable()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.mes_contable IS NULL THEN
        NEW.mes_contable = EXTRACT(MONTH FROM NEW.fecha_emision);
    END IF;
    
    IF NEW.anio_contable IS NULL THEN
        NEW.anio_contable = EXTRACT(YEAR FROM NEW.fecha_emision);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_periodo_contable
BEFORE INSERT OR UPDATE ON facturas
FOR EACH ROW
EXECUTE FUNCTION set_periodo_contable();

-- Datos de ejemplo para desarrollo
INSERT INTO usuarios (nombre, email, ruc, empresa) VALUES
('Admin FacturaBot', 'admin@facturabot.ec', '0912345678001', 'FacturaBot');

COMMENT ON TABLE facturas IS 'Facturas electrónicas procesadas del SRI';
COMMENT ON TABLE proveedores IS 'Catálogo de proveedores/emisores de facturas';
COMMENT ON TABLE detalles_factura IS 'Items/productos de cada factura';
COMMENT ON COLUMN facturas.clave_acceso IS 'Clave de acceso única de 49 dígitos del SRI';
COMMENT ON COLUMN facturas.estado IS 'Estado del procesamiento: pendiente, revisado, exportado';