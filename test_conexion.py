"""
Script de Verificación de Conexión PostgreSQL

Verifica que la base de datos esté correctamente configurada
y muestra información útil del sistema.

Uso:
    python test_conexion.py
"""
import sys
from pathlib import Path

# Solución para imports: agregar directorio raíz al path
directorio_raiz = Path(__file__).parent
if str(directorio_raiz) not in sys.path:
    sys.path.insert(0, str(directorio_raiz))

from config import Config
from src.database.connection import DatabaseManager

def print_separator(char="=", length=60):
    """Imprime una línea separadora"""
    print(char * length)

def test_basic_connection():
    """Prueba la conexión básica a PostgreSQL"""
    print("\n🔌 PROBANDO CONEXIÓN A POSTGRESQL")
    print_separator()
    
    print(f"\nConfiguración:")
    print(f"  Host: {Config.DB_HOST}")
    print(f"  Puerto: {Config.DB_PORT}")
    print(f"  Base de datos: {Config.DB_NAME}")
    print(f"  Usuario: {Config.DB_USER}")
    print(f"  Password: {'*' * len(Config.DB_PASSWORD)} (oculta)")
    
    db = DatabaseManager()
    
    print("\n⏳ Conectando...")
    
    if db.test_connection():
        print("✅ ¡CONEXIÓN EXITOSA!\n")
        return db
    else:
        print("❌ NO SE PUDO CONECTAR\n")
        print("💡 Verifica:")
        print("  1. PostgreSQL está corriendo")
        print("  2. Credenciales en .env son correctas")
        print("  3. Base de datos 'facturabot' existe")
        print("  4. Usuario tiene permisos de acceso\n")
        return None

def show_database_info(db):
    """Muestra información de la base de datos"""
    print("\n📊 INFORMACIÓN DE LA BASE DE DATOS")
    print_separator()
    
    try:
        with db.get_cursor() as cursor:
            # Versión de PostgreSQL
            cursor.execute("SELECT version();")
            version = cursor.fetchone()['version']
            print(f"\n✅ Versión de PostgreSQL:")
            print(f"   {version.split(',')[0]}")
            
            # Base de datos actual
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()['current_database']
            print(f"\n✅ Base de datos actual: {db_name}")
            
            # Tamaño de la base de datos
            cursor.execute(f"""
                SELECT pg_size_pretty(pg_database_size('{db_name}'));
            """)
            size = cursor.fetchone()['pg_size_pretty']
            print(f"✅ Tamaño de la base de datos: {size}")
            
    except Exception as e:
        print(f"❌ Error al obtener información: {e}")

def show_tables_info(db):
    """Muestra información de las tablas"""
    print("\n\n📋 TABLAS EN LA BASE DE DATOS")
    print_separator()
    
    try:
        with db.get_cursor() as cursor:
            # Listar tablas
            cursor.execute("""
                SELECT 
                    table_name,
                    (SELECT COUNT(*) 
                     FROM information_schema.columns 
                     WHERE columns.table_name = tables.table_name) as num_columns
                FROM information_schema.tables tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            tablas = cursor.fetchall()
            
            if not tablas:
                print("\n⚠️  No se encontraron tablas")
                print("   Ejecuta: python setup_db.py")
                return False
            
            print(f"\n✅ {len(tablas)} tabla(s) encontrada(s):\n")
            
            for i, tabla in enumerate(tablas, 1):
                nombre = tabla['table_name']
                cols = tabla['num_columns']
                
                # Contar registros
                cursor.execute(f"SELECT COUNT(*) as count FROM {nombre}")
                count = cursor.fetchone()['count']
                
                print(f"   {i}. {nombre}")
                print(f"      Columnas: {cols} | Registros: {count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error al listar tablas: {e}")
        return False

def show_table_details(db):
    """Muestra detalles de la tabla facturas"""
    print("\n\n🔍 ESTRUCTURA DE TABLA 'facturas'")
    print_separator()
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = 'facturas'
                ORDER BY ordinal_position
            """)
            
            columnas = cursor.fetchall()
            
            if not columnas:
                print("\n⚠️  Tabla 'facturas' no existe")
                return
            
            print(f"\n✅ {len(columnas)} columna(s):\n")
            
            for col in columnas[:15]:  # Mostrar primeras 15
                nombre = col['column_name']
                tipo = col['data_type']
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = col['column_default'] or "Sin default"
                
                print(f"   • {nombre}")
                print(f"     Tipo: {tipo} | {nullable}")
                if len(default) < 50:
                    print(f"     Default: {default}")
            
            if len(columnas) > 15:
                print(f"\n   ... y {len(columnas) - 15} columnas más")
            
    except Exception as e:
        print(f"❌ Error al obtener estructura: {e}")

def show_views_info(db):
    """Muestra información de las vistas"""
    print("\n\n👁️  VISTAS EN LA BASE DE DATOS")
    print_separator()
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT table_name
                FROM information_schema.views
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            vistas = cursor.fetchall()
            
            if not vistas:
                print("\n⚠️  No se encontraron vistas")
                return
            
            print(f"\n✅ {len(vistas)} vista(s) creada(s):\n")
            
            for vista in vistas:
                print(f"   • {vista['table_name']}")
            
    except Exception as e:
        print(f"❌ Error al listar vistas: {e}")

def test_basic_queries(db):
    """Prueba consultas básicas"""
    print("\n\n🧪 PROBANDO CONSULTAS BÁSICAS")
    print_separator()
    
    try:
        with db.get_cursor() as cursor:
            # Contar usuarios
            cursor.execute("SELECT COUNT(*) as count FROM usuarios")
            usuarios = cursor.fetchone()['count']
            print(f"\n✅ Usuarios en sistema: {usuarios}")
            
            # Contar proveedores
            cursor.execute("SELECT COUNT(*) as count FROM proveedores")
            proveedores = cursor.fetchone()['count']
            print(f"✅ Proveedores registrados: {proveedores}")
            
            # Contar facturas
            cursor.execute("SELECT COUNT(*) as count FROM facturas")
            facturas = cursor.fetchone()['count']
            print(f"✅ Facturas procesadas: {facturas}")
            
            # Contar detalles
            cursor.execute("SELECT COUNT(*) as count FROM detalles_factura")
            detalles = cursor.fetchone()['count']
            print(f"✅ Detalles de facturas: {detalles}")
            
            # Si hay facturas, mostrar resumen
            if facturas > 0:
                cursor.execute("""
                    SELECT 
                        SUM(total) as total_general,
                        SUM(iva) as total_iva,
                        COUNT(DISTINCT proveedor_id) as proveedores_unicos
                    FROM facturas
                """)
                resumen = cursor.fetchone()
                
                print(f"\n📊 Resumen de facturas:")
                print(f"   Total general: ${resumen['total_general']:,.2f}")
                print(f"   Total IVA: ${resumen['total_iva']:,.2f}")
                print(f"   Proveedores únicos: {resumen['proveedores_unicos']}")
            
    except Exception as e:
        print(f"❌ Error en consultas: {e}")

def test_insert_capability(db):
    """Prueba capacidad de inserción (sin insertar realmente)"""
    print("\n\n✏️  VERIFICANDO PERMISOS DE ESCRITURA")
    print_separator()
    
    try:
        with db.get_cursor() as cursor:
            # Probar permisos sin hacer cambios
            cursor.execute("""
                SELECT has_table_privilege('usuarios', 'INSERT') as can_insert,
                       has_table_privilege('usuarios', 'UPDATE') as can_update,
                       has_table_privilege('usuarios', 'DELETE') as can_delete
            """)
            
            perms = cursor.fetchone()
            
            print(f"\n✅ Permisos en tabla 'usuarios':")
            print(f"   INSERT: {'✓' if perms['can_insert'] else '✗'}")
            print(f"   UPDATE: {'✓' if perms['can_update'] else '✗'}")
            print(f"   DELETE: {'✓' if perms['can_delete'] else '✗'}")
            
            if not (perms['can_insert'] and perms['can_update']):
                print("\n⚠️  Permisos limitados detectados")
            
    except Exception as e:
        print(f"❌ Error al verificar permisos: {e}")

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("  FacturaBot - Verificación de Base de Datos")
    print("="*60)
    
    # 1. Probar conexión básica
    db = test_basic_connection()
    
    if not db:
        print("\n" + "="*60)
        print("  ❌ VERIFICACIÓN FALLIDA")
        print("="*60 + "\n")
        sys.exit(1)
    
    # 2. Mostrar información general
    show_database_info(db)
    
    # 3. Mostrar tablas
    tablas_ok = show_tables_info(db)
    
    if not tablas_ok:
        print("\n⚠️  Base de datos sin tablas")
        print("   Ejecuta: python setup_db.py\n")
        sys.exit(1)
    
    # 4. Detalles de tabla facturas
    show_table_details(db)
    
    # 5. Vistas
    show_views_info(db)
    
    # 6. Probar consultas
    test_basic_queries(db)
    
    # 7. Verificar permisos
    test_insert_capability(db)
    
    # Mensaje final
    print("\n" + "="*60)
    print("  🎉 VERIFICACIÓN COMPLETADA EXITOSAMENTE")
    print("="*60 + "\n")
    print("La base de datos está lista para usar.")
    print("\nPróximos pasos:")
    print("  1. Procesar facturas: python main.py")
    print("  2. Ver documentación: README.md\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Verificación cancelada por el usuario\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)