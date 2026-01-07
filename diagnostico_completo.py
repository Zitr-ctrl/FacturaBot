"""
Script de diagnóstico para FacturaBot
Verifica la configuración y detecta problemas
"""
import sys
from pathlib import Path

print("="*70)
print("  DIAGNÓSTICO FACTURABOT")
print("="*70)
print()

# 1. Verificar estructura de directorios
print("📁 1. ESTRUCTURA DE DIRECTORIOS")
print("-" * 70)

directorios_requeridos = [
    'src',
    'src/parsers',
    'src/validators',
    'src/database',
    'src/models',
    'tests/sample_invoices',
]

for dir_path in directorios_requeridos:
    path = Path(dir_path)
    if path.exists():
        print(f"  ✅ {dir_path}/")
    else:
        print(f"  ❌ {dir_path}/ - FALTA")

print()

# 2. Verificar archivos clave
print("📄 2. ARCHIVOS CLAVE")
print("-" * 70)

archivos_requeridos = {
    'main.py': Path('main.py'),
    'xml_parser.py': Path('src/parsers/xml_parser.py'),
    'sri_validator.py': Path('src/validators/sri_validator.py'),
    'connection.py': Path('src/database/connection.py'),
    'schema.sql': Path('src/database/schema.sql'),
}

for nombre, ruta in archivos_requeridos.items():
    if ruta.exists():
        tamanio = ruta.stat().st_size
        print(f"  ✅ {nombre} ({tamanio:,} bytes)")
    else:
        print(f"  ❌ {nombre} - NO ENCONTRADO")

print()

# 3. Verificar métodos clave en sri_validator.py
print("🔍 3. MÉTODOS EN sri_validator.py")
print("-" * 70)

validator_path = Path('src/validators/sri_validator.py')
if validator_path.exists():
    with open(validator_path, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    metodos_clave = [
        'def validar_factura',
        'def validar_ruc',
        'def validar_identificacion',  # NUEVO - debe estar
        'def validar_cedula',  # NUEVO - debe estar
        'def validar_clave_acceso',
    ]
    
    for metodo in metodos_clave:
        if metodo in contenido:
            # Contar líneas del método
            lineas = [l for l in contenido.split('\n') if metodo in l]
            print(f"  ✅ {metodo}() encontrado (línea aprox: {contenido[:contenido.find(metodo)].count(chr(10))+1})")
        else:
            print(f"  ❌ {metodo}() - NO ENCONTRADO")
            if metodo == 'def validar_identificacion':
                print("      ⚠️  ESTE MÉTODO ES NECESARIO PARA ACEPTAR CÉDULAS")
    
    # Verificar que el validador use validar_identificacion
    if 'validar_identificacion(factura.ruc_comprador)' in contenido:
        print(f"  ✅ Validación de comprador actualizada (usa validar_identificacion)")
    else:
        print(f"  ❌ Validación de comprador NO actualizada")
        print("      ⚠️  Aún usa validar_ruc en lugar de validar_identificacion")
else:
    print("  ❌ Archivo no encontrado")

print()

# 4. Verificar manejo de XML en parser
print("🔍 4. MANEJO DE XML EN xml_parser.py")
print("-" * 70)

parser_path = Path('src/parsers/xml_parser.py')
if parser_path.exists():
    with open(parser_path, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Verificar manejo de comprobante HTML-escaped
    if 'html.unescape' in contenido:
        print("  ✅ Decodificación de HTML entities implementada")
    else:
        print("  ❌ Decodificación de HTML entities NO implementada")
        print("      ⚠️  No podrá parsear facturas reales del SRI")
    
    # Verificar manejo de declaración XML
    if "startswith('<?xml')" in contenido or 'startswith("<?xml")' in contenido:
        print("  ✅ Manejo de declaración XML duplicada implementado")
    else:
        print("  ❌ Manejo de declaración XML duplicada NO implementado")
        print("      ⚠️  Puede fallar con facturas reales del SRI")
    
    # Verificar manejo de ambiente
    if 'PRODUCCIÓN' in contenido or 'PRODUCCION' in contenido.upper():
        print("  ✅ Manejo de ambiente en formato texto implementado")
    else:
        print("  ⚠️  Manejo de ambiente puede no soportar formato texto")
else:
    print("  ❌ Archivo no encontrado")

print()

# 5. Probar validación de cédula directamente
print("🧪 5. PRUEBA DE VALIDACIÓN DE CÉDULA")
print("-" * 70)

cedula_prueba = "0904932340"
print(f"Cédula de prueba: {cedula_prueba}")

try:
    # Importar el validador
    sys.path.insert(0, str(Path.cwd()))
    from src.validators.sri_validator import SRIValidator
    
    # Probar validar_cedula si existe
    if hasattr(SRIValidator, 'validar_cedula'):
        resultado = SRIValidator.validar_cedula(cedula_prueba)
        print(f"  ✅ validar_cedula() existe")
        print(f"     Resultado: {resultado}")
        if resultado:
            print(f"     ✅ La cédula ES VÁLIDA")
        else:
            print(f"     ❌ La cédula ES INVÁLIDA")
    else:
        print(f"  ❌ validar_cedula() NO EXISTE en el código")
        print(f"     ⚠️  El validador rechazará todas las cédulas")
    
    # Probar validar_identificacion si existe
    if hasattr(SRIValidator, 'validar_identificacion'):
        resultado = SRIValidator.validar_identificacion(cedula_prueba)
        print(f"  ✅ validar_identificacion() existe")
        print(f"     Resultado: {resultado}")
        if resultado:
            print(f"     ✅ La identificación ES VÁLIDA")
        else:
            print(f"     ❌ La identificación ES INVÁLIDA")
    else:
        print(f"  ❌ validar_identificacion() NO EXISTE en el código")
        print(f"     ⚠️  El validador rechazará todas las cédulas")
    
except Exception as e:
    print(f"  ❌ Error al importar validador: {e}")
    print(f"     Verifica que el archivo esté correcto")

print()

# 6. Verificar facturas de prueba
print("📄 6. FACTURAS DE PRUEBA DISPONIBLES")
print("-" * 70)

sample_dir = Path('tests/sample_invoices')
if sample_dir.exists():
    archivos = list(sample_dir.glob('*.xml'))
    if archivos:
        print(f"  ✅ {len(archivos)} archivo(s) XML encontrado(s):")
        for archivo in archivos[:5]:  # Mostrar máximo 5
            tamanio = archivo.stat().st_size
            print(f"     - {archivo.name} ({tamanio:,} bytes)")
        if len(archivos) > 5:
            print(f"     ... y {len(archivos)-5} más")
    else:
        print(f"  ⚠️  No hay archivos XML en {sample_dir}/")
else:
    print(f"  ❌ Directorio no existe: {sample_dir}/")

print()

# 7. Resumen y recomendaciones
print("="*70)
print("  RESUMEN Y RECOMENDACIONES")
print("="*70)
print()

# Determinar si falta validar_identificacion
validator_ok = False
if validator_path.exists():
    with open(validator_path, 'r', encoding='utf-8') as f:
        contenido = f.read()
    validator_ok = 'def validar_identificacion' in contenido and 'def validar_cedula' in contenido

parser_ok = False
if parser_path.exists():
    with open(parser_path, 'r', encoding='utf-8') as f:
        contenido = f.read()
    parser_ok = 'html.unescape' in contenido

if validator_ok and parser_ok:
    print("✅ TODOS LOS PARCHES ESTÁN APLICADOS")
    print()
    print("El sistema debería funcionar correctamente.")
    print()
    print("Si aún falla, verifica:")
    print("  1. Que guardaste los cambios en los archivos")
    print("  2. Que no haya errores de sintaxis")
    print("  3. Ejecuta: python main.py")
else:
    print("⚠️  FALTAN PARCHES POR APLICAR")
    print()
    if not validator_ok:
        print("❌ sri_validator.py - FALTA ACTUALIZAR")
        print("   Debe incluir:")
        print("   - def validar_identificacion()")
        print("   - def validar_cedula()")
        print()
    if not parser_ok:
        print("❌ xml_parser.py - FALTA ACTUALIZAR")
        print("   Debe incluir:")
        print("   - Decodificación con html.unescape()")
        print("   - Manejo de declaración XML duplicada")
        print()
    
    print("SOLUCIÓN:")
    print("  1. Descarga los archivos actualizados de Claude")
    print("  2. Reemplaza los archivos en tu proyecto")
    print("  3. Guarda y ejecuta: python verificar_parches.py")
    print("  4. Cuando todo esté ✅, ejecuta: python main.py")

print()
print("="*70)