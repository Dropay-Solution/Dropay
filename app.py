from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Función para conectar a la base de datoss
def obtener_conexion():
    conn = sqlite3.connect('tienda.db')
    conn.row_factory = sqlite3.Row
    return conn

# Ruta de inicio
@app.route('/')
def index():
    if 'user_role' in session:
        if session['user_role'] == 'admin':
            return redirect(url_for('admin_panel'))
        elif session['user_role'] == 'cliente':
            return redirect(url_for('cliente_panel'))
    return redirect(url_for('login'))

# Ruta para iniciar sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form['nombre']
        contraseña = request.form['contraseña']

        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE nombre = ? AND contraseña = ?", (nombre, contraseña))
        usuario = cursor.fetchone()

        if usuario:
            session['username'] = usuario['nombre']
            session['user_role'] = usuario['rol']
            session['user_id'] = usuario['id']
            if usuario['rol'] == 'admin':
                return redirect(url_for('admin_panel'))
            else:
                return redirect(url_for('cliente_panel'))
        else:
            return render_template('login.html', error="Credenciales incorrectas")
    
    return render_template('login.html')

# Panel del administrador
@app.route('/admin')
def admin_panel():
    if 'user_role' in session and session['user_role'] == 'admin':
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos")
        productos = cursor.fetchall()
        conn.close()
        return render_template('admin.html', productos=productos)
    else:
        return redirect(url_for('login'))

# Ruta para agregar producto (Administrador)
@app.route('/agregar_producto', methods=['GET', 'POST'])
def agregar_producto():
    if 'user_role' in session and session['user_role'] == 'admin':
        if request.method == 'POST':
            nombre = request.form['nombre']
            precio = request.form['precio']

            # Procesar la imagen
            if 'imagen' not in request.files:
                return "No se ha subido ninguna imagen"
            archivo_imagen = request.files['imagen']

            if archivo_imagen.filename == '':
                return "Nombre de archivo inválido"

            if archivo_imagen:
                filename = secure_filename(archivo_imagen.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                archivo_imagen.save(filepath)

                # Guardar el nuevo producto en la base de datos
                conn = obtener_conexion()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO productos (nombre, precio, imagen)
                    VALUES (?, ?, ?)
                """, (nombre, precio, filename))
                conn.commit()
                conn.close()

                return redirect(url_for('admin_panel'))

        return render_template('agregar_producto.html')
    else:
        return redirect(url_for('login'))

# Ruta para ver los productos enviados (Administrador)
@app.route('/admin/enviados')
def admin_ver_enviados():
    if 'user_role' in session and session['user_role'] == 'admin':
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id, p.nombre AS producto_nombre, u.nombre AS usuario_nombre, e.destino, e.celular, 
                   e.fecha_envio, e.estado, p.imagen
            FROM envios e
            JOIN productos p ON e.producto_id = p.id
            JOIN usuarios u ON e.usuario_id = u.id
            ORDER BY e.fecha_envio DESC
        """)
        envios = cursor.fetchall()
        conn.close()
        return render_template('admin_enviados.html', envios=envios)
    else:
        return redirect(url_for('login'))

# Ruta para cambiar el estado de un envío (Administrador)
@app.route('/cambiar_estado/<int:envio_id>', methods=['POST'])
def cambiar_estado(envio_id):
    nuevo_estado = request.form['nuevo_estado']
    
    conn = obtener_conexion()
    cursor = conn.cursor()

    # Actualizar el estado del envío en la base de datos
    cursor.execute("UPDATE envios SET estado = ? WHERE id = ?", (nuevo_estado, envio_id))

    # Si se marca como entregado, cambiar el campo entregado a 1
    if nuevo_estado == 'Entregado':
        cursor.execute("UPDATE envios SET entregado = 1 WHERE id = ?", (envio_id,))
    
    conn.commit()
    conn.close()

    return redirect(url_for('admin_ver_enviados'))

    
@app.route('/marcar_entregado/<int:envio_id>', methods=['POST'])
def marcar_entregado(envio_id):
    if 'user_role' in session and session['user_role'] == 'admin':
        conn = obtener_conexion()
        cursor = conn.cursor()

        # Actualizar el estado del envío a 'entregado'
        cursor.execute("UPDATE envios SET entregado = 1 WHERE id = ?", (envio_id,))
        conn.commit()
        conn.close()

        return redirect(url_for('admin_ver_enviados'))
    else:
        return redirect(url_for('login'))


# Panel del cliente
@app.route('/cliente')
def cliente_panel():
    if 'user_role' in session and session['user_role'] == 'cliente':
        conn = obtener_conexion()
        cursor = conn.cursor()

        # Obtener todos los productos para el cliente
        cursor.execute("SELECT * FROM productos")
        productos = cursor.fetchall()

        # Obtener el saldo basado en los productos entregados
        cursor.execute("""
            SELECT SUM(p.precio) 
            FROM productos p 
            JOIN envios e ON p.id = e.producto_id 
            WHERE e.entregado = 1 AND e.usuario_id = ?
        """, (session['user_id'],))
        saldo = cursor.fetchone()[0]

        conn.close()

        # Si no hay saldo, se asigna 0
        if saldo is None:
            saldo = 0

        # Pasar el saldo al template
        return render_template('cliente.html', productos=productos, saldo=saldo)
    else:
        return redirect(url_for('login'))



# Ruta para ver los productos enviados (Cliente)
@app.route('/enviados')
def ver_enviados():
    if 'user_role' in session and session['user_role'] == 'cliente':
        conn = obtener_conexion()
        cursor = conn.cursor()

        # Obtener el parámetro de orden (ascendente o descendente)
        orden = request.args.get('orden', 'desc')  # Por defecto 'desc' para ordenar de más reciente a más antiguo

        if orden == 'asc':
            cursor.execute("""
                SELECT e.id, p.nombre AS producto_nombre, e.nombre_cliente, e.destino, e.celular, 
                       e.fecha_envio, e.estado
                FROM envios e
                JOIN productos p ON e.producto_id = p.id
                WHERE e.usuario_id = ?
                ORDER BY e.fecha_envio ASC
            """, (session['user_id'],))
        else:
            cursor.execute("""
                SELECT e.id, p.nombre AS producto_nombre, e.nombre_cliente, e.destino, e.celular, 
                       e.fecha_envio, e.estado
                FROM envios e
                JOIN productos p ON e.producto_id = p.id
                WHERE e.usuario_id = ?
                ORDER BY e.fecha_envio DESC
            """, (session['user_id'],))

        envios = cursor.fetchall()
        conn.close()

        return render_template('enviados_cliente.html', envios=envios, orden=orden)
    else:
        return redirect(url_for('login'))


# Ruta para enviar un producto (Cliente)
@app.route('/enviar_producto', methods=['POST'])
def enviar_producto():
    if 'user_role' in session and session['user_role'] == 'cliente':
        producto_id = request.form['producto_id']
        nombre_cliente_final = request.form['nombre_cliente_final']
        destino = request.form['destino']
        celular = request.form['celular']
        usuario_id = session['user_id']  # Usar el ID del cliente logueado (cliente1, cliente2, etc.)

        conn = obtener_conexion()
        cursor = conn.cursor()

        # Insertar el nuevo envío en la tabla envios
        cursor.execute("""
            INSERT INTO envios (producto_id, nombre_cliente, destino, celular, fecha_envio, estado, usuario_id)
            VALUES (?, ?, ?, ?, datetime('now'), 'Enviado', ?)
        """, (producto_id, nombre_cliente_final, destino, celular, usuario_id))

        conn.commit()
        conn.close()

        return redirect(url_for('ver_enviados'))
    else:
        return redirect(url_for('login'))


# Ruta para ver la billetera (Cliente)
@app.route('/billetera')
def billetera():
    if 'user_role' in session and session['user_role'] == 'cliente':
        conn = obtener_conexion()
        cursor = conn.cursor()

        # Obtener el saldo basado en los productos entregados
        cursor.execute("""
            SELECT SUM(p.precio) 
            FROM productos p 
            JOIN envios e ON p.id = e.producto_id 
            WHERE e.entregado = 1 AND e.usuario_id = ?
        """, (session['user_id'],))
        saldo = cursor.fetchone()[0]  # Se obtiene el saldo total
        conn.close()

        if saldo is None:
            saldo = 0  # Si no hay productos entregados, el saldo es 0
        return render_template('billetera.html', saldo=saldo)
    else:
        return redirect(url_for('login'))

    

# Ruta para editar un producto (Administrador)
@app.route('/editar_producto/<int:producto_id>', methods=['GET', 'POST'])
def editar_producto(producto_id):
    conn = obtener_conexion()
    cursor = conn.cursor()

    # Obtener el producto actual
    cursor.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
    producto = cursor.fetchone()

    if request.method == 'POST':
        # Obtener los nuevos valores del formulario
        nombre = request.form['nombre']
        precio = request.form['precio']

        # Actualizar el producto en la base de datos
        cursor.execute("""
            UPDATE productos
            SET nombre = ?, precio = ?
            WHERE id = ?
        """, (nombre, precio, producto_id))

        conn.commit()
        conn.close()

        return redirect(url_for('admin_panel'))

    conn.close()
    return render_template('editar_producto.html', producto=producto)

# Ruta para eliminar un producto (Administrador)
@app.route('/eliminar_producto/<int:producto_id>', methods=['POST'])
def eliminar_producto(producto_id):
    if 'user_role' in session and session['user_role'] == 'admin':
        conn = obtener_conexion()
        cursor = conn.cursor()

        # Eliminar el producto de la base de datos
        cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
        conn.commit()
        conn.close()

        return redirect(url_for('admin_panel'))
    else:
        return redirect(url_for('login'))


# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
