"""
Exportador de facturas a Excel con formato profesional
"""
import pandas as pd
from datetime import datetime
from typing import List, Dict
from pathlib import Path


class ExcelExporter:
    """Exporta facturas y reportes a Excel"""
    
    def __init__(self, output_dir: str = 'exports'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def exportar_facturas(self, facturas: List[Dict], 
                         nombre_archivo: str = None) -> str:
        """
        Exporta lista de facturas a Excel
        
        Returns:
            Ruta del archivo generado
        """
        if not facturas:
            raise ValueError("No hay facturas para exportar")
        
        # Preparar datos para DataFrame
        datos = []
        for f in facturas:
            datos.append({
                'Fecha': f.get('fecha_emision'),
                'Número': f.get('numero_factura'),
                'Proveedor': f.get('proveedor') or f.get('razon_social_comprador'),
                'RUC Proveedor': f.get('ruc_proveedor') or f.get('ruc_comprador'),
                'Subtotal': float(f.get('subtotal_sin_impuestos', 0)),
                'IVA 0%': float(f.get('subtotal_iva_0', 0)),
                'IVA 12%': float(f.get('subtotal_iva_12', 0)),
                'IVA': float(f.get('iva', 0)),
                'Total': float(f.get('total', 0)),
                'Categoría': f.get('categoria', 'Sin categoría'),
                'Estado': f.get('estado', 'Pendiente'),
                'Clave Acceso': f.get('clave_acceso', '')
            })
        
        df = pd.DataFrame(datos)
        
        # Generar nombre de archivo
        if not nombre_archivo:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f'facturas_{timestamp}.xlsx'
        
        if not nombre_archivo.endswith('.xlsx'):
            nombre_archivo += '.xlsx'
        
        ruta_archivo = self.output_dir / nombre_archivo
        
        # Crear Excel con formato
        with pd.ExcelWriter(ruta_archivo, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Facturas', index=False)
            
            # Formatear hoja
            workbook = writer.book
            worksheet = writer.sheets['Facturas']
            
            # Ajustar ancho de columnas
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Agregar hoja de resumen
            self._agregar_hoja_resumen(writer, df)
        
        return str(ruta_archivo)
    
    def exportar_reporte_mensual(self, reporte: Dict, 
                                nombre_archivo: str = None) -> str:
        """
        Exporta reporte mensual a Excel
        
        Args:
            reporte: Dict con datos del reporte mensual
        
        Returns:
            Ruta del archivo generado
        """
        if not nombre_archivo:
            nombre_archivo = f"reporte_{reporte['anio']}_{reporte['mes']:02d}.xlsx"
        
        ruta_archivo = self.output_dir / nombre_archivo
        
        with pd.ExcelWriter(ruta_archivo, engine='openpyxl') as writer:
            # Hoja de resumen general
            resumen_data = {
                'Métrica': [
                    'Total Facturas',
                    'Subtotal',
                    'IVA',
                    'Total General',
                    'Proveedores Únicos'
                ],
                'Valor': [
                    reporte['total_facturas'],
                    f"${reporte['total_subtotal']:.2f}",
                    f"${reporte['total_iva']:.2f}",
                    f"${reporte['total_general']:.2f}",
                    reporte['total_proveedores']
                ]
            }
            
            df_resumen = pd.DataFrame(resumen_data)
            df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
            
            # Hoja por categoría
            if reporte.get('por_categoria'):
                df_categorias = pd.DataFrame(reporte['por_categoria'])
                df_categorias.to_excel(writer, sheet_name='Por Categoría', index=False)
        
        return str(ruta_archivo)
    
    def exportar_para_sri(self, facturas: List[Dict], 
                         nombre_archivo: str = None) -> str:
        """
        Exporta en formato optimizado para declaración SRI
        
        Formato simplificado para anexos transaccionales
        """
        if not nombre_archivo:
            timestamp = datetime.now().strftime('%Y%m')
            nombre_archivo = f'sri_anexo_{timestamp}.xlsx'
        
        ruta_archivo = self.output_dir / nombre_archivo
        
        # Preparar datos según formato SRI
        datos = []
        for f in facturas:
            datos.append({
                'Fecha': f.get('fecha_emision'),
                'Tipo Comprobante': 'FACTURA',
                'Serie Comprobante': f.get('numero_factura', '').split('-')[0] + '-' + 
                                    f.get('numero_factura', '').split('-')[1] if '-' in f.get('numero_factura', '') else '',
                'Número': f.get('numero_factura', '').split('-')[2] if '-' in f.get('numero_factura', '') else '',
                'RUC Proveedor': f.get('ruc_proveedor') or f.get('ruc_comprador'),
                'Razón Social': f.get('proveedor') or f.get('razon_social_comprador'),
                'Base Imponible 0%': float(f.get('subtotal_iva_0', 0)),
                'Base Imponible 12%': float(f.get('subtotal_iva_12', 0)),
                'IVA 12%': float(f.get('iva', 0)),
                'Total': float(f.get('total', 0)),
                'Autorización': f.get('numero_autorizacion', '')
            })
        
        df = pd.DataFrame(datos)
        
        with pd.ExcelWriter(ruta_archivo, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Compras', index=False)
            
            # Agregar totales al final
            worksheet = writer.sheets['Compras']
            ultima_fila = len(df) + 2
            
            worksheet.cell(row=ultima_fila, column=1, value='TOTALES')
            worksheet.cell(row=ultima_fila, column=7, 
                          value=df['Base Imponible 0%'].sum())
            worksheet.cell(row=ultima_fila, column=8, 
                          value=df['Base Imponible 12%'].sum())
            worksheet.cell(row=ultima_fila, column=9, 
                          value=df['IVA 12%'].sum())
            worksheet.cell(row=ultima_fila, column=10, 
                          value=df['Total'].sum())
        
        return str(ruta_archivo)
    
    def _agregar_hoja_resumen(self, writer, df: pd.DataFrame):
        """Agrega hoja de resumen al Excel"""
        resumen = {
            'Métrica': [
                'Total Facturas',
                'Total Subtotal',
                'Total IVA',
                'Total General',
                'Promedio por Factura'
            ],
            'Valor': [
                len(df),
                f"${df['Subtotal'].sum():.2f}",
                f"${df['IVA'].sum():.2f}",
                f"${df['Total'].sum():.2f}",
                f"${df['Total'].mean():.2f}"
            ]
        }
        
        df_resumen = pd.DataFrame(resumen)
        df_resumen.to_excel(writer, sheet_name='Resumen', index=False)