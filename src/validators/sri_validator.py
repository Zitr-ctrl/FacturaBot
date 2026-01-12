"""
Validador de datos de facturas según normativas del SRI (Ecuador)
"""
import re
from datetime import datetime
from typing import Tuple, List
from ..models.invoice import Factura


class SRIValidator:
    """Validador de facturas electrónicas según reglas del SRI"""
    
    # Dígitos verificadores para validación de RUC
    COEFICIENTES_RUC_NATURAL = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    COEFICIENTES_RUC_JURIDICA = [4, 3, 2, 7, 6, 5, 4, 3, 2]
    COEFICIENTES_RUC_PUBLICA = [3, 2, 7, 6, 5, 4, 3, 2]
    
    @staticmethod
    def validar_factura(factura: Factura) -> Tuple[bool, List[str]]:
        """
        Valida una factura completa
        
        Returns:
            (es_valida, lista_de_errores)
        """
        errores = []
        
        # Validar RUCs
        if not SRIValidator.validar_ruc(factura.ruc_emisor):
            errores.append(f"RUC emisor inválido: {factura.ruc_emisor}")
        
        # RUC comprador puede ser RUC (13 dígitos) o cédula (10 dígitos)
        if not SRIValidator.validar_identificacion(factura.ruc_comprador):
            errores.append(f"Identificación comprador inválida: {factura.ruc_comprador}")
        
        # Validar clave de acceso
        if not SRIValidator.validar_clave_acceso(factura.clave_acceso):
            errores.append(f"Clave de acceso inválida: {factura.clave_acceso}")
        
        # Validar totales
        total_calculado = factura.subtotal_sin_impuestos + factura.iva + factura.propina
        if abs(total_calculado - factura.total) > 0.03:
            errores.append(
                f"Total inconsistente. Calculado: {total_calculado:.2f}, "
                f"Declarado: {factura.total:.2f}"
            )
        
        # Validar que tenga detalles
        if not factura.detalles:
            errores.append("La factura no tiene detalles/items")
        
        # Validar fecha
        if factura.fecha_emision > datetime.now():
            errores.append("Fecha de emisión es futura")
        
        es_valida = len(errores) == 0
        return es_valida, errores
    
    @staticmethod
    def validar_ruc(ruc: str) -> bool:
        """
        Valida un RUC ecuatoriano según algoritmo del SRI
        
        El RUC tiene 13 dígitos:
        - 10 primeros: cédula o identificación
        - 3 últimos: establecimiento (001, 002, etc.)
        
        Tipos:
        - Personas naturales: tercer dígito < 6
        - Sociedades privadas: tercer dígito = 9
        - Entidades públicas: tercer dígito = 6
        """
        if not ruc or len(ruc) != 13:
            return False
        
        if not ruc.isdigit():
            return False
        
        # Los últimos 3 dígitos deben ser >= 001
        establecimiento = ruc[10:13]
        if int(establecimiento) < 1:
            return False
        
        # Validar según tipo
        tercer_digito = int(ruc[2])
        
        if tercer_digito < 6:
            # Persona natural
            return SRIValidator._validar_ruc_natural(ruc)
        elif tercer_digito == 6:
            # Entidad pública
            return SRIValidator._validar_ruc_publica(ruc)
        elif tercer_digito == 9:
            # Sociedad privada
            return SRIValidator._validar_ruc_juridica(ruc)
        else:
            return False
    
    @staticmethod
    def _validar_ruc_natural(ruc: str) -> bool:
        """Valida RUC de persona natural"""
        suma = 0
        for i, coef in enumerate(SRIValidator.COEFICIENTES_RUC_NATURAL):
            valor = int(ruc[i]) * coef
            suma += valor if valor < 10 else valor - 9
        
        residuo = suma % 10
        digito_verificador = 0 if residuo == 0 else 10 - residuo
        
        return digito_verificador == int(ruc[9])
    
    @staticmethod
    def _validar_ruc_juridica(ruc: str) -> bool:
        """Valida RUC de sociedad privada"""
        suma = sum(
            int(ruc[i]) * coef 
            for i, coef in enumerate(SRIValidator.COEFICIENTES_RUC_JURIDICA)
        )
        
        residuo = suma % 11
        digito_verificador = 0 if residuo == 0 else 11 - residuo
        
        return digito_verificador == int(ruc[9])
    
    @staticmethod
    def _validar_ruc_publica(ruc: str) -> bool:
        """Valida RUC de entidad pública"""
        suma = sum(
            int(ruc[i]) * coef 
            for i, coef in enumerate(SRIValidator.COEFICIENTES_RUC_PUBLICA)
        )
        
        residuo = suma % 11
        digito_verificador = 0 if residuo == 0 else 11 - residuo
        
        return digito_verificador == int(ruc[8])
    
    @staticmethod
    def validar_identificacion(identificacion: str) -> bool:
        """
        Valida una identificación que puede ser RUC (13 dígitos) o cédula (10 dígitos)
        
        Args:
            identificacion: RUC o cédula a validar
            
        Returns:
            True si es válida, False en caso contrario
        """
        if not identificacion or not identificacion.isdigit():
            return False
        
        longitud = len(identificacion)
        
        # RUC (13 dígitos)
        if longitud == 13:
            return SRIValidator.validar_ruc(identificacion)
        
        # Cédula (10 dígitos)
        elif longitud == 10:
            return SRIValidator.validar_cedula(identificacion)
        
        # Otras longitudes no son válidas
        return False
    
    @staticmethod
    def validar_cedula(cedula: str) -> bool:
        """
        Valida una cédula ecuatoriana (10 dígitos)
        
        Args:
            cedula: Cédula de 10 dígitos
            
        Returns:
            True si es válida, False en caso contrario
        """
        if not cedula or len(cedula) != 10:
            return False
        
        if not cedula.isdigit():
            return False
        
        # Los dos primeros dígitos deben corresponder a una provincia (01-24)
        provincia = int(cedula[0:2])
        if provincia < 1 or provincia > 24:
            return False
        
        # El tercer dígito debe ser menor a 6 (persona natural)
        tercer_digito = int(cedula[2])
        if tercer_digito >= 6:
            return False
        
        # Validar dígito verificador usando el algoritmo módulo 10
        coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
        suma = 0
        
        for i, coef in enumerate(coeficientes):
            valor = int(cedula[i]) * coef
            suma += valor if valor < 10 else valor - 9
        
        residuo = suma % 10
        digito_verificador = 0 if residuo == 0 else 10 - residuo
        
        return digito_verificador == int(cedula[9])
    
    @staticmethod
    def validar_clave_acceso(clave: str) -> bool:
        """
        Valida la clave de acceso de 49 dígitos
        
        Formato: DDMMAAAATCXXXXXXXXEEEESSSSSSSSSC
        - DD/MM/AAAA: fecha
        - T: tipo de comprobante
        - C: RUC (primeros 10)
        - XXXXXX: ambiente, etc.
        - EEE: establecimiento
        - SSSSSSSSS: secuencial
        - C: dígito verificador (módulo 11)
        """
        if not clave or len(clave) != 49:
            return False
        
        if not clave.isdigit():
            return False
        
        # Validar fecha (primeros 8 dígitos)
        try:
            dia = int(clave[0:2])
            mes = int(clave[2:4])
            anio = int(clave[4:8])
            
            if not (1 <= dia <= 31 and 1 <= mes <= 12):
                return False
            
            # Validar que la fecha sea coherente
            datetime(anio, mes, dia)
        except (ValueError, OverflowError):
            return False
        
        # Validar dígito verificador (módulo 11)
        suma = 0
        factor = 7
        
        for i in range(48):
            suma += int(clave[i]) * factor
            factor = factor - 1 if factor > 2 else 7
        
        residuo = suma % 11
        digito_verificador = 0 if residuo == 0 else 11 - residuo
        
        return digito_verificador == int(clave[48])
    
    @staticmethod
    def validar_formato_factura(numero_factura: str) -> bool:
        """
        Valida el formato de número de factura: XXX-XXX-XXXXXXXXX
        - 3 dígitos establecimiento
        - 3 dígitos punto de emisión
        - 9 dígitos secuencial
        """
        patron = r'^\d{3}-\d{3}-\d{9}$'
        return bool(re.match(patron, numero_factura))