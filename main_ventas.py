import sys
from controladores import controlador_ventas
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox, QTableWidgetItem
from PySide6.QtUiTools import QUiLoader
import os
from datetime import datetime


class VentanaVentas(QWidget):
    def __init__(self, ventana_menu=None, id_usuario_real=1, nombre_empleado="Yahir"):
        super().__init__()
        
        self.ventana_menu = ventana_menu
        self.id_usuario_real = id_usuario_real
        self.nombre_empleado = nombre_empleado
        
        loader = QUiLoader()
        ruta_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_ui = os.path.join(ruta_actual, "interfaces", "modulo_ventas.ui")
        
        self.ui = loader.load(ruta_ui, self)
        if self.ui:
            self.ui.setWindowTitle("Ferretería Moret - Terminal de Ventas POS")
            self.ui.setFixedSize(1024, 768)
        
        self.ui.btn_volver.clicked.connect(self.volver_al_menu)
        self.ui.btn_volver_2.clicked.connect(self.volver_al_menu)
        self.ui.btn_volver_3.clicked.connect(self.volver_al_menu)
        self.ui.btn_volver_4.clicked.connect(self.volver_al_menu)

        self.ui.btn_agregar_lista.clicked.connect(self.agregar_producto_tabla)
        self.ui.btn_quitar_lista.clicked.connect(self.quitar_producto_tabla)
        self.ui.btn_pagar_venta.clicked.connect(self.procesar_cobro)
        self.ui.txt_efectivo_recibido.textChanged.connect(self.calcular_cambio_en_caliente)
        
        self.ui.btn_buscar_historial.clicked.connect(self.cargar_historial_ventas)
        self.ui.combo_filtro_fecha.currentIndexChanged.connect(self.cargar_historial_ventas)
        self.ui.btn_ver_ticket.clicked.connect(self.ver_ticket_historial)
        
        self.ui.btn_cargar_venta_devolucion.clicked.connect(self.cargar_folio_devolucion)
        self.ui.btn_confirmar_devolucion.clicked.connect(self.aplicar_devolucion)
        
        self.ui.btn_cerrar_caja.clicked.connect(self.imprimir_corte_caja)

        self.total_final = 0.0
        self.limpiar_pantalla_venta()
        self.cargar_historial_ventas()
        self.actualizar_modulo_caja()

    def volver_al_menu(self):
        if self.ventana_menu:
            self.ventana_menu.ui.show()  # Cambiado: mostrar self.ventana_menu.ui
        self.ui.close()  # Cambiado de self.close()


    def limpiar_pantalla_venta(self):
        self.ui.tabla_ventas.setRowCount(0)
        self.ui.txt_subtotal.setText("$ 0.00")
        self.ui.txt_iva.setText("$ 0.00")
        self.ui.txt_total_venta.setText("$ 0.00")
        self.ui.txt_efectivo_recibido.clear()
        self.ui.txt_cambio_cliente.setText("$ 0.00")
        self.total_final = 0.0

    def agregar_producto_tabla(self):
        id_prod = self.ui.txt_codigo_producto.text().strip()
        cantidad_texto = self.ui.txt_cantidad_producto.text()
        
        if not id_prod or not cantidad_texto: return
        cantidad = int(cantidad_texto)

        try:
            producto = controlador_ventas.obtener_producto_por_id(id_prod)
            
            if producto:
                descripcion, precio, stock = producto
                if stock < cantidad:
                    QMessageBox.warning(self.ui, "Stock", f"Solo quedan {stock} unidades en almacén.")
                    return
                
                subtotal_item = precio * cantidad
                fila_idx = self.ui.tabla_ventas.rowCount()
                self.ui.tabla_ventas.insertRow(fila_idx)
                
                self.ui.tabla_ventas.setItem(fila_idx, 0, QTableWidgetItem(id_prod))
                self.ui.tabla_ventas.setItem(fila_idx, 1, QTableWidgetItem(descripcion))
                self.ui.tabla_ventas.setItem(fila_idx, 2, QTableWidgetItem(f"{precio:.2f}"))
                self.ui.tabla_ventas.setItem(fila_idx, 3, QTableWidgetItem(str(cantidad)))
                self.ui.tabla_ventas.setItem(fila_idx, 4, QTableWidgetItem(f"{subtotal_item:.2f}"))
                
                self.recalcular_totales_desglose()
                self.ui.txt_codigo_producto.clear()
            else:
                QMessageBox.critical(self.ui, "Error", f"Producto con ID '{id_prod}' no encontrado o está inactivo.")
        except Exception as e: 
            print(f"Error al agregar producto: {e}")



    def quitar_producto_tabla(self):
        fila = self.ui.tabla_ventas.currentRow()
        if fila != -1:
            self.ui.tabla_ventas.removeRow(fila)
            self.recalcular_totales_desglose()



    def recalcular_totales_desglose(self):
        suma_carrito = 0.0
        for i in range(self.ui.tabla_ventas.rowCount()):
            suma_carrito += float(self.ui.tabla_ventas.item(i, 4).text())
        
        subtotal = suma_carrito / 1.16
        iva = suma_carrito - subtotal
        self.total_final = suma_carrito
        
        self.ui.txt_subtotal.setText(f"$ {subtotal:.2f}")
        self.ui.txt_iva.setText(f"$ {iva:.2f}")
        self.ui.txt_total_venta.setText(f"$ {self.total_final:.2f}")
        self.calcular_cambio_en_caliente()




    def calcular_cambio_en_caliente(self):
        efectivo_texto = self.ui.txt_efectivo_recibido.text().strip()
        if not efectivo_texto:
            self.ui.txt_cambio_cliente.setText("$ 0.00")
            return
        try:
            efectivo = float(efectivo_texto)
            cambio = efectivo - self.total_final
            if cambio >= 0:
                self.ui.txt_cambio_cliente.setText(f"$ {cambio:.2f}")
            else:
                self.ui.txt_cambio_cliente.setText("Falta dinero")
        except ValueError:
            self.ui.txt_cambio_cliente.setText("Inválido")




    def procesar_cobro(self):
        filas = self.ui.tabla_ventas.rowCount()
        if filas == 0: return
        
        efectivo_texto = self.ui.txt_efectivo_recibido.text().strip()
        if not efectivo_texto:
            QMessageBox.warning(self.ui, "Cobro", "Falta ingresar el efectivo recibido.")
            return
            
        efectivo = float(efectivo_texto)
        if efectivo < self.total_final:
            QMessageBox.warning(self.ui, "Cobro", "El efectivo es menor al total.")
            return

        cambio_final = efectivo - self.total_final

        if QMessageBox.question(self.ui, "Confirmar Venta", f"¿Cobrar $ {self.total_final:.2f}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                subtotal_calc = self.total_final / 1.16
                impuesto_calc = self.total_final - subtotal_calc
                
                carrito_bd = []
                datos_productos_ticket = []
                
                for i in range(filas):
                    id_prod = self.ui.tabla_ventas.item(i, 0).text()
                    descripcion = self.ui.tabla_ventas.item(i, 1).text()
                    precio = float(self.ui.tabla_ventas.item(i, 2).text())
                    cantidad = int(self.ui.tabla_ventas.item(i, 3).text())
                    subtotal_item = float(self.ui.tabla_ventas.item(i, 4).text())
                    
                    carrito_bd.append((id_prod, cantidad, precio, subtotal_item))
                    datos_productos_ticket.append((descripcion, cantidad, precio, subtotal_item))
                
                # se envia al controlador todo
                id_nueva_venta = controlador_ventas.registrar_venta(
                    subtotal_calc, impuesto_calc, self.total_final, self.id_usuario_real, carrito_bd
                )
                
                self.generar_archivo_ticket(id_nueva_venta, datos_productos_ticket, efectivo, cambio_final)
                QMessageBox.information(self.ui, "Venta Exitosa", f"Venta registrada con Folio #{id_nueva_venta}. Cambio: $ {cambio_final:.2f}")
                
                self.limpiar_pantalla_venta()
                self.cargar_historial_ventas()
                self.actualizar_modulo_caja()
                
            except Exception as e: 
                QMessageBox.critical(self.ui, "Error", f"Error en el cobro: {e}")




    def generar_archivo_ticket(self, folio, productos, recibido, cambio):
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nombre_archivo = f"ticket_{folio}.txt"
        subtotal = self.total_final / 1.16
        iva = self.total_final - subtotal
        
        with open(nombre_archivo, "w", encoding="utf-8") as f:
            f.write("=========================================\n")
            f.write("           FERRETERÍA MORET              \n")
            f.write("      Xalapa - Coatepec, Veracruz        \n")
            f.write("=========================================\n")
            f.write(f"Folio Venta:  {folio}\n")
            f.write(f"Fecha Emisión: {fecha_actual}\n")
            f.write(f"Atendió:      {self.nombre_empleado}\n") 
            f.write("-----------------------------------------\n")
            f.write("Cant  Descripción       P.Unit   Subtot  \n")
            f.write("-----------------------------------------\n")
            
            for desc, cant, punit, subt in productos:
                desc_corta = desc[:15].ljust(15)
                f.write(f"{str(cant).ljust(5)} {desc_corta} ${str(f'{punit:.2f}').ljust(7)} ${subt:.2f}\n")
                
            f.write("-----------------------------------------\n")
            f.write(f"Subtotal:                      $ {subtotal:.2f}\n")
            f.write(f"IVA (16%):                     $ {iva:.2f}\n")
            f.write(f"TOTAL A PAGAR:                 $ {self.total_final:.2f}\n")
            f.write(f"Efectivo Recibido:             $ {recibido:.2f}\n")
            f.write(f"Cambio a Devolver:             $ {cambio:.2f}\n")
            f.write("=========================================\n")
            
        os.system(f"notepad.exe {nombre_archivo}")





    def cargar_historial_ventas(self):
        folio_buscar = self.ui.txt_buscar_folio.text().strip()
        filtro_fecha = self.ui.combo_filtro_fecha.currentText()
        orden = "DESC" if "recientes" in filtro_fecha.lower() else "ASC"
        
        try:
            resultados = controlador_ventas.obtener_historial_ventas(folio_buscar, orden)
            self.ui.tabla_historial.setRowCount(0)
            
            for fila_idx, datos in enumerate(resultados):
                self.ui.tabla_historial.insertRow(fila_idx)
                for col_idx, valor in enumerate(datos):
                    self.ui.tabla_historial.setItem(fila_idx, col_idx, QTableWidgetItem(str(valor)))
        except Exception as e: 
            print(f"Error cargando historial: {e}")




    def ver_ticket_historial(self):
        fila = self.ui.tabla_historial.currentRow()
        if fila == -1: 
            QMessageBox.warning(self.ui, "Aviso", "Selecciona una venta del historial para ver el ticket.")
            return
        folio = self.ui.tabla_historial.item(fila, 0).text()
        nombre_archivo = f"ticket_{folio}.txt"
        
        if os.path.exists(nombre_archivo):
            os.system(f"notepad.exe {nombre_archivo}")
        else:
            QMessageBox.warning(self.ui, "Archivo no encontrado", f"El archivo del ticket #{folio} no se encuentra localmente.")




    def cargar_folio_devolucion(self):
        folio = self.ui.txt_folio_devolucion.text().strip()
        if not folio: return
        
        try:
            resultado = controlador_ventas.obtener_venta_por_folio(folio)
            self.ui.tabla_folios_devolucion.setRowCount(0)
            
            if resultado:
                self.ui.tabla_folios_devolucion.insertRow(0)
                for col_idx, valor in enumerate(resultado):
                    self.ui.tabla_folios_devolucion.setItem(0, col_idx, QTableWidgetItem(str(valor)))
                self.ui.tabla_folios_devolucion.selectRow(0)
            else:
                QMessageBox.warning(self.ui, "No encontrado", "El folio de venta ingresado no existe.")
        except Exception as e: 
            print(f"Error cargando folio: {e}")




    def aplicar_devolucion(self):
        fila = self.ui.tabla_folios_devolucion.currentRow()
        if fila == -1: 
            QMessageBox.warning(self.ui, "Aviso", "Busca y selecciona una venta en la tabla para anularla.")
            return
            
        id_venta = self.ui.tabla_folios_devolucion.item(fila, 0).text()
        estatus = self.ui.tabla_folios_devolucion.item(fila, 2).text()
        motivo = self.ui.txt_motivo_anulacion.text().strip()
        
        if estatus == "Cancelada": # Actualizado para coincidir con la BD
            QMessageBox.warning(self.ui, "Aviso", "Esta venta ya fue anulada previamente.")
            return
            
        if not motivo:
            QMessageBox.warning(self.ui, "Falta Motivo", "Es obligatorio escribir el motivo de la anulación.")
            return
            
        if QMessageBox.question(self.ui, "Confirmar Anulación", f"¿Seguro que deseas anular la venta #{id_venta} y regresar el stock?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                controlador_ventas.anular_venta(id_venta, motivo)
                
                QMessageBox.information(self.ui, "Anulación Exitosa", f"Venta #{id_venta} marcada como 'Cancelada' y stock restaurado automáticamente.")
                
                self.ui.txt_motivo_anulacion.clear()
                self.cargar_folio_devolucion() 
                self.cargar_historial_ventas()
                self.actualizar_modulo_caja()
                
            except Exception as e: 
                print(f"Error anulando venta: {e}")



                

    def actualizar_modulo_caja(self):
        try:
            ingresos = controlador_ventas.obtener_ingresos_activos()
            caja_inicial = 500.00
            
            self.ui.txt_caja_inicial.setText(f"$ {caja_inicial:.2f}")
            self.ui.txt_ingresos_ventas.setText(f"$ {ingresos:.2f}")
            self.ui.txt_caja_total.setText(f"$ {(caja_inicial + ingresos):.2f}")
        except Exception as e: 
            print(f"Error actualizando caja: {e}")

            

    def imprimir_corte_caja(self):
        caja_total = self.ui.txt_caja_total.text()
        QMessageBox.information(self.ui, "Corte de Caja", f"Turno cerrado con éxito.\nTotal de efectivo esperado en caja: {caja_total}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaVentas()
    ventana.ui.show()
    sys.exit(app.exec())
