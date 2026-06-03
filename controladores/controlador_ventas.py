# controladores/controlador_ventas.py
from controladores.conexion_bd import obtener_conexion

def obtener_producto_por_id(id_prod):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT descripcion, precio_venta, stock FROM productos WHERE id_producto = %s AND estatus = 'Activo'", (id_prod,))
    producto = cursor.fetchone()
    cursor.close()
    conexion.close()
    return producto

def registrar_venta(subtotal, impuesto, total, id_usuario, carrito):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    # crea el registro principal de la venta
    cursor.execute(
        "INSERT INTO ventas (subtotal, impuesto, total, id_usuario, estatus) VALUES (%s, %s, %s, %s, 'Completada')",
        (subtotal, impuesto, total, id_usuario)
    )
    id_nueva_venta = cursor.lastrowid
    
    # Se guarda el detalle de los productos (El trigger tr_descontar_stock_venta restará el stock)
    for id_prod, cantidad, precio, subtotal_item in carrito:
        cursor.execute(
            "INSERT INTO detalle_ventas (id_venta, id_producto, cantidad, precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s)",
            (id_nueva_venta, id_prod, cantidad, precio, subtotal_item)
        )
        
    conexion.commit()
    cursor.close()
    conexion.close()
    return id_nueva_venta

def obtener_historial_ventas(folio_buscar, orden):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    if folio_buscar:
        cursor.execute(f"SELECT id_venta, fecha, total, id_usuario, estatus FROM ventas WHERE id_venta = %s ORDER BY id_venta {orden}", (folio_buscar,))
    else:
        cursor.execute(f"SELECT id_venta, fecha, total, id_usuario, estatus FROM ventas ORDER BY id_venta {orden}")
    resultados = cursor.fetchall()
    cursor.close()
    conexion.close()
    return resultados

def obtener_venta_por_folio(folio):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_venta, total, estatus FROM ventas WHERE id_venta = %s", (folio,))
    resultado = cursor.fetchone()
    cursor.close()
    conexion.close()
    return resultado

def anular_venta(id_venta, motivo):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    # Se usa cancelada 'Cancelada' por que asi esta en la base de datos (ENUM 'Completada', 'Cancelada')
    cursor.execute("UPDATE ventas SET estatus = 'Cancelada', motivo_anulacion = %s WHERE id_venta = %s", (motivo, id_venta))
    # El trigger tr_revertir_stock_cancelacion devolverá los productos automáticamente.
    conexion.commit()
    cursor.close()
    conexion.close()

def obtener_ingresos_activos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT SUM(total) FROM ventas WHERE estatus = 'Completada'")
    res = cursor.fetchone()
    cursor.close()
    conexion.close()
    return float(res[0]) if res[0] is not None else 0.0