# controladores/controlador_usuarios.py
from controladores.conexion_bd import obtener_conexion

def obtener_usuarios(busqueda=""):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    parametros = []
    if busqueda:
        query = "SELECT id_usuario, nombre_completo, username, rol, estatus FROM usuarios WHERE (nombre_completo LIKE %s OR username LIKE %s)"
        parametros.extend([f"%{busqueda}%", f"%{busqueda}%"])
    else:
        query = "SELECT id_usuario, nombre_completo, username, rol, estatus FROM usuarios WHERE estatus = 'Activo'"
        
    cursor.execute(query, parametros)
    resultados = cursor.fetchall()
    
    cursor.close()
    conexion.close()
    return resultados

def verificar_usuario_existente(username):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    cursor.execute("SELECT id_usuario FROM usuarios WHERE username = %s", (username,))
    existe = cursor.fetchone() is not None  # Devuelve True si encontró algo, False si está libre
    
    cursor.close()
    conexion.close()
    return existe

def registrar_usuario(nombre, username, password, rol):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    query = """INSERT INTO usuarios (nombre_completo, username, password_hash, rol, estatus) 
               VALUES (%s, %s, %s, %s, 'Activo')"""
    cursor.execute(query, (nombre, username, password, rol))
    conexion.commit()
    
    cursor.close()
    conexion.close()

def actualizar_usuario(id_usuario, nombre, username, password, rol):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    # si escribieron contraseña se actualiza si no nadota
    if password.strip() != "":
        query = """UPDATE usuarios 
                   SET nombre_completo=%s, username=%s, password_hash=%s, rol=%s 
                   WHERE id_usuario=%s"""
        valores = (nombre, username, password, rol, id_usuario)
    else:
        query = """UPDATE usuarios 
                   SET nombre_completo=%s, username=%s, rol=%s 
                   WHERE id_usuario=%s"""
        valores = (nombre, username, rol, id_usuario)
        
    cursor.execute(query, valores)
    conexion.commit()
    
    cursor.close()
    conexion.close()

def desactivar_usuario(id_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    query = "UPDATE usuarios SET estatus = 'Inactivo' WHERE id_usuario = %s"
    cursor.execute(query, (id_usuario,))
    conexion.commit()
    
    cursor.close()
    conexion.close()