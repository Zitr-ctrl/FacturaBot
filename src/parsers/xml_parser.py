"""
Parser de Facturas Electrónicas XML del SRI (Ecuador)

Procesa archivos XML en formato RIDE (Representación Impresa de Documentos Electrónicos)
según especificaciones del Servicio de Rentas Internas.
"""
from lxml import etree
from datetime import datetime
from typing import Optional
from ..models.invoice import Factura, DetalleFactura


class FacturaXMLParser:
    """Parser para facturas electrónicas en formato XML del SRI"""
    
    # Namespaces comunes en XML del SRI
    NAMESPACES = {
        'ds': 'http://www.w3.org/2000/09/xmldsig#',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }
    
    def __init__(self):
        self.tree = None
        self.root = None
    
    def parse_file(self, xml_path: str) -> Factura:
        """
        Procesa un archivo XML de factura
        
        Args:
            xml_path: Ruta al archivo XML
            
        Returns:
            Objeto Factura con los datos extraídos
        """
        self.tree = etree.parse(xml_path)
        self.root = self.tree.getroot()
        
        return self._extract_factura()
    
    def parse_string(self, xml_string: str) -> Factura:
        """
        Procesa un string XML de factura
        
        Args:
            xml_string: Contenido XML como string
            
        Returns:
            Objeto Factura con los datos extraídos
        """
        self.root = etree.fromstring(xml_string.encode('utf-8'))
        
        return self._extract_factura()
    
    def _extract_factura(self) -> Factura:
        """Extrae todos los datos de la factura del XML"""
        
        # Información de autorizacion (si existe en el XML)
        autorizacion_elem = self.root.find('.//numeroAutorizacion')
        fecha_autorizacion_elem = self.root.find('.//fechaAutorizacion')
        
        # Buscar el nodo principal de la factura
        factura_node = self.root.find('.//factura')
        if factura_node is None:
            factura_node = self.root.find('.//comprobante/factura')
        if factura_node is None:
            factura_node = self.root  # El root mismo puede ser la factura
        
        # Extraer información básica
        info_tributaria = factura_node.find('infoTributaria')
        info_factura = factura_node.find('infoFactura')
        detalles_node = factura_node.find('detalles')
        
        if info_tributaria is None or info_factura is None:
            raise ValueError("XML no contiene estructura válida de factura SRI")
        
        # Datos del emisor
        ruc_emisor = self._get_text(info_tributaria, 'ruc')
        razon_social_emisor = self._get_text(info_tributaria, 'razonSocial')
        nombre_comercial = self._get_text(info_tributaria, 'nombreComercial')
        direccion_emisor = self._get_text(info_tributaria, 'dirMatriz')
        
        # Datos del comprador
        ruc_comprador = self._get_text(info_factura, 'identificacionComprador')
        razon_social_comprador = self._get_text(info_factura, 'razonSocialComprador')
        
        # Datos de la factura
        numero_factura = self._get_text(info_tributaria, 'estab') + '-' + \
                        self._get_text(info_tributaria, 'ptoEmi') + '-' + \
                        self._get_text(info_tributaria, 'secuencial')
        
        fecha_emision_str = self._get_text(info_factura, 'fechaEmision')
        fecha_emision = self._parse_fecha(fecha_emision_str)
        
        # Clave de acceso
        clave_acceso = self._get_text(info_tributaria, 'claveAcceso')
        
        # Ambiente y tipo de emisión
        ambiente = self._get_text(info_tributaria, 'ambiente')
        ambiente = 'PRODUCCION' if ambiente == '1' else 'PRUEBAS'
        tipo_emision = self._get_text(info_tributaria, 'tipoEmision')
        tipo_emision = 'NORMAL' if tipo_emision == '1' else 'CONTINGENCIA'
        
        # Totales
        total_sin_impuestos = self._get_float(info_factura, 'totalSinImpuestos')
        propina = self._get_float(info_factura, 'propina', default=0.0)
        importe_total = self._get_float(info_factura, 'importeTotal')
        
        # Calcular IVA y subtotales
        iva_total, subtotal_iva_0, subtotal_iva_12 = self._extract_impuestos(info_factura)
        
        # Extraer detalles
        detalles = self._extract_detalles(detalles_node)
        
        # Crear objeto Factura
        factura = Factura(
            ruc_emisor=ruc_emisor,
            razon_social_emisor=razon_social_emisor,
            nombre_comercial_emisor=nombre_comercial,
            direccion_emisor=direccion_emisor,
            ruc_comprador=ruc_comprador,
            razon_social_comprador=razon_social_comprador,
            numero_autorizacion=autorizacion_elem.text if autorizacion_elem is not None else clave_acceso,
            numero_factura=numero_factura,
            fecha_emision=fecha_emision,
            fecha_autorizacion=self._parse_fecha(fecha_autorizacion_elem.text) if fecha_autorizacion_elem is not None else None,
            subtotal_sin_impuestos=total_sin_impuestos,
            subtotal_iva_0=subtotal_iva_0,
            subtotal_iva_12=subtotal_iva_12,
            iva=iva_total,
            propina=propina,
            total=importe_total,
            detalles=detalles,
            ambiente=ambiente,
            tipo_emision=tipo_emision,
            clave_acceso=clave_acceso
        )
        
        return factura
    
    def _extract_impuestos(self, info_factura) -> tuple[float, float, float]:
        """
        Extrae información de impuestos (IVA)
        
        Returns:
            (iva_total, subtotal_iva_0, subtotal_iva_12)
        """
        iva_total = 0.0
        subtotal_iva_0 = 0.0
        subtotal_iva_12 = 0.0
        subtotal_iva_15 = 0.0
        
        impuestos = info_factura.find('totalConImpuestos')
        if impuestos is not None:
            for total_impuesto in impuestos.findall('totalImpuesto'):
                codigo = self._get_text(total_impuesto, 'codigo')
                codigo_porcentaje = self._get_text(total_impuesto, 'codigoPorcentaje')
                base_imponible = self._get_float(total_impuesto, 'baseImponible')
                valor = self._get_float(total_impuesto, 'valor')
                
                # Código 2 = IVA
                if codigo == '2':
                    iva_total += valor
                    
                    # Determinar tarifa según código de porcentaje
                    if codigo_porcentaje in ['0', '6']:  # IVA 0%
                        subtotal_iva_0 += base_imponible
                    elif codigo_porcentaje in ['2', '3']:  # IVA 12% o 14%
                        subtotal_iva_12 += base_imponible
                    elif codigo_porcentaje == '4':  # IVA 15%
                        subtotal_iva_15 += base_imponible
        
        # Por simplicidad, agrupamos 12%, 14% y 15% en subtotal_iva_12
        subtotal_iva_12 += subtotal_iva_15
        
        return iva_total, subtotal_iva_0, subtotal_iva_12
    
    def _extract_detalles(self, detalles_node) -> list[DetalleFactura]:
        """Extrae los detalles/items de la factura"""
        detalles = []
        
        if detalles_node is not None:
            for detalle in detalles_node.findall('detalle'):
                codigo = self._get_text(detalle, 'codigoPrincipal', default='N/A')
                descripcion = self._get_text(detalle, 'descripcion')
                cantidad = self._get_float(detalle, 'cantidad')
                precio_unitario = self._get_float(detalle, 'precioUnitario')
                descuento = self._get_float(detalle, 'descuento', default=0.0)
                precio_total = self._get_float(detalle, 'precioTotalSinImpuesto')
                
                detalle_obj = DetalleFactura(
                    codigo=codigo,
                    descripcion=descripcion,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    descuento=descuento,
                    precio_total=precio_total
                )
                detalles.append(detalle_obj)
        
        return detalles
    
    def _get_text(self, parent, tag: str, default: str = '') -> str:
        """Obtiene el texto de un elemento hijo"""
        elem = parent.find(tag)
        return elem.text.strip() if elem is not None and elem.text else default
    
    def _get_float(self, parent, tag: str, default: float = 0.0) -> float:
        """Obtiene un valor numérico de un elemento hijo"""
        text = self._get_text(parent, tag)
        try:
            return float(text) if text else default
        except ValueError:
            return default
    
    def _parse_fecha(self, fecha_str: str) -> Optional[datetime]:
        """Parsea una fecha en formato DD/MM/YYYY"""
        if not fecha_str:
            return None
        
        try:
            return datetime.strptime(fecha_str, '%d/%m/%Y')
        except ValueError:
            try:
                # Intentar formato alternativo
                return datetime.strptime(fecha_str, '%d/%m/%Y %H:%M:%S')
            except ValueError:
                return None