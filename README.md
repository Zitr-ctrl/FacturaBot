# FacturaBot - Procesador de Facturas Electrónicas SRI

Sistema automatizado para procesar facturas electrónicas XML del SRI (Ecuador).

## Características

- ✅ Procesamiento de facturas XML (formato RIDE)
- ✅ Extracción automática de datos fiscales
- ✅ Validación de formato y cálculos
- ✅ Almacenamiento en PostgreSQL
- ✅ Exportación a Excel/CSV

## Tecnologías

- Python 3.11+
- PostgreSQL
- lxml (parsing XML)
- pandas (manipulación de datos)
- psycopg2 (conexión PostgreSQL)

## Estructura del Proyecto

```
facturabot/
├── src/
│   ├── parsers/
│   │   └── xml_parser.py       # Parser de XML SRI
│   ├── models/
│   │   └── invoice.py          # Modelo de datos
│   ├── database/
│   │   ├── connection.py       # Conexión PostgreSQL
│   │   └── schema.sql          # Schema de BD
│   ├── validators/
│   │   └── sri_validator.py    # Validaciones SRI
│   └── exporters/
│       └── excel_exporter.py   # Exportación a Excel
├── tests/
│   └── sample_invoices/        # Facturas de ejemplo
├── requirements.txt
├── config.py
└── main.py
```

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```python
from src.parsers.xml_parser import FacturaParser

parser = FacturaParser()
factura = parser.parse_xml('factura.xml')
print(factura.to_dict())
```

## Autor

Josue Ortíz - OrtizDev