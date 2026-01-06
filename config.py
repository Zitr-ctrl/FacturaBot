"""
Configuración de FacturaBot
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración general del sistema"""
    
    # Base de datos PostgreSQL
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'facturabot')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '12345')
    
    # Rutas
    UPLOAD_FOLDER = 'uploads/facturas'
    EXPORT_FOLDER = 'exports'
    
    # Validaciones SRI
    RUC_LENGTH = 13
    FECHA_FORMAT = '%d/%m/%Y'
    
    # Límites
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    @classmethod
    def get_db_url(cls):
        """Retorna la URL de conexión a PostgreSQL"""
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"