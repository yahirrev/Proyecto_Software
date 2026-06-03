import sys
import mysql.connector
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget
from PySide6.QtUiTools import QUiLoader
import os

from main_inventario import VentanaInventario
from main_usuarios import VentanaUsuarios
from main_ventas import VentanaVentas


class VentanaMenuPrincipal(QWidget):
    def __init__(self, id_usuario, nombre_usuario, rol_usuario):
        super().__init__()
        
        loader = QUiLoader()
        ruta_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_ui = os.path.join(ruta_actual, "menu_principal.ui")
        self.ui = loader.load(ruta_ui, self)
        self.ui.setWindowTitle("Ferretería Moret - Menú Principal")
        self.ui.setFixedSize(1024, 768) 
        
        self.id_usuario = id_usuario
        self.nombre = nombre_usuario
        self.rol = rol_usuario
        
        self.ui.btn_modulo_usuarios.clicked.connect(self.abrir_usuarios)
        self.ui.btn_modulo_inventario.clicked.connect(self.abrir_inventario)
        self.ui.btn_modulo_ventas.clicked.connect(self.abrir_ventas)
        
        if self.rol == "Cajero":
            self.ui.btn_modulo_inventario.setEnabled(False)
            self.ui.btn_modulo_usuarios.setEnabled(False)
            self.ui.btn_modulo_inventario.setText("Inventario (Restringido)")
            self.ui.btn_modulo_usuarios.setText("Usuarios (Restringido)")

    def abrir_inventario(self):
        self.ventana_inv = VentanaInventario(self)
        self.ventana_inv.ui.show()
        self.ui.hide()  # Cambiado de self.hide()
        
    def abrir_usuarios(self):
        self.ventana_usu = VentanaUsuarios(self)
        self.ui.hide()  # Cambiado de self.hide()
        self.ventana_usu.ui.show()

    def abrir_ventas(self):
        self.ventana_vtas = VentanaVentas(self, id_usuario_real=self.id_usuario, nombre_empleado=self.nombre)
        self.ventana_vtas.ui.show()
        self.ui.hide()  # Cambiado de self.hide()


class VentanaLogin(QMainWindow):
    def __init__(self):
        super().__init__()
        loader = QUiLoader()
        ruta_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_ui = os.path.join(ruta_actual, "login.ui")
        self.ui = loader.load(ruta_ui, self)
        self.ui.setWindowTitle("Ferretería Moret - Control de Acceso")
        self.ui.setFixedSize(1024, 768)
        
        self.ui.btn_ingresar.clicked.connect(self.verificar_credenciales)

    def verificar_credenciales(self):
        usuario = self.ui.txt_usuario.text().strip()
        password = self.ui.txt_password.text().strip()

        if not usuario or not password:
            QMessageBox.warning(self.ui, "Atención", "Por favor ingresa usuario y contraseña.")
            return

        try:
            conexion = mysql.connector.connect(
                host="localhost", user="root", password="", database="ferreteria_sistema"
            )
            cursor = conexion.cursor()

            consulta = """
                SELECT id_usuario, nombre_completo, rol 
                FROM usuarios 
                WHERE username = %s AND password_hash = %s AND estatus = 'Activo'
            """
            cursor.execute(consulta, (usuario, password))
            resultado = cursor.fetchone()

            if resultado:
                id_empleado = resultado[0]
                nombre_empleado = resultado[1]
                rol_empleado = resultado[2]
                
                QMessageBox.information(self.ui, "Acceso Concedido", f"¡Bienvenido {nombre_empleado}!")
                
                self.nueva_ventana = VentanaMenuPrincipal(id_empleado, nombre_empleado, rol_empleado)
                self.nueva_ventana.ui.show()
                self.nueva_ventana.ui.raise_()
                self.nueva_ventana.ui.activateWindow()
                
                self.ui.close()
                
            else:
                QMessageBox.critical(self.ui, "Acceso Denegado", "Credenciales incorrectas o usuario inactivo.")

            cursor.close()
            conexion.close()

        except mysql.connector.Error as e:
            QMessageBox.critical(self.ui, "Error de Servidor", f"No se pudo conectar a la base de datos:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaLogin()
    ventana.ui.show()
    sys.exit(app.exec())
