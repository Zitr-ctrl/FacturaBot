"""
Módulo de conexión y operaciones con PostgreSQL
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import List, Dict, Optional, Any
from datetime import datetime
import config
from ..models.invoice import Factura


class DatabaseManager:
    """Gestor de base de datos PostgreSQL"""
    
    def __init__(self):
        self.connection_params = {
            'host': config.Config.DB_HOST,
            'port': config.Config.DB_PORT,
            'database': config.Config.DB_NAME,
            'user': config.Config.DB_USER,
            'password': config.Config.DB_PASSWORD
        }
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexiones a la BD"""
        conn = psycopg2.connect(**self.connection_params)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @contextmanager
    def get_cursor(self, dict_cursor=True):
        """Context manager para cursores"""
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()
    
    def test_connection(self) -> bool:
        """Prueba la conexión a la base de datos"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute('SELECT 1')
                return True
        except Exception as e:
            print(f"Error de conexión: {e}")
            return False
    
    def insertar_factura(self, factura: Factura, usuario_id: int = 1, 
                        categoria: str = None) -> int:
        """
        Inserta una factura en la base de datos
        
        Returns:
            ID de la factura insertada
        """
        # Primero, verificar/crear proveedor
        proveedor_id = self._obtener_o_crear_proveedor(
            factura.ruc_emisor,
            factura.razon_social_emisor,
            factura.nombre_comercial_emisor,
            factura.direccion_emisor
        )
        
        # Insertar factura
        query = """
        INSERT INTO facturas (
            usuario_id, proveedor_id,
            ruc_comprador, razon_social_comprador,
            numero_autorizacion, numero_factura, clave_acceso,
            fecha_emision, fecha_autorizacion,
            subtotal_sin_impuestos, subtotal_iva_0, subtotal_iva_12,
            iva, propina, total,
            ambiente, tipo_emision,
            categoria, estado
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, (
                usuario_id, proveedor_id,
                factura.ruc_comprador, factura.razon_social_comprador,
                factura.numero_autorizacion, factura.numero_factura, 
                factura.clave_acceso,
                factura.fecha_emision, factura.fecha_autorizacion,
                factura.subtotal_sin_impuestos, factura.subtotal_iva_0, 
                factura.subtotal_iva_12,
                factura.iva, factura.propina, factura.total,
                factura.ambiente, factura.tipo_emision,
                categoria, 'pendiente'
            ))
            
            factura_id = cursor.fetchone()['id']
            
            # Insertar detalles
            if factura.detalles:
                self._insertar_detalles(cursor, factura_id, factura.detalles)
            
            return factura_id
    
    def _obtener_o_crear_proveedor(self, ruc: str, razon_social: str,
                                   nombre_comercial: str = None,
                                   direccion: str = None) -> int:
        """Busca o crea un proveedor, retorna su ID"""
        
        with self.get_cursor() as cursor:
            # Buscar proveedor existente
            cursor.execute(
                "SELECT id FROM proveedores WHERE ruc = %s",
                (ruc,)
            )
            result = cursor.fetchone()
            
            if result:
                return result['id']
            
            # Crear nuevo proveedor
            cursor.execute("""
                INSERT INTO proveedores (ruc, razon_social, nombre_comercial, direccion)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (ruc, razon_social, nombre_comercial, direccion))
            
            return cursor.fetchone()['id']
    
    def _insertar_detalles(self, cursor, factura_id: int, detalles: List) -> None:
        """Inserta los detalles de una factura"""
        query = """
        INSERT INTO detalles_factura (
            factura_id, codigo_producto, descripcion,
            cantidad, precio_unitario, descuento, precio_total
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        for detalle in detalles:
            cursor.execute(query, (
                factura_id,
                detalle.codigo,
                detalle.descripcion,
                detalle.cantidad,
                detalle.precio_unitario,
                detalle.descuento,
                detalle.precio_total
            ))
    
    def obtener_facturas(self, usuario_id: int = None, 
                        fecha_desde: datetime = None,
                        fecha_hasta: datetime = None,
                        categoria: str = None,
                        estado: str = None,
                        limite: int = 100) -> List[Dict]:
        """Obtiene facturas con filtros opcionales"""
        
        query = """
        SELECT 
            f.*,
            p.razon_social as proveedor,
            p.ruc as ruc_proveedor
        FROM facturas f
        LEFT JOIN proveedores p ON f.proveedor_id = p.id
        WHERE 1=1
        """
        params = []
        
        if usuario_id:
            query += " AND f.usuario_id = %s"
            params.append(usuario_id)
        
        if fecha_desde:
            query += " AND f.fecha_emision >= %s"
            params.append(fecha_desde)
        
        if fecha_hasta:
            query += " AND f.fecha_emision <= %s"
            params.append(fecha_hasta)
        
        if categoria:
            query += " AND f.categoria = %s"
            params.append(categoria)
        
        if estado:
            query += " AND f.estado = %s"
            params.append(estado)
        
        query += " ORDER BY f.fecha_emision DESC LIMIT %s"
        params.append(limite)
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def obtener_reporte_mensual(self, usuario_id: int, 
                               anio: int, mes: int) -> Dict[str, Any]:
        """Genera reporte mensual de facturas"""
        
        query = """
        SELECT 
            COUNT(*) as total_facturas,
            SUM(subtotal_sin_impuestos) as total_subtotal,
            SUM(iva) as total_iva,
            SUM(total) as total_general,
            categoria,
            COUNT(DISTINCT proveedor_id) as total_proveedores
        FROM facturas
        WHERE usuario_id = %s 
          AND anio_contable = %s 
          AND mes_contable = %s
        GROUP BY categoria
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, (usuario_id, anio, mes))
            resultados = cursor.fetchall()
            
            # Consolidar resultados
            reporte = {
                'anio': anio,
                'mes': mes,
                'total_facturas': 0,
                'total_subtotal': 0,
                'total_iva': 0,
                'total_general': 0,
                'por_categoria': [],
                'total_proveedores': 0
            }
            
            proveedores_unicos = set()
            
            for row in resultados:
                reporte['total_facturas'] += row['total_facturas']
                reporte['total_subtotal'] += float(row['total_subtotal'] or 0)
                reporte['total_iva'] += float(row['total_iva'] or 0)
                reporte['total_general'] += float(row['total_general'] or 0)
                
                reporte['por_categoria'].append({
                    'categoria': row['categoria'] or 'Sin categoría',
                    'facturas': row['total_facturas'],
                    'total': float(row['total_general'] or 0)
                })
            
            # Contar proveedores únicos del mes
            cursor.execute("""
                SELECT COUNT(DISTINCT proveedor_id) as total
                FROM facturas
                WHERE usuario_id = %s 
                  AND anio_contable = %s 
                  AND mes_contable = %s
            """, (usuario_id, anio, mes))
            
            reporte['total_proveedores'] = cursor.fetchone()['total']
            
            return reporte
    
    def actualizar_categoria(self, factura_id: int, categoria: str, 
                           subcategoria: str = None) -> bool:
        """Actualiza la categoría de una factura"""
        query = """
        UPDATE facturas 
        SET categoria = %s, subcategoria = %s, estado = 'revisado'
        WHERE id = %s
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, (categoria, subcategoria, factura_id))
            return cursor.rowcount > 0
    
    def marcar_como_exportado(self, factura_ids: List[int]) -> int:
        """Marca facturas como exportadas"""
        query = """
        UPDATE facturas 
        SET estado = 'exportado'
        WHERE id = ANY(%s)
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, (factura_ids,))
            return cursor.rowcount