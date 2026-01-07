"""
Modelo de datos para Factura Electrónica SRI
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict

@dataclass
class DetalleFactura:
    """Detalle de ítem en la factura"""
    codigo: str
    descripcion: str
    cantidad: float
    precio_unitario: float
    descuento: float
    precio_total: float
    
    def to_dict(self) -> Dict:
        return {
            'codigo': self.codigo,
            'descripcion': self.descripcion,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'descuento': self.descuento,
            'precio_total': self.precio_total
        }


@dataclass
class Factura:
    """Modelo principal de Factura Electrónica"""
    
    # Información del emisor
    ruc_emisor: str
    razon_social_emisor: str
    nombre_comercial_emisor: Optional[str]
    direccion_emisor: str
    
    # Información del comprador
    ruc_comprador: str
    razon_social_comprador: str
    
    # Datos de la factura
    numero_autorizacion: str
    numero_factura: str
    fecha_emision: datetime
    fecha_autorizacion: Optional[datetime]
    
    # Totales
    subtotal_sin_impuestos: float
    subtotal_iva_0: float
    subtotal_iva_12: float
    iva: float
    propina: float
    total: float
    
    # Detalles
    detalles: List[DetalleFactura]
    
    # Metadata
    ambiente: str  # PRODUCCION o PRUEBAS
    tipo_emision: str  # NORMAL
    clave_acceso: str
    
    def __post_init__(self):
        """Validaciones básicas después de inicialización"""
        if len(self.ruc_emisor) != 13:
            raise ValueError(f"RUC emisor inválido: {self.ruc_emisor}")
        
        # RUC comprador puede ser cédula (10 dígitos) o RUC (13 dígitos)
        if len(self.ruc_comprador) not in [10, 13]:
            raise ValueError(f"Identificación comprador inválida (debe ser cédula de 10 o RUC de 13 dígitos): {self.ruc_comprador}")
        
        # Validar que el total calculado coincida
        total_calculado = (
            self.subtotal_sin_impuestos + 
            self.iva + 
            self.propina
        )
        
        if abs(total_calculado - self.total) > 0.01:  # Margen de error por redondeo
            raise ValueError(
                f"Total inconsistente. Calculado: {total_calculado}, "
                f"Declarado: {self.total}"
            )
    
    def to_dict(self) -> Dict:
        """Convierte la factura a diccionario"""
        return {
            'ruc_emisor': self.ruc_emisor,
            'razon_social_emisor': self.razon_social_emisor,
            'nombre_comercial_emisor': self.nombre_comercial_emisor,
            'direccion_emisor': self.direccion_emisor,
            'ruc_comprador': self.ruc_comprador,
            'razon_social_comprador': self.razon_social_comprador,
            'numero_autorizacion': self.numero_autorizacion,
            'numero_factura': self.numero_factura,
            'fecha_emision': self.fecha_emision.isoformat() if self.fecha_emision else None,
            'fecha_autorizacion': self.fecha_autorizacion.isoformat() if self.fecha_autorizacion else None,
            'subtotal_sin_impuestos': self.subtotal_sin_impuestos,
            'subtotal_iva_0': self.subtotal_iva_0,
            'subtotal_iva_12': self.subtotal_iva_12,
            'iva': self.iva,
            'propina': self.propina,
            'total': self.total,
            'ambiente': self.ambiente,
            'tipo_emision': self.tipo_emision,
            'clave_acceso': self.clave_acceso,
            'cantidad_detalles': len(self.detalles)
        }
    
    def get_resumen(self) -> str:
        """Retorna un resumen legible de la factura"""
        return f"""
        Factura: {self.numero_factura}
        Emisor: {self.razon_social_emisor} (RUC: {self.ruc_emisor})
        Comprador: {self.razon_social_comprador} (RUC: {self.ruc_comprador})
        Fecha: {self.fecha_emision.strftime('%d/%m/%Y')}
        Subtotal: ${self.subtotal_sin_impuestos:.2f}
        IVA: ${self.iva:.2f}
        Total: ${self.total:.2f}
        Items: {len(self.detalles)}
        """