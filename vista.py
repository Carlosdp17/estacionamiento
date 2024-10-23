import tkinter as tk
from tkinter import ttk, Menu, Entry, StringVar, messagebox, colorchooser
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import *
from PIL import Image, ImageTk
import os
import random
from modelo import conexion
from modelo import cargar_configuracion
from modelo import guardar_configuracion
#from modelo import mostrar_descripcion
#from modelo import ocultar_descripcion
from modelo import registrar_vehiculo
from modelo import salida_tarifa
from modelo import modificar_vehiculo
from modelo import buscar
#from modelo import listar
from modelo import borrar
from modelo import borrar_campos
from modelo import borrar_todos_los_datos
#from modelo import salir_configuracion
from modelo import registrar_vehiculo
from modelo import mostrar_recaudacion_diaria
#from modelo import salir_qr
#from modelo import salir_iconos
#from modelo import seleccionar_vehiculo
#from modelo import deseleccionar_vehiculo
from modelo import validar_entrada_decimal
from modelo import validar_entrada_numerica
#from modelo import salir_manual
#from modelo import salir_calendario
from modelo import abrir_manual
#from modelo import actualizar_grafico
from modelo import generar_qr
#from modelo import inicializar_variables
import modelo
from modelo import disponibilidad


# Lista global para almacenar las referencias a las imágenes
imagenes = []
id_seleccionado = None
########################################################################################################################################
# LISTAR
def listar(tree, variable_1, variable_2, variable_3):
    borrar_campos(variable_1, variable_2, variable_3)
    deseleccionar_vehiculo(tree, variable_1, variable_2, variable_3)
    # Limpiar la tabla
    for item in tree.get_children():
        tree.delete(item)
    # Conectar con base de datos
    conectar = conexion()
    cursor = conectar.cursor()
    sql = "SELECT * FROM autos"
    cursor.execute(sql)
    filas = cursor.fetchall()
    # Insertar todos los registros
    for fila in filas:
        tree.insert("", "0", values=fila)
    conectar.close()

def seleccionar_vehiculo(variable_1, variable_2, variable_3, tree):
    global id_seleccionado
    selected_item = tree.selection()               # Obtiene el identificador del elemento seleccionado en la tabla
    if selected_item:                              # Verificar si hay algún elemento seleccionado
        item = tree.item(selected_item)            # Obtiene los datos del elemento seleccionado en la tabla
        valores = item['values']                   # Extracción de valores
        id_seleccionado = valores[0]               # Asumiendo que el ID es el primer valor en la lista de valores
        borrar_campos(variable_1, variable_2, variable_3)                            # Borra texto en caso de que esté escrito el entry
        variable_1.set(valores[1])        # Inserta 2° valor (dominio) en el entry_dominio
        variable_2.set(valores[2])                 # inserta 3° valor (tipo) en el entry_tipo
        variable_3.set(valores[1])# Inserta 2° valor (dominio) en el entry_realizar_salida

def deseleccionar_vehiculo(tree, variable_1, variable_2, variable_3):
    global id_seleccionado
    selected_item = tree.selection()               # Obtiene el identificador del elemento seleccionado en la tabla
    if selected_item:                              # Verificar si hay algún elemento seleccionado
        tree.selection_remove(selected_item)       # Deselecciona el elemento
        id_seleccionado = None                     # Reinicia el valor de id_seleccionado
        borrar_campos(variable_1, variable_2, variable_3) 

########################################################################################################################################
# Función para cargar una imagen
def cargar_imagen(ruta, tamaño=(25, 25)):
    try:
        img = Image.open(ruta)
        img = img.resize(tamaño, Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        imagenes.append(img_tk)  # Almacenar la referencia
        return img_tk
    except Exception as e:
        print(f"Error al cargar la imagen: {e}")
        return None

def vista_registrar(tree, variable_1, variable_2, variable_3):
    resultado = registrar_vehiculo(variable_1, variable_2)
    
    if resultado == "dominio_vacio":
        messagebox.showinfo("Recuerde", "Debe completar el campo de Dominio.")
    elif resultado == "dominio_invalido":
        messagebox.showerror("Error", "El dominio no debe contener espacios y solo debe contener caracteres alfanuméricos.")
    elif resultado == "tipo_invalido":
        messagebox.showinfo("Recuerde!!!", "Seleccione tipo de vehículo de lista desplegable")
    elif resultado == "vehiculo_registrado":
        listar(tree, variable_1, variable_2, variable_3)
        messagebox.showinfo("Ingresando vehículo", "Vehículo dado de alta")
    elif resultado == "sin_cocheras":
        messagebox.showerror("Error", "No hay cocheras disponibles")

def vista_salida_tarifa(tree, variable_1, variable_2, variable_3):
    resultado, tarifa, tiempo_estacionado, dominio_min = salida_tarifa(variable_1, variable_2, variable_3)
    
    if resultado == "dominio_vacio":
        messagebox.showinfo("Recuerde", "Debe completar el campo de Dominio salida.")
    elif resultado == "tarifa_no_encontrada":
        messagebox.showerror("Error", f"No se encontró una tarifa para el tipo de vehículo.")
    elif resultado == "vehiculo_no_encontrado":
        messagebox.showerror("Error", "No se encontró un vehículo sin salida registrada con ese dominio.")
    elif resultado == "salida_registrada":
        listar(tree, variable_1, variable_2, variable_3)
        messagebox.showinfo("Salida registrada", f"Salida registrada para el vehículo con dominio {dominio_min}.")
        messagebox.showinfo(f"La tarifa total es: ${tarifa:.2f}", f"El vehículo con dominio {dominio_min} ha estado estacionado por {tiempo_estacionado}.")

def vista_buscar(variable_1, variable_2, variable_3, tree):
    dominio_buscado = variable_1.get()
    resultado, filas = buscar(dominio_buscado)
    
    if resultado == "dominio_vacio":
        messagebox.showinfo("Recuerde", "Debe completar el campo de Dominio.")
    elif resultado == "dominio_invalido":
        messagebox.showinfo("Error", "El dominio no debe contener espacios.")
    elif resultado == "vehiculo_no_encontrado":
        listar(tree, variable_1, variable_2, variable_3)
        messagebox.showinfo("Atención", "Vehículo no encontrado")
    elif resultado == "vehiculo_encontrado":
        # Limpiar la tabla
        for item in tree.get_children():
            tree.delete(item)
        
        # Insertar los resultados en la tabla
        for fila in filas:
            tree.insert("", "end", values=fila)
        
        borrar_campos(variable_1, variable_2, variable_3)

def vista_borrar(tree, variable_1, variable_2, variable_3):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showinfo("Atención", "No se ha seleccionado ningún vehículo")
        return
    
    # Obtener el ID del vehículo seleccionado
    id_seleccionado = tree.item(selected_item, 'values')[0]
    
    resultado = borrar(id_seleccionado, confirmar=False)
    
    if resultado == "confirmar_eliminacion":
        confirmar = messagebox.askyesno("Confirmar eliminación", "¿Estás seguro de que deseas eliminar este vehículo?")
        if confirmar:
            resultado = borrar(id_seleccionado, confirmar=True)
            if resultado == "vehiculo_eliminado":
                listar(tree, variable_1, variable_2, variable_3)
                messagebox.showinfo("Acción realizada", "Vehículo eliminado")
        else:
            listar(tree, variable_1, variable_2, variable_3)
    elif resultado == "no_salida_registrada":
        messagebox.showerror("Error", "No se puede eliminar el vehículo sin registrar su salida")
    
    borrar_campos(variable_1, variable_2, variable_3)

def vista_modificar_vehiculo(variable_1, variable_2, tree, variable_3):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showinfo("Atención!!!", "No se ha seleccionado ningún vehículo de la tabla. Seleccionelo por favor")
        return
    
    item = tree.item(selected_item)
    valores = item['values']
    id = valores[0]
    nuevo_dominio = variable_1.get().lower()
    nuevo_tipo = variable_2.get().lower()
    
    resultado = modificar_vehiculo(id, nuevo_dominio, nuevo_tipo)
    
    if resultado == "dominio_invalido":
        deseleccionar_vehiculo(tree, variable_1, variable_2, variable_3)
        messagebox.showinfo("Error", "El dominio no debe contener espacios y solo debe contener caracteres alfanuméricos.")
    elif resultado == "tipo_invalido":
        messagebox.showinfo("Recuerde!!!", "Seleccione vehículo de lista desplegable")
    elif resultado == "sin_cambios":
        deseleccionar_vehiculo(tree, variable_1, variable_2, variable_3)
        messagebox.showinfo("Atención!!!", "No se realizaron cambios en el vehículo.")
    elif resultado == "vehiculo_modificado":
        # Actualizar el ítem en el tree
        tree.item(selected_item, values=(id, nuevo_dominio, nuevo_tipo, valores[3], valores[4], valores[5], valores[6], valores[7], valores[8], valores[9]))
        deseleccionar_vehiculo(tree, variable_1, variable_2, variable_3)
        messagebox.showinfo("Atención!!!", "Vehículo modificado")
    
    borrar_campos(variable_1, variable_2, variable_3)

def vista_borrar_todos_los_datos(tree, variable_1, variable_2, variable_3, confirmar=False):
    resultado = borrar_todos_los_datos(confirmar=False)
    
    if resultado == "conexion_error":
        messagebox.showerror("Error", "No se pudo conectar a la base de datos.")
    elif resultado == "confirmar_eliminacion":
        confirmar = messagebox.askyesno("Confirmar eliminación", "¿Estás seguro de que deseas reiniciar Base de datos?\n Eliminarás toda la información")
        if confirmar:
            resultado = borrar_todos_los_datos(tree, confirmar=True)
            if resultado == "exito":
                listar(tree, variable_1, variable_2, variable_3)
                messagebox.showinfo("Éxito", "Todos los datos han sido borrados y los IDs han sido reiniciados.")
            elif resultado == "tabla_autos_no_existe":
                messagebox.showerror("Error", "La tabla 'autos' no existe.")
            elif resultado == "tabla_configuracion_no_existe":
                messagebox.showerror("Error", "La tabla 'configuración' no existe.")
    elif resultado == "tabla_autos_no_existe":
        messagebox.showerror("Error", "La tabla 'autos' no existe.")
    elif resultado == "tabla_configuracion_no_existe":
        messagebox.showerror("Error", "La tabla 'configuración' no existe.")

def vista_guardar_configuracion(entry_capacidad, entry_tarifa_auto, entry_tarifa_camioneta, entry_tarifa_moto, frame_configuracion):
    resultado = guardar_configuracion(entry_capacidad, entry_tarifa_auto, entry_tarifa_camioneta, entry_tarifa_moto)
    
    if resultado == "configuracion_actualizada":
        messagebox.showinfo("Configuración", "Valores actualizados correctamente")
        # Ocultar el frame de configuración
        frame_configuracion.grid_remove()

def vista_recaudacion_diaria(tree, calendario, frame_qr, frame_calendario, variable_1, variable_2, variable_3):
    fecha = calendario.get_date()
    resultado, filas, total_tarifa_formateada = mostrar_recaudacion_diaria(fecha)
    
    # Limpiar la tabla
    for item in tree.get_children():
        tree.delete(item)
    
    if resultado == "sin_datos":
        listar(tree, variable_1, variable_2, variable_3)
        messagebox.showinfo("Recaudación Diaria", "No hay datos de recaudación del día para mostrar. Seleccione otra fecha.")
    elif resultado == "datos_mostrados":
        # Insertar todos los registros
        for fila in filas:
            tree.insert("", "end", values=fila)
        
        # Insertar la fila con el total de tarifas
        tree.insert("", "end", values=("", "", "", "", "", "", "", "", "Total", total_tarifa_formateada), tags=('total',))
        tree.tag_configure('total', background='lightgray', font=('Helvetica', 12, 'bold'))
        
        messagebox.showinfo("Recaudación Diaria", f"Total recaudado: ${total_tarifa_formateada}")
    
    mostrar_calendario(frame_qr, frame_calendario)
    borrar_campos(variable_1, variable_2, variable_3)

def mostrar_descripcion(event, texto, root, descripcion):
    x = event.widget.winfo_rootx() - root.winfo_rootx() + event.widget.winfo_width() // 2
    y = event.widget.winfo_rooty() - root.winfo_rooty() + event.widget.winfo_height()
    
    # Ajustar la posición si la descripción se sale de los límites de la ventana
    if x + descripcion.winfo_reqwidth() > root.winfo_width():
        x = root.winfo_width() - descripcion.winfo_reqwidth()
    if y + descripcion.winfo_reqheight() > root.winfo_height():
        y = root.winfo_height() - descripcion.winfo_reqheight()

    descripcion.config(text=texto)
    descripcion.place(x=x, y=y)

def ocultar_descripcion(event, descripcion):
    descripcion.place_forget()

########################################################################################################################################

def salir_configuracion(frame_configuracion, frame_qr, frame_calendario, frame_manual):
    limpiar_frame_qr(frame_qr)
    limpiar_frame_calendario(frame_calendario)
    limpiar_frame_manual(frame_manual)
    if frame_configuracion.winfo_viewable():
        frame_configuracion.grid_remove()
    else:
        frame_configuracion.grid()

def mostrar_calendario(frame_qr, frame_calendario):
    if frame_qr.winfo_viewable():
        frame_qr.grid_remove()
        frame_calendario.grid()
    else:
        frame_calendario.grid()

def salir_calendario(tree, frame_calendario, frame_configuracion, frame_qr, frame_manual, variable_1, variable_2, variable_3):
    limpiar_frame_configuracion(frame_configuracion)
    limpiar_frame_qr(frame_qr)
    limpiar_frame_manual(frame_manual)
    if frame_calendario.winfo_viewable():
        frame_calendario.grid_remove()
    else:
        frame_calendario.grid()
    listar(tree, variable_1, variable_2, variable_3)

def salir_manual(frame_manual, frame_configuracion, frame_calendario, frame_qr):
    limpiar_frame_configuracion(frame_configuracion)
    limpiar_frame_calendario(frame_calendario)
    limpiar_frame_qr(frame_qr)
    if frame_manual.winfo_viewable():
        frame_manual.grid_remove()
    else:
        frame_manual.grid()

def salir_iconos(frame_iconos):
    if frame_iconos.winfo_viewable():
        frame_iconos.grid_remove()
    else:
        frame_iconos.grid()

def salir_qr(frame_qr, frame_configuracion, frame_calendario, frame_manual):
    limpiar_frame_configuracion(frame_configuracion)
    limpiar_frame_calendario(frame_calendario)
    limpiar_frame_manual(frame_manual)
    if frame_qr.winfo_viewable():
        frame_qr.grid_remove()
    else:
        frame_qr.grid()

def limpiar_frame_configuracion(frame_configuracion):
    if frame_configuracion.winfo_viewable():
        frame_configuracion.grid_remove()

def limpiar_frame_calendario(frame_calendario):
    if frame_calendario.winfo_viewable():
        frame_calendario.grid_remove()

def limpiar_frame_manual(frame_manual):
    if frame_manual.winfo_viewable():
        frame_manual.grid_remove()

def limpiar_frame_qr(frame_qr):
    if frame_qr.winfo_viewable():
        frame_qr.grid_remove()

########################################################################################################################################

def elegir_color(root):
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

def cambiar_color(root, frame):
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

def estilo_original(root, frame, color_original):
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

def vista_principal(root):
    root.title("Gestión de Estacionamiento")
    root.state('zoomed')
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.join(BASE_DIR, "img", "estacionamiento.ico")
    root.iconbitmap(ruta)
    root.grid_columnconfigure(0, weight=1)

    frame = tk.Frame(root)
    frame.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")
    frame.grid_columnconfigure(9, weight=1)

    frame_qr = tk.Frame(root, bg=None)
    frame_qr.grid(row=6, column=0)

    frame_configuracion = tk.Frame(root, bg=None)
    frame_configuracion.grid(row=6, column=0, padx=10, pady=10)

    frame_manual = tk.Frame(root, bg=None)
    frame_manual.grid(row=6, column=0, padx=10, pady=10, sticky="nsew")

    frame_calendario = tk.Frame(root, bg=None)
    frame_calendario.grid(row=6, column=0, padx=10, pady=10, columnspan=11, sticky="nsew")

    descripcion = tk.Label(root, text="", fg='white', bg="grey")
    color_original = frame.cget("bg")
    
    #inicializar_variables()
    cargar_configuracion()
    
    variable_1, variable_2, variable_3 = StringVar(), StringVar(), StringVar()

    frame_iconos = tk.Frame(root)
    frame_iconos.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
    frame_iconos.grid_columnconfigure(7, weight=1)
    separator = ttk.Separator(root, orient='horizontal')
    separator.grid(row=1, column=0, sticky="ewn")

    # Rutas de los íconos
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.join(BASE_DIR, "img", "estacionamiento.ico")
    ruta1 = os.path.join(BASE_DIR, "img", "acceso.ico")
    ruta2 = os.path.join(BASE_DIR, "img", "salida1.ico")
    ruta3 = os.path.join(BASE_DIR, "img", "modificar.ico")
    ruta4 = os.path.join(BASE_DIR, "img", "buscar.ico")
    ruta5 = os.path.join(BASE_DIR, "img", "actualizar.ico")
    ruta6 = os.path.join(BASE_DIR, "img", "borrar.ico")
    ruta7 = os.path.join(BASE_DIR, "img", "configuracion.ico")
    ruta8 = os.path.join(BASE_DIR, "img", "recaudacion.ico")
    ruta9 = os.path.join(BASE_DIR, "img", "sobre.ico")
    ruta10 = os.path.join(BASE_DIR, "img", "oculto1.ico")

    # Crear los botones con los íconos y agregar funcionalidad
    img1_tk = cargar_imagen(ruta1)
    btn_reg = tk.Button(frame_iconos, image=img1_tk, command=lambda:vista_registrar(tree, variable_1, variable_2, variable_3))
    btn_reg.config(cursor='hand2')
    btn_reg.grid(row=0, column=0, padx=10, pady=5, sticky="w")
    btn_reg.bind("<Enter>", lambda event: mostrar_descripcion(event, "Ingresar vehículo", root, descripcion))
    btn_reg.bind("<Leave>", lambda event: ocultar_descripcion(event, descripcion))

    img2_tk = cargar_imagen(ruta2)
    btn_sal = tk.Button(frame_iconos, image=img2_tk, command=lambda:vista_salida_tarifa(tree, variable_1, variable_2, variable_3))
    btn_sal.config(cursor='hand2')
    btn_sal.grid(row=0, column=1, padx=10, pady=5, sticky="w")
    btn_sal.bind("<Enter>", lambda event: mostrar_descripcion(event, "Registrar salida", root, descripcion))
    btn_sal.bind("<Leave>", lambda event: ocultar_descripcion(event, descripcion))

    img3_tk = cargar_imagen(ruta3)
    btn_mod = tk.Button(frame_iconos, image=img3_tk, command=lambda:vista_modificar_vehiculo(variable_1, variable_2, tree, variable_3))
    btn_mod.config(cursor='hand2')
    btn_mod.grid(row=0, column=2, padx=10, pady=5, sticky="w")
    btn_mod.bind("<Enter>", lambda event: mostrar_descripcion(event, "Modificar", root, descripcion))
    btn_mod.bind("<Leave>", lambda event: ocultar_descripcion(event, descripcion))

    img4_tk = cargar_imagen(ruta4)
    btn_bus = tk.Button(frame_iconos, image=img4_tk, command=lambda:vista_buscar(variable_1, variable_2, variable_3, tree))
    btn_bus.config(cursor='hand2')
    btn_bus.grid(row=0, column=3, padx=10, pady=5, sticky="w")
    btn_bus.bind("<Enter>", lambda event: mostrar_descripcion(event, "Buscar", root, descripcion))
    btn_bus.bind("<Leave>", lambda event: ocultar_descripcion(event, descripcion))

    img5_tk = cargar_imagen(ruta5)
    btn_act = tk.Button(frame_iconos, image=img5_tk, command=lambda:listar(tree, variable_1, variable_2, variable_3))
    btn_act.config(cursor='hand2')
    btn_act.grid(row=0, column=4, padx=10, pady=5, sticky="w")
    btn_act.bind("<Enter>", lambda event: mostrar_descripcion(event, "Actualizar", root, descripcion))
    btn_act.bind("<Leave>", lambda event: ocultar_descripcion(event, descripcion))

    img6_tk = cargar_imagen(ruta6)
    btn_eli = tk.Button(frame_iconos, image=img6_tk, command=lambda:vista_borrar(tree, variable_1, variable_2, variable_3))
    btn_eli.config(cursor='hand2')
    btn_eli.grid(row=0, column=5, padx=10, pady=5, sticky="w")
    btn_eli.bind("<Enter>", lambda event: mostrar_descripcion(event, "Eliminar", root, descripcion))
    btn_eli.bind("<Leave>", lambda event: ocultar_descripcion(event, descripcion))

    img7_tk = cargar_imagen(ruta7)
    btn_con = tk.Button(frame_iconos, image=img7_tk, command=lambda: salir_configuracion(frame_configuracion, frame_qr, frame_calendario, frame_manual))
    btn_con.config(cursor='hand2')
    btn_con.grid(row=0, column=6, padx=10, pady=5, sticky="w")
    btn_con.bind("<Enter>", lambda event: mostrar_descripcion(event, "Configuración", root, descripcion))
    btn_con.bind("<Leave>", lambda event: ocultar_descripcion(event, descripcion))

    img8_tk = cargar_imagen(ruta8)
    btn_rec = tk.Button(frame_iconos, image=img8_tk, command=lambda:vista_recaudacion_diaria(tree, calendario, frame_qr, frame_calendario, variable_1, variable_2, variable_3))
    btn_rec.config(cursor='hand2')
    btn_rec.grid(row=0, column=7, padx=10, pady=5, sticky="w")
    btn_rec.bind("<Enter>", lambda event: mostrar_descripcion(event, "Recaudación", root, descripcion))
    btn_rec.bind("<Leave>", lambda event: ocultar_descripcion(event, descripcion))

    img9_tk = cargar_imagen(ruta9)
    btn_inf = tk.Button(frame_iconos, image=img9_tk, command=lambda: salir_qr(frame_qr, frame_configuracion, frame_calendario, frame_manual))
    btn_inf.config(cursor='hand2')
    btn_inf.grid(row=0, column=8, padx=10, pady=5, sticky="w")
    btn_inf.bind("<Enter>", lambda event: mostrar_descripcion(event, "Información", root, descripcion))
    btn_inf.bind("<Leave>", lambda event: ocultar_descripcion(event, descripcion))

    img10_tk = cargar_imagen(ruta10)
    btn_ocu = tk.Button(frame_iconos, image=img10_tk, command=lambda: salir_iconos(frame_iconos))
    btn_ocu.config(cursor='hand2')
    btn_ocu.grid(row=0, column=9, padx=10, pady=5, sticky="e")
    btn_ocu.bind("<Enter>", lambda event: mostrar_descripcion(event, "Ocultar iconos", root, descripcion))
    btn_ocu.bind("<Leave>", lambda event:ocultar_descripcion(event, descripcion))

    ### LABEL Y ENTRY ###
    label_dominio = tk.Label(frame, text="Dominio:")
    label_dominio.grid(row=0, column=0, padx=5, pady=5)
    entry_dominio = Entry(frame, textvariable = variable_1)
    entry_dominio.grid(row=0, column=1, padx=5, pady=5)

    label_tipo = tk.Label(frame, text="Tipo:")
    label_tipo.grid(row=1, column=0, padx=5, pady=5)
    entry_tipo = ttk.Combobox(frame, textvariable= variable_2, values=["Auto", "Camioneta", "Moto"])
    entry_tipo.grid(row=1, column=1, padx=5, pady=5)

    label_realizar_salida = tk.Label(frame, text="Dominio salida:")
    label_realizar_salida.grid(row=4, column=0, padx=5, pady=5, sticky="e")
    entry_realizar_salida = Entry(frame, textvariable = variable_3)
    entry_realizar_salida.grid(row=4, column=1, padx=5, pady=5, sticky="e")

    ### BOTONES ###
    btn_registrar = tk.Button(frame, text="Registrar Vehículo", command=lambda:vista_registrar(tree, variable_1, variable_2, variable_3))
    btn_registrar.config(cursor='hand2')
    btn_registrar.grid(row=2, column=0, padx=10, pady=5, sticky='ew')

    btn_eliminar = tk.Button(frame, text="Eliminar Vehículo", command=lambda:vista_borrar(tree, variable_1, variable_2, variable_3))
    btn_eliminar.config(cursor='hand2')
    btn_eliminar.grid(row=2, column=2, padx=10, pady=5, sticky='ew')

    btn_modificar = tk.Button(frame, text="Modificar Vehículo", command=lambda:vista_modificar_vehiculo(variable_1, variable_2, tree, variable_3))
    btn_modificar.config(cursor='hand2')
    btn_modificar.grid(row=2, column=3, padx=10, pady=5, sticky='ew')

    btn_buscar = tk.Button(frame, text=" Buscar por dominio ", command=lambda:vista_buscar(variable_1, variable_2, variable_3, tree))
    btn_buscar.config(cursor='hand2')
    btn_buscar.grid(row=2, column=4, padx=10, pady=5, sticky='ew')

    btn_listar = tk.Button(frame, text=" Actualizar ", command=lambda:listar(tree, variable_1, variable_2, variable_3))
    btn_listar.config(cursor='hand2')
    btn_listar.grid(row=2, column=5, padx=10, pady=5, sticky='ew')

    btn_registrar_salida = tk.Button(frame, text="Registrar Salida", command=lambda:vista_salida_tarifa(tree, variable_1, variable_2, variable_3))
    btn_registrar_salida.config(cursor='hand2')
    btn_registrar_salida.grid(row=4, column=2, padx=10, pady=5, sticky='ew')

    btn_recaudacion = tk.Button(frame, text="Mostrar Recaudación", command=lambda:vista_recaudacion_diaria(tree, calendario, frame_qr, frame_calendario, variable_1, variable_2, variable_3))
    btn_recaudacion.config(cursor='hand2')
    btn_recaudacion.grid(row=4, column=10, padx=10, pady=5, sticky="ew")

    #btn_deshacer_salida = tk.Button(frame, text="Deshacer última Salida", command=lambda:deshacer_ultima_salida(tree))
    #btn_deshacer_salida.config(cursor='hand2')
    #btn_deshacer_salida.grid(row=4, column=3, padx=10, pady=5, sticky='nsew')

    ### TABLA ###
    tree = ttk.Treeview(frame, columns=("ID", "Dominio", "Tipo", "Fecha", "Hora", 
    "Salida Registrada", "Fecha Salida", "Hora Salida", "Tiempo estacionado",
    "Tarifa"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Dominio", text="Dominio")
    tree.heading("Tipo", text="Tipo")
    tree.heading("Fecha", text="Fecha")
    tree.heading("Hora", text="Hora")
    tree.heading("Salida Registrada", text="Salida Registrada")
    tree.heading("Fecha Salida", text="Fecha Salida")
    tree.heading("Hora Salida", text="Hora Salida")
    tree.heading("Tiempo estacionado", text="Tiempo estacionado")
    tree.heading("Tarifa", text="Tarifa")

    tree.column("ID", width=50)
    tree.column("Dominio", width=100)
    tree.column("Tipo", width=100)
    tree.column("Fecha", width=100)
    tree.column("Hora", width=100)
    tree.column("Salida Registrada", width=100)
    tree.column("Fecha Salida", width=100)
    tree.column("Hora Salida", width=100)
    tree.column("Tiempo estacionado", width=120)
    tree.column("Tarifa", width=100)

    tree.grid(row=3, column=0, columnspan= 11, sticky="nsew")

    # Crear Scrollbar vertical
    scrollbar_vertical = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    scrollbar_vertical.grid(row=3, column=11, sticky="ns")
    tree.configure(yscrollcommand=scrollbar_vertical.set)

    # Vincular la selección de la tabla con la función seleccionar_vehiculo
    tree.bind("<<TreeviewSelect>>", lambda event: seleccionar_vehiculo(variable_1, variable_2, variable_3, tree))


    # Crear un menú
    menu_bar = Menu(root)
    root.config(menu=menu_bar)
    # Añadir un menú llamado "Menú"
    menu_principal = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Menú", menu=menu_principal)
    # Añadir las opciones "Configuración" y "Salir" a Menú y un separador
    menu_principal.add_command(label="Configuración", command=lambda: salir_configuracion(frame_configuracion, frame_qr, frame_calendario, frame_manual))
    menu_principal.add_separator()  # Añadir un separador
    menu_principal.add_command(label="Salir", command=root.quit)

    # Validación de entrada ################################################################################
    vcmd_numerica = (root.register(validar_entrada_numerica), '%P')
    vcmd_decimal = (root.register(validar_entrada_decimal), '%P')

    # Cargar configuración
    # Crear variables
    capacidad_var = StringVar(value=modelo.capacidad)
    tarifa_auto_var = StringVar(value=modelo.tarifas['auto'])
    tarifa_camioneta_var = StringVar(value=modelo.tarifas['camioneta'])
    tarifa_moto_var = StringVar(value=modelo.tarifas['moto'])

    # Campos de entrada configuracion
    label_capacidad = tk.Label(frame_configuracion, text="Capacidad:")
    label_capacidad.grid(row=0, column=0, padx=10, pady=5)
    entry_capacidad = tk.Entry(frame_configuracion, textvariable=capacidad_var, validate='key', validatecommand=vcmd_numerica)
    entry_capacidad.grid(row=0, column=1, padx=10, pady=5)
    

    label_tarifa_auto = tk.Label(frame_configuracion, text="Tarifa Auto:")
    label_tarifa_auto.grid(row=1, column=0, padx=10, pady=5)
    entry_tarifa_auto = tk.Entry(frame_configuracion, textvariable=tarifa_auto_var, validate='key', validatecommand=vcmd_decimal)
    entry_tarifa_auto.grid(row=1, column=1, padx=10, pady=5)
    

    label_tarifa_camioneta = tk.Label(frame_configuracion, text="Tarifa Camioneta:")
    label_tarifa_camioneta.grid(row=2, column=0, padx=10, pady=5)
    entry_tarifa_camioneta = tk.Entry(frame_configuracion, textvariable=tarifa_camioneta_var, validate='key', validatecommand=vcmd_decimal)
    entry_tarifa_camioneta.grid(row=2, column=1, padx=10, pady=5)
    

    label_tarifa_moto = tk.Label(frame_configuracion, text="Tarifa Moto:")
    label_tarifa_moto.grid(row=3, column=0, padx=10, pady=5)
    entry_tarifa_moto = tk.Entry(frame_configuracion, textvariable=tarifa_moto_var, validate='key', validatecommand=vcmd_decimal)
    entry_tarifa_moto.grid(row=3, column=1, padx=10, pady=5)
    
    # Insertar valores en los campos de entrada
    entry_capacidad.insert(0, modelo.tarifas)
    entry_tarifa_auto.insert(0, modelo.tarifas['auto'])
    entry_tarifa_camioneta.insert(0, modelo.tarifas['camioneta'])
    entry_tarifa_moto.insert(0, modelo.tarifas['moto'])

    btn_guardar = tk.Button(frame_configuracion, text="Guardar", command=lambda: vista_guardar_configuracion(entry_capacidad, entry_tarifa_auto, entry_tarifa_camioneta, entry_tarifa_moto, frame_configuracion))
    btn_guardar.config(cursor='hand2')
    btn_guardar.grid(row=4, column=0, columnspan=2, pady=10)

    btn_ocultar = tk.Button(frame_configuracion, text="Ocultar", command=lambda: salir_configuracion(frame_configuracion, frame_qr, frame_calendario, frame_manual))
    btn_ocultar.config(cursor='hand2')
    btn_ocultar.grid(row=4, column=1, padx=10, pady=5)

    # Inicialmente ocultar el frame de configuración
    frame_configuracion.grid_remove()

    # Añadir un menú llamado "vista"
    vista = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Vista", menu=vista)

    # Añadir las opciones "Elegir color de fondo", "Color aleatorio", "Color original", "Barra de iconos"
    vista.add_command(label="Elegir color de fondo", command=lambda: elegir_color(root))
    vista.add_command(label="Color de fondo aleatorio", command=lambda:cambiar_color(root, frame))
    vista.add_command(label="Color original", command=lambda: estilo_original(root, frame, color_original))
    vista.add_separator()  # Añadir un separador
    vista.add_command(label="Barra de iconos", command=lambda: salir_iconos(frame_iconos))

    # Añadir un menú llamado "Base de datos"
    base = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Base de Datos", menu=base)
    base.add_command(label="Vaciar base de datos", command=lambda:vista_borrar_todos_los_datos(tree, variable_1, variable_2, variable_3, confirmar=False))

    # Añadir un menú llamado "Ayuda"
    ayuda = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Ayuda", menu=ayuda)
    ayuda.add_command(label="Funciones básicas", command=lambda:salir_manual(frame_manual, frame_configuracion, frame_calendario, frame_qr))
    ayuda.add_command(label="Manual de usuario", command=abrir_manual)
    

    tk.Label(frame_manual, text=(
        "INGRESAR VEHÍCULO: Complete los campos de dominio "
        "y tipo y luego presione boton de Registrar Vehículo"
    )).grid(row=0, column=0, sticky='w')
    tk.Label(frame_manual, text=(
        "REGISTRAR SALIDA: Complete el campo de Dominio "
        "salida y luego presione boton de Registrar Salida"
    )).grid(row=1, column=0, sticky='w')
    tk.Label(frame_manual, text=(
        "ELIMINAR VEHÍCULO: Seleccione en la tabla, con el cursor, el vehículo "
        "que desea eliminar y luego presione boton de Eliminar Vehículo"
    )).grid(row=2, column=0, sticky='w')
    tk.Label(frame_manual, text=(
        "MODIFICAR VEHÍCULO: Seleccione en la tabla, con el cursor, el vehículo "
        "que desea modificar, modifique el dominio o tipo y luego presione boton de Modificar"
    )).grid(row=3, column=0, sticky='w')
    tk.Label(frame_manual, text=(
        "BUSCAR POR DOMINIO: Complete el campo de Dominio y luego presione boton "
        "de Buscar por Dominio")).grid(row=4, column=0, sticky='w')
    tk.Label(frame_manual, text=(
        "ACTUALIZAR TABLA: Este botón actualiza la tabla luego de modificar, "
        "eliminar o cuando lo necesite")).grid(row=5, column=0, sticky='w')
    tk.Label(frame_manual, text=(
        "CONFIGURACION: Dentro de Menú se encuntra Configuración que nos permite "
        "configurar la capacidad del estacionamiento y las tarifas de los distintos vehículos"
    )).grid(row=6, column=0, sticky='w')
    tk.Label(frame_manual, text=(
        "RECAUDACIÓN: Muestra la recaudación del día por defecto. Se puede seleccionar "
        "dia en el calendario y luego de presionar botón 'ver recaudación' muestra recaudación "
        "del día elejido")).grid(row=7, column=0, sticky='w')
    btn_cerrar_manual = tk.Button(frame_manual, text="Cerra Manual", command=lambda:salir_manual(frame_manual, frame_configuracion, frame_calendario, frame_qr))
    btn_cerrar_manual.config(cursor='hand2')
    btn_cerrar_manual.grid(row=8, column=0, padx=10, pady=5, sticky='w')
    # Inicialmente ocultar el frame de Manual de usuario
    frame_manual.grid_remove()

    # Añadir un menú llamado "Info"
    ayuda = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Información", menu=ayuda)
    imagen_pil = Image.open(ruta)  
    imagen_redimensionada = imagen_pil.resize((20, 20))
    imagen = ImageTk.PhotoImage(imagen_redimensionada)
    imagenes.append(imagen)  # Almacenar la referencia
    ayuda.add_command(label="  Gestión de estacionamiento",image=imagen, compound=tk.LEFT, command=lambda: salir_qr(frame_qr, frame_configuracion, frame_calendario, frame_manual))

    # Código QR con información
    # Información del estacionamiento
    info_estacionamiento = "UTN - Python 3 - Nivel Inicial\nCurso: 999194877\nAlumno: Carlos Potenza\npotenzacd@gmail.com"
    # Generar el código QR
    qr_img = generar_qr(info_estacionamiento)
    # Convertir la imagen del código QR a un formato compatible con Tkinter
    qr_img_tk = ImageTk.PhotoImage(qr_img)
    
    # Crear un label para mostrar el código QR
    qr_label = tk.Label(frame_qr, image=qr_img_tk)
    qr_label.image = qr_img_tk  # Mantener una referencia a la imagen
    qr_label.grid(row=0, column=0, padx=10, pady=5)
    # Crear boton en frame de qr para ocultarlo
    btn_qr = tk.Button(frame_qr, text="Ocultar", command=lambda: salir_qr(frame_qr, frame_configuracion, frame_calendario, frame_manual))
    btn_qr.config(cursor='hand2')
    btn_qr.grid(row=1, column=0, padx=10, pady=5)
    # Inicialmente ocultar el frame de configuración
    frame_qr.grid_remove()

    
    calendario = Calendar(
        frame_calendario,
        selectmode="day",
        background="black",
        selectbackground="blue",
        normalbackground="white",
        weekendbackground="light blue",
        othermonthbackground="pink",
        othermonthwebackground="pink",
    )

    calendario.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    salir_calend = tk.Button(frame_calendario, text="Ocultar", command=lambda:salir_calendario(tree, frame_calendario, frame_configuracion, frame_qr, frame_manual, variable_1, variable_2, variable_3))
    salir_calend.config(cursor='hand2')
    salir_calend.grid(row=0, column=1, padx=10, pady=5)

    # Actualizar recaudación al seleccionar una nueva fecha
    calendario.bind("<<CalendarSelected>>", lambda event: vista_recaudacion_diaria(tree, calendario, frame_qr, frame_calendario, variable_1, variable_2, variable_3))

    # Inicialmente ocultar el frame de calendario
    frame_calendario.grid_remove()

    # Crear la figura y el eje para el gráfico
    fig = Figure(figsize=(3, 4), dpi=75, facecolor='#EEEEEE')
    ax = fig.add_subplot(111)

    # Crear un lienzo para el gráfico
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().grid(row=3, column=12, padx=10, pady=10, sticky="nsew")

    actualizar_grafico(root, ax, canvas)
    listar(tree, variable_1, variable_2, variable_3)
