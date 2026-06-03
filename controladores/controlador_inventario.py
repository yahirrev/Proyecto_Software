# controlador_inventario.py
from controladores.conexion_bd import obtener_conexion

def obtener_todos_los_productos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM productos WHERE estatus = 'Activo'")
    resultados = cursor.fetchall()
    cursor.close()
    conexion.close()
    return resultados

def guardar_producto(nombre, categoria, descripcion, precio, stock):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO productos (nombre, categoria, descripcion, precio_venta, stock) VALUES (%s, %s, %s, %s, %s)",
        (nombre, categoria, descripcion, precio, stock)
    )
    conexion.commit()
    cursor.close()
    conexion.close()