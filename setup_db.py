"""
Script de configuración automática de PostgreSQL para FacturaBot

Este script:
1. Crea la base de datos 'facturabot' si no existe
2. Ejecuta el schema.sql para crear todas las tablas
3. Verifica la instalación

Uso:
    python setup_db.py
"""
import psycopg2
from psycopg2 import Error
import sys
from pathlib import Path

# Solución para imports: agregar directorio raíz al path
directorio_raiz = Path(__file__).parent
if str(directorio_raiz) not in sys.path:
    sys.path.insert(0, str(directorio_raiz))

def get_credentials():
    """Solicita credenciales de PostgreSQL al usuario"""
    print("\n" + "="*60)
    print("CONFIGURACIÓN DE BASE DE DATOS - FacturaBot")
    print("="*60 + "\n")
    
    print("Ingresa las credenciales de PostgreSQL:")
    print("(Si instalaste PostgreSQL localmente, el usuario es 'postgres')\n")
    
    host = input("Host [localhost]: ").strip() or "localhost"
    port = input("Puerto [5432]: ").strip() or "5432"
    user = input("Usuario [postgres]: ").strip() or "postgres"
    password = input("Password: ").strip()
    
    if not password:
        print("\n❌ La contraseña no puede estar vacía")
        sys.exit(1)
    
    return {
        'host': host,
        'port': port,
        'user': user,
        'password': password
    }

def test_connection(creds):
    """Prueba la conexión a PostgreSQL"""
    print("\n🔌 Probando conexión a PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host=creds['host'],
            port=creds['port'],
            database='postgres',  # Base de datos por defecto
            user=creds['user'],
            password=creds['password']
        )
        conn.close()
        print("✅ Conexión exitosa\n")
        return True
    except Error as e:
        print(f"❌ Error de conexión: {e}\n")
        print("💡 Verifica:")
        print("  1. PostgreSQL está instalado y corriendo")
        print("  2. Las credenciales son correctas")
        print("  3. El usuario tiene permisos para crear bases de datos\n")
        return False

def create_database(creds):
    """Crea la base de datos facturabot"""
    print("📦 Creando base de datos 'facturabot'...")
    
    try:
        # Conectar a la base de datos postgres
        conn = psycopg2.connect(
            host=creds['host'],
            port=creds['port'],
            database='postgres',
            user=creds['user'],
            password=creds['password']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Verificar si ya existe
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = 'facturabot'"
        )
        exists = cursor.fetchone()
        
        if exists:
            print("ℹ️  Base de datos 'facturabot' ya existe")
            respuesta = input("¿Deseas recrearla? Esto eliminará todos los datos (s/N): ")
            
            if respuesta.lower() == 's':
                # Desconectar usuarios activos
                cursor.execute("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = 'facturabot' AND pid <> pg_backend_pid()
                """)
                
                # Eliminar base de datos
                cursor.execute("DROP DATABASE facturabot")
                print("🗑️  Base de datos anterior eliminada")
                
                # Crear nueva
                cursor.execute("CREATE DATABASE facturabot")
                print("✅ Base de datos 'facturabot' creada\n")
            else:
                print("ℹ️  Usando base de datos existente\n")
        else:
            # Crear base de datos nueva
            cursor.execute("CREATE DATABASE facturabot")
            print("✅ Base de datos 'facturabot' creada exitosamente\n")
        
        cursor.close()
        conn.close()
        return True
        
    except Error as e:
        print(f"❌ Error al crear base de datos: {e}\n")
        return False

def create_tables(creds):
    """Ejecuta el schema.sql para crear tablas"""
    print("🏗️  Creando tablas...")
    
    # Buscar archivo schema.sql
    schema_path = Path(__file__).parent / 'src' / 'database' / 'schema.sql'
    
    if not schema_path.exists():
        print(f"❌ No se encontró el archivo: {schema_path}\n")
        return False
    
    try:
        # Conectar a facturabot
        conn = psycopg2.connect(
            host=creds['host'],
            port=creds['port'],
            database='facturabot',
            user=creds['user'],
            password=creds['password']
        )
        
        cursor = conn.cursor()
        
        # Leer y ejecutar schema.sql
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        conn.commit()
        
        print("✅ Tablas creadas exitosamente\n")
        
        # Verificar tablas creadas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tablas = cursor.fetchall()
        print(f"📊 Tablas creadas ({len(tablas)}):")
        for tabla in tablas:
            print(f"   ✓ {tabla[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Error as e:
        print(f"❌ Error al crear tablas: {e}\n")
        return False

def verify_installation(creds):
    """Verifica que todo esté correctamente instalado"""
    print("\n" + "="*60)
    print("VERIFICACIÓN DE INSTALACIÓN")
    print("="*60 + "\n")
    
    try:
        conn = psycopg2.connect(
            host=creds['host'],
            port=creds['port'],
            database='facturabot',
            user=creds['user'],
            password=creds['password']
        )
        
        cursor = conn.cursor()
        
        # Verificar versión de PostgreSQL
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL versión:")
        print(f"   {version.split(',')[0]}\n")
        
        # Contar tablas
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        num_tablas = cursor.fetchone()[0]
        print(f"✅ Tablas creadas: {num_tablas}\n")
        
        # Verificar usuario admin
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        num_usuarios = cursor.fetchone()[0]
        print(f"✅ Usuarios en sistema: {num_usuarios}\n")
        
        # Verificar vistas
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.views 
            WHERE table_schema = 'public'
        """)
        num_vistas = cursor.fetchone()[0]
        print(f"✅ Vistas creadas: {num_vistas}\n")
        
        cursor.close()
        conn.close()
        
        print("🎉 ¡Instalación completa y verificada!")
        return True
        
    except Error as e:
        print(f"❌ Error en verificación: {e}\n")
        return False

def create_env_file(creds):
    """Crea/actualiza el archivo .env con las credenciales"""
    print("\n📝 Configurando archivo .env...")
    
    env_content = f"""# Configuración de Base de Datos PostgreSQL
DB_HOST={creds['host']}
DB_PORT={creds['port']}
DB_NAME=facturabot
DB_USER={creds['user']}
DB_PASSWORD={creds['password']}

# Configuración de la aplicación
ENVIRONMENT=development
DEBUG=True
"""
    
    env_path = Path(__file__).parent / '.env'
    
    # Si existe .env, preguntar si sobrescribir
    if env_path.exists():
        respuesta = input("¿Sobrescribir archivo .env existente? (s/N): ")
        if respuesta.lower() != 's':
            print("ℹ️  Archivo .env no modificado")
            return
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Archivo .env creado/actualizado\n")

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("  FacturaBot - Configuración Automática de PostgreSQL")
    print("="*60)
    
    # 1. Obtener credenciales
    creds = get_credentials()
    
    # 2. Probar conexión
    if not test_connection(creds):
        sys.exit(1)
    
    # 3. Crear base de datos
    if not create_database(creds):
        sys.exit(1)
    
    # 4. Crear tablas
    if not create_tables(creds):
        sys.exit(1)
    
    # 5. Verificar instalación
    if not verify_installation(creds):
        sys.exit(1)
    
    # 6. Crear archivo .env
    create_env_file(creds)
    
    # Mensaje final
    print("\n" + "="*60)
    print("  🎉 CONFIGURACIÓN COMPLETADA")
    print("="*60 + "\n")
    print("Próximos pasos:")
    print("  1. Ejecuta: python test_conexion.py")
    print("  2. Prueba el sistema: python main.py")
    print("\n¡FacturaBot está listo para usar!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Configuración cancelada por el usuario\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}\n")
        sys.exit(1)