# test_conexion.py
import mysql.connector

# TUS DATOS DE INFINITYFREE (cámbialos)
db_config = {
    'host': 'sql110.infinityfree.com',      # Tu host
    'user': 'if0_41409995',                  # Tu usuario
    'password': 'TU_CONTRASEÑA_AQUI',        # La contraseña del panel
    'database': 'if0_41409995_Local_market', # Tu base de datos
    'port': 3306
}

print("🔌 Probando conexión a InfinityFree...")
print(f"Host: {db_config['host']}")
print(f"Usuario: {db_config['user']}")
print(f"Base de datos: {db_config['database']}")
print("-" * 40)

try:
    # Intentar conectar
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    # Obtener tablas
    cursor.execute("SHOW TABLES")
    tablas = cursor.fetchall()
    
    print("✅ ¡CONEXIÓN EXITOSA!\n")
    print(f"📊 Tablas encontradas: {len(tablas)}")
    
    if tablas:
        print("\n📋 Lista de tablas:")
        for i, tabla in enumerate(tablas, 1):
            print(f"   {i}. {tabla[0]}")
            
        # Probar una consulta en la primera tabla
        primera_tabla = tablas[0][0]
        cursor.execute(f"SELECT COUNT(*) FROM {primera_tabla}")
        count = cursor.fetchone()[0]
        print(f"\n📊 Registros en '{primera_tabla}': {count}")
    else:
        print("⚠️ No hay tablas en la base de datos")
    
    cursor.close()
    conn.close()
    
except mysql.connector.Error as e:
    print(f"❌ ERROR DE CONEXIÓN:")
    print(f"   Código: {e.errno}")
    print(f"   Mensaje: {e}")
    print(f"   SQLSTATE: {e.sqlstate}")
    
except Exception as e:
    print(f"❌ ERROR INESPERADO: {e}")