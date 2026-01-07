"""
FacturaBot - Sistema de Procesamiento de Facturas Electrónicas SRI

Ejemplo de uso del sistema completo
Autor: Josue Ortíz - OrtizDev
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Solución para imports: agregar directorio raíz al path
directorio_raiz = Path(__file__).parent
if str(directorio_raiz) not in sys.path:
    sys.path.insert(0, str(directorio_raiz))

from src.parsers.xml_parser import FacturaXMLParser
from src.validators.sri_validator import SRIValidator
from src.database.connection import DatabaseManager
from src.exporters.excel_exporter import ExcelExporter


def procesar_factura_xml(ruta_xml: str, db: DatabaseManager = None, 
                         guardar_en_bd: bool = False):
    """
    Procesa una factura XML del SRI
    
    Args:
        ruta_xml: Ruta al archivo XML
        db: Instancia de DatabaseManager (opcional)
        guardar_en_bd: Si es True, guarda en la base de datos
    """
    print(f"\n{'='*60}")
    print(f"Procesando: {Path(ruta_xml).name}")
    print(f"{'='*60}\n")
    
    # 1. Parsear XML
    parser = FacturaXMLParser()
    try:
        factura = parser.parse_file(ruta_xml)
        print("✅ XML parseado exitosamente")
    except Exception as e:
        print(f"❌ Error al parsear XML: {e}")
        return None
    
    # 2. Validar datos
    es_valida, errores = SRIValidator.validar_factura(factura)
    
    if es_valida:
        print("✅ Factura válida según reglas del SRI")
    else:
        print("⚠️  Factura tiene errores de validación:")
        for error in errores:
            print(f"   - {error}")
    
    # 3. Mostrar resumen
    print(factura.get_resumen())
    
    # 4. Guardar en BD si se solicita
    if guardar_en_bd and db:
        try:
            factura_id = db.insertar_factura(factura, usuario_id=1, categoria='Sin categoría')
            print(f"✅ Factura guardada en BD con ID: {factura_id}")
        except Exception as e:
            print(f"❌ Error al guardar en BD: {e}")
            return None
    
    return factura


def ejemplo_completo():
    """Ejemplo de uso completo del sistema"""
    
    print("\n" + "="*60)
    print("FACTURABOT - Sistema de Procesamiento de Facturas")
    print("="*60 + "\n")
    
    # Inicializar componentes
    db = DatabaseManager()
    exporter = ExcelExporter()
    
    # Verificar conexión a BD (opcional)
    print("🔌 Verificando conexión a PostgreSQL...")
    if db.test_connection():
        print("✅ Conexión exitosa a la base de datos\n")
        usar_bd = True
    else:
        print("⚠️  No se pudo conectar a PostgreSQL")
        print("   El sistema funcionará sin base de datos\n")
        usar_bd = False
    
    # Directorio de facturas de prueba
    directorio_facturas = Path("tests/sample_invoices")
    
    if not directorio_facturas.exists():
        print(f"⚠️  No se encontró el directorio: {directorio_facturas}")
        print("   Crea el directorio y coloca archivos XML de prueba\n")
        return
    
    # Procesar todas las facturas XML en el directorio
    archivos_xml = list(directorio_facturas.glob("*.xml"))
    
    if not archivos_xml:
        print("⚠️  No se encontraron archivos XML en el directorio")
        return
    
    print(f"📄 Se encontraron {len(archivos_xml)} archivos XML\n")
    
    facturas_procesadas = []
    
    for archivo_xml in archivos_xml:
        factura = procesar_factura_xml(
            str(archivo_xml), 
            db=db if usar_bd else None,
            guardar_en_bd=usar_bd
        )
        
        if factura:
            facturas_procesadas.append(factura)
    
    print(f"\n{'='*60}")
    print(f"RESUMEN DE PROCESAMIENTO")
    print(f"{'='*60}\n")
    print(f"Total archivos: {len(archivos_xml)}")
    print(f"Procesados exitosamente: {len(facturas_procesadas)}")
    print(f"Errores: {len(archivos_xml) - len(facturas_procesadas)}")
    
    # Si hay facturas procesadas y BD activa, generar reportes
    if facturas_procesadas and usar_bd:
        print(f"\n{'='*60}")
        print(f"GENERANDO REPORTES")
        print(f"{'='*60}\n")
        
        # Obtener facturas de la BD
        facturas_bd = db.obtener_facturas(usuario_id=1, limite=100)
        
        if facturas_bd:
            # Exportar a Excel
            try:
                archivo_excel = exporter.exportar_facturas(facturas_bd)
                print(f"✅ Facturas exportadas a: {archivo_excel}")
            except Exception as e:
                print(f"❌ Error al exportar: {e}")
            
            # Generar reporte mensual
            fecha_primera = facturas_bd[0]['fecha_emision']
            try:
                reporte = db.obtener_reporte_mensual(1, fecha_primera.year, fecha_primera.month)
                archivo_reporte = exporter.exportar_reporte_mensual(reporte)
                print(f"✅ Reporte mensual generado: {archivo_reporte}")
                
                print("\nResumen del mes:")
                print(f"  Total facturas: {reporte['total_facturas']}")
                print(f"  Total general: ${reporte['total_general']:.2f}")
                print(f"  IVA: ${reporte['total_iva']:.2f}")
                print(f"  Proveedores: {reporte['total_proveedores']}")
            except Exception as e:
                print(f"❌ Error al generar reporte: {e}")


def ejemplo_simple():
    """Ejemplo simple sin base de datos"""
    
    print("\n" + "="*60)
    print("EJEMPLO SIMPLE - Procesamiento de factura XML")
    print("="*60 + "\n")
    
    # Crear factura de ejemplo XML
    xml_ejemplo = """<?xml version="1.0" encoding="UTF-8"?>
<autorizacion>
    <factura>
        <infoTributaria>
            <ambiente>1</ambiente>
            <tipoEmision>1</tipoEmision>
            <razonSocial>EMPRESA EJEMPLO S.A.</razonSocial>
            <nombreComercial>EJEMPLO</nombreComercial>
            <ruc>0912345678001</ruc>
            <claveAcceso>05012025010912345678001110010010000000011234567813</claveAcceso>
            <estab>001</estab>
            <ptoEmi>001</ptoEmi>
            <secuencial>000000001</secuencial>
            <dirMatriz>AV. EJEMPLO 123 Y CALLE DEMO</dirMatriz>
        </infoTributaria>
        <infoFactura>
            <fechaEmision>05/01/2025</fechaEmision>
            <identificacionComprador>0987654321001</identificacionComprador>
            <razonSocialComprador>CLIENTE DEMO CIA LTDA</razonSocialComprador>
            <totalSinImpuestos>100.00</totalSinImpuestos>
            <totalConImpuestos>
                <totalImpuesto>
                    <codigo>2</codigo>
                    <codigoPorcentaje>2</codigoPorcentaje>
                    <baseImponible>100.00</baseImponible>
                    <valor>12.00</valor>
                </totalImpuesto>
            </totalConImpuestos>
            <propina>0.00</propina>
            <importeTotal>112.00</importeTotal>
        </infoFactura>
        <detalles>
            <detalle>
                <codigoPrincipal>PROD001</codigoPrincipal>
                <descripcion>Producto de ejemplo</descripcion>
                <cantidad>1.00</cantidad>
                <precioUnitario>100.00</precioUnitario>
                <descuento>0.00</descuento>
                <precioTotalSinImpuesto>100.00</precioTotalSinImpuesto>
            </detalle>
        </detalles>
    </factura>
</autorizacion>"""
    
    # Guardar XML temporal
    ruta_temp = Path("temp_factura.xml")
    ruta_temp.write_text(xml_ejemplo, encoding='utf-8')
    
    try:
        # Procesar
        parser = FacturaXMLParser()
        factura = parser.parse_file(str(ruta_temp))
        
        print("✅ Factura procesada exitosamente")
        print(factura.get_resumen())
        
        # Validar
        es_valida, errores = SRIValidator.validar_factura(factura)
        print(f"\n{'Válida' if es_valida else 'Inválida'}: {len(errores)} errores")
        
        if errores:
            for error in errores:
                print(f"  - {error}")
        
        # Mostrar datos extraídos
        print("\nDatos extraídos:")
        print(f"  RUC Emisor: {factura.ruc_emisor}")
        print(f"  Razón Social: {factura.razon_social_emisor}")
        print(f"  Total: ${factura.total:.2f}")
        print(f"  Items: {len(factura.detalles)}")
        
    finally:
        # Limpiar archivo temporal
        if ruta_temp.exists():
            ruta_temp.unlink()


if __name__ == "__main__":
    # Puedes ejecutar el ejemplo completo o el simple
    
    # Para ejemplo simple (sin BD):
    #ejemplo_simple()
    
    # Para ejemplo completo (con BD):
    ejemplo_completo()