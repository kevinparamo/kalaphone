import secrets 
import os
from datetime import timedelta
from decimal import Decimal
# Descargables

from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_mail import Mail, Message
 
#Nueva Lib 
import mysql.connector
from mysql.connector import Error 

app = Flask(__name__) 
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=120)

app.config['MAIL_SERVER'] = 'smtp.gmail.com' 
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'krunker.io.link@gmail.com'
app.config['MAIL_PASSWORD'] = 'tlwrtzwgcgonvmnq'
app.config['MAIL_DEFAULT_SENDER'] = 'krunker.io.link@gmail.com'
mail = Mail(app)


@app.route("/")
def index():
    return render_template("home.html")
 

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password") 
    rol = request.form.get("rol")
    
    db_connection = mysql.connector.connect( 
        host="mysql.codeflex.com.co",
        user="AplicativoPOS",
        password="3961",
        database="AplicativoPOSfinal"
    )
    
    try:
        cursor = db_connection.cursor()
        query = "SELECT * FROM usuario WHERE Usuario = %s AND Contrasenia = %s AND rol = %s"
        cursor.execute(query, (username, password, rol))
        user = cursor.fetchone() 
        cursor.close()
        db_connection.close()
        if user:
            session['logged_in'] = True
            session['rol'] = rol
            return redirect(url_for("principal"))
        else:
            error_message = "Credenciales incorrectas"
            return render_template("mensaje.html", message=error_message)
    except Exception as e:
        error_message = "Error al procesar la solicitud: {}".format(str(e))
        return render_template("mensaje.html", message=error_message)


# Ruta para la página principal
@app.route("/principal")
def principal():
    if 'logged_in' in session and session['logged_in']:
        return render_template("principal.html")
    else:
        return render_template("warning.html")


@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    return redirect(url_for("index"))
 

# Ruta para la solicitud de recuperación de contraseña
@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    try:
        db_connection = mysql.connector.connect(
            host="mysql.codeflex.com.co",
            user="AplicativoPOS",
            password="3961",
            database="AplicativoPOSfinal"
        )
        
        email = request.form.get("email")
        token = generate_password_reset_token()
        cursor = db_connection.cursor()
        # Verificar si hay algún dato con ese usuario
        query = "SELECT id FROM generador WHERE Correo = %s"
        cursor.execute(query, (email,))
        existing_id = cursor.fetchone()
        
        if existing_id:
            # Si hay datos, actualiza el id
            query = "UPDATE generador SET id = %s WHERE Correo = %s"
            cursor.execute(query, (token, email))
        else:
            # Si no hay datos, inserta un nuevo registro
            query = "INSERT INTO generador (id, Correo) VALUES (%s, %s)"
            cursor.execute(query, (token, email))
        
        db_connection.commit()
        cursor.close()
        db_connection.close()
        send_password_reset_email(email, token)
        return render_template("mensajeenviado.html")
    except mysql.connector.Error as err:
        error_message = "Error al procesar la solicitud: {}".format(str(err))
        return render_template("mensaje.html", message=error_message)


def generate_password_reset_token():
    token = secrets.token_urlsafe(32)
    return token


def send_password_reset_email(email, token):
    # Construye el cuerpo del correo electrónico con un enlace de restablecimiento de contraseña
    reset_url = url_for('reset_password', token=token, _external=True)
    body = f"Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}"
    # Crea y envía el mensaje de correo electrónico
    msg = Message("Recuperación de Contraseña", recipients=[email])
    msg.body = body
    mail.send(msg)

#Lugar para actualizar contraseña
@app.route("/reset-password/<token>", methods=["GET"])
def reset_password(token): 
    try:
        db_connection = mysql.connector.connect(
            host="mysql.codeflex.com.co",
            user="AplicativoPOS",
            password="3961",
            database="AplicativoPOSfinal"
        )
        
        cursor = db_connection.cursor()
        # Verificar si hay algún ID que coincida con el token en la tabla de generador
        query = "SELECT id FROM generador WHERE id = %s"
        cursor.execute(query, (token,))
        existing_id = cursor.fetchone()
        
        if existing_id:
            db_connection.commit()
            cursor.close()
            db_connection.close()
            return render_template("reset.html")
        else:
            db_connection.commit()
            cursor.close()
            db_connection.close()
            error_message = "Token incorrecto"
            return render_template("mensaje.html", message=error_message)
 
    except mysql.connector.Error as err:
        error_message = "Error al procesar la solicitud: {}".format(str(err))
        return render_template("mensaje.html", message=error_message)


@app.route("/reset-passwordON/<token>",methods=["POST"])
def reset_passwordON(token): 
    try:
        # Extraer correo y contraseña del formulario enviado por el usuario
        correo_usuario = request.form.get("Correo")
        nueva_contrasenia = request.form.get("password")
        # Conexión a la base de datos
        db_connection = mysql.connector.connect(
            host="mysql.codeflex.com.co",
            user="AplicativoPOS",
            password="3961",
            database="AplicativoPOSfinal"
        )
        cursor = db_connection.cursor()
        # Verificar si hay algún registro que coincida con el token en la tabla generador
        query = "SELECT Correo FROM generador WHERE id = %s"
        cursor.execute(query, (token,))
        correo_generador = cursor.fetchone()
        if correo_generador:
            # Si el token coincide, verificar si el correo coincide con el proporcionado por el usuario
            if correo_usuario == correo_generador[0]:
                # Si los correos coinciden, actualizar la contraseña en la tabla usuario
                update_query = "UPDATE usuario SET contrasenia = %s WHERE email = %s"
                cursor.execute(update_query, (nueva_contrasenia, correo_usuario))
                db_connection.commit()
                cursor.close()
                db_connection.close()
                return render_template("mensajeenviado2.html")
            else:
                # Si los correos no coinciden, mostrar un mensaje de error
                error_message = "El correo proporcionado no coincide con el registrado para este token."
                return render_template("mensaje.html", message=error_message)
        else:
            # Si no se encuentra ningun registro con el token, mostrar un mensaje de error
            error_message = "Token incorrecto"
            return render_template("mensaje.html", message=error_message)
    except mysql.connector.Error as err:
        # Manejar errores de base de datos
        error_message = "Error al procesar la solicitud: {}".format(str(err))
        return render_template("mensaje.html", message=error_message)

# INICIO CAJA ----------------------------------------------------------------------------------------------------------- 
@app.route("/caja")
def caja():
    try:
        db_connection = mysql.connector.connect(
            host="mysql.codeflex.com.co",
            user="AplicativoPOS",
            password="3961",
            database="AplicativoPOSfinal"
        )
        cursor = db_connection.cursor()
        cursor.execute("SHOW TABLE STATUS LIKE 'venta'")
        table_status = cursor.fetchone()
        if table_status is not None:
            next_id = table_status[10]
            cursor.execute("SELECT COUNT(*) FROM venta")
            count = cursor.fetchone()[0]
            if count == 0:
                next_id = 1
            else:
                cursor.execute("SELECT MAX(id_venta) FROM venta")
                last_id = cursor.fetchone()[0]
                next_id = last_id + 1
            cursor.execute("SELECT MAX(id_factura) FROM venta")
            last_code = cursor.fetchone()[0]
            if last_code is not None:
                new_code = str(int(last_code) + 1).zfill(7)
            else:
                new_code = "0000001"
            cursor.execute("SELECT * FROM venta")
            myresult = cursor.fetchall()
            insertObjects = []
            columnNames = [column[0] for column in cursor.description]
            for record in myresult:
                insertObjects.append(dict(zip(columnNames, record)))
                
            cursor.execute("SELECT id_cliente FROM cliente")
            ids_clientes = cursor.fetchall()
            ids_clientes = [cliente[0] for cliente in ids_clientes]
                
            cursor.close()
            db_connection.close()
            
            if 'logged_in' in session and session['logged_in']:
                return render_template("caja.html", data=insertObjects, next_id=next_id, new_code=new_code, ids_clientes=ids_clientes)
            else:
                return render_template("warning.html")
            
        else:
            return "No se pudo obtener información de la tabla 'venta'"
    except Exception as e:
        return f"Error: {str(e)}"


@app.route('/guardarVenta', methods=['POST'])
def addGuardarVenta():
    # Credenciales de MySQL
    host = "mysql.codeflex.com.co"
    user = "AplicativoPOS"
    password = "3961"
    database = "AplicativoPOSfinal"

    # Obtener los datos del formulario de venta
    id_venta = request.form['id_venta']
    id_factura = request.form['id_factura']
    cliente_id_cliente = request.form['cliente_id_cliente']
    medio_pago = request.form['medio_pago']
    descuento = request.form['descuento']
    iva = request.form['iva']
    fecha_registro = request.form['fecha_registro']
    observaciones = request.form['observaciones']
    total_a_pagar = request.form['total_a_pagar']
    total_a_pagar_iva = request.form['total_a_pagar_iva']

    # Verificar que todos los campos necesarios estén presentes
    if id_venta and id_factura and cliente_id_cliente and medio_pago and descuento and iva and fecha_registro and observaciones and total_a_pagar:
        try:
            # Conectar a la base de datos
            db_connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            cursor = db_connection.cursor()

            # Verificar si el cliente existe en la tabla 'cliente'
            cursor.execute("SELECT * FROM cliente WHERE id_cliente = %s", (cliente_id_cliente,))
            cliente = cursor.fetchone()
            if not cliente:
                return "El cliente especificado no existe."

            # Insertar los datos en la tabla 'venta'
            sql_venta = "INSERT INTO venta (id_venta, id_factura, cliente_id_cliente, medio_pago, descuento, iva, fecha_registro, observaciones, total_a_pagar, total_a_pagar_iva_descuento) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            data_venta = (id_venta, id_factura, cliente_id_cliente, medio_pago, descuento, iva, fecha_registro, observaciones, total_a_pagar,total_a_pagar_iva)
            cursor.execute(sql_venta, data_venta)
            # Obtener el ID de la venta recién insertada 
            venta_id = cursor.lastrowid 
            # Obtener los detalles de la venta del formulario
            detalles_venta = request.form.getlist('detalle_venta')

            # Insertar los detalles de la venta en la tabla 'detalle_venta'
            for detalle in detalles_venta:
                descripcion, cantidad, valor_unitario, id_producto = detalle.split(',')
                sql_detalle_venta = "INSERT INTO detalle_venta (descripcion, cantidad, valor_unitario, id_venta, id_producto) VALUES (%s, %s, %s, %s, %s)"
                data_detalle_venta = (descripcion, cantidad, valor_unitario, venta_id, id_producto)
                cursor.execute(sql_detalle_venta, data_detalle_venta)
                
            # Confirmar los cambios en la base de datos
            db_connection.commit()
            # Cerrar la conexión
            cursor.close()
            db_connection.close()
            # Redirigir a la página de caja
            return redirect(url_for('caja'))
        except Exception as e:
            # Manejar errores
            return f"Error al guardar la venta: {str(e)}"
    else:
        # Si no se proporcionaron todos los campos necesarios
        return "Por favor, complete todos los campos."


 
@app.route('/deleteVenta/<string:id_venta>')
def deleteVenta(id_venta):
    # Credenciales de MySQL
    host = "mysql.codeflex.com.co"
    user = "AplicativoPOS"
    password = "3961"
    database = "AplicativoPOSfinal"
    try: 
        # Conectar a la base de datos
        db_connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = db_connection.cursor()
        # Verificar si existen registros relacionados en detalle_venta
        check_detalle_sql = "SELECT * FROM detalle_venta WHERE id_venta = %s"
        cursor.execute(check_detalle_sql, (id_venta,))
        detalle_result = cursor.fetchone()
        if detalle_result:
            return render_template("warning2.html")
        delete_venta_sql = "DELETE FROM venta WHERE id_venta = %s"
        cursor.execute(delete_venta_sql, (id_venta,))
        db_connection.commit()
        # Cerrar la conexión
        cursor.close()
        db_connection.close()
        return redirect(url_for('caja'))
    except Exception as e:
        print("Error al eliminar la venta:", e)
        # Si ocurre un error, hacer rollback y cerrar la conexión
        db_connection.rollback()
        cursor.close()
        db_connection.close()
        return f"Error al eliminar la venta. Por favor, inténtalo de nuevo más tarde. {str(e)}"


@app.route('/detalle_venta/<id_venta>')
def detalle_venta(id_venta):
    # Credenciales de MySQL
    host = "mysql.codeflex.com.co"
    user = "AplicativoPOS"
    password = "3961"
    database = "AplicativoPOSfinal"
    try:
        # Conectar a la base de datos
        db_connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = db_connection.cursor()
        # Ejecuta una consulta para obtener los detalles de la venta con el id_venta proporcionado
        cursor.execute("SELECT * FROM venta WHERE id_venta = %s", (id_venta,))
        venta_db = cursor.fetchone()  # Obtiene el primer resultado
        
        cursor.execute("SELECT dv.id_detalle_venta, dv.codigo, dv.cantidad, dv.descripcion, dv.valor_unitario, v.total_a_pagar, v.id_venta FROM detalle_venta dv INNER JOIN venta v ON dv.id_venta = v.id_venta WHERE dv.id_venta = %s", (id_venta,))
        productos_db = cursor.fetchall()  # Obtiene todos los resultados
        
        # Cierra la conexión con la base de datos
        cursor.close()
        db_connection.close()
        # Renderiza la plantilla con los detalles de la venta de la base de datos
        return render_template('detalle_venta.html', venta=venta_db, productos=productos_db)
    except Exception as e:
        # Maneja cualquier error que pueda ocurrir durante el proceso
        return f"Error al obtener los detalles de la venta: {str(e)}"



@app.route('/eliminar_producto_venta/<id_detalle>/<codigo_producto>/<cantidad_producto>/<valor_unitario>/<id_venta>', methods=['GET'])
def eliminarventaproducto(id_detalle,codigo_producto,cantidad_producto,valor_unitario,id_venta):
    try:   
        # Credenciales de MySQL
        host = "mysql.codeflex.com.co"
        user = "AplicativoPOS"
        password = "3961"
        database = "AplicativoPOSfinal"
        # Establecer conexión con la base de datos
        db_connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = db_connection.cursor()
        
        
        # Actualizar el stock en la tabla producto
        sql_update_stock = "UPDATE producto SET stock = stock + %s WHERE codigo = %s"
        cursor.execute(sql_update_stock, (cantidad_producto, codigo_producto))
        db_connection.commit()
        
        # Calcular el total a restar
        total_a_restar = float(valor_unitario) * int(cantidad_producto)
        
        # Actualizar el total_a_pagar en la tabla venta
        sql_update_total_a_pagar = "UPDATE venta SET total_a_pagar = total_a_pagar - %s WHERE id_venta = %s"
        cursor.execute(sql_update_total_a_pagar, (total_a_restar, id_venta))
        db_connection.commit() 
        
        
        # Consulta SQL para eliminar el registro de la tabla detalle_venta
        sql = "DELETE FROM detalle_venta WHERE id_detalle_venta = %s"
        cursor.execute(sql, (id_detalle,))
        db_connection.commit() 
        return jsonify({'mensaje': "Registro eliminado correctamente"})
    except Exception as ex:
        return jsonify({'mensaje': "Error: " + str(ex)})
    finally:
        if 'db_connection' in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()




@app.route('/guardar_detalles_venta', methods=['POST'])
def guardar_detalles_venta():
    try:
        # Credenciales de MySQL
        host = "mysql.codeflex.com.co"
        user = "AplicativoPOS"
        password = "3961"
        database = "AplicativoPOSfinal"
        # Datos específicos para la inserción
        descripcion = request.json['descripcion']
        cantidad = int(request.json['cantidad'])
        valor_unitario = float(request.json['valor_unitario'])
        id_venta = int(request.json['id_venta'])
        codigo = int(request.json['codigo'])

        print("Cantidad a restar del stock:", cantidad)
        print("Código del producto:", codigo)

        # Verificar si el producto existe y hay suficiente stock
        db_connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password, 
            database=database
        )
        cursor = db_connection.cursor()
        sql_check_product = "SELECT stock FROM producto WHERE codigo = %s"
        cursor.execute(sql_check_product, (codigo,))
        product_info = cursor.fetchone()
        if product_info is None:
            cursor.close()
            db_connection.close()
            return "Error: El producto con el código especificado no existe."
        current_stock = product_info[0]
        if current_stock < cantidad:
            cursor.close() 
            db_connection.close()
            return "Error: No hay suficiente stock para este producto."
         
        
        # Restar la cantidad vendida del stock en la tabla de productos
        new_stock = current_stock - cantidad
        sql_update_stock = "UPDATE producto SET stock = %s WHERE codigo = %s"
        cursor.execute(sql_update_stock, (new_stock, codigo))
        db_connection.commit() 
        
        
        # Multiplicar el valor unitario por la cantidad
        total_a_pagar = valor_unitario * cantidad
        
        # Actualizar el total_a_pagar en la tabla venta
        sql_update_total_a_pagar = "UPDATE venta SET total_a_pagar = total_a_pagar + %s WHERE id_venta = %s"
        cursor.execute(sql_update_total_a_pagar, (total_a_pagar, id_venta))
        db_connection.commit() 

        # Verificar si la venta existe
        sql_check_venta = "SELECT COUNT(*) FROM venta WHERE id_venta = %s"
        cursor.execute(sql_check_venta, (id_venta,))
        venta_count = cursor.fetchone()[0]
        cursor.close()
        db_connection.close()
        if venta_count == 0:
            return "Error: La venta con el ID especificado no existe."
        
        # Realizar la inserción en la tabla detalle_venta
        db_connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password, 
            database=database 
        )
        cursor = db_connection.cursor()
        sql_insert_detalle_venta = "INSERT INTO detalle_venta (descripcion, cantidad, valor_unitario, id_venta, codigo) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql_insert_detalle_venta, (descripcion, cantidad, valor_unitario, id_venta, codigo))
        
        db_connection.commit()
        cursor.close()
        db_connection.close()
        return "Detalles de venta guardados exitosamente."
    except Exception as e:
        return f"Error al guardar los detalles de la venta: {str(e)}"


    
    
@app.route("/generar_ticket/<int:id_venta>")
def generar_ticket(id_venta):
    # Credenciales de MySQL
    host = "mysql.codeflex.com.co"
    user = "AplicativoPOS"
    password = "3961"
    database = "AplicativoPOSfinal"
    try: 
        # Conectar a la base de datos
        db_connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = db_connection.cursor()
        
         
        cursor.execute("SELECT total_a_pagar, descuento, iva FROM venta WHERE id_venta = %s", (id_venta,))
        venta_data = cursor.fetchone()
        
        total_a_pagar = Decimal(venta_data[0])
        descuento = Decimal(venta_data[1])
        iva = Decimal(venta_data[2])
        
        if total_a_pagar <= descuento:
            return "Error: El descuento es mayor que el total a pagar"
        
        total_con_descuento = total_a_pagar - descuento
        
        total_con_iva = total_con_descuento * (Decimal(1) + iva / Decimal(100))
        
        cursor.execute("UPDATE venta SET total_a_pagar_iva_descuento = %s WHERE id_venta = %s", (total_con_iva, id_venta,))
        db_connection.commit()
        
        # Ejecutar una consulta para obtener los detalles de la venta con el id_venta proporcionado
        cursor.execute("SELECT dv.cantidad, dv.descripcion, dv.valor_unitario, v.total_a_pagar, v.total_a_pagar_iva_descuento , v.id_factura, v.fecha_registro  FROM detalle_venta dv INNER JOIN venta v ON dv.id_venta = v.id_venta WHERE dv.id_venta = %s", (id_venta,))
        venta_data = cursor.fetchall()
        # Cerrar la conexión con la base de datos
        cursor.close()
        db_connection.close()
        # Verificar si se encontraron datos para la venta especificada
        if not venta_data:
            return "Error: No se encontraron datos para la venta especificada"
        # Renderizar la plantilla HTML con los detalles de la venta
        return render_template("factura.html", venta=venta_data)
    except mysql.connector.Error as e:
        # Manejar cualquier error que pueda ocurrir durante el proceso
        return f"Error al generar el ticket: {str(e)}"
    
# FIN CAJA ----------------------------------------------------------------------------------------------------------- 

# INICIO CLIENTES  ----------------------------------------------------------------------------------------------------------- 
@app.route("/clientes")
def clientes():
    # Credenciales de MySQL
    host = "mysql.codeflex.com.co"
    user = "AplicativoPOS"
    password = "3961"
    database = "AplicativoPOSfinal"
    try:
        # Conectar a la base de datos
        db_connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = db_connection.cursor()

        # Obtener el próximo valor autoincremental de id_cliente
        cursor.execute("SHOW TABLE STATUS LIKE 'cliente'")
        table_status = cursor.fetchone()
        next_id = table_status[10]  # El índice 10 corresponde a la columna Auto_increment
        
        # Contar la cantidad de registros
        cursor.execute("SELECT COUNT(*) FROM cliente")
        count = cursor.fetchone()[0]
        if count == 0:
            next_id = 1  # Si no hay registros, comenzar desde 1
        else:
            # Obtener el último ID y ajustar para el siguiente ID
            cursor.execute("SELECT MAX(id_cliente) FROM cliente")
            last_id = cursor.fetchone()[0]
            next_id = last_id + 1
        
        # Obtener los clientes existentes
        cursor.execute("SELECT * FROM cliente")
        myresult = cursor.fetchall()
        # Convertir datos a diccionario
        insertObjects = []
        columnNames = [column[0] for column in cursor.description]
        for record in myresult:
            insertObjects.append(dict(zip(columnNames, record)))
        
        # Cerrar la conexión
        cursor.close()
        db_connection.close()
        
        if 'logged_in' in session and session['logged_in']:
            return render_template("clientes.html", data=insertObjects, next_id=next_id)
        else:
            return render_template("warning.html")
        
    except Exception as e:
        return f"Error al obtener clientes: {str(e)}"


@app.route('/guardarClientes', methods=['POST'])
def addGuardarClientes():    
    # Credenciales de MySQL
    host = "mysql.codeflex.com.co"
    user = "AplicativoPOS"
    password = "3961"
    database = "AplicativoPOSfinal"

    # Obtener datos del formulario
    id_cliente = request.form['id_cliente']
    tipo_identificacion = request.form['tipo_identificacion']
    numero_identificacion = request.form['numero_identificacion']
    nombre_completo = request.form['nombre_completo']
    email = request.form['email']
    direccion = request.form['direccion']
    telefono = request.form['telefono']
    
    if id_cliente and tipo_identificacion and numero_identificacion and nombre_completo and  email and direccion and  telefono:
        try:
            # Conectar a la base de datos
            db_connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            cursor = db_connection.cursor()

            # Ejecutar la inserción en la tabla 'cliente'
            sql = "INSERT INTO cliente (id_cliente, tipo_identificacion, numero_identificacion, nombre_completo, email, direccion, telefono) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            data = (id_cliente, tipo_identificacion, numero_identificacion, nombre_completo, email, direccion, telefono)
            cursor.execute(sql, data)
            db_connection.commit()

            # Cerrar la conexión
            cursor.close()
            db_connection.close()

            # Redirigir a la página de clientes
            return redirect(url_for('clientes'))
        except Exception as e:
            return f"Error al guardar el cliente: {str(e)}"
    else:
        return "Por favor, complete todos los campos."



@app.route('/deleteCliente/<string:id_cliente>')
def deleteCliente (id_cliente):
    # Credenciales de MySQL
    host = "mysql.codeflex.com.co"
    user = "AplicativoPOS"
    password = "3961"
    database = "AplicativoPOSfinal"
    try:
        # Conectar a la base de datos
        db_connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = db_connection.cursor()
        # Eliminar las ventas asociadas al cliente
        sql_delete_ventas = "DELETE FROM venta WHERE cliente_id_cliente=%s"
        cursor.execute(sql_delete_ventas, (id_cliente,))
        db_connection.commit()
        # Luego, eliminar el cliente
        sql_delete_cliente = "DELETE FROM cliente WHERE id_cliente=%s"
        cursor.execute(sql_delete_cliente, (id_cliente,))
        db_connection.commit()
        # Cerrar la conexión
        cursor.close()
        db_connection.close()
        return redirect(url_for('clientes'))
    except Exception as e:
        return f"Error al eliminar el cliente: {str(e)}"
    
    
@app.route('/editar_cliente', methods=['POST'])
def editar_cliente():
    # Credenciales de MySQL
    host = "mysql.codeflex.com.co"
    user = "AplicativoPOS" 
    password = "3961"
    database = "AplicativoPOSfinal"
    if request.method == 'POST':
        id_cliente = request.form['id_cliente']
        tipo_identificacion = request.form['edit_tipo_identificacion']
        numero_identificacion = request.form['edit_numero_identificacion']
        nombre_completo = request.form['edit_nombre_completo']
        email = request.form['edit_email']
        direccion = request.form['edit_direccion']
        telefono = request.form['edit_telefono']
        if id_cliente and tipo_identificacion and numero_identificacion and nombre_completo and email and direccion and telefono:
            try:
                # Conectar a la base de datos
                db_connection = mysql.connector.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=database
                )
                cursor = db_connection.cursor()
                # Ejecutar la actualización en la tabla 'cliente'
                sql = "UPDATE cliente SET tipo_identificacion=%s, numero_identificacion=%s, nombre_completo=%s, email=%s, direccion=%s, telefono=%s WHERE id_cliente=%s"
                data = (tipo_identificacion, numero_identificacion, nombre_completo, email, direccion, telefono, id_cliente)
                cursor.execute(sql, data)
                db_connection.commit()
                # Cerrar la conexión
                cursor.close()
                db_connection.close()
                return redirect(url_for('clientes'))
            except Exception as e:
                return jsonify({'message': f'Error al editar el cliente: {str(e)}'})
        else:
            return jsonify({'message': 'Todos los campos son obligatorios'})

# FIN CLIENTE ----------------------------------------------------------------------------------------------------------- 

# INICIO PRODUCTOS ----------------------------------------------------------------------------------------------------------- 
@app.route('/users/<id_producto>', methods=['GET'])
def get_user (id_producto):
    try:   
        # Credenciales de MySQL
        host = "mysql.codeflex.com.co"
        user = "AplicativoPOS"
        password = "3961"
        database = "AplicativoPOSfinal"
        
        # Establecer conexión con la base de datos
        db_connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = db_connection.cursor()
        # Consulta SQL para obtener los datos del producto
        sql = "SELECT id_producto, codigo, descripcion, valor_unitario FROM producto WHERE codigo = %s"
        cursor.execute(sql, (id_producto,))
        datos = cursor.fetchone()
        if datos is not None:
            producto = {'id_producto': datos[0], 'codigo': datos[1], 'descripcion': datos[2], 'valor_unitario': datos[3]}
            return jsonify({'producto': producto, 'mensaje': "producto encontrado"})
        else:
            return jsonify({'mensaje': "Producto no encontrado"})
    except Exception as ex:
        return jsonify({'mensaje': "Error: " + str(ex)})
    finally:
        if 'db_connection' in locals() and db_connection.is_connected():
            cursor.close()
            db_connection.close()


@app.route("/productos")
def productos():
    try:
        # Credenciales de MySQL
        host = "mysql.codeflex.com.co"
        user = "AplicativoPOS"
        password = "3961"
        database = "AplicativoPOSfinal"
        # Establecer conexión con la base de datos
        db_connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = db_connection.cursor()
        # Obtener el próximo valor autoincremental de id_producto
        cursor.execute("SHOW TABLE STATUS LIKE 'producto'")
        table_status = cursor.fetchone()
        next_id = table_status[10]  # El índice 10 corresponde a la columna Auto_increment

        # Contar la cantidad de registros
        cursor.execute("SELECT COUNT(*) FROM producto")
        count = cursor.fetchone()[0]
        if count == 0:
            next_id = 1  # Si no hay registros, comenzar desde 1
        else:
            # Obtener el último ID y ajustar para el siguiente ID
            cursor.execute("SELECT MAX(id_producto) FROM producto")
            last_id = cursor.fetchone()[0]
            next_id = last_id + 1
        # Obtener el último código
        cursor.execute("SELECT MAX(codigo) FROM producto")
        last_code = cursor.fetchone()[0]
        if last_code:
            new_code = str(int(last_code) + 1).zfill(5)  # Incrementar el último código y rellenar con ceros
        else:
            new_code = "00001"  # Si no hay códigos en la base de datos, iniciar desde "00001"

        # Obtener los productos existentes
        cursor.execute("SELECT * FROM producto")
        myresult = cursor.fetchall()

        # Convertir datos a diccionario
        insertObjec = []
        columnNames = [column[0] for column in cursor.description]
        for record in myresult:
            insertObjec.append(dict(zip(columnNames, record)))
            
        cursor.execute("SELECT nombre_proveedor FROM proveedor")
        proveedores = cursor.fetchall()
        proveedores = [proveedor[0] for proveedor in proveedores]

        cursor.close()
        db_connection.close()

        if 'logged_in' in session and session['logged_in']:
            return render_template("productos.html", data=insertObjec, next_id=next_id, new_code=new_code, proveedores=proveedores)
        else:
            return render_template("warning.html")

    except mysql.connector.Error as error:
        return f"Error al conectar a la base de datos: {error}"
    
    
@app.route('/guardar', methods=['POST'])
def addGuardar():
    try:
        # Credenciales de MySQL
        host = "mysql.codeflex.com.co"
        user = "AplicativoPOS"
        password = "3961"
        database = "AplicativoPOSfinal"
        # Obtener los datos del formulario
        codigo = request.form['codigo']
        descripcion = request.form['descripcion']
        categoria = request.form['categoria']
        nombre_proveedor = request.form['nombre_proveedor']
        stock = request.form['stock']
        valorUnitario = request.form['valor_unitario']
        unidadMedida = request.form['unidad_medida']
        if codigo and descripcion and categoria and nombre_proveedor and stock and valorUnitario and unidadMedida:
            # Establecer conexión con la base de datos
            db_connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            cursor = db_connection.cursor()

            # Ejecutar la inserción en la tabla producto
            sql = "INSERT INTO producto (codigo, descripcion, categoria, nombre_proveedor, stock, valor_unitario, unidad_medida) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            data = (codigo, descripcion, categoria, nombre_proveedor, stock, valorUnitario, unidadMedida)
            cursor.execute(sql, data)
            db_connection.commit()
            cursor.close()
            db_connection.close()
    except mysql.connector.Error as error:
        return f"Error al conectar a la base de datos: {error}"
    return redirect(url_for('productos'))


# Ruta para agregar stock
@app.route('/addStock', methods=['POST'])
def addStock():
    try:
        # Credenciales de MySQL
        host = "mysql.codeflex.com.co"
        user = "AplicativoPOS"
        password = "3961"
        database = "AplicativoPOSfinal"
        id_producto = request.form['id_producto']
        cantidad = request.form['cantidad']
        if id_producto and cantidad:
            # Establecer conexión con la base de datos
            db_connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            cursor = db_connection.cursor()
            # Obtener el stock actual del producto
            cursor.execute("SELECT stock FROM producto WHERE id_producto = %s", (id_producto,))
            stock_actual = cursor.fetchone()[0]
            # Sumar la cantidad proporcionada al stock actual
            nuevo_stock = stock_actual + int(cantidad)
            # Actualizar el stock en la base de datos
            cursor.execute("UPDATE producto SET stock = %s WHERE id_producto = %s", (nuevo_stock, id_producto))
            db_connection.commit()
            # Cerrar cursor y conexión a la base de datos
            cursor.close()
            db_connection.close()
    except mysql.connector.Error as error:
        return f"Error al conectar a la base de datos: {error}"
    return redirect(url_for('productos'))


@app.route('/editar_producto', methods=['POST'])
def editar_producto():
    try:
        # Credenciales de MySQL
        host = "mysql.codeflex.com.co"
        user = "AplicativoPOS"
        password = "3961"
        database = "AplicativoPOSfinal"
        if request.method == 'POST': 
            id_producto = request.form['edit_id_producto']
            codigo = request.form['edit_codigo']
            descripcion = request.form['edit_descripcion']
            categoria = request.form['edit_categoria']
            nombre_proveedor = request.form['edit_nombre_proveedor']
            valor_unitario = request.form['edit_valor_unitario']
            unidad_medida = request.form['edit_unidad_medida']
            stock = request.form['edit_stock']
            if id_producto and codigo and descripcion and categoria and nombre_proveedor and valor_unitario and unidad_medida and stock:
                # Establecer conexión con la base de datos
                db_connection = mysql.connector.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=database
                )
                cursor = db_connection.cursor()
                # Actualizar el producto en la base de datos
                sql = "UPDATE producto SET codigo = %s, descripcion = %s, categoria = %s, nombre_proveedor = %s, valor_unitario = %s, unidad_medida = %s, stock = %s WHERE id_producto = %s"
                data = (codigo, descripcion, categoria, nombre_proveedor, valor_unitario, unidad_medida, stock, id_producto)
                cursor.execute(sql, data)
                db_connection.commit()
                # Cerrar cursor y conexión a la base de datos
                cursor.close()
                db_connection.close()
                return redirect(url_for('productos'))
            else:
                return 'Todos los campos son obligatorios', 400
    except mysql.connector.Error as error:
        return f"Error al conectar a la base de datos: {error}", 500
    


@app.route('/deleteProducto/<string:id_producto>')
def delete (id_producto):
    try:
        # Credenciales de MySQL
        host = "mysql.codeflex.com.co"
        user = "AplicativoPOS"
        password = "3961"
        database = "AplicativoPOSfinal"
        # Establecer conexión con la base de datos
        db_connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = db_connection.cursor()
        # Eliminar las filas en detalle_venta asociadas al producto
        sql_delete_detalle_venta = "DELETE FROM detalle_venta WHERE codigo = (SELECT codigo FROM producto WHERE id_producto = %s)"
        cursor.execute(sql_delete_detalle_venta, (id_producto,))
        db_connection.commit()
        # Luego eliminar el producto
        sql_delete_producto = "DELETE FROM producto WHERE id_producto=%s"
        cursor.execute(sql_delete_producto, (id_producto,))
        db_connection.commit()
        # Cerrar cursor y conexión a la base de datos
        cursor.close()
        db_connection.close()
    except mysql.connector.Error as error:
        return f"Error al conectar a la base de datos: {error}"
    return redirect(url_for('productos'))

    
# FIN PRODUCTOS ----------------------------------------------------------------------------------------------------------- 

# INICIO PROVEEDORES -----------------------------------------------------------------------------------------------------------
@app.route("/proveedores")
def proveedores():
    try:
        # Credenciales de MySQL
        host = "mysql.codeflex.com.co"
        user = "AplicativoPOS"
        password = "3961"
        database = "AplicativoPOSfinal"
        # Establecer conexión con la base de datos
        db_connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = db_connection.cursor()
        # Obtener el próximo valor autoincremental de id_proveedor
        cursor.execute("SHOW TABLE STATUS LIKE 'proveedor'")
        table_status = cursor.fetchone()
        next_id = table_status[10]  # El índice 10 corresponde a la columna Auto_increment
        # Contar la cantidad de registros
        cursor.execute("SELECT COUNT(*) FROM proveedor")
        count = cursor.fetchone()[0]
        if count == 0:
            next_id = 1  # Si no hay registros, comenzar desde 1
        else:
            # Obtener el último ID y ajustar para el siguiente ID
            cursor.execute("SELECT MAX(id_proveedor) FROM proveedor")
            last_id = cursor.fetchone()[0]
            next_id = last_id + 1
        # Obtener los proveedores existentes
        cursor.execute("SELECT * FROM proveedor")
        myresult = cursor.fetchall()
        # Convertir datos a diccionario
        insertObjec = []
        columnNames = [column[0] for column in cursor.description]
        for record in myresult:
            insertObjec.append(dict(zip(columnNames, record)))
        cursor.close()
        db_connection.close()
        
        if 'logged_in' in session and session['logged_in']:
            return render_template("proveedores.html", data=insertObjec, next_id=next_id)
        else:
            return render_template("warning.html")
        
    except mysql.connector.Error as error:
        return f"Error al conectar a la base de datos: {error}"



@app.route('/guardarProveedores', methods=['POST'])
def addGuardarProveedores():
    try:
        # Credenciales de MySQL
        host = "mysql.codeflex.com.co"
        user = "AplicativoPOS"
        password = "3961"
        database = "AplicativoPOSfinal"
        # Obtener los datos del formulario
        id_proveedor = request.form['id_proveedor']
        tipo_identificacion = request.form['tipo_identificacion']
        numero_identificacion = request.form['numero_identificacion']
        nombre_proveedor = request.form['nombre_proveedor']
        email = request.form['email']
        direccion = request.form['direccion']
        telefono = request.form['telefono']
        dia_de_visita = request.form['dia_de_visita']
        dia_de_entrega = request.form['dia_de_entrega']
        if id_proveedor and tipo_identificacion and numero_identificacion and nombre_proveedor and email and direccion and telefono and dia_de_visita and dia_de_entrega:
            # Establecer conexión con la base de datos
            db_connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            cursor = db_connection.cursor()
            # Ejecutar la inserción en la tabla proveedor
            sql = "INSERT INTO proveedor (id_proveedor, tipo_identificacion, numero_identificacion, nombre_proveedor, email, direccion, telefono, dia_de_visita, dia_de_entrega) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            data = (id_proveedor, tipo_identificacion, numero_identificacion, nombre_proveedor, email, direccion, telefono, dia_de_visita, dia_de_entrega)
            cursor.execute(sql, data)
            db_connection.commit()
            cursor.close()
            db_connection.close()
    except mysql.connector.Error as error:
        return f"Error al conectar a la base de datos: {error}"
    return redirect(url_for('proveedores'))


@app.route('/deleteProveedor/<string:id_proveedor>')
def deleteProveedor(id_proveedor):
    try:
        # Credenciales de MySQL
        host = "mysql.codeflex.com.co"
        user = "AplicativoPOS"
        password = "3961"
        database = "AplicativoPOSfinal"
        # Establecer conexión con la base de datos
        db_connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = db_connection.cursor()
        # Eliminar las filas de detalle_venta asociadas a los productos del proveedor
        sql_delete_detalle_venta = """
        DELETE detalle_venta
        FROM detalle_venta
        INNER JOIN producto ON detalle_venta.codigo = producto.codigo
        WHERE producto.nombre_proveedor = (
            SELECT nombre_proveedor FROM proveedor WHERE id_proveedor = %s
        )
        """
        cursor.execute(sql_delete_detalle_venta, (id_proveedor,))
        # Confirmar la eliminación de las filas de detalle_venta
        db_connection.commit()
        # Eliminar las filas de producto asociadas al proveedor
        sql_delete_productos = "DELETE FROM producto WHERE nombre_proveedor = (SELECT nombre_proveedor FROM proveedor WHERE id_proveedor = %s)"
        cursor.execute(sql_delete_productos, (id_proveedor,))
        # Confirmar la eliminación de los productos
        db_connection.commit()
        # Eliminar el proveedor
        sql_delete_proveedor = "DELETE FROM proveedor WHERE id_proveedor = %s"
        cursor.execute(sql_delete_proveedor, (id_proveedor,))
        # Confirmar la eliminación del proveedor
        db_connection.commit()
        # Cerrar cursor y conexión a la base de datos
        cursor.close()
        db_connection.close()
    except mysql.connector.Error as error:
        return f"Error al conectar a la base de datos: {error}"
    return redirect(url_for('proveedores'))
    
    
    
@app.route('/editar_proveedor', methods=['POST'])
def editar_proveedor():
    try: 
        # Credenciales de MySQL
        host = "mysql.codeflex.com.co" 
        user = "AplicativoPOS"
        password = "3961"
        database = "AplicativoPOSfinal"
        if request.method == 'POST':
            id_proveedor = request.form['id_proveedor']
            tipo_identificacion = request.form['tipo_identificacion']
            numero_identificacion = request.form['numero_identificacion']
            nombre_proveedor = request.form['nombre_proveedor']
            email = request.form['email']
            direccion = request.form['direccion']
            telefono = request.form['telefono']
            dia_de_visita = request.form['dia_de_visita']
            dia_de_entrega = request.form['dia_de_entrega']
            if id_proveedor and tipo_identificacion and numero_identificacion and nombre_proveedor and email and direccion and telefono and dia_de_visita and dia_de_entrega:
                # Establecer conexión con la base de datos
                db_connection = mysql.connector.connect(
                    host=host,
                    user=user,
                    password=password, 
                    database=database
                )
                cursor = db_connection.cursor()
                # Ejecutar la actualización en la tabla proveedor
                sql = "UPDATE proveedor SET tipo_identificacion = %s, numero_identificacion = %s, nombre_proveedor = %s, email = %s, direccion = %s, telefono = %s, dia_de_visita = %s, dia_de_entrega = %s WHERE id_proveedor = %s"
                data = (tipo_identificacion, numero_identificacion, nombre_proveedor, email, direccion, telefono, dia_de_visita, dia_de_entrega, id_proveedor)
                cursor.execute(sql, data)
                db_connection.commit()
                cursor.close()
                db_connection.close()
                return redirect(url_for('proveedores'))
            else:
                # Devuelve un mensaje de error si algún campo está vacío
                return jsonify({'message': 'Todos los campos son obligatorios'})
        else:
            # Devuelve un mensaje de error si el método de solicitud no es POST
            return jsonify({'message': 'El método de solicitud debe ser POST'})
    except mysql.connector.Error as error:
        return f"Error al conectar a la base de datos: {error}"
# FIN PROVEEDORES -----------------------------------------------------------------------------------------------------------
 
 
# INICIO USUARIOS -----------------------------------------------------------------------------------------------------------

# Ruta para mostrar usuarios
@app.route("/usuarios")
def usuarios():
    # Credenciales de la base de datos
    host = "mysql.codeflex.com.co"
    user = "AplicativoPOS"
    password = "3961"
    database = "AplicativoPOSfinal"
    # Conectar a la base de datos
    db_connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    cursor = db_connection.cursor()
    # Obtener el último ID insertado antes de eliminar registros
    cursor.execute("SELECT MAX(id_usuario) FROM usuario")
    last_id = cursor.fetchone()[0]

    # Calcular el próximo ID
    if last_id is None:
        next_id = 1
    else:
        next_id = last_id + 1
    
    # Obtener los usuarios existentes
    cursor.execute("SELECT * FROM usuario")
    myresult = cursor.fetchall()
    # Convertir datos a diccionario
    insertObjec = []
    columnNames = [column[0] for column in cursor.description]
    for record in myresult:
        insertObjec.append(dict(zip(columnNames, record)))
    
    # Cerrar conexión
    cursor.close()
    db_connection.close()
    
    if 'logged_in' in session and session['logged_in']:
        return render_template("usuarios.html", data=insertObjec, next_id=next_id)
    else:
        return render_template("warning.html")
    


# Ruta para guardar usuarios
@app.route('/guardarUsuario', methods=['POST'])
def addGuardarUsuario():    
    nombre = request.form['nombre']
    tipo_Identificacion = request.form['tipo_identificacion']
    numero_identificacion = request.form['numero_identificacion']
    email = request.form['email']
    usuario = request.form['usuario']
    contrasenia = request.form['contrasenia']
    tipo_usuario = request.form['tipo_usuario']
    if nombre and tipo_Identificacion and numero_identificacion and email and usuario and contrasenia and tipo_usuario:
        # Credenciales de la base de datos
        host = "mysql.codeflex.com.co"
        user = "AplicativoPOS"
        password = "3961"
        database = "AplicativoPOSfinal"
        # Conectar a la base de datos
        db_connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = db_connection.cursor()
        # Obtener el último ID insertado antes de eliminar registros
        cursor.execute("SELECT MAX(id_usuario) FROM usuario")
        last_id = cursor.fetchone()[0]

        # Calcular el próximo ID
        if last_id is None:
            next_id = 1
        else:
            next_id = last_id + 1
            
        # Insertar el nuevo usuario en la tabla usuarios
        sql = "INSERT INTO usuario(id_usuario, nombre, tipo_identificacion, numero_identificacion, email, usuario, contrasenia, rol) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        data = (next_id, nombre, tipo_Identificacion, numero_identificacion, email, usuario, contrasenia, tipo_usuario)
        cursor.execute(sql, data)
        db_connection.commit()
        # Cerrar la conexión
        cursor.close()
        db_connection.close()
    return redirect(url_for('usuarios'))


  
@app.route('/deleteUsuarios/<string:id_usuario>')
def deleteUsuarios(id_usuario):
    # Credenciales de la base de datos
    host = "mysql.codeflex.com.co"
    user = "AplicativoPOS"
    password = "3961"
    database = "AplicativoPOSfinal"
    # Conectar a la base de datos
    db_connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    cursor = db_connection.cursor()
    # Ejecutar la consulta para eliminar el usuario
    sql = "DELETE FROM usuario WHERE id_usuario=%s"
    data = (id_usuario,)
    cursor.execute(sql, data)
    db_connection.commit()
    # Cerrar la conexión
    cursor.close()
    db_connection.close()
    return redirect(url_for('usuarios'))


@app.route('/editar_usuario', methods=['POST'])
def editaruser():
    # Credenciales de la base de datos 
    host = "mysql.codeflex.com.co"
    user = "AplicativoPOS"
    password = "3961"
    database = "AplicativoPOSfinal"
    # Conectar a la base de datos
    db_connection = mysql.connector.connect( 
        host=host,
        user=user,
        password=password,
        database=database
    )
    cursor = db_connection.cursor()
    if request.method == 'POST':
        id_usuario = request.json['id_usuario']
        nombre = request.json['edit_nombre']
        tipo_Identificacion = request.json['edit_tipo_identificacion']
        numero_identificacion = request.json['edit_numero_identificacion']
        email = request.json['edit_email']
        usuario = request.json['edit_usuario']
        contrasenia = request.json['edit_contrasenia']
        tipo_usuario = request.json['edit_tipo_usuario']
        if nombre and tipo_Identificacion and numero_identificacion  and email and usuario and contrasenia and tipo_usuario:
            # Ejecutar la consulta para actualizar el usuario
            sql = "UPDATE usuario SET nombre=%s, tipo_Identificacion=%s, numero_identificacion=%s, email=%s, usuario=%s, contrasenia=%s, rol=%s WHERE id_usuario=%s"
            data = (nombre, tipo_Identificacion, numero_identificacion, email, usuario, contrasenia, tipo_usuario, id_usuario)
            cursor.execute(sql, data)
            db_connection.commit()
            # Cerrar la conexión
            cursor.close()
            db_connection.close()
            return 'Perfecto'
        else:
            return 'Todos los campos son obligatorios'
        
# FIN USUARIOS -----------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)


