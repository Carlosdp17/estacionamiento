from datetime import datetime
import sqlite3
import os
import re
import qrcode

# Variables globales
cocheras_ocupadas = 0
estado_anterior = {}
id_seleccionado = None

BASE_DIR = os.path.dirname((os.path.abspath(__file__)))
ruta_base = os.path.join(BASE_DIR, 'estacionamiento_base.db')

#### FUNCIONES PRINCIPALES ####
###############################

def conexion():
    conectar = sqlite3.connect(ruta_base)
    return conectar

def crear_tabla():
    conectar = conexion()
    cursor = conectar.cursor()
    sql = """
    CREATE TABLE IF NOT EXISTS autos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dominio TEXT NOT NULL,
        tipo TEXT NOT NULL,
        fecha_actual TEXT NOT NULL,
        hora_entrada TEXT NOT NULL,
        salida_registrada BOOLEAN NOT NULL,
        fecha_salida TEXT,
        hora_salida TEXT,
        tiempo_estacionado TEXT,
        tarifa INTEGER
    )
    """
    cursor.execute(sql)
    conectar.commit()
    conectar.close()

def crear_tabla_configuracion():
    conectar = conexion()
    cursor = conectar.cursor()
    sql = """
    CREATE TABLE IF NOT EXISTS configuracion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        capacidad INTEGER NOT NULL,
        tarifa_auto REAL NOT NULL,
        tarifa_camioneta REAL NOT NULL,
        tarifa_moto REAL NOT NULL
    )
    """
    cursor.execute(sql)
    conectar.commit()
    conectar.close()

# Bloque try-except para manejar posibles errores
try:
    conexion()
    crear_tabla()
    crear_tabla_configuracion()
    
except:
    print("Hay un error")

def crear_tabla_configuracion():
    try:
        conectar = conexion()
        if conectar:
            cursor = conectar.cursor()
            sql = """
            CREATE TABLE IF NOT EXISTS configuracion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capacidad INTEGER NOT NULL,
                tarifa_auto REAL NOT NULL,
                tarifa_camioneta REAL NOT NULL,
                tarifa_moto REAL NOT NULL
            )
            """
            cursor.execute(sql)
            conectar.commit()
            conectar.close()
            print("Tabla 'configuracion' creada o ya existe.")
    except sqlite3.Error as e:
        print(f"Error al crear la tabla configuracion: {e}")

# ALTA
def registrar_vehiculo(variable_1, variable_2):
    global cocheras_disponibles
    dominio_min = variable_1.get().lower()
    tipo_min = variable_2.get().lower()
    
    # Validar que el campo de dominio no esté vacío
    if not dominio_min:
        return "dominio_vacio"
    
    # Validar que el dominio no contenga espacios y solo acepte caracteres alfanuméricos
    if not re.match(r'^[a-zA-Z0-9]+$', dominio_min):
        return "dominio_invalido"
    
    # Validar el tipo de vehículo
    if not tipo_min in ["auto", "camioneta", "moto"]:
        return "tipo_invalido"
    
    fecha_actual = datetime.today().strftime("%d/%m/%Y")
    hora_entrada = datetime.today().strftime("%H:%M:%S")
    
    if cocheras_disponibles > 0:
        # Conectar a la base de datos
        conectar = conexion()
        cursor = conectar.cursor()
        sql = """
            INSERT INTO autos (dominio, tipo, fecha_actual, hora_entrada, salida_registrada, fecha_salida, hora_salida, tiempo_estacionado, tarifa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        parametros = (dominio_min, tipo_min, fecha_actual, hora_entrada, False, None, None, None, None)
        cursor.execute(sql, parametros)
        conectar.commit()
        conectar.close()
        
        return "vehiculo_registrado"
    else:
        return "sin_cocheras"

def salida_tarifa(variable_1, variable_2, variable_3):
    global estado_anterior, tarifas, cocheras_ocupadas
    dominio_min = variable_3.get().lower()  # Convertir StringVar a str
    if not dominio_min:
        return "dominio_vacio", None, None, None
    
    id_a_salir = None

    # Conectar a la base de datos
    conectar = conexion()
    cursor = conectar.cursor()

    # Buscar todos los registros del vehículo en la base de datos
    sql = "SELECT id, tipo, fecha_actual, hora_entrada, salida_registrada FROM autos WHERE dominio = ?"
    parametros = (dominio_min, )
    cursor.execute(sql, parametros)
    resultados = cursor.fetchall()

    # Iterar sobre los resultados para encontrar un registro sin salida registrada
    for resultado in resultados:
        id_a_salir, tipo_vehiculo, fecha_actual, hora_entrada, salida_registrada = resultado
        
        if not salida_registrada:
            # Guardar el estado anterior
            estado_anterior[id_a_salir] = (resultado, dominio_min)
            fecha_salida = datetime.today().strftime("%d/%m/%Y")
            hora_salida = datetime.today().strftime("%H:%M:%S")

            # Convertir las fechas y horas a objetos datetime
            fecha_entrada = datetime.strptime(fecha_actual + ' ' + hora_entrada, "%d/%m/%Y %H:%M:%S")
            fecha_salida_dt = datetime.strptime(fecha_salida + ' ' + hora_salida, "%d/%m/%Y %H:%M:%S")

            # Calcular la diferencia de tiempo
            tiempo_estacionado = fecha_salida_dt - fecha_entrada
            total_segundos = int(tiempo_estacionado.total_seconds())
            horas_estacionado = total_segundos // 3600
            minutos_estacionado = (total_segundos % 3600) // 60
            segundos_estacionado = total_segundos % 60

            horas_estacionado_2 = tiempo_estacionado.total_seconds() / 3600

            # Calcular la tarifa
            tarifa_por_hora = tarifas.get(tipo_vehiculo)
            if tarifa_por_hora is None:
                return "tarifa_no_encontrada", None, None, None

            tarifa = round(horas_estacionado_2 * tarifa_por_hora, 2)
            tiempo_estacionado_str = f"{horas_estacionado}h{minutos_estacionado}m{segundos_estacionado}s"

            # Actualizar la base de datos
            sql = """
                UPDATE autos
                SET fecha_salida = ?, hora_salida = ?, tiempo_estacionado = ?, tarifa = ?, salida_registrada = ?
                WHERE id = ?
            """
            parametros = (fecha_salida, hora_salida, tiempo_estacionado_str, tarifa, True, id_a_salir)
            cursor.execute(sql, parametros)
            conectar.commit()

            # Decrementar las cocheras ocupadas
            cocheras_ocupadas -= 1  

            #listar(tree, variable_1, variable_2, variable_3)
            borrar_campos(variable_1, variable_2, variable_3)
            conectar.close()
            return "salida_registrada", tarifa, tiempo_estacionado_str, dominio_min

    conectar.close()
    return "vehiculo_no_encontrado", None, None, None

# def deshacer_ultima_salida(tree):
#     global estado_anterior, cocheras_ocupadas

#     if not estado_anterior:
#         messagebox.showerror("Error", "No hay ninguna salida para deshacer.")
#         return
#     confirmar = messagebox.askyesno("Confirmar deshacer", "¿Estás seguro de que quieres deshacer la última salida?")
#     if confirmar:
#     # Obtener el último estado guardado
#         ultimo_estado = list(estado_anterior.values())[-1]
#         ((id_a_restaurar, tipo_vehiculo, fecha_actual, hora_entrada, salida_registrada), dominio_min) = ultimo_estado
        
#         # Restaurar el estado anterior en la base de datos
#         conectar = conexion()
#         cursor = conectar.cursor()
#         sql= """
#             UPDATE autos
#             SET fecha_salida = NULL, hora_salida = NULL, tiempo_estacionado = NULL, tarifa = NULL, salida_registrada = ?
#             WHERE id = ?
#         """
#         parametros = (False, id_a_restaurar)
#         cursor.execute(sql, parametros)
#         conectar.commit()
#         conectar.close()

#         # Incrementar las cocheras ocupadas
#         cocheras_ocupadas += 1

#         # Eliminar el estado guardado
#         del estado_anterior[id_a_restaurar]

#         messagebox.showinfo("Deshacer salida", f"Se ha deshecho la salida del vehículo con dominio {dominio_min}.")
#         listar(tree)
#     else:
#         messagebox.showinfo("Deshacer salida", "La acción de deshacer la salida ha sido cancelada.")

# BUSQUEDA
def buscar(dominio_buscado):
    dominio_buscado = dominio_buscado.lower()
    
    # Validar que el campo de dominio no esté vacío
    if not dominio_buscado:
        return "dominio_vacio"
    
    # Validar que el nuevo dominio no contenga espacios
    if not re.match(r'^\S+$', dominio_buscado):
        return "dominio_invalido"
    
    conectar = conexion()
    cursor = conectar.cursor()
    sql = "SELECT * FROM autos WHERE dominio = ?"
    parametro = (dominio_buscado,)
    cursor.execute(sql, parametro)
    filas = cursor.fetchall()
    conectar.close()
    
    if not filas:
        return "vehiculo_no_encontrado", []
    
    return "vehiculo_encontrado", filas

# BAJA
def borrar(id_seleccionado, confirmar=False):
    # Conectar a la base de datos
    conectar = conexion()
    cursor = conectar.cursor()

    # Verificar si el vehículo seleccionado tiene salida registrada
    sql = "SELECT salida_registrada FROM autos WHERE id = ?"
    parametro = (id_seleccionado,)
    cursor.execute(sql, parametro)
    resultado = cursor.fetchone()
    salida_registrada = resultado[0]
    
    if salida_registrada:
        if not confirmar:
            conectar.close()
            return "confirmar_eliminacion"
        
        # Eliminar el registro de la base de datos
        sql = "DELETE FROM autos WHERE id = ?"
        parametro = (id_seleccionado,)
        cursor.execute(sql, parametro)
        conectar.commit()
        conectar.close()
        return "vehiculo_eliminado"
    else:
        conectar.close()
        return "no_salida_registrada"

def modificar_vehiculo(id, nuevo_dominio, nuevo_tipo):
    # Validar que el dominio no contenga espacios y solo acepte caracteres alfanuméricos
    if not re.match(r'^[a-zA-Z0-9]+$', nuevo_dominio):
        return "dominio_invalido"
    
    # Validar el tipo de vehículo
    if nuevo_tipo not in ["auto", "camioneta", "moto"]:
        return "tipo_invalido"
    
    # Conectar a la base de datos
    conectar = conexion()
    cursor = conectar.cursor()
    
    # Verificar si hay cambios
    sql = "SELECT dominio, tipo FROM autos WHERE id = ?"
    cursor.execute(sql, (id,))
    valores = cursor.fetchone()
    
    if nuevo_dominio == valores[0] and nuevo_tipo == valores[1]:
        conectar.close()
        return "sin_cambios"
    
    # Actualizar la base de datos
    sql = "UPDATE autos SET dominio = ?, tipo = ? WHERE id = ?"
    parametros = (nuevo_dominio, nuevo_tipo, id)
    cursor.execute(sql, parametros)
    conectar.commit()
    conectar.close()
    
    return "vehiculo_modificado"


#### FUNCIONES ADICIONALES ####
###############################
   

# Vaciar Base de datos
def borrar_todos_los_datos( confirmar=False):
    global cocheras_ocupadas
    conectar = conexion()
    if conectar is None:
        return "conexion_error"

    cursor = conectar.cursor()
    
    if not confirmar:
        conectar.close()
        return "confirmar_eliminacion"
    
    # Verificar si las tablas existen antes de intentar borrar
    sql = "SELECT name FROM sqlite_master WHERE type='table' AND name='autos';"
    cursor.execute(sql)
    if cursor.fetchone() is not None:
        # Borrar todos los registros de la tabla 'autos'
        sql_borrar_autos = "DELETE FROM autos"
        cursor.execute(sql_borrar_autos)

        # Reiniciar el contador de IDs de la tabla 'autos'
        sql_reinicio_id = "DELETE FROM sqlite_sequence WHERE name='autos'"
        cursor.execute(sql_reinicio_id)
    else:
        conectar.close()
        return "tabla_autos_no_existe"
    
    sql = "SELECT name FROM sqlite_master WHERE type='table' AND name='configuracion';"
    cursor.execute(sql)
    if cursor.fetchone() is not None:
        # Borrar todos los registros de la tabla 'configuración'
        sql_borrar_configuracion = "DELETE FROM configuracion"
        cursor.execute(sql_borrar_configuracion)

        # Reiniciar el contador de IDs de la tabla 'configuración'
        sql_reinicio_id = "DELETE FROM sqlite_sequence WHERE name='configuracion'"
        cursor.execute(sql_reinicio_id)
    else:
        conectar.close()
        return "tabla_configuracion_no_existe"

    conectar.commit()
    conectar.close()
    cocheras_ocupadas = 0
    #listar(tree, variable_1, variable_2, variable_3)
    return "exito"

# DISPONIBILIDAD
def disponibilidad():
    global cocheras_disponibles
    global capacidad
    conectar = conexion()
    cursor = conectar.cursor()
    sql = "SELECT COUNT(*) FROM autos WHERE salida_registrada = 0"
    cursor.execute(sql)
    cocheras_ocupadas = cursor.fetchone()[0]
    cocheras_disponibles = capacidad - cocheras_ocupadas
    conectar.close()
    return cocheras_ocupadas, cocheras_disponibles

"""
LA PASE A VISTA
def actualizar_grafico(root, ax, canvas):
    
    cocheras_ocupadas, cocheras_disponibles = disponibilidad()
    
    ax.clear()
    labels = 'Ocupadas', 'Disponibles'
    sizes = [cocheras_ocupadas, cocheras_disponibles]
    colors = ['red', 'green']
    explode = (0.1, 0)  # "Explota" la primera sección
    wedges, texts, autotexts= ax.pie(sizes, autopct='%1.1f%%', startangle=90, colors=colors, explode=explode, shadow=True, textprops={'fontsize': 10, 'color': 'black'})
    ax.axis('equal')  # Para que el gráfico sea un círculo
    ax.set_title((f"Cocheras disponibles: {cocheras_disponibles}"), fontsize=12, color='black')  # Añadir título
    # Añadir leyenda
    ax.legend(wedges, labels, loc="lower center", fontsize=10, bbox_to_anchor=(0.5, -0.1))
    canvas.draw()
    root.after(2000, actualizar_grafico, root, ax, canvas)  # Actualiza cada 2000 ms (2 segundos)
"""

# CONFIGURACIÓN

def cargar_configuracion():
    global capacidad, tarifas
    conectar = conexion()
    cursor = conectar.cursor()
    sql = "SELECT capacidad, tarifa_auto, tarifa_camioneta, tarifa_moto FROM configuracion LIMIT 1"
    cursor.execute(sql)
    configuracion = cursor.fetchone()
    if configuracion:
        capacidad, tarifa_auto, tarifa_camioneta, tarifa_moto = configuracion
        tarifas = {'auto': tarifa_auto, 'camioneta': tarifa_camioneta, 'moto': tarifa_moto}
    else:
        # Si no hay configuración guardada, usar valores por defecto
        capacidad = 50
        tarifas = {'auto': 1000.0, 'camioneta': 1500.0, 'moto': 700.0}
    
    conectar.close()

# Función para guardar la configuración y ocultar el frame
def guardar_configuracion(entry_capacidad, entry_tarifa_auto, entry_tarifa_camioneta, entry_tarifa_moto):
    global capacidad
    
    capacidad = int(entry_capacidad.get())
    tarifas['auto'] = float(entry_tarifa_auto.get())
    tarifas['camioneta'] = float(entry_tarifa_camioneta.get())
    tarifas['moto'] = float(entry_tarifa_moto.get())

    conectar = conexion()
    cursor = conectar.cursor()
    # Elimina la configuración anterior
    sql = "DELETE FROM configuracion"
    cursor.execute(sql)
    # Nueva configuración
    sql = """
        INSERT INTO configuracion (capacidad, tarifa_auto, tarifa_camioneta, tarifa_moto)
        VALUES (?, ?, ?, ?)
    """
    parametros = (capacidad, tarifas['auto'], tarifas['camioneta'], tarifas['moto'])
    cursor.execute(sql, parametros)
    conectar.commit()
    conectar.close()
    
    return "configuracion_actualizada"

# Función para mostrar/ocultar la configuración


# def inicializar_variables():
#     global variable_1, variable_2, variable_3, capacidad, tarifas
#     #variable_1 = tk.StringVar()
#     #variable_2 = tk.StringVar()
#     #variable_3 = tk.StringVar()
#     capacidad = StringVar()
#     tarifas = {
#             'auto': StringVar(),
#             'camioneta': StringVar(),
#             'moto': StringVar()
#         }

def borrar_campos(variable_1, variable_2, variable_3):
    variable_1.set('')
    variable_2.set('')
    variable_3.set('')

def mostrar_recaudacion_diaria(fecha):
    # Obtener la fecha actual en el formato adecuado
    fecha_formateada = datetime.strptime(fecha, "%d/%m/%y").strftime("%d/%m/%Y")
    fecha_salida = fecha_formateada
    
    # Conectar con base de datos
    conectar = conexion()
    cursor = conectar.cursor()
    sql = "SELECT * FROM autos WHERE fecha_salida = ?"
    parametro = (fecha_salida,)
    cursor.execute(sql, parametro)
    filas = cursor.fetchall()
    conectar.close()
    
    total_tarifa = sum(fila[-1] for fila in filas)  # Asumiendo que la tarifa es el último valor en cada fila
    total_tarifa_formateada = f"{total_tarifa:.2f}"
    
    if filas:
        return "datos_mostrados", filas, total_tarifa_formateada
    else:
        return "sin_datos", [], None

def generar_qr(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=4,
        border=3,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img


BASE_DIR = os.path.dirname((os.path.abspath(__file__)))
ruta_manual = os.path.join(BASE_DIR, 'img', 'doc_gestion_estacionamiento.pdf')

def abrir_manual():
    os.startfile(ruta_manual)

def validar_entrada_numerica(texto):
    return re.fullmatch(r'^\d*$', texto) is not None

def validar_entrada_decimal(texto):
    return re.fullmatch(r'^\d*\.?\d*$', texto) is not None
