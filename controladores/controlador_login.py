# controladores/controlador_login.py
from controladores.conexion_bd import obtener_conexion

def verificar_usuario(username, password):

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    consulta = """
        SELECT id_usuario, nombre_completo, rol 
        FROM usuarios 
        WHERE username = %s AND password_hash = %s AND estatus = 'Activo'
    """
    
    cursor.execute(consulta, (username, password))
    resultado = cursor.fetchone()
    
    cursor.close()
    conexion.close()
    

    return resultado