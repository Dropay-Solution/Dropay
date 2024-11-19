import sqlite3

def obtener_conexion():
    conn = sqlite3.connect('tienda.db')
    return conn

def crear_base_datos():
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # Tabla de productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            precio REAL,
            imagen TEXT
        )
    ''')

    # Tabla de envíos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS envios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            nombre_cliente TEXT,
            destino TEXT,
            celular TEXT,
            entregado BOOLEAN DEFAULT 0,
            FOREIGN KEY(producto_id) REFERENCES productos(id)
        )
    ''')

    conn.commit()
    conn.close()

# Ejecutar creación de la base de datos al iniciar
crear_base_datos()
