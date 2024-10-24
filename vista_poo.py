import tkinter as tk
from tkinter import ttk, Menu, Entry, StringVar, messagebox, colorchooser
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import *
from PIL import Image, ImageTk
import os
import random
from modelo_poo import ConexionDB, Tablas, Estacionamiento

# Lista global para almacenar las referencias a las imágenes
imagenes = []
id_seleccionado = None

class FuncionesAuxiliares:
    def __init__(self):
        self.conexion = ConexionDB()
        self.estacionamiento = Estacionamiento(None, None, None)

    def seleccionar_vehiculo(self, variable_1, variable_2, variable_3, tree):
        global id_seleccionado
        selected_item = tree.selection()  # Obtiene el identificador del elemento seleccionado en la tabla
        if selected_item:  # Verificar si hay algún elemento seleccionado
            item = tree.item(selected_item)  # Obtiene los datos del elemento seleccionado en la tabla
            valores = item['values']  # Extracción de valores
            id_seleccionado = valores[0]  # Asumiendo que el ID es el primer valor en la lista de valores
            self.estacionamiento.borrar_campos(variable_1, variable_2, variable_3)  # Borra texto en caso de que esté escrito el entry
            variable_1.set(valores[1])  # Inserta 2° valor (dominio) en el entry_dominio
            variable_2.set(valores[2])  # Inserta 3° valor (tipo) en el entry_tipo
            variable_3.set(valores[1])  # Inserta 2° valor (dominio) en el entry_realizar_salida

    def deseleccionar_vehiculo(self, tree, variable_1, variable_2, variable_3):
        global id_seleccionado
        selected_item = tree.selection()  # Obtiene el identificador del elemento seleccionado en la tabla
        if selected_item:  # Verificar si hay algún elemento seleccionado
            tree.selection_remove(selected_item)  # Deselecciona el elemento
            id_seleccionado = None  # Reinicia el valor de id_seleccionado
            self.estacionamiento.borrar_campos(variable_1, variable_2, variable_3)

    def listar(self, tree, variable_1, variable_2, variable_3):
        self.estacionamiento.borrar_campos(variable_1, variable_2, variable_3)
        self.deseleccionar_vehiculo(tree, variable_1, variable_2, variable_3)
        # Limpiar la tabla
        for item in tree.get_children():
            tree.delete(item)
        # Conectar con base de datos
        conectar = ConexionDB()
        cursor = conectar.cursor
        sql = "SELECT * FROM autos"
        cursor.execute(sql)
        filas = cursor.fetchall()
        # Insertar todos los registros
        for fila in filas:
            tree.insert("", "0", values=fila)
        conectar.cerrar()

    def cargar_imagen(self, ruta, tamaño=(25, 25)):
        try:
            img = Image.open(ruta)
            img = img.resize(tamaño, Image.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)
            imagenes.append(img_tk)  # Almacenar la referencia
            return img_tk
        except Exception as e:
            print(f"Error al cargar la imagen: {e}")
            return None

    def vista_registrar(self, tree, variable_1, variable_2, variable_3):
        resultado = self.estacionamiento.registrar_vehiculo(variable_1, variable_2)
        
        if resultado == "dominio_vacio":
            messagebox.showinfo("Recuerde", "Debe completar el campo de Dominio.")
        elif resultado == "dominio_invalido":
            messagebox.showerror("Error", "El dominio no debe contener espacios y solo debe contener caracteres alfanuméricos.")
        elif resultado == "tipo_invalido":
            messagebox.showinfo("Recuerde!!!", "Seleccione tipo de vehículo de lista desplegable")
        elif resultado == "vehiculo_registrado":
            self.listar(tree, variable_1, variable_2, variable_3)
            messagebox.showinfo("Ingresando vehículo", "Vehículo dado de alta")
        elif resultado == "sin_cocheras":
            messagebox.showerror("Error", "No hay cocheras disponibles")

    def vista_salida_tarifa(self, tree, variable_1, variable_2, variable_3):
        resultado, tarifa, tiempo_estacionado, dominio_min = self.estacionamiento.salida_tarifa(variable_1, variable_2, variable_3)
        
        if resultado == "dominio_vacio":
            messagebox.showinfo("Recuerde", "Debe completar el campo de Dominio salida.")
        elif resultado == "tarifa_no_encontrada":
            messagebox.showerror("Error", f"No se encontró una tarifa para el tipo de vehículo.")
        elif resultado == "vehiculo_no_encontrado":
            messagebox.showerror("Error", "No se encontró un vehículo sin salida registrada con ese dominio.")
        elif resultado == "salida_registrada":
            self.listar(tree, variable_1, variable_2, variable_3)
            messagebox.showinfo("Salida registrada", f"Salida registrada para el vehículo con dominio {dominio_min}.")
            messagebox.showinfo(f"La tarifa total es: ${tarifa:.2f}", f"El vehículo con dominio {dominio_min} ha estado estacionado por {tiempo_estacionado}.")

    def vista_buscar(self, variable_1, variable_2, variable_3, tree):
        dominio_buscado = variable_1.get()
        resultado, filas = self.estacionamiento.buscar(dominio_buscado)
        
        if resultado == "dominio_vacio":
            messagebox.showinfo("Recuerde", "Debe completar el campo de Dominio.")
        elif resultado == "dominio_invalido":
            messagebox.showinfo("Error", "El dominio no debe contener espacios.")
        elif resultado == "vehiculo_no_encontrado":
            self.listar(tree, variable_1, variable_2, variable_3)
            messagebox.showinfo("Atención", "Vehículo no encontrado")
        elif resultado == "vehiculo_encontrado":
            # Limpiar la tabla
            for item in tree.get_children():
                tree.delete(item)
            
            # Insertar los resultados en la tabla
            for fila in filas:
                tree.insert("", "end", values=fila)
            
            self.estacionamiento.borrar_campos(variable_1, variable_2, variable_3)

    def vista_borrar(self, tree, variable_1, variable_2, variable_3):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showinfo("Atención", "No se ha seleccionado ningún vehículo")
            return
        
        # Obtener el ID del vehículo seleccionado
        id_seleccionado = tree.item(selected_item, 'values')[0]
        
        resultado = self.estacionamiento.borrar(id_seleccionado, confirmar=False)
        
        if resultado == "confirmar_eliminacion":
            confirmar = messagebox.askyesno("Confirmar eliminación", "¿Estás seguro de que deseas eliminar este vehículo?")
            if confirmar:
                resultado = self.estacionamiento.borrar(id_seleccionado, confirmar=True)
                if resultado == "vehiculo_eliminado":
                    self.listar(tree, variable_1, variable_2, variable_3)
                    messagebox.showinfo("Acción realizada", "Vehículo eliminado")
            else:
                self.listar(tree, variable_1, variable_2, variable_3)
        elif resultado == "no_salida_registrada":
            messagebox.showerror("Error", "No se puede eliminar el vehículo sin registrar su salida")
        
        self.estacionamiento.borrar_campos(variable_1, variable_2, variable_3)

    def vista_modificar_vehiculo(self, variable_1, variable_2, tree, variable_3):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showinfo("Atención!!!", "No se ha seleccionado ningún vehículo de la tabla. Seleccionelo por favor")
            return
        
        item = tree.item(selected_item)
        valores = item['values']
        id = valores[0]
        nuevo_dominio = variable_1.get().lower()
        nuevo_tipo = variable_2.get().lower()
        
        resultado = self.estacionamiento.modificar_vehiculo(id, nuevo_dominio, nuevo_tipo)
        
        if resultado == "dominio_invalido":
            self.deseleccionar_vehiculo(tree, variable_1, variable_2, variable_3)
            messagebox.showinfo("Error", "El dominio no debe contener espacios y solo debe contener caracteres alfanuméricos.")
        elif resultado == "tipo_invalido":
            messagebox.showinfo("Recuerde!!!", "Seleccione vehículo de lista desplegable")
        elif resultado == "sin_cambios":
            self.deseleccionar_vehiculo(tree, variable_1, variable_2, variable_3)
            messagebox.showinfo("Atención!!!", "No se realizaron cambios en el vehículo.")
        elif resultado == "vehiculo_modificado":
            # Actualizar el ítem en el tree
            tree.item(selected_item, values=(id, nuevo_dominio, nuevo_tipo, valores[3], valores[4], valores[5], valores[6], valores[7], valores[8], valores[9]))
            self.deseleccionar_vehiculo(tree, variable_1, variable_2, variable_3)
            messagebox.showinfo("Atención!!!", "Vehículo modificado")
        
        self.estacionamiento.borrar_campos(variable_1, variable_2, variable_3)

    def vista_borrar_todos_los_datos(self, tree, variable_1, variable_2, variable_3, confirmar=False):
        resultado = self.estacionamiento.borrar_todos_los_datos(confirmar=False)
        
        if resultado == "conexion_error":
            messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
        elif resultado == "confirmar_eliminacion":
            confirmar = messagebox.askyesno("Confirmar eliminación", "¿Estás seguro de que deseas reiniciar Base de datos?\n Eliminarás toda la información")
            if confirmar:
                resultado = self.estacionamiento.borrar_todos_los_datos(tree, confirmar=True)
                if resultado == "exito":
                    self.listar(tree, variable_1, variable_2, variable_3)
                    messagebox.showinfo("Éxito", "Todos los datos han sido borrados y los IDs han sido reiniciados.")
                elif resultado == "tabla_autos_no_existe":
                    messagebox.showerror("Error", "La tabla 'autos' no existe.")
                elif resultado == "tabla_configuracion_no_existe":
                    messagebox.showerror("Error", "La tabla 'configuración' no existe.")
        elif resultado == "tabla_autos_no_existe":
            messagebox.showerror("Error", "La tabla 'autos' no existe.")
        elif resultado == "tabla_configuracion_no_existe":
            messagebox.showerror("Error", "La tabla 'configuración' no existe.")

    def vista_guardar_configuracion(self, entry_capacidad, entry_tarifa_auto, entry_tarifa_camioneta, entry_tarifa_moto, frame_configuracion):
        resultado = self.estacionamiento.guardar_configuracion(entry_capacidad, entry_tarifa_auto, entry_tarifa_camioneta, entry_tarifa_moto)
        
        if resultado == "configuracion_actualizada":
            messagebox.showinfo("Configuración", "Valores actualizados correctamente")
            # Ocultar el frame de configuración
            frame_configuracion.grid_remove()

    def vista_recaudacion_diaria(self, tree, calendario, frame_qr, frame_calendario, variable_1, variable_2, variable_3):
        self.mostrar_calendario(frame_qr, frame_calendario)
        self.fecha = calendario.get_date()
        resultado, filas, total_tarifa_formateada = self.estacionamiento.mostrar_recaudacion_diaria(self.fecha)
        
        # Limpiar la tabla
        for item in tree.get_children():
            tree.delete(item)
        
        if resultado == "sin_datos":
            self.listar(tree, variable_1, variable_2, variable_3)
            messagebox.showinfo("Recaudación Diaria", "No hay datos de recaudación del día para mostrar. Seleccione otra fecha.")
        elif resultado == "datos_mostrados":
            # Insertar todos los registros
            for fila in filas:
                tree.insert("", "end", values=fila)
            
            # Insertar la fila con el total de tarifas
            tree.insert("", "end", values=("", "", "", "", "", "", "", "", "Total", total_tarifa_formateada), tags=('total',))
            tree.tag_configure('total', background='lightgray', font=('Helvetica', 12, 'bold'))
            
            messagebox.showinfo("Recaudación Diaria", f"Total recaudado: ${total_tarifa_formateada}")
        
        
        self.estacionamiento.borrar_campos(variable_1, variable_2, variable_3)

    def mostrar_descripcion(self, event, texto, root, descripcion):
        x = event.widget.winfo_rootx() - root.winfo_rootx() + event.widget.winfo_width() // 2
        y = event.widget.winfo_rooty() - root.winfo_rooty() + event.widget.winfo_height()
        
        # Ajustar la posición si la descripción se sale de los límites de la ventana
        if x + descripcion.winfo_reqwidth() > root.winfo_width():
            x = root.winfo_width() - descripcion.winfo_reqwidth()
        if y + descripcion.winfo_reqheight() > root.winfo_height():
            y = root.winfo_height() - descripcion.winfo_reqheight()

        descripcion.config(text=texto)
        descripcion.place(x=x, y=y)

    def ocultar_descripcion(self, event, descripcion):
        descripcion.place_forget()

    def salir_configuracion(self, frame_configuracion, frame_qr, frame_calendario, frame_manual):
        self.limpiar_frame_qr(frame_qr)
        self.limpiar_frame_calendario(frame_calendario)
        self.limpiar_frame_manual(frame_manual)
        if frame_configuracion.winfo_viewable():
            frame_configuracion.grid_remove()
        else:
            frame_configuracion.grid()

    def mostrar_calendario(self,frame_qr, frame_calendario):
        if frame_qr.winfo_viewable():
            frame_qr.grid_remove()
            frame_calendario.grid()
        else:
            frame_calendario.grid()

    def salir_calendario(self, tree, frame_calendario, frame_configuracion, frame_qr, frame_manual, variable_1, variable_2, variable_3):
        self.limpiar_frame_configuracion(frame_configuracion)
        self.limpiar_frame_qr(frame_qr)
        self.limpiar_frame_manual(frame_manual)
        if frame_calendario.winfo_viewable():
            frame_calendario.grid_remove()
        else:
            frame_calendario.grid()
        self.listar(tree, variable_1, variable_2, variable_3)

    def salir_manual(self, frame_manual, frame_configuracion, frame_calendario, frame_qr):
        self.limpiar_frame_configuracion(frame_configuracion)
        self.limpiar_frame_calendario(frame_calendario)
        self.limpiar_frame_qr(frame_qr)
        if frame_manual.winfo_viewable():
            frame_manual.grid_remove()
        else:
            frame_manual.grid()

    def salir_iconos(self, frame_iconos):
        if frame_iconos.winfo_viewable():
            frame_iconos.grid_remove()
        else:
            frame_iconos.grid()

    def salir_qr(self, frame_qr, frame_configuracion, frame_calendario, frame_manual):
        self.limpiar_frame_configuracion(frame_configuracion)
        self.limpiar_frame_calendario(frame_calendario)
        self.limpiar_frame_manual(frame_manual)
        if frame_qr.winfo_viewable():
            frame_qr.grid_remove()
        else:
            frame_qr.grid()

    def limpiar_frame_configuracion(self, frame_configuracion):
        if frame_configuracion.winfo_viewable():
            frame_configuracion.grid_remove()

    def limpiar_frame_calendario(self, frame_calendario):
        if frame_calendario.winfo_viewable():
            frame_calendario.grid_remove()

    def limpiar_frame_manual(self, frame_manual):
        if frame_manual.winfo_viewable():
            frame_manual.grid_remove()

    def limpiar_frame_qr(self, frame_qr):
        if frame_qr.winfo_viewable():
            frame_qr.grid_remove()

    def elegir_color(self, root):
        color = colorchooser.askcolor()
        if color[1]:
            # Cambiar el color de fondo del frame principal
            root.config(bg=color[1])
            
            # Cambiar el color de fondo de todos los frames y widgets en root
            for widget in root.winfo_children():
                if isinstance(widget, tk.Frame):
                    widget.config(bg=color[1])
                    for sub_widget in widget.winfo_children():
                        if isinstance(sub_widget, (tk.Frame, tk.Label, tk.Button)) and not isinstance(sub_widget, tk.Entry):
                            sub_widget.config(bg=color[1])

    def cambiar_color(self, root, frame):
        colores = ["#F95E67", "#5FFA96", "#64C8FA", "#FAF5A5", "#F49EFA", "#FAC56E", "#FA9DCF"]
        color_aleatorio = random.choice(colores)
        root.config(bg=color_aleatorio)
        frame.config(bg=color_aleatorio)
        
        for fondos in root.winfo_children():
            if isinstance(fondos, tk.Frame):
                fondos.config(bg=color_aleatorio)
                for widget in fondos.winfo_children():
                    config = widget.config()
                    if config is not None and 'bg' in config and not isinstance(widget, tk.Entry):
                        widget.config(bg=color_aleatorio)

    def estilo_original(self, root, frame, color_original):
        root.config(bg=color_original)
        frame.config(bg=color_original)
        for fondos in root.winfo_children():
            if isinstance(fondos, tk.Frame):
                fondos.config(bg=color_original)
                for widget in fondos.winfo_children():
                    config = widget.config()
                    if config is not None:
                        if 'bg' in config and not isinstance(widget, tk.Entry):
                            widget.config(bg=color_original)
                        if 'fg' in config:
                            widget.config(fg="black")
 
    def actualizar_grafico(self, root, ax, canvas):
        
        cocheras_ocupadas, cocheras_disponibles = self.estacionamiento.disponibilidad()
        
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
        root.after(2000, self.actualizar_grafico, root, ax, canvas)  # Actualiza cada 2000 ms (2 segundos)
    

class VistaPrincipal:
    def __init__(self, root):
        self.root = root   # Asigna el parámetro root al atributo root de la instancia
        self.root.title("Gestión de Estacionamiento")
        self.root.state('zoomed')
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.ruta = os.path.join(BASE_DIR, "img", "estacionamiento.ico")
        self.root.iconbitmap(self.ruta)
        self.root.grid_columnconfigure(0, weight=1)

        # Crea el frame principal
        self.frame = tk.Frame(self.root)   #Crea un frame dentro de la ventana principal
        self.frame.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")
        self.frame.grid_columnconfigure(9, weight=1)

        # Creacion frames secundarios
        self.frame_qr = tk.Frame(self.root, bg=None)
        self.frame_qr.grid(row=6, column=0)

        self.frame_configuracion = tk.Frame(self.root, bg=None)
        self.frame_configuracion.grid(row=6, column=0, padx=10, pady=10)

        self.frame_manual = tk.Frame(self.root, bg=None)
        self.frame_manual.grid(row=6, column=0, padx=10, pady=10, sticky="nsew")

        self.frame_calendario = tk.Frame(self.root, bg=None)
        self.frame_calendario.grid(row=6, column=0, padx=10, pady=10, columnspan=11, sticky="nsew")

        # Crea etiqueta descriptiva
        self.descripcion = tk.Label(self.root, text="", fg='white', bg="grey")

        # Guarda color original
        self.color_original = self.frame.cget("bg")
        
        # Inicializar la instancia de Estacionamiento
        self.estacionamiento = Estacionamiento(None, None, None)   # Crea una instancia de la clase Estacionamiento
        #self.estacionamiento.cargar_configuracion()   # Carga la configuracion del estacionamiento

        # Crear la figura y el eje para el gráfico
        self.fig = Figure(figsize=(3, 4), dpi=75, facecolor='#EEEEEE')
        self.ax = self.fig.add_subplot(111)

        # Crear un lienzo para el gráfico
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=3, column=12, padx=10, pady=10, sticky="nsew")

        # Instanciar FuncionesAuxiliares 
        self.funciones_auxiliares = FuncionesAuxiliares()   # Instanciación: self.funciones_auxiliares permite que VistaPrincipal utilice métodos de FuncionesAuxiliares
        self.funciones_auxiliares.actualizar_grafico(self.root, self.ax, self.canvas)
        
        # Inicializar variables
        self.variable_1, self.variable_2, self.variable_3 = StringVar(), StringVar(), StringVar()
        self.capacidad_var = StringVar(value=self.estacionamiento.capacidad)
        self.tarifa_auto_var = StringVar(value=self.estacionamiento.tarifas['auto'])
        self.tarifa_camioneta_var = StringVar(value=self.estacionamiento.tarifas['camioneta'])
        self.tarifa_moto_var = StringVar(value=self.estacionamiento.tarifas['moto'])

        # Crea y configura frame de iconos 
        self.frame_iconos = tk.Frame(self.root)
        self.frame_iconos.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self.frame_iconos.grid_columnconfigure(7, weight=1)
        separator = ttk.Separator(self.root, orient='horizontal')
        separator.grid(row=1, column=0, sticky="ewn")

        # Rutas de los íconos
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.ruta1 = os.path.join(self.BASE_DIR, "img", "acceso.ico")
        self.ruta2 = os.path.join(self.BASE_DIR, "img", "salida1.ico")
        self.ruta3 = os.path.join(self.BASE_DIR, "img", "modificar.ico")
        self.ruta4 = os.path.join(self.BASE_DIR, "img", "buscar.ico")
        self.ruta5 = os.path.join(self.BASE_DIR, "img", "actualizar.ico")
        self.ruta6 = os.path.join(self.BASE_DIR, "img", "borrar.ico")
        self.ruta7 = os.path.join(self.BASE_DIR, "img", "configuracion.ico")
        self.ruta8 = os.path.join(self.BASE_DIR, "img", "recaudacion.ico")
        self.ruta9 = os.path.join(self.BASE_DIR, "img", "sobre.ico")
        self.ruta10 = os.path.join(self.BASE_DIR, "img", "oculto1.ico")

        ### TABLA ###
        self.tree = ttk.Treeview(self.frame, columns=("ID", "Dominio", "Tipo", "Fecha", "Hora", 
        "Salida Registrada", "Fecha Salida", "Hora Salida", "Tiempo estacionado",
        "Tarifa"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Dominio", text="Dominio")
        self.tree.heading("Tipo", text="Tipo")
        self.tree.heading("Fecha", text="Fecha")
        self.tree.heading("Hora", text="Hora")
        self.tree.heading("Salida Registrada", text="Salida Registrada")
        self.tree.heading("Fecha Salida", text="Fecha Salida")
        self.tree.heading("Hora Salida", text="Hora Salida")
        self.tree.heading("Tiempo estacionado", text="Tiempo estacionado")
        self.tree.heading("Tarifa", text="Tarifa")

        self.tree.column("ID", width=50)
        self.tree.column("Dominio", width=100)
        self.tree.column("Tipo", width=100)
        self.tree.column("Fecha", width=100)
        self.tree.column("Hora", width=100)
        self.tree.column("Salida Registrada", width=100)
        self.tree.column("Fecha Salida", width=100)
        self.tree.column("Hora Salida", width=100)
        self.tree.column("Tiempo estacionado", width=120)
        self.tree.column("Tarifa", width=100)

        self.tree.grid(row=3, column=0, columnspan= 11, sticky="nsew")

        # Crear Scrollbar vertical
        self.scrollbar_vertical = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        self.scrollbar_vertical.grid(row=3, column=11, sticky="ns")
        self.tree.configure(yscrollcommand=self.scrollbar_vertical.set)

        # Vincular la selección de la tabla con la función seleccionar_vehiculo
        self.tree.bind("<<TreeviewSelect>>", lambda event: self.funciones_auxiliares.seleccionar_vehiculo(self.variable_1, self.variable_2,self.variable_3, self.tree))

        # Crear barra menu
        self.barra_menu()
        # Crear los botones con los íconos y agregar funcionalidad
        self.crear_iconos()
        # Crear los label, entry y botones
        self.crear_label_entry_botones()
        # Crear calendario
        self.calendario()
        # Llamar a la función listar para mostrar los datos iniciales
        self.listar()

    def crear_iconos(self):
        img1_tk = self.funciones_auxiliares.cargar_imagen(self.ruta1)
        self.btn_reg = tk.Button(self.frame_iconos, image=img1_tk, command=lambda:self.funciones_auxiliares.vista_registrar(self.tree, self.variable_1, self.variable_2, self.variable_3))
        self.btn_reg.config(cursor='hand2')
        self.btn_reg.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.btn_reg.bind("<Enter>", lambda event: self.funciones_auxiliares.mostrar_descripcion(event, "Ingresar vehículo", self.root, self.descripcion))
        self.btn_reg.bind("<Leave>", lambda event: self.funciones_auxiliares.ocultar_descripcion(event, self.descripcion))

        img2_tk = self.funciones_auxiliares.cargar_imagen(self.ruta2)
        self.btn_sal = tk.Button(self.frame_iconos, image=img2_tk, command=lambda:self.funciones_auxiliares.vista_salida_tarifa(self.tree, self.variable_1, self.variable_2, self.variable_3))
        self.btn_sal.config(cursor='hand2')
        self.btn_sal.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.btn_sal.bind("<Enter>", lambda event: self.funciones_auxiliares.mostrar_descripcion(event, "Registrar salida", self.root, self.descripcion))
        self.btn_sal.bind("<Leave>", lambda event: self.funciones_auxiliares.ocultar_descripcion(event, self.descripcion))

        img3_tk = self.funciones_auxiliares.cargar_imagen(self.ruta3)
        self.btn_mod = tk.Button(self.frame_iconos, image=img3_tk, command=lambda:self.funciones_auxiliares.vista_modificar_vehiculo(self.variable_1, self.variable_2, self.tree, self.variable_3))
        self.btn_mod.config(cursor='hand2')
        self.btn_mod.grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.btn_mod.bind("<Enter>", lambda event: self.funciones_auxiliares.mostrar_descripcion(event, "Modificar", root, self.descripcion))
        self.btn_mod.bind("<Leave>", lambda event: self.funciones_auxiliares.ocultar_descripcion(event, self.descripcion))

        img4_tk = self.funciones_auxiliares.cargar_imagen(self.ruta4)
        self.btn_bus = tk.Button(self.frame_iconos, image=img4_tk, command=lambda:self.funciones_auxiliares.vista_buscar(self.variable_1, self.variable_2, self.variable_3, self.tree))
        self.btn_bus.config(cursor='hand2')
        self.btn_bus.grid(row=0, column=3, padx=10, pady=5, sticky="w")
        self.btn_bus.bind("<Enter>", lambda event: self.funciones_auxiliares.mostrar_descripcion(event, "Buscar", root, self.descripcion))
        self.btn_bus.bind("<Leave>", lambda event: self.funciones_auxiliares.ocultar_descripcion(event, self.descripcion))

        img5_tk = self.funciones_auxiliares.cargar_imagen(self.ruta5)
        self.btn_act = tk.Button(self.frame_iconos, image=img5_tk, command=lambda:self.funciones_auxiliares.listar(self.tree, self.variable_1, self.variable_2, self.variable_3))
        self.btn_act.config(cursor='hand2')
        self.btn_act.grid(row=0, column=4, padx=10, pady=5, sticky="w")
        self.btn_act.bind("<Enter>", lambda event: self.funciones_auxiliares.mostrar_descripcion(event, "Actualizar", root, self.descripcion))
        self.btn_act.bind("<Leave>", lambda event: self.funciones_auxiliares.ocultar_descripcion(event, self.descripcion))

        img6_tk = self.funciones_auxiliares.cargar_imagen(self.ruta6)
        self.btn_eli = tk.Button(self.frame_iconos, image=img6_tk, command=lambda:self.funciones_auxiliares.vista_borrar(self.tree, self.variable_1, self.variable_2, self.variable_3))
        self.btn_eli.config(cursor='hand2')
        self.btn_eli.grid(row=0, column=5, padx=10, pady=5, sticky="w")
        self.btn_eli.bind("<Enter>", lambda event: self.funciones_auxiliares.mostrar_descripcion(event, "Eliminar", root, self.descripcion))
        self.btn_eli.bind("<Leave>", lambda event: self.funciones_auxiliares.ocultar_descripcion(event, self.descripcion))

        img7_tk = self.funciones_auxiliares.cargar_imagen(self.ruta7)
        self.btn_con = tk.Button(self.frame_iconos, image=img7_tk, command=lambda: self.funciones_auxiliares.salir_configuracion(self.frame_configuracion, self.frame_qr, self.frame_calendario, self.frame_manual))
        self.btn_con.config(cursor='hand2')
        self.btn_con.grid(row=0, column=6, padx=10, pady=5, sticky="w")
        self.btn_con.bind("<Enter>", lambda event: self.funciones_auxiliares.mostrar_descripcion(event, "Configuración", root, self.descripcion))
        self.btn_con.bind("<Leave>", lambda event: self.funciones_auxiliares.ocultar_descripcion(event, self.descripcion))

        img8_tk = self.funciones_auxiliares.cargar_imagen(self.ruta8)
        self.btn_rec = tk.Button(self.frame_iconos, image=img8_tk, command=lambda:self.funciones_auxiliares.vista_recaudacion_diaria(self.tree, self.calendario, self.frame_qr, self.frame_calendario, self.variable_1, self.variable_2, self.variable_3))
        self.btn_rec.config(cursor='hand2')
        self.btn_rec.grid(row=0, column=7, padx=10, pady=5, sticky="w")
        self.btn_rec.bind("<Enter>", lambda event: self.funciones_auxiliares.mostrar_descripcion(event, "Recaudación", root, self.descripcion))
        self.btn_rec.bind("<Leave>", lambda event: self.funciones_auxiliares.ocultar_descripcion(event, self.descripcion))

        img9_tk = self.funciones_auxiliares.cargar_imagen(self.ruta9)
        self.btn_inf = tk.Button(self.frame_iconos, image=img9_tk, command=lambda: self.funciones_auxiliares.salir_qr(self.frame_qr, self.frame_configuracion, self.frame_calendario, self.frame_manual))
        self.btn_inf.config(cursor='hand2')
        self.btn_inf.grid(row=0, column=8, padx=10, pady=5, sticky="w")
        self.btn_inf.bind("<Enter>", lambda event: self.funciones_auxiliares.mostrar_descripcion(event, "Información", root, self.descripcion))
        self.btn_inf.bind("<Leave>", lambda event: self.funciones_auxiliares.ocultar_descripcion(event, self.descripcion))

        img10_tk = self.funciones_auxiliares.cargar_imagen(self.ruta10)
        self.btn_ocu = tk.Button(self.frame_iconos, image=img10_tk, command=lambda: self.funciones_auxiliares.salir_iconos(self.frame_iconos))
        self.btn_ocu.config(cursor='hand2')
        self.btn_ocu.grid(row=0, column=9, padx=10, pady=5, sticky="e")
        self.btn_ocu.bind("<Enter>", lambda event: self.funciones_auxiliares.mostrar_descripcion(event, "Ocultar iconos", root, self.descripcion))
        self.btn_ocu.bind("<Leave>", lambda event:self.funciones_auxiliares.ocultar_descripcion(event, self.descripcion))
        
    def crear_label_entry_botones(self):

        ### LABEL Y ENTRY ###
        self.label_dominio = tk.Label(self.frame, text="Dominio:")
        self.label_dominio.grid(row=0, column=0, padx=5, pady=5)
        self.entry_dominio = Entry(self.frame, textvariable = self.variable_1)
        self.entry_dominio.grid(row=0, column=1, padx=5, pady=5)

        self.label_tipo = tk.Label(self.frame, text="Tipo:")
        self.label_tipo.grid(row=1, column=0, padx=5, pady=5)
        self.entry_tipo = ttk.Combobox(self.frame, textvariable= self.variable_2, values=["Auto", "Camioneta", "Moto"])
        self.entry_tipo.grid(row=1, column=1, padx=5, pady=5)

        self.label_realizar_salida = tk.Label(self.frame, text="Dominio salida:")
        self.label_realizar_salida.grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.entry_realizar_salida = Entry(self.frame, textvariable = self.variable_3)
        self.entry_realizar_salida.grid(row=4, column=1, padx=5, pady=5, sticky="e")

        ### BOTONES ###
        self.btn_registrar = tk.Button(self.frame, text="Registrar Vehículo", command=lambda:self.funciones_auxiliares.vista_registrar(self.tree, self.variable_1, self.variable_2, self.variable_3))
        self.btn_registrar.config(cursor='hand2')
        self.btn_registrar.grid(row=2, column=0, padx=10, pady=5, sticky='ew')

        self.btn_eliminar = tk.Button(self.frame, text="Eliminar Vehículo", command=lambda:self.funciones_auxiliares.vista_borrar(self.tree, self.variable_1, self.variable_2, self.variable_3))
        self.btn_eliminar.config(cursor='hand2')
        self.btn_eliminar.grid(row=2, column=2, padx=10, pady=5, sticky='ew')

        self.btn_modificar = tk.Button(self.frame, text="Modificar Vehículo", command=lambda:self.funciones_auxiliares.vista_modificar_vehiculo(self.variable_1, self.variable_2, self.tree, self.variable_3))
        self.btn_modificar.config(cursor='hand2')
        self.btn_modificar.grid(row=2, column=3, padx=10, pady=5, sticky='ew')

        self.btn_buscar = tk.Button(self.frame, text=" Buscar por dominio ", command=lambda:self.funciones_auxiliares.vista_buscar(self.variable_1, self.variable_2, self.variable_3, self.tree))
        self.btn_buscar.config(cursor='hand2')
        self.btn_buscar.grid(row=2, column=4, padx=10, pady=5, sticky='ew')

        self.btn_listar = tk.Button(self.frame, text=" Actualizar ", command=lambda:self.funciones_auxiliares.listar(self.tree, self.variable_1, self.variable_2, self.variable_3))
        self.btn_listar.config(cursor='hand2')
        self.btn_listar.grid(row=2, column=5, padx=10, pady=5, sticky='ew')

        self.btn_registrar_salida = tk.Button(self.frame, text="Registrar Salida", command=lambda:self.funciones_auxiliares.vista_salida_tarifa(self.tree, self.variable_1, self.variable_2, self.variable_3))
        self.btn_registrar_salida.config(cursor='hand2')
        self.btn_registrar_salida.grid(row=4, column=2, padx=10, pady=5, sticky='ew')

        self.btn_recaudacion = tk.Button(self.frame, text="Mostrar Recaudación", command=lambda:self.funciones_auxiliares.vista_recaudacion_diaria(self.tree, self.calendario, self.frame_qr, self.frame_calendario, self.variable_1, self.variable_2, self.variable_3))
        self.btn_recaudacion.config(cursor='hand2')
        self.btn_recaudacion.grid(row=4, column=10, padx=10, pady=5, sticky="ew")
        
    def barra_menu(self):
        # Crear un menú
        menu_bar = Menu(root)
        root.config(menu=menu_bar)
        # Añadir un menú llamado "Menú"
        menu_principal = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Menú", menu=menu_principal)
        # Añadir las opciones "Configuración" y "Salir" a Menú y un separador
        menu_principal.add_command(label="Configuración", command=lambda: self.funciones_auxiliares.salir_configuracion(self.frame_configuracion, self.frame_qr, self.frame_calendario, self.frame_manual))
        menu_principal.add_separator()  # Añadir un separador
        menu_principal.add_command(label="Salir", command=root.quit)

        # Validación de entrada para entrys de Configuracions
        vcmd_numerica = (root.register(self.estacionamiento.validar_entrada_numerica), '%P')
        vcmd_decimal = (root.register(self.estacionamiento.validar_entrada_decimal), '%P')

        # Cargar configuración
        # Crear variables
        # self.capacidad_var = StringVar(value=modelo_poo.capacidad)
        # self.tarifa_auto_var = StringVar(value=modelo_poo.tarifas['auto'])
        # self.tarifa_camioneta_var = StringVar(value=modelo_poo.tarifas['camioneta'])
        # self.tarifa_moto_var = StringVar(value=modelo_poo.tarifas['moto'])

        # Campos de entrada configuracion
        self.label_capacidad = tk.Label(self.frame_configuracion, text="Capacidad:")
        self.label_capacidad.grid(row=0, column=0, padx=10, pady=5)
        self.entry_capacidad = tk.Entry(self.frame_configuracion, textvariable=self.capacidad_var, validate='key', validatecommand=vcmd_numerica)
        self.entry_capacidad.grid(row=0, column=1, padx=10, pady=5)
        

        self.label_tarifa_auto = tk.Label(self.frame_configuracion, text="Tarifa Auto:")
        self.label_tarifa_auto.grid(row=1, column=0, padx=10, pady=5)
        self.entry_tarifa_auto = tk.Entry(self.frame_configuracion, textvariable=self.tarifa_auto_var, validate='key', validatecommand=vcmd_decimal)
        self.entry_tarifa_auto.grid(row=1, column=1, padx=10, pady=5)
        

        self.label_tarifa_camioneta = tk.Label(self.frame_configuracion, text="Tarifa Camioneta:")
        self.label_tarifa_camioneta.grid(row=2, column=0, padx=10, pady=5)
        self.entry_tarifa_camioneta = tk.Entry(self.frame_configuracion, textvariable=self.tarifa_camioneta_var, validate='key', validatecommand=vcmd_decimal)
        self.entry_tarifa_camioneta.grid(row=2, column=1, padx=10, pady=5)
        

        self.label_tarifa_moto = tk.Label(self.frame_configuracion, text="Tarifa Moto:")
        self.label_tarifa_moto.grid(row=3, column=0, padx=10, pady=5)
        self.entry_tarifa_moto = tk.Entry(self.frame_configuracion, textvariable=self.tarifa_moto_var, validate='key', validatecommand=vcmd_decimal)
        self.entry_tarifa_moto.grid(row=3, column=1, padx=10, pady=5)
        
        # Insertar valores en los campos de entrada
        # self.entry_capacidad.insert(0, self.modelo_poo.tarifas)
        # self.entry_tarifa_auto.insert(0, self.modelo_poo.tarifas['auto'])
        # self.entry_tarifa_camioneta.insert(0, self.modelo_poo.tarifas['camioneta'])
        # self.entry_tarifa_moto.insert(0, self.modelo_poo.tarifas['moto'])

        self.btn_guardar = tk.Button(self.frame_configuracion, text="Guardar", command=lambda: self.funciones_auxiliares.vista_guardar_configuracion(self.entry_capacidad, self.entry_tarifa_auto, self.entry_tarifa_camioneta, self.entry_tarifa_moto, self.frame_configuracion))
        self.btn_guardar.config(cursor='hand2')
        self.btn_guardar.grid(row=4, column=0, columnspan=2, pady=10)

        self.btn_ocultar = tk.Button(self.frame_configuracion, text="Ocultar", command=lambda: self.funciones_auxiliares.salir_configuracion(self.frame_configuracion, self.frame_qr, self.frame_calendario, self.frame_manual))
        self.btn_ocultar.config(cursor='hand2')
        self.btn_ocultar.grid(row=4, column=1, padx=10, pady=5)

        # Inicialmente ocultar el frame de configuración
        self.frame_configuracion.grid_remove()

        # Añadir un menú llamado "vista"
        vista = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Vista", menu=vista)

        # Añadir las opciones "Elegir color de fondo", "Color aleatorio", "Color original", "Barra de iconos"
        vista.add_command(label="Elegir color de fondo", command=lambda: self.funciones_auxiliares.elegir_color(root))
        vista.add_command(label="Color de fondo aleatorio", command=lambda:self.funciones_auxiliares.cambiar_color(root, self.frame))
        vista.add_command(label="Color original", command=lambda: self.funciones_auxiliares.estilo_original(root, self.frame, self.color_original))
        vista.add_separator()  # Añadir un separador
        vista.add_command(label="Barra de iconos", command=lambda: self.funciones_auxiliares.salir_iconos(self.frame_iconos))

        # Añadir un menú llamado "Base de datos"
        base = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Base de Datos", menu=base)
        base.add_command(label="Vaciar base de datos", command=lambda:self.funciones_auxiliares.vista_borrar_todos_los_datos(self.tree, self.variable_1, self.variable_2, self.variable_3, confirmar=False))

        # Añadir un menú llamado "Ayuda"
        ayuda = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Ayuda", menu=ayuda)
        ayuda.add_command(label="Funciones básicas", command=lambda:self.funciones_auxiliares.salir_manual(self.frame_manual, self.frame_configuracion, self.frame_calendario, self.frame_qr))
        ayuda.add_command(label="Manual de usuario", command=self.estacionamiento.abrir_manual)
        

        tk.Label(self.frame_manual, text=(
            "INGRESAR VEHÍCULO: Complete los campos de dominio "
            "y tipo y luego presione boton de Registrar Vehículo"
        )).grid(row=0, column=0, sticky='w')
        tk.Label(self.frame_manual, text=(
            "REGISTRAR SALIDA: Complete el campo de Dominio "
            "salida y luego presione boton de Registrar Salida"
        )).grid(row=1, column=0, sticky='w')
        tk.Label(self.frame_manual, text=(
            "ELIMINAR VEHÍCULO: Seleccione en la tabla, con el cursor, el vehículo "
            "que desea eliminar y luego presione boton de Eliminar Vehículo"
        )).grid(row=2, column=0, sticky='w')
        tk.Label(self.frame_manual, text=(
            "MODIFICAR VEHÍCULO: Seleccione en la tabla, con el cursor, el vehículo "
            "que desea modificar, modifique el dominio o tipo y luego presione boton de Modificar"
        )).grid(row=3, column=0, sticky='w')
        tk.Label(self.frame_manual, text=(
            "BUSCAR POR DOMINIO: Complete el campo de Dominio y luego presione boton "
            "de Buscar por Dominio")).grid(row=4, column=0, sticky='w')
        tk.Label(self.frame_manual, text=(
            "ACTUALIZAR TABLA: Este botón actualiza la tabla luego de modificar, "
            "eliminar o cuando lo necesite")).grid(row=5, column=0, sticky='w')
        tk.Label(self.frame_manual, text=(
            "CONFIGURACION: Dentro de Menú se encuntra Configuración que nos permite "
            "configurar la capacidad del estacionamiento y las tarifas de los distintos vehículos"
        )).grid(row=6, column=0, sticky='w')
        tk.Label(self.frame_manual, text=(
            "RECAUDACIÓN: Muestra la recaudación del día por defecto. Se puede seleccionar "
            "dia en el calendario y luego de presionar botón 'ver recaudación' muestra recaudación "
            "del día elejido")).grid(row=7, column=0, sticky='w')
        btn_cerrar_manual = tk.Button(self.frame_manual, text="Cerra Manual", command=lambda:self.funciones_auxiliares.salir_manual(self.frame_manual, self.frame_configuracion, self.frame_calendario, self.frame_qr))
        btn_cerrar_manual.config(cursor='hand2')
        btn_cerrar_manual.grid(row=8, column=0, padx=10, pady=5, sticky='w')
        # Inicialmente ocultar el frame de Manual de usuario
        self.frame_manual.grid_remove()

        # Añadir un menú llamado "Info"
        ayuda = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Información", menu=ayuda)
        imagen_pil = Image.open(self.ruta)  
        imagen_redimensionada = imagen_pil.resize((20, 20))
        imagen = ImageTk.PhotoImage(imagen_redimensionada)
        imagenes.append(imagen)  # Almacenar la referencia
        ayuda.add_command(label="  Gestión de estacionamiento",image=imagen, compound=tk.LEFT, command=lambda: self.funciones_auxiliares.salir_qr(self.frame_qr, self.frame_configuracion, self.frame_calendario, self.frame_manual))

        # Código QR con información
        # Información del estacionamiento
        info_estacionamiento = "UTN - Python 3 - Nivel Inicial\nCurso: 999194877\nAlumno: Carlos Potenza\npotenzacd@gmail.com"
        # Generar el código QR
        qr_img = self.estacionamiento.generar_qr(info_estacionamiento)
        # Convertir la imagen del código QR a un formato compatible con Tkinter
        qr_img_tk = ImageTk.PhotoImage(qr_img)
        
        # Crear un label para mostrar el código QR
        self.qr_label = tk.Label(self.frame_qr, image=qr_img_tk)
        self.qr_label.image = qr_img_tk  # Mantener una referencia a la imagen
        self.qr_label.grid(row=0, column=0, padx=10, pady=5)
        # Crear boton en frame de qr para ocultarlo
        self.btn_qr = tk.Button(self.frame_qr, text="Ocultar", command=lambda: self.funciones_auxiliares.salir_qr(self.frame_qr, self.frame_configuracion, self.frame_calendario, self.frame_manual))
        self.btn_qr.config(cursor='hand2')
        self.btn_qr.grid(row=1, column=0, padx=10, pady=5)
        # Inicialmente ocultar el frame de configuración
        self.frame_qr.grid_remove()

    def calendario(self):
        self.calendario = Calendar(
            self.frame_calendario,
            selectmode="day",
            background="black",
            selectbackground="blue",
            normalbackground="white",
            weekendbackground="light blue",
            othermonthbackground="pink",
            othermonthwebackground="pink",
        )

        self.calendario.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        salir_calend = tk.Button(self.frame_calendario, text="Ocultar", command=lambda:self.funciones_auxiliares.salir_calendario(self.tree, self.frame_calendario, self.frame_configuracion, self.frame_qr, self.frame_manual, self.variable_1, self.variable_2, self.variable_3))
        salir_calend.config(cursor='hand2')
        salir_calend.grid(row=0, column=1, padx=10, pady=5)

        # Actualizar recaudación al seleccionar una nueva fecha
        self.calendario.bind("<<CalendarSelected>>", lambda event: self.funciones_auxiliares.vista_recaudacion_diaria(self.tree, self.calendario, self.frame_qr, self.frame_calendario, self.variable_1, self.variable_2, self.variable_3))

        # Inicialmente ocultar el frame de calendario
        self.frame_calendario.grid_remove()
        
    def actualizar_grafico(self):
        self.funciones_auxiliares.actualizar_grafico(self.root, self.ax, self.canvas)

    def listar(self):
        self.funciones_auxiliares.listar(self.tree, self.variable_1, self.variable_2, self.variable_3)

    

if __name__ == "__main__":
    root = tk.Tk()
    app = VistaPrincipal(root)
    root.mainloop()

