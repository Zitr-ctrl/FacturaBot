"""
Script de Diagnóstico - FacturaBot
Ayuda a identificar problemas de configuración
"""
import sys
from pathlib import Path

print("\n" + "="*60)
print("  FacturaBot - Diagnóstico del Sistema")
print("="*60 + "\n")

# 1. Versión de Python
print("1️⃣  VERSIÓN DE PYTHON")
print("-" * 60)
print(f"   Versión: {sys.version}")
print(f"   Ejecutable: {sys.executable}")
print(f"   Versión requerida: 3.11+")

version_info = sys.version_info
if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 11):
    print("   ⚠️  ADVERTENCIA: Se recomienda Python 3.11 o superior")
else:
    print("   ✅ Versión compatible")

# 2. Directorio actual
print("\n2️⃣  DIRECTORIOS")
print("-" * 60)
print(f"   Directorio actual: {Path.cwd()}")
print(f"   Directorio del script: {Path(__file__).parent}")

# Agregar al path
directorio_raiz = Path(__file__).parent
sys.path.insert(0, str(directorio_raiz))
print(f"   Directorio raíz agregado al path: {directorio_raiz}")

# 3. Verificar estructura de carpetas
print("\n3️⃣  ESTRUCTURA DEL PROYECTO")
print("-" * 60)

carpetas_requeridas = [
    'src',
    'src/database',
    'src/parsers',
    'src/models',
    'src/validators',
    'src/exporters',
    'tests',
    'tests/sample_invoices'
]

for carpeta in carpetas_requeridas:
    ruta = directorio_raiz / carpeta
    if ruta.exists():
        print(f"   ✓ {carpeta}/")
    else:
        print(f"   ✗ {carpeta}/ - FALTA")

# 4. Verificar archivos __init__.py
print("\n4️⃣  ARCHIVOS __init__.py")
print("-" * 60)

init_files = [
    'src/__init__.py',
    'src/database/__init__.py',
    'src/parsers/__init__.py',
    'src/models/__init__.py',
    'src/validators/__init__.py',
    'src/exporters/__init__.py'
]

for init_file in init_files:
    ruta = directorio_raiz / init_file
    if ruta.exists():
        print(f"   ✓ {init_file}")
    else:
        print(f"   ✗ {init_file} - FALTA (crear archivo vacío)")

# 5. Verificar archivos clave
print("\n5️⃣  ARCHIVOS PRINCIPALES")
print("-" * 60)

archivos_clave = [
    'main.py',
    'config.py',
    'requirements.txt',
    '.env',
    'src/database/schema.sql',
    'src/parsers/xml_parser.py',
    'tests/sample_invoices/factura_ejemplo_001.xml'
]

for archivo in archivos_clave:
    ruta = directorio_raiz / archivo
    if ruta.exists():
        print(f"   ✓ {archivo}")
    else:
        print(f"   ✗ {archivo} - FALTA")

# 6. Intentar imports
print("\n6️⃣  PRUEBA DE IMPORTS")
print("-" * 60)

imports_prueba = [
    ('config', 'Configuración'),
    ('src.parsers.xml_parser', 'Parser XML'),
    ('src.models.invoice', 'Modelos'),
    ('src.validators.sri_validator', 'Validador SRI'),
    ('src.database.connection', 'Base de datos'),
    ('src.exporters.excel_exporter', 'Exportador Excel')
]

errores_import = []

for modulo, descripcion in imports_prueba:
    try:
        __import__(modulo)
        print(f"   ✓ {descripcion} ({modulo})")
    except ImportError as e:
        print(f"   ✗ {descripcion} ({modulo}) - ERROR")
        errores_import.append((modulo, str(e)))

# 7. Verificar dependencias instaladas
print("\n7️⃣  DEPENDENCIAS DE PYTHON")
print("-" * 60)

dependencias = [
    'lxml',
    'psycopg2',
    'pandas',
    'openpyxl',
    'dotenv'
]

dependencias_faltantes = []

for dep in dependencias:
    try:
        if dep == 'dotenv':
            __import__('dotenv')
        else:
            __import__(dep)
        print(f"   ✓ {dep}")
    except ImportError:
        print(f"   ✗ {dep} - NO INSTALADO")
        dependencias_faltantes.append(dep)

# 8. Verificar archivo .env
print("\n8️⃣  CONFIGURACIÓN (.env)")
print("-" * 60)

env_path = directorio_raiz / '.env'
if env_path.exists():
    print("   ✓ Archivo .env existe")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        import os
        print(f"   DB_HOST: {os.getenv('DB_HOST', 'NO CONFIGURADO')}")
        print(f"   DB_PORT: {os.getenv('DB_PORT', 'NO CONFIGURADO')}")
        print(f"   DB_NAME: {os.getenv('DB_NAME', 'NO CONFIGURADO')}")
        print(f"   DB_USER: {os.getenv('DB_USER', 'NO CONFIGURADO')}")
        
        password = os.getenv('DB_PASSWORD', '')
        if password:
            print(f"   DB_PASSWORD: {'*' * len(password)} (configurado)")
        else:
            print(f"   DB_PASSWORD: NO CONFIGURADO")
    except:
        print("   ⚠️  Error al leer .env")
else:
    print("   ✗ Archivo .env NO EXISTE")
    print("   💡 Copia .env.example a .env y configúralo")

# 9. Probar conexión a PostgreSQL (si está configurado)
print("\n9️⃣  CONEXIÓN A POSTGRESQL")
print("-" * 60)

try:
    from src.database.connection import DatabaseManager
    
    db = DatabaseManager()
    if db.test_connection():
        print("   ✅ Conexión a PostgreSQL exitosa")
        
        # Contar tablas
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            num_tablas = cursor.fetchone()['count']
            print(f"   📊 Tablas en base de datos: {num_tablas}")
            
            if num_tablas < 4:
                print("   ⚠️  Faltan tablas, ejecuta: python setup_db.py")
    else:
        print("   ✗ No se pudo conectar a PostgreSQL")
        print("   💡 Verifica que PostgreSQL esté corriendo")
        print("   💡 Verifica credenciales en .env")
except Exception as e:
    print(f"   ⚠️  No se pudo verificar PostgreSQL: {str(e)[:50]}")
    print("   💡 PostgreSQL es opcional para pruebas iniciales")

# RESUMEN FINAL
print("\n" + "="*60)
print("  RESUMEN DEL DIAGNÓSTICO")
print("="*60 + "\n")

problemas = []

if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 11):
    problemas.append("Python antiguo (se recomienda 3.11+)")

if any(not (directorio_raiz / carpeta).exists() for carpeta in carpetas_requeridas):
    problemas.append("Faltan carpetas del proyecto")

if any(not (directorio_raiz / init).exists() for init in init_files):
    problemas.append("Faltan archivos __init__.py")

if dependencias_faltantes:
    problemas.append(f"Dependencias faltantes: {', '.join(dependencias_faltantes)}")

if errores_import:
    problemas.append("Errores de importación")

if not env_path.exists():
    problemas.append("Falta archivo .env")

if problemas:
    print("❌ SE ENCONTRARON PROBLEMAS:\n")
    for i, problema in enumerate(problemas, 1):
        print(f"   {i}. {problema}")
    
    print("\n💡 SOLUCIONES RECOMENDADAS:\n")
    
    if "Dependencias faltantes" in str(problemas):
        print("   → Ejecuta: pip install -r requirements.txt")
    
    if "Faltan archivos __init__.py" in str(problemas):
        print("   → Crea archivos __init__.py vacíos en src/ y subcarpetas")
    
    if "Falta archivo .env" in str(problemas):
        print("   → Ejecuta: python setup_db.py")
        print("   → O copia .env.example a .env y edítalo")
    
    if errores_import:
        print("\n   Errores de importación detectados:")
        for modulo, error in errores_import:
            print(f"     - {modulo}: {error[:60]}")
    
    print("\n   📖 Ver guía completa: ERRORES_COMUNES.md")
else:
    print("✅ ¡TODO ESTÁ CONFIGURADO CORRECTAMENTE!")
    print("\n   Próximos pasos:")
    print("   1. Ejecuta: python main.py")
    print("   2. Revisa los archivos generados en exports/")
    print("\n   ¡FacturaBot está listo para usar! 🎉")

print("\n" + "="*60 + "\n")