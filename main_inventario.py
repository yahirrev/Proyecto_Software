import sys
import mysql.connector
from mysql.connector import Error
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox, QTableWidgetItem
from PySide6.QtUiTools import QUiLoader
import controladores.controlador_inventario as controlador_inventario
import os


class VentanaInventario(QWidget):
    def __init__(self, ventana_menu=None):
        super().__init__()
        
        self.ventana_menu = ventana_menu
        
        loader = QUiLoader()
        ruta_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_ui = os.path.join(ruta_actual, "interfaces", "modulo_inventario.ui")
        
        self.ui = loader.load(ruta_ui, self)
        if self.ui:
            self.ui.setWindowTitle("Ferretería Moret - Control de Inventario")
            self.ui.setFixedSize(1024, 768)
        
        self.ui.btn_volver.clicked.connect(self.volver_al_menu)
        
        self.ui.btn_guardar.clicked.connect(self.registrar_producto)
        self.ui.btn_editar.clicked.connect(self.cargar_atributos_totales) 
        self.ui.btn_actualizar.clicked.connect(self.actualizar_producto)
        self.ui.btn_desactivar_prod.clicked.connect(self.desactivar_producto)
        
        self.ui.txt_buscar.textChanged.connect(self.cargar_tabla_productos)
        self.ui.combo_filtro.currentIndexChanged.connect(self.cargar_tabla_productos)
        
        self.id_producto_seleccionado = None 
        self.cargar_tabla_productos()

    def volver_al_menu(self):
        if self.ventana_menu:
            self.ventana_menu.ui.show()  # Cambiado: mostrar self.ventana_menu.ui
        self.ui.close()  # Cambiado de self.close()

    def conectar_bd(self):
        return mysql.connector.connect(
            host="localhost", user="root", password="", database="ferreteria_sistema"
        )

    def cargar_tabla_productos(self):
        try:
            conexion = self.conectar_bd()
            cursor = conexion.cursor()
            
            texto_busqueda = self.ui.txt_buscar.text()
            filtro_combo = self.ui.combo_filtro.currentText()
            
            query = "SELECT id_producto, nombre, categoria, descripcion, precio_venta, stock, estatus FROM productos WHERE 1=1"
            parametros = []
            
            if texto_busqueda:
                query += " AND (nombre LIKE %s OR categoria LIKE %s)"
                parametros.extend([f"%{texto_busqueda}%", f"%{texto_busqueda}%"])
                
            if filtro_combo == "Stock Mínimo":
                query += " AND stock <= 5 AND estatus = 'Activo'"
            elif filtro_combo == "Inactivos":
                query += " AND estatus = 'Inactivo'"
            else:
                query += " AND estatus = 'Activo'" 
                
            cursor.execute(query, parametros)
            resultados = cursor.fetchall()
            
            self.ui.tabla_productos.setRowCount(0)
            for fila_idx, fila_datos in enumerate(resultados):
                self.ui.tabla_productos.insertRow(fila_idx)
                for col_idx, valor in enumerate(fila_datos):
                    item = QTableWidgetItem(str(valor))
                    self.ui.tabla_productos.setItem(fila_idx, col_idx, item)
                    
            cursor.close()
            conexion.close()
        except Error as e:
            print(f"Error al cargar tabla: {e}")

    def cargar_atributos_totales(self):
        fila_seleccionada = self.ui.tabla_productos.currentRow()
        
        if fila_seleccionada == -1:
            QMessageBox.warning(self.ui, "Atención", "Por favor, selecciona una fila de la tabla antes de cargar los datos.")
            return
            
        self.id_producto_seleccionado = self.ui.tabla_productos.item(fila_seleccionada, 0).text()
        nombre = self.ui.tabla_productos.item(fila_seleccionada, 1).text()
        categoria = self.ui.tabla_productos.item(fila_seleccionada, 2).text()
        descripcion = self.ui.tabla_productos.item(fila_seleccionada, 3).text()
        precio = self.ui.tabla_productos.item(fila_seleccionada, 4).text()
        stock = self.ui.tabla_productos.item(fila_seleccionada, 5).text()
        
        self.ui.txt_nombre.setText(nombre)
        self.ui.txt_categoria.setText(categoria)
        self.ui.txt_descripcion.setText(descripcion)
        self.ui.txt_precio.setText(precio)
        self.ui.spin_stock.setValue(int(stock))
        
        QMessageBox.information(self.ui, "Atributos Cargados", f"Producto ID {self.id_producto_seleccionado} listo para ser modificado.")

    def registrar_producto(self):
        nombre = self.ui.txt_nombre.text()
        categoria = self.ui.txt_categoria.text()
        descripcion = self.ui.txt_descripcion.text()
        precio = self.ui.txt_precio.text()
        stock = self.ui.spin_stock.value()
        
        if not nombre or not categoria or not precio:
            QMessageBox.warning(self.ui, "Campos Vacíos", "Nombre, Categoría y Precio son campos obligatorios.")
            return
            
        try:
            precio_num = float(precio)
            if precio_num <= 0:
                QMessageBox.warning(self.ui, "Validación", "El precio de venta debe ser mayor a 0.")
                return
                

            controlador_inventario.guardar_producto(nombre, categoria, descripcion, precio_num, stock)
            
            QMessageBox.information(self.ui, "Éxito", "Nuevo artículo almacenado de manera permanente.")
            self.limpiar_formulario()
            self.cargar_tabla_productos()
            
        except ValueError:
            QMessageBox.warning(self.ui, "Error de Formato", "El precio debe ser un valor numérico.")
        except Error as e:
            QMessageBox.critical(self.ui, "Error", f"Error de Base de Datos: {e}")

    def actualizar_producto(self):
        if not self.id_producto_seleccionado:
            QMessageBox.warning(self.ui, "Atención", "No hay ningún producto cargado. Selecciona uno y presiona 'Cargar para Modificar'.")
            return
            
        nombre = self.ui.txt_nombre.text()
        categoria = self.ui.txt_categoria.text()
        descripcion = self.ui.txt_descripcion.text()
        precio = self.ui.txt_precio.text()
        stock = self.ui.spin_stock.value()
        
        try:
            precio_num = float(precio)
            if precio_num <= 0:
                QMessageBox.warning(self.ui, "Validación", "El precio debe ser mayor a 0.")
                return
                
            conexion = self.conectar_bd()
            cursor = conexion.cursor()
            
            query = "UPDATE productos SET nombre=%s, categoria=%s, descripcion=%s, precio_venta=%s, stock=%s WHERE id_producto=%s"
            cursor.execute(query, (nombre, categoria, descripcion, precio_num, stock, self.id_producto_seleccionado))
            conexion.commit()
            
            QMessageBox.information(self.ui, "Éxito", "Atributos del producto actualizados correctamente.")
            self.limpiar_formulario()
            self.cargar_tabla_productos()
            
            cursor.close()
            conexion.close()
        except Error as e:
            QMessageBox.critical(self.ui, "Error", f"No se pudo actualizar: {e}")

    def desactivar_producto(self):
        if not self.id_producto_seleccionado:
            QMessageBox.warning(self.ui, "Atención", "Carga primero el producto que deseas inactivar.")
            return
            
        respuesta = QMessageBox.question(
            self.ui, "Confirmar Inactivación",
            "¿Deseas marcar este producto como Inactivo?\nSe preservará en el historial pero se ocultará de las ventas.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if respuesta == QMessageBox.Yes:
            try:
                conexion = self.conectar_bd()
                cursor = conexion.cursor()
                
                query = "UPDATE productos SET estatus = 'Inactivo' WHERE id_producto = %s"
                cursor.execute(query, (self.id_producto_seleccionado,))
                conexion.commit()
                
                QMessageBox.information(self.ui, "Estatus Modificado", "Producto marcado como Inactivo con éxito.")
                self.limpiar_formulario()
                self.cargar_tabla_productos()
                
                cursor.close()
                conexion.close()
            except Error as e:
                QMessageBox.critical(self.ui, "Error", f"No se pudo modificar el estatus: {e}")

    def limpiar_formulario(self):
        self.id_producto_seleccionado = None
        self.ui.txt_nombre.clear()
        self.ui.txt_categoria.clear()
        self.ui.txt_descripcion.clear()
        self.ui.txt_precio.clear()
        self.ui.spin_stock.setValue(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaInventario()
    ventana.ui.show()
    sys.exit(app.exec())
