import sqlite3

# Conectar a la base de datos
conexion = sqlite3.connect('tienda.db')
cursor = conexion.cursor()

# Crear los usuarios
usuarios = [
    ('admin', 'adminpass', 'admin'),
    ('cliente1', 'cliente1pass', 'cliente'),
    ('cliente2', 'cliente2pass', 'cliente')
]

# Insertar los usuarios en la tabla usuarios
cursor.executemany('''
    INSERT INTO usuarios (nombre, contraseña, rol)
    VALUES (?, ?, ?)
''', usuarios)

# Confirmar los cambios
conexion.commit()

# Verificar los usuarios insertados
cursor.execute("SELECT * FROM usuarios")
usuarios_insertados = cursor.fetchall()
for usuario in usuarios_insertados:
    print(usuario)

# Cerrar la conexión
conexion.close()
