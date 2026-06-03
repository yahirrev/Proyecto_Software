# conexion_bd.py
import mysql.connector

def obtener_conexion():
    return mysql.connector.connect(
        host="localhost", 
        user="root", 
        password="", 
        database="ferreteria_sistema"
    )