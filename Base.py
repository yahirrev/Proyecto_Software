import mysql.connector
from mysql.connector import Error

def configurar_base_datos():
    try:
        # Conexión inicial al servidor de XAMPP
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conexion.cursor()

        # Creamos y nos posicionamos en la nueva base de datos limpia
        cursor.execute("CREATE DATABASE IF NOT EXISTS ferreteria_sistema;")
        cursor.execute("USE ferreteria_sistema;")
        
        print("1. Creando tablas relacionales basadas en los ID de producto...")

        # --- MÓDULO DE USUARIOS (REQ-USU) ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            nombre_completo VARCHAR(100) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            rol ENUM('Administrador', 'Cajero') NOT NULL,
            estatus ENUM('Activo', 'Inactivo') DEFAULT 'Activo'
        );
        """)

        # --- MÓDULO DE INVENTARIO (REQ-INV) - Código de barras removido ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id_producto INT AUTO_INCREMENT PRIMARY KEY, -- Este será el identificador único para todo el sistema
            nombre VARCHAR(100) NOT NULL,
            categoria VARCHAR(50) NOT NULL,
            descripcion TEXT,
            precio_venta DECIMAL(10, 2) NOT NULL CHECK (precio_venta > 0), -- Validación de precio > 0 (REQ-INV-01)
            stock INT NOT NULL DEFAULT 0,
            estatus ENUM('Activo', 'Inactivo') DEFAULT 'Activo' -- Para la baja lógica (REQ-INV-04)
        );
        """)

        # --- MÓDULO DE VENTAS (REQ-VEN - Maestro) ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id_venta INT AUTO_INCREMENT PRIMARY KEY,
            folio VARCHAR(20) UNIQUE NOT NULL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            subtotal DECIMAL(10, 2) NOT NULL,
            impuesto DECIMAL(10, 2) NOT NULL,
            total DECIMAL(10, 2) NOT NULL,
            id_usuario INT NOT NULL, -- Quién realizó la venta (REQ-VEN-02)
            estatus ENUM('Completada', 'Cancelada') DEFAULT 'Completada', -- Para anulaciones (REQ-VEN-03)
            motivo_anulacion TEXT, -- Campo obligatorio en cancelaciones
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
        );
        """)

        # --- MÓDULO DE VENTAS (REQ-VEN - Detalle / Tabla intermedia) ---
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id_detalle INT AUTO_INCREMENT PRIMARY KEY,
            id_venta INT NOT NULL,
            id_producto INT NOT NULL, -- Relación directa con el ID del producto
            cantidad INT NOT NULL CHECK (cantidad > 0),
            precio_unitario DECIMAL(10, 2) NOT NULL,
            subtotal DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (id_venta) REFERENCES ventas(id_venta) ON DELETE CASCADE,
            FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
        );
        """)

        print("2. Instalando Triggers automatizados en MySQL...")

        # TRIGGER 1: Restar stock automáticamente al insertar un producto en el carrito (REQ-VEN-01)
        cursor.execute("DROP TRIGGER IF EXISTS tr_descontar_stock_venta;")
        cursor.execute("""
        CREATE TRIGGER tr_descontar_stock_venta
        AFTER INSERT ON detalle_ventas
        FOR EACH ROW
        BEGIN
            UPDATE productos 
            SET stock = stock - NEW.cantidad
            WHERE id_producto = NEW.id_producto;
        END;
        """)

        # TRIGGER 2: Devolver stock automáticamente si se cancela la venta mediante el Folio (REQ-VEN-03)
        cursor.execute("DROP TRIGGER IF EXISTS tr_revertir_stock_cancelacion;")
        cursor.execute("""
        CREATE TRIGGER tr_revertir_stock_cancelacion
        AFTER UPDATE ON ventas
        FOR EACH ROW
        BEGIN
            IF OLD.estatus = 'Completada' AND NEW.estatus = 'Cancelada' THEN
                UPDATE productos p
                INNER JOIN detalle_ventas dv ON p.id_producto = dv.id_producto
                SET p.stock = p.stock + dv.cantidad
                WHERE dv.id_venta = NEW.id_venta;
            END IF;
        END;
        """)

        # TRIGGER 3: Validación estricta que bloquea el pago si no hay suficiente inventario físico (REQ-VEN-04)
        cursor.execute("DROP TRIGGER IF EXISTS tr_validar_stock_existente;")
        cursor.execute("""
        CREATE TRIGGER tr_validar_stock_existente
        BEFORE INSERT ON detalle_ventas
        FOR EACH ROW
        BEGIN
            DECLARE v_stock_actual INT;
            
            SELECT stock INTO v_stock_actual FROM productos WHERE id_producto = NEW.id_producto;
            
            IF NEW.cantidad > v_stock_actual THEN
                SIGNAL SQLSTATE '45000' 
                SET MESSAGE_TEXT = 'Error: La cantidad solicitada excede el inventario físico disponible.';
            END IF;
        END;
        """)

        print("3. Insertando registros iniciales de prueba...")

        # Usuarios de prueba para el Login (REQ-USU-01 y REQ-NF-01)
        cursor.execute("""
        INSERT IGNORE INTO usuarios (id_usuario, username, nombre_completo, password_hash, rol, estatus) VALUES 
        (1, 'ayahir', 'Yahir Administrador', '12345', 'Administrador', 'Activo'),
        (2, 'crobert', 'Robert Cajero', '54321', 'Cajero', 'Activo'),
        (3, 'empleado_baja', 'Juan Pérez', 'juan123', 'Cajero', 'Inactivo');
        """)

        # Productos de prueba identificados únicamente por su ID numérico (REQ-INV-01)
        cursor.execute("""
        INSERT IGNORE INTO productos (id_producto, nombre, categoria, descripcion, precio_venta, stock, estatus) VALUES 
        (1, 'Martillo de Uña 16oz', 'Herramientas Manuales', 'Martillo con mango de fibra de vidrio', 185.00, 20, 'Activo'),
        (2, 'Taladro Rotomartillo 1/2', 'Herramientas Eléctricas', 'Taladro de velocidad variable 550W', 1250.00, 5, 'Activo'),
        (3, 'Clavos de acero 2 pulgadas (kg)', 'Fijaciones', 'Paquete de clavos estándar', 65.00, 50, 'Activo'),
        (4, 'Pintura obsoleta descontinuada', 'Pinturas', 'Artículo marcado como obsoleto', 120.00, 2, 'Inactivo');
        """)

        conexion.commit()
        print("\n¡Excelente! La base de datos 'ferreteria_sistema' se ha creado perfectamente en phpMyAdmin sin códigos de barras.")
        
        cursor.close()
        conexion.close()

    except Error as e:
        print(f"Hubo un error al estructurar la base de datos: {e}")

if __name__ == "__main__":
    configurar_base_datos()