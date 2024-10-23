import sqlite3
import os
from datetime import datetime
import re
import qrcode

BASE_DIR = os.path.dirname((os.path.abspath(__file__)))
ruta_base = os.path.join(BASE_DIR, 'estacionamiento_base.db')

class ConexionDB:
    def __init__(self):
        self.base_datos = ruta_base
        self.conexion = sqlite3.connect(self.base_datos)
        self.cursor = self.conexion.cursor()

    def cerrar(self):
        self.conexion.commit()
        self.conexion.close()

class Tablas:
    def __init__(self):
        self.conexion = ConexionDB()

    def crear_tabla_configuracion(self):
        sql = """
        CREATE TABLE IF NOT EXISTS configuracion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capacidad INTEGER NOT NULL,
            tarifa_auto REAL NOT NULL,
            tarifa_camioneta REAL NOT NULL,
            tarifa_moto REAL NOT NULL
        )
        """
        try:
            self.conexion.cursor.execute(sql)
        except sqlite3.Error as e:
            print(f"Error al crear la tabla configuracion: {e}")
        # finally:
        #     self.conexion.cerrar()

    def crear_tabla_vehiculos(self):
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
        try:
            self.conexion.cursor.execute(sql)
        except sqlite3.Error as e:
            print(f"Error al crear la tabla autos: {e}")
        # finally:
        #     self.conexion.cerrar()

    def cerrar_conexion(self):
        self.conexion.cerrar()

class Estacionamiento:
    def __init__(self, variable_1, variable_2, variable_3):
        self.capacidad = self.obtener_capacidad()
        self.variable_1 = variable_1
        self.variable_2 = variable_2
        self.variable_3 = variable_3
        self.cocheras_ocupadas = 0  # Inicializa cocheras_ocupadas
        self.tarifas = {'auto': 1000.0, 'camioneta': 1500.0, 'moto': 700.0}  # Valores por defecto
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.ruta_manual = os.path.join(self.BASE_DIR, 'img', 'doc_gestion_estacionamiento.pdf')
        self.conexion = ConexionDB()  # Inicializa la conexión a la base de datos
        self.tablas = Tablas()  # Inicializar la instancia de Tablas
        self.tablas.crear_tabla_configuracion()
        self.tablas.crear_tabla_vehiculos()
        self.tablas.cerrar_conexion()
        self.cargar_configuracion() #cargar configuracion al inicializar

    def obtener_capacidad(self):
        conectar = ConexionDB()
        cursor = conectar.cursor
        sql = "SELECT capacidad FROM configuracion LIMIT 1"
        try:
            cursor.execute(sql)
            fila = cursor.fetchone()
            if fila is not None:
                capacidad = fila[0]
            else:
                print("No se encontró la configuración de capacidad.")
                capacidad = 30  # O algún valor por defecto
        except sqlite3.Error as e:
            print(f"Error al obtener la capacidad: {e}")
            capacidad = 30
        finally:
            conectar.cerrar()
        self.capacidad = capacidad  # Actualiza self.capacidad con el valor obtenido de la base de datos
        return capacidad

    def disponibilidad(self):
        self.obtener_capacidad()
        conectar = ConexionDB()
        cursor = conectar.cursor
        sql = "SELECT COUNT(*) FROM autos WHERE salida_registrada = 0"
        try:
            cursor.execute(sql)
            self.cocheras_ocupadas = cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"Error al obtener la disponibilidad: {e}")
            self.cocheras_ocupadas = 0
        finally:
            conectar.cerrar()
        cocheras_disponibles = self.capacidad - self.cocheras_ocupadas
        return self.cocheras_ocupadas, cocheras_disponibles
    
    def borrar_campos(self, variable_1, variable_2, variable_3):
        variable_1.set('')
        variable_2.set('')
        variable_3.set('')

    ### ALTA ###
    def registrar_vehiculo(self, variable_1, variable_2):
        cocheras_ocupadas, cocheras_disponibles = self.disponibilidad()
        
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
            conectar = ConexionDB()
            cursor = conectar.cursor
            sql = """
                INSERT INTO autos (dominio, tipo, fecha_actual, hora_entrada, salida_registrada, fecha_salida, hora_salida, tiempo_estacionado, tarifa)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            parametros = (dominio_min, tipo_min, fecha_actual, hora_entrada, False, None, None, None, None)
            cursor.execute(sql, parametros)
            conectar.conexion.commit()
            conectar.cerrar()

            return "vehiculo_registrado"
        else:
            return "sin_cocheras"
        
    ### SALIDA Y CALCULO DE TARIFA ###
    def salida_tarifa(self, variable_1, variable_2, variable_3):
        
        dominio_min = variable_3.get().lower()  # Convertir StringVar a str
        if not dominio_min:
            return "dominio_vacio", None, None, None
        
        id_a_salir = None

        # Conectar a la base de datos
        conectar = ConexionDB()
        cursor = conectar.cursor
        # Buscar todos los registros del vehículo en la base de datos
        sql = "SELECT id, tipo, fecha_actual, hora_entrada, salida_registrada FROM autos WHERE dominio = ?"
        parametros = (dominio_min,)
        cursor.execute(sql, parametros)
        resultados = cursor.fetchall()

        # Iterar sobre los resultados para encontrar un registro sin salida registrada
        for resultado in resultados:
            id_a_salir, tipo_vehiculo, fecha_actual, hora_entrada, salida_registrada = resultado

            if not salida_registrada:
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

                # Obtener la tarifa desde la base de datos según el tipo de vehículo
                if tipo_vehiculo == 'auto':
                    sql_tarifa = "SELECT tarifa_auto FROM configuracion"
                elif tipo_vehiculo == 'camioneta':
                    sql_tarifa = "SELECT tarifa_camioneta FROM configuracion"
                elif tipo_vehiculo == 'moto':
                    sql_tarifa = "SELECT tarifa_moto FROM configuracion"
                # else:
                #     messagebox.showerror("Error", f"Tipo de vehículo no válido: {tipo_vehiculo}")
                #     return

                cursor.execute(sql_tarifa)
                tarifa_por_hora = cursor.fetchone()
                if tarifa_por_hora is None:
                    return "tarifa_no_encontrada", None, None, None

                tarifa = round(horas_estacionado_2 * tarifa_por_hora[0], 2)
                tiempo_estacionado_str = f"{horas_estacionado}h{minutos_estacionado}m{segundos_estacionado}s"

                # Actualizar la base de datos
                sql = """
                    UPDATE autos
                    SET fecha_salida = ?, hora_salida = ?, tiempo_estacionado = ?, tarifa = ?, salida_registrada = ?
                    WHERE id = ?
                """
                parametros = (fecha_salida, hora_salida, tiempo_estacionado_str, tarifa, True, id_a_salir)
                try:
                    cursor.execute(sql, parametros)
                    conectar.conexion.commit()

                    # Decrementar las cocheras ocupadas
                    self.cocheras_ocupadas -= 1

                    self.borrar_campos(variable_1, variable_2, variable_3)
                    return "salida_registrada", tarifa, tiempo_estacionado_str, dominio_min
                except sqlite3.Error as e:
                    print(f"Error al registrar la salida: {e}")
                    return "error_salida", None, None, None
                finally:
                    conectar.cerrar()

        conectar.cerrar()
        return "vehiculo_no_encontrado", None, None, None
    
    ### BUSQUEDA ###
    def buscar(self, dominio_buscado):
        dominio_buscado = dominio_buscado.lower()
        
        # Validar que el campo de dominio no esté vacío
        if not dominio_buscado:
            return "dominio_vacio"
        
        # Validar que el nuevo dominio no contenga espacios
        if not re.match(r'^\S+$', dominio_buscado):
            return "dominio_invalido"
        
        conectar = ConexionDB()
        cursor = conectar.cursor
        sql = "SELECT * FROM autos WHERE dominio = ?"
        parametro = (dominio_buscado,)
        cursor.execute(sql, parametro)
        filas = cursor.fetchall()
        conectar.cerrar()
        
        if not filas:
            return "vehiculo_no_encontrado", []
        
        return "vehiculo_encontrado", filas

    ### BAJA ###
    def borrar(self, id_seleccionado, confirmar=False):
        # Conectar a la base de datos
        conectar = ConexionDB()
        cursor = conectar.cursor

        # Verificar si el vehículo seleccionado tiene salida registrada
        sql = "SELECT salida_registrada FROM autos WHERE id = ?"
        parametro = (id_seleccionado,)
        cursor.execute(sql, parametro)
        resultado = cursor.fetchone()
        salida_registrada = resultado[0]
        
        if salida_registrada:
            if not confirmar:
                conectar.cerrar()
                return "confirmar_eliminacion"
            
            # Eliminar el registro de la base de datos
            sql = "DELETE FROM autos WHERE id = ?"
            parametro = (id_seleccionado,)
            cursor.execute(sql, parametro)
            
            conectar.cerrar()
            return "vehiculo_eliminado"
        else:
            conectar.cerrar()
            return "no_salida_registrada"

    ### MODIFICACION ###
    def modificar_vehiculo(self, id, nuevo_dominio, nuevo_tipo):
        # Validar que el dominio no contenga espacios y solo acepte caracteres alfanuméricos
        if not re.match(r'^[a-zA-Z0-9]+$', nuevo_dominio):
            return "dominio_invalido"
        
        # Validar el tipo de vehículo
        if nuevo_tipo not in ["auto", "camioneta", "moto"]:
            return "tipo_invalido"
        
        # Conectar a la base de datos
        conectar = ConexionDB()
        cursor = conectar.cursor
        
        # Verificar si hay cambios
        sql = "SELECT dominio, tipo FROM autos WHERE id = ?"
        cursor.execute(sql, (id,))
        valores = cursor.fetchone()
        
        if nuevo_dominio == valores[0] and nuevo_tipo == valores[1]:
            conectar.cerrar()
            return "sin_cambios"
        
        # Actualizar la base de datos
        sql = "UPDATE autos SET dominio = ?, tipo = ? WHERE id = ?"
        parametros = (nuevo_dominio, nuevo_tipo, id)
        cursor.execute(sql, parametros)
        
        conectar.cerrar()
        
        return "vehiculo_modificado"

    def mostrar_recaudacion_diaria(self, fecha):
        # Obtener la fecha actual en el formato adecuado
        fecha_formateada = datetime.strptime(fecha, "%d/%m/%y").strftime("%d/%m/%Y")
        fecha_salida = fecha_formateada
        
        # Conectar con base de datos
        conectar = ConexionDB()
        cursor = conectar.cursor
        sql = "SELECT * FROM autos WHERE fecha_salida = ?"
        parametro = (fecha_salida,)
        cursor.execute(sql, parametro)
        filas = cursor.fetchall()
        conectar.cerrar()
        
        total_tarifa = sum(fila[-1] for fila in filas)  # Asumiendo que la tarifa es el último valor en cada fila
        total_tarifa_formateada = f"{total_tarifa:.2f}"
        
        if filas:
            return "datos_mostrados", filas, total_tarifa_formateada
        else:
            return "sin_datos", [], None
        
    def borrar_todos_los_datos(self, confirmar=False):
        conectar = ConexionDB()
        if conectar is None:
            return "conexion_error"

        cursor = conectar.cursor
        
        if not confirmar:
            conectar.cerrar()
            return "confirmar_eliminacion"
        
        try:
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
                return "tabla_configuracion_no_existe"

            self.cocheras_ocupadas = 0  # Reinicia el contador de cocheras ocupadas
            # listar(tree, self.variable_1, self.variable_2, self.variable_3)
            return "exito"
        finally:
            conectar.cerrar()

    def cargar_configuracion(self):
        conectar = ConexionDB()
        cursor = conectar.cursor
        sql = "SELECT capacidad, tarifa_auto, tarifa_camioneta, tarifa_moto FROM configuracion LIMIT 1"
        cursor.execute(sql)
        configuracion = cursor.fetchone()
        if configuracion:
            self.capacidad,self.tarifa_auto, self.tarifa_camioneta, self.tarifa_moto = configuracion
            self.tarifas = {'auto': self.tarifa_auto, 'camioneta': self.tarifa_camioneta, 'moto': self.tarifa_moto}
        else:
            # Si no hay configuración guardada, usar valores por defecto
            self.capacidad = 50
            self.tarifas = {'auto': 1000, 'camioneta': 1500, 'moto': 700}
        
        conectar.cerrar()

    def guardar_configuracion(self, entry_capacidad, entry_tarifa_auto, entry_tarifa_camioneta, entry_tarifa_moto):
        self.capacidad = int(entry_capacidad.get())
        self.tarifas['auto'] = float(entry_tarifa_auto.get())
        self.tarifas['camioneta'] = float(entry_tarifa_camioneta.get())
        self.tarifas['moto'] = float(entry_tarifa_moto.get())

        conectar = ConexionDB()
        cursor = conectar.cursor
        # Elimina la configuración anterior
        sql = "DELETE FROM configuracion"
        cursor.execute(sql)
        # Nueva configuración
        sql = """
            INSERT INTO configuracion (capacidad, tarifa_auto, tarifa_camioneta, tarifa_moto)
            VALUES (?, ?, ?, ?)
        """
        parametros = (self.capacidad, self.tarifas['auto'], self.tarifas['camioneta'], self.tarifas['moto'])
        cursor.execute(sql, parametros)
        conectar.cerrar()
        
        return "configuracion_actualizada"

    def generar_qr(self, data: str):
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

    def abrir_manual(self):
        os.startfile(self.ruta_manual)

    def validar_entrada_numerica(self, texto: str):
        return re.fullmatch(r'^\d*$', texto) is not None

    def validar_entrada_decimal(self, texto: str):
        return re.fullmatch(r'^\d*\.?\d*$', texto) is not None