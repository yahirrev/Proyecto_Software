import sys
import mysql.connector
from mysql.connector import Error
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox, QTableWidgetItem
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMainWindow
import os
from controladores import controlador_usuarios


class VentanaUsuarios(QMainWindow): 
    def __init__(self, ventana_menu=None):
        super().__init__()
        
        self.ventana_menu = ventana_menu
        
        loader = QUiLoader()
        ruta_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_ui = os.path.join(ruta_actual, "interfaces", "modulo_usuarios.ui")

        self.ui = loader.load(ruta_ui, self)
        self.ui.setWindowTitle("Ferretería Moret - Control de Usuarios y Personal")

        if self.ui:
            self.ui.setMinimumSize(800, 600)

        self.ui.btn_volver.clicked.connect(self.volver_al_menu)
        
        self.ui.btn_guardar_usuario.clicked.connect(self.registrar_usuario)
        self.ui.btn_cargar_usuario.clicked.connect(self.cargar_atributos_usuario)
        self.ui.btn_actualizar_usuario.clicked.connect(self.actualizar_usuario)
        self.ui.btn_desactivar_usuario.clicked.connect(self.desactivar_usuario)
        
        self.ui.txt_buscar_usuario.textChanged.connect(self.cargar_tabla_usuarios)
        
        self.id_usuario_seleccionado = None
        self.cargar_tabla_usuarios()

    def volver_al_menu(self):
        if self.ventana_menu:
            self.ventana_menu.ui.show()  # Cambiado: mostrar self.ventana_menu.ui
        self.ui.close()  # Cambiado de self.close()


    def cargar_tabla_usuarios(self):
        try:
            busqueda = self.ui.txt_buscar_usuario.text()
            # llama al consolador 
            resultados = controlador_usuarios.obtener_usuarios(busqueda)
            
            self.ui.tabla_usuarios.setRowCount(0)
            for fila_idx, fila_datos in enumerate(resultados):
                self.ui.tabla_usuarios.insertRow(fila_idx)
                for col_idx, valor in enumerate(fila_datos):
                    item = QTableWidgetItem(str(valor))
                    self.ui.tabla_usuarios.setItem(fila_idx, col_idx, item)
                    
        except Exception as e:
            print(f"Error al cargar tabla de usuarios: {e}")

    def cargar_atributos_usuario(self):
        fila_seleccionada = self.ui.tabla_usuarios.currentRow()
        
        if fila_seleccionada == -1:
            QMessageBox.warning(self.ui, "Atención", "Selecciona un empleado de la lista y presiona 'Cargar para Modificar'.")
            return
            
        self.id_usuario_seleccionado = self.ui.tabla_usuarios.item(fila_seleccionada, 0).text()
        nombre = self.ui.tabla_usuarios.item(fila_seleccionada, 1).text()
        username = self.ui.tabla_usuarios.item(fila_seleccionada, 2).text()
        rol = self.ui.tabla_usuarios.item(fila_seleccionada, 3).text()
        
        self.ui.txt_nombre_completo.setText(nombre)
        self.ui.txt_username.setText(username)
        self.ui.txt_password_user.setText("") 
        
        idx = self.ui.combo_rol.findText(rol)
        if idx != -1:
            self.ui.combo_rol.setCurrentIndex(idx)
            
        QMessageBox.information(self.ui, "Personal Cargado", f"Datos del usuario '{username}' cargados en el panel de edición.")

    def registrar_usuario(self):
        nombre = self.ui.txt_nombre_completo.text()
        username = self.ui.txt_username.text()
        password = self.ui.txt_password_user.text()
        rol = self.ui.combo_rol.currentText()
        
        if not nombre or not username or not password:
            QMessageBox.warning(self.ui, "Campos Vacíos", "Todos los campos de registro son obligatorios.")
            return
            
        try:
            # Valida si existe
            if controlador_usuarios.verificar_usuario_existente(username):
                QMessageBox.warning(self.ui, "Usuario Duplicado", f"El alias de usuario '{username}' ya existe. Elige otro.")
                return
                
            # Se registra
            controlador_usuarios.registrar_usuario(nombre, username, password, rol)
            
            QMessageBox.information(self.ui, "Éxito", "Nuevo empleado incorporado al sistema correctamente.")
            self.limpiar_formulario()
            self.cargar_tabla_usuarios()
            
        except Exception as e:
            QMessageBox.critical(self.ui, "Error", f"No se pudo guardar el usuario: {e}")

    def actualizar_usuario(self):
        if not self.id_usuario_seleccionado:
            QMessageBox.warning(self.ui, "Atención", "Primero selecciona un usuario de la tabla y presiona 'Cargar para Modificar'.")
            return
            
        nombre = self.ui.txt_nombre_completo.text()
        username = self.ui.txt_username.text()
        password = self.ui.txt_password_user.text()
        rol = self.ui.combo_rol.currentText()
        
        if not nombre or not username:
            QMessageBox.warning(self.ui, "Campos Vacíos", "El Nombre y el Usuario no pueden quedar vacíos.")
            return
            
        try:
            # se usa el consolador para esta madre
            controlador_usuarios.actualizar_usuario(self.id_usuario_seleccionado, nombre, username, password, rol)
            
            QMessageBox.information(self.ui, "Éxito", "Información del empleado actualizada correctamente.")
            self.limpiar_formulario()
            self.cargar_tabla_usuarios()
            
        except Exception as e:
            QMessageBox.critical(self.ui, "Error", f"No se pudo actualizar el registro: {e}")


    def desactivar_usuario(self):
        if not self.id_usuario_seleccionado:
            QMessageBox.warning(self.ui, "Atención", "Carga primero el perfil de personal que deseas dar de baja.")
            return
            
        respuesta = QMessageBox.question(
            self.ui, "Confirmar Baja",
            "¿Estás seguro de inhabilitar esta cuenta?\nEl empleado perderá el acceso inmediato al sistema.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if respuesta == QMessageBox.Yes:
            try:
                # Se da debaja el usuario con el consolador
                controlador_usuarios.desactivar_usuario(self.id_usuario_seleccionado)
                
                QMessageBox.information(self.ui, "Estatus Modificado", "La cuenta de usuario ha sido dada de baja.")
                self.limpiar_formulario()
                self.cargar_tabla_usuarios()
                
            except Exception as e:
                QMessageBox.critical(self.ui, "Error", f"No se pudo cambiar el estatus: {e}")

    def limpiar_formulario(self):
        self.id_usuario_seleccionado = None
        self.ui.txt_nombre_completo.clear()
        self.ui.txt_username.clear()
        self.ui.txt_password_user.clear()
        self.ui.combo_rol.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaUsuarios()
    ventana.ui.show()
    sys.exit(app.exec())
