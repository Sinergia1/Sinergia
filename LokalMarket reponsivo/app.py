from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from flask_mail import Mail, Message
import mysql.connector
import os
from dotenv import load_dotenv
import logging
import time
import hashlib
import hmac
import json
import secrets
import string
from werkzeug.utils import secure_filename

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

load_dotenv()

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# ===== CONFIGURACIÓN DE EMAIL =====
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'tu_correo@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'tu_contraseña_de_aplicacion')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME', 'tu_correo@gmail.com')

# ===== CONFIGURACIÓN PARA SUBIDA DE ARCHIVOS =====
UPLOAD_FOLDER = 'static/uploads'
PRODUCTOS_FOLDER = os.path.join(UPLOAD_FOLDER, 'productos')
PERFILES_FOLDER = os.path.join(UPLOAD_FOLDER, 'perfiles')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB máximo

# Crear carpetas necesarias
os.makedirs(PRODUCTOS_FOLDER, exist_ok=True)
os.makedirs(PERFILES_FOLDER, exist_ok=True)

mail = Mail(app)

# ===== CONFIGURACIÓN DE LA BASE DE DATOS (TIDB CLOUD) =====
# Usando DATABASE_URL para simplificar
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql://3rwEX3bM6GgimVG.root:HxpS7cifPX2bMUJ8@gateway01.us-east-1.prod.aws.tidbcloud.com:4000/IF0_41409995_Local_market')

def get_db_connection():
    """Conecta a la base de datos TiDB Cloud"""
    try:
        # Extraer datos de la URL
        # Formato: mysql://usuario:contraseña@host:puerto/base_datos
        url = DATABASE_URL.replace('mysql://', '')
        user_pass, host_port_db = url.split('@')
        user, password = user_pass.split(':')
        host_port, database = host_port_db.split('/')
        
        if ':' in host_port:
            host, port = host_port.split(':')
            port = int(port)
        else:
            host = host_port
            port = 4000
        
        config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'port': port,
            'ssl_disabled': False,
            'use_pure': True
        }
        
        conn = mysql.connector.connect(**config)
        print("✅ Conectado a TiDB Cloud exitosamente")
        return conn
    except mysql.connector.Error as err:
        print(f"❌ Error conectando a TiDB Cloud: {err}")
        return None

# ===== FUNCIÓN PARA VERIFICAR EXTENSIÓN DE ARCHIVO =====
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ===== FUNCIÓN PARA HASH DE CONTRASEÑAS =====
def hash_password(password):
    """Genera un hash SHA-256 de la contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password, hashed_password):
    """Verifica si la contraseña coincide con el hash"""
    return hmac.compare_digest(hash_password(plain_password), hashed_password)

# ===== RUTAS PARA HTML =====
@app.route('/')
def index():
    return render_template('inicio.html')

@app.route('/<path:filename>')
def serve_files(filename):
    if filename.endswith('.html'):
        try:
            return render_template(filename)
        except:
            return f"Archivo {filename} no encontrado", 404
    return send_from_directory('static', filename)

# ===== API ENDPOINTS PARA SUBIDA DE IMÁGENES =====
@app.route('/api/upload/producto', methods=['POST'])
def upload_producto_imagen():
    """Sube una imagen de producto"""
    try:
        if 'imagen' not in request.files:
            return jsonify({'error': 'No se envió ninguna imagen'}), 400
        
        file = request.files['imagen']
        
        if file.filename == '':
            return jsonify({'error': 'Nombre de archivo vacío'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de archivo no permitido. Use PNG, JPG, JPEG, GIF o WEBP'}), 400
        
        # Generar nombre seguro con timestamp
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        new_filename = f"producto_{int(time.time())}_{secrets.token_hex(4)}{ext}"
        
        filepath = os.path.join(PRODUCTOS_FOLDER, new_filename)
        file.save(filepath)
        
        imagen_url = f"/static/uploads/productos/{new_filename}"
        
        return jsonify({
            'success': True,
            'imagen_url': imagen_url
        })
        
    except Exception as e:
        print(f"❌ Error subiendo imagen: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload/perfil', methods=['POST'])
def upload_perfil_imagen():
    """Sube una imagen de perfil"""
    try:
        if 'foto' not in request.files:
            return jsonify({'error': 'No se envió ninguna imagen'}), 400
        
        file = request.files['foto']
        usuario_id = request.form.get('usuario_id')
        
        if not usuario_id:
            return jsonify({'error': 'ID de usuario requerido'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'Nombre de archivo vacío'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de archivo no permitido'}), 400
        
        # Generar nombre seguro
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        new_filename = f"perfil_{usuario_id}_{int(time.time())}{ext}"
        
        filepath = os.path.join(PERFILES_FOLDER, new_filename)
        file.save(filepath)
        
        foto_url = f"/static/uploads/perfiles/{new_filename}"
        
        # Actualizar en base de datos
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión'}), 500
        
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE usuarios SET foto_url = %s WHERE id = %s",
                (foto_url, usuario_id)
            )
            conn.commit()
            
            return jsonify({
                'success': True,
                'foto_url': foto_url
            })
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"❌ Error subiendo foto de perfil: {e}")
        return jsonify({'error': str(e)}), 500

# ===== API ENDPOINTS PARA CATEGORÍAS =====
@app.route('/api/categorias/todas', methods=['GET'])
def get_todas_categorias():
    """Obtiene todas las categorías de todos los productos (para filtros)"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT DISTINCT categoria 
            FROM productos 
            WHERE activo = 1 AND categoria IS NOT NULL AND categoria != ''
            ORDER BY categoria
        """)
        
        resultados = cursor.fetchall()
        categorias = [r['categoria'] for r in resultados]
        
        return jsonify(categorias)
    except Exception as e:
        print(f"Error obteniendo categorías: {e}")
        return jsonify([])
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empresas/<int:empresa_id>/categorias', methods=['GET'])
def get_categorias_empresa(empresa_id):
    """Obtiene las categorías personalizadas de una empresa"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Obtener categorías únicas de los productos de la empresa
        cursor.execute("""
            SELECT DISTINCT categoria 
            FROM productos 
            WHERE empresa_id = %s AND activo = 1
            ORDER BY categoria
        """, (empresa_id,))
        
        resultados = cursor.fetchall()
        categorias = [r['categoria'] for r in resultados]
        
        return jsonify(categorias)
    except Exception as e:
        print(f"Error obteniendo categorías: {e}")
        return jsonify([])
    finally:
        cursor.close()
        conn.close()

# ===== API ENDPOINTS PARA PRODUCTOS =====
@app.route('/api/productos', methods=['GET'])
def get_productos():
    """Devuelve todos los productos"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor(dictionary=True)
    categoria = request.args.get('categoria')
    empresa_id = request.args.get('empresa_id')
    
    try:
        query = """
            SELECT p.*, e.nombre as empresa_nombre 
            FROM productos p
            JOIN empresa e ON p.empresa_id = e.id
            WHERE p.activo = 1
        """
        params = []
        
        if categoria and categoria != 'todos':
            query += " AND p.categoria = %s"
            params.append(categoria)
        
        if empresa_id:
            query += " AND p.empresa_id = %s"
            params.append(empresa_id)
        
        cursor.execute(query, params)
        productos = cursor.fetchall()
        return jsonify(productos)
    except Exception as e:
        print(f"❌ Error en /api/productos: {e}")
        return jsonify([])
    finally:
        cursor.close()
        conn.close()

@app.route('/api/productos', methods=['POST'])
def crear_producto():
    """Crea un nuevo producto (sin descripción obligatoria)"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO productos 
            (empresa_id, nombre, precio, categoria, imagen_url, cantidad_stock, activo)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
        """, (
            data['empresa_id'],
            data['nombre'],
            data['precio'],
            data['categoria'],
            data.get('imagen_url'),
            data['cantidad_stock']
        ))
        
        conn.commit()
        producto_id = cursor.lastrowid
        
        return jsonify({
            'success': True,
            'id': producto_id,
            'message': 'Producto creado exitosamente'
        })
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creando producto: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/productos/<int:producto_id>', methods=['GET'])
def get_producto(producto_id):
    """Devuelve un producto específico"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.*, e.nombre as empresa_nombre 
            FROM productos p
            JOIN empresa e ON p.empresa_id = e.id
            WHERE p.id = %s
        """, (producto_id,))
        producto = cursor.fetchone()
        return jsonify(producto) if producto else ('', 404)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/productos/<int:producto_id>', methods=['PUT'])
def actualizar_producto(producto_id):
    """Actualiza un producto"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE productos 
            SET nombre = %s, precio = %s, categoria = %s, 
                imagen_url = %s, cantidad_stock = %s
            WHERE id = %s
        """, (
            data['nombre'],
            data['precio'],
            data['categoria'],
            data.get('imagen_url'),
            data['cantidad_stock'],
            producto_id
        ))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Producto actualizado'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/productos/<int:producto_id>', methods=['DELETE'])
def eliminar_producto(producto_id):
    """Elimina (desactiva) un producto"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE productos SET activo = 0 WHERE id = %s", (producto_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Producto eliminado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ===== API ENDPOINTS PARA EMPRESAS =====
@app.route('/api/empresas/buscar', methods=['GET'])
def buscar_empresa():
    """Busca empresa por nombre (para tiendas.html)"""
    nombre = request.args.get('nombre')
    if not nombre:
        return jsonify({'error': 'Se requiere nombre'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Buscar por nombre exacto o parcial
        cursor.execute("SELECT * FROM empresa WHERE nombre LIKE %s AND activo = 1", (f'%{nombre}%',))
        empresa = cursor.fetchone()
        
        if not empresa:
            return jsonify({'error': 'Empresa no encontrada'}), 404
            
        return jsonify(empresa)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empresas', methods=['GET'])
def get_empresas():
    """Devuelve todas las empresas"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM empresa WHERE activo = 1")
        empresas = cursor.fetchall()
        return jsonify(empresas)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empresas/<int:empresa_id>', methods=['GET'])
def get_empresa_by_id(empresa_id):
    """Obtiene empresa por ID"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM empresa WHERE id = %s", (empresa_id,))
        empresa = cursor.fetchone()
        return jsonify(empresa) if empresa else ('', 404)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empresas/<int:empresa_id>/productos', methods=['GET'])
def get_productos_empresa(empresa_id):
    """Productos de una empresa específica"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM productos 
            WHERE empresa_id = %s AND activo = 1
            ORDER BY creado_en DESC
        """, (empresa_id,))
        productos = cursor.fetchall()
        return jsonify(productos)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empresas/<int:empresa_id>/stats', methods=['GET'])
def get_empresa_stats(empresa_id):
    """Estadísticas de una empresa"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Total de productos
        cursor.execute("SELECT COUNT(*) as total FROM productos WHERE empresa_id = %s AND activo = 1", (empresa_id,))
        total_productos = cursor.fetchone()['total']
        
        # Total de ventas (productos vendidos)
        cursor.execute("""
            SELECT SUM(pi.cantidad) as total
            FROM pedido_items pi
            JOIN productos p ON pi.producto_id = p.id
            WHERE p.empresa_id = %s
        """, (empresa_id,))
        result = cursor.fetchone()
        total_ventas = result['total'] or 0
        
        # Categorías únicas
        cursor.execute("""
            SELECT COUNT(DISTINCT categoria) as total 
            FROM productos 
            WHERE empresa_id = %s AND activo = 1
        """, (empresa_id,))
        total_categorias = cursor.fetchone()['total']
        
        return jsonify({
            'productos': total_productos,
            'ventas': total_ventas,
            'categorias': total_categorias
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empresas/<int:empresa_id>/pedidos', methods=['GET'])
def get_pedidos_empresa(empresa_id):
    """Pedidos recibidos por una empresa"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT DISTINCT p.*, u.nombre as cliente_nombre
            FROM pedidos p
            JOIN pedido_items pi ON p.id = pi.pedido_id
            JOIN productos prod ON pi.producto_id = prod.id
            JOIN usuarios u ON p.usuario_id = u.id
            WHERE prod.empresa_id = %s
            ORDER BY p.fecha DESC
        """, (empresa_id,))
        pedidos = cursor.fetchall()
        return jsonify(pedidos)
    finally:
        cursor.close()
        conn.close()

# ===== API ENDPOINTS PARA USUARIOS =====
@app.route('/api/login', methods=['POST'])
def login():
    """Inicia sesión con verificación de contraseña"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.id, u.nombre, u.correo, u.contrasena_hash, u.foto_url, 
                   u.direcciones, u.telefono, u.rol, u.empresa_id,
                   e.nombre as empresa_nombre
            FROM usuarios u
            LEFT JOIN empresa e ON u.empresa_id = e.id
            WHERE u.correo = %s AND u.activo = 1
        """, (data['email'],))
        usuario = cursor.fetchone()
        
        if usuario:
            if verify_password(data['password'], usuario['contrasena_hash']):
                del usuario['contrasena_hash']
                
                if usuario['direcciones'] and isinstance(usuario['direcciones'], str):
                    try:
                        usuario['direcciones'] = json.loads(usuario['direcciones'])
                    except:
                        usuario['direcciones'] = []
                
                print(f"✅ Login exitoso: {usuario['nombre']} - Rol: {usuario['rol']}")
                return jsonify(usuario)
            else:
                return jsonify({'error': 'Contraseña incorrecta'}), 401
        else:
            return jsonify({'error': 'Usuario no encontrado'}), 401
            
    except Exception as e:
        print(f"Error en login: {e}")
        return jsonify({'error': 'Error en el servidor'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/registro', methods=['POST'])
def registro():
    """Registra un nuevo usuario"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (data['email'],))
        if cursor.fetchone():
            return jsonify({'error': 'El correo ya está registrado'}), 400
        
        hashed_password = hash_password(data['password'])
        
        cursor.execute("""
            INSERT INTO usuarios (nombre, correo, contrasena_hash, rol)
            VALUES (%s, %s, %s, 'cliente')
        """, (data['nombre'], data['email'], hashed_password))
        
        conn.commit()
        usuario_id = cursor.lastrowid
        
        cursor.execute("""
            SELECT id, nombre, correo, foto_url, direcciones, telefono, rol, empresa_id
            FROM usuarios 
            WHERE id = %s
        """, (usuario_id,))
        
        usuario = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        usuario_dict = dict(zip(columns, usuario))
        
        return jsonify(usuario_dict)
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/usuarios/<int:usuario_id>', methods=['GET'])
def get_usuario(usuario_id):
    """Obtiene datos de un usuario"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, nombre, correo, foto_url, direcciones, telefono, rol, empresa_id
            FROM usuarios 
            WHERE id = %s
        """, (usuario_id,))
        usuario = cursor.fetchone()
        
        if usuario and usuario['direcciones'] and isinstance(usuario['direcciones'], str):
            try:
                usuario['direcciones'] = json.loads(usuario['direcciones'])
            except:
                usuario['direcciones'] = []
        
        return jsonify(usuario) if usuario else ('', 404)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/usuarios/<int:usuario_id>', methods=['PUT'])
def actualizar_usuario(usuario_id):
    """Actualiza los datos de un usuario"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE usuarios 
            SET nombre = %s, correo = %s, telefono = %s
            WHERE id = %s
        """, (data.get('nombre'), data.get('correo'), data.get('telefono'), usuario_id))
        
        conn.commit()
        
        cursor.execute("""
            SELECT id, nombre, correo, foto_url, direcciones, telefono, rol, empresa_id
            FROM usuarios 
            WHERE id = %s
        """, (usuario_id,))
        
        columns = [column[0] for column in cursor.description]
        usuario = dict(zip(columns, cursor.fetchone()))
        
        if usuario and usuario['direcciones'] and isinstance(usuario['direcciones'], str):
            try:
                usuario['direcciones'] = json.loads(usuario['direcciones'])
            except:
                usuario['direcciones'] = []
        
        return jsonify(usuario)
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/usuarios/<int:usuario_id>/password', methods=['PUT'])
def actualizar_password(usuario_id):
    """Actualiza la contraseña de un usuario"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT contrasena_hash FROM usuarios WHERE id = %s", (usuario_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        current_hash = result[0]
        
        if not verify_password(data['current_password'], current_hash):
            return jsonify({'error': 'Contraseña actual incorrecta'}), 401
        
        new_hash = hash_password(data['new_password'])
        cursor.execute("UPDATE usuarios SET contrasena_hash = %s WHERE id = %s", (new_hash, usuario_id))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Contraseña actualizada correctamente'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ===== API ENDPOINTS PARA CARRITO =====
@app.route('/api/carrito/<string:session_id>', methods=['GET'])
def get_carrito(session_id):
    """Obtiene el carrito de una sesión"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                c.id,
                c.producto_id,
                c.cantidad,
                p.nombre,
                p.precio,
                p.imagen_url,
                e.nombre as empresa_nombre
            FROM carrito_temp c
            JOIN productos p ON c.producto_id = p.id
            JOIN empresa e ON p.empresa_id = e.id
            WHERE c.session_id = %s
        """, (session_id,))
        items = cursor.fetchall()
        return jsonify(items)
    except Exception as e:
        print(f"❌ Error en get_carrito: {e}")
        return jsonify([])
    finally:
        cursor.close()
        conn.close()

@app.route('/api/carrito/agregar', methods=['POST'])
def agregar_carrito():
    """Agrega un producto al carrito"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, cantidad FROM carrito_temp 
            WHERE session_id = %s AND producto_id = %s
        """, (data['session_id'], data['producto_id']))
        existente = cursor.fetchone()
        
        if existente:
            cursor.execute("""
                UPDATE carrito_temp 
                SET cantidad = cantidad + %s 
                WHERE id = %s
            """, (data['cantidad'], existente[0]))
        else:
            cursor.execute("""
                INSERT INTO carrito_temp (session_id, producto_id, cantidad)
                VALUES (%s, %s, %s)
            """, (data['session_id'], data['producto_id'], data['cantidad']))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/carrito/actualizar', methods=['PUT'])
def actualizar_carrito():
    """Actualiza cantidad de un item"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE carrito_temp 
            SET cantidad = %s 
            WHERE id = %s
        """, (data['cantidad'], data['item_id']))
        conn.commit()
        return jsonify({'success': True})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/carrito/eliminar/<int:item_id>', methods=['DELETE'])
def eliminar_item(item_id):
    """Elimina un item del carrito"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM carrito_temp WHERE id = %s", (item_id,))
        conn.commit()
        return jsonify({'success': True})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/carrito/limpiar/<string:session_id>', methods=['DELETE'])
def limpiar_carrito(session_id):
    """Vacía el carrito de una sesión"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM carrito_temp WHERE session_id = %s", (session_id,))
        conn.commit()
        return jsonify({'success': True})
    finally:
        cursor.close()
        conn.close()

# ===== API ENDPOINTS PARA PEDIDOS =====
@app.route('/api/pedidos', methods=['POST'])
def crear_pedido():
    """Crea un nuevo pedido"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO pedidos (usuario_id, total, direccion_entrega, notas)
            VALUES (%s, %s, %s, %s)
        """, (data['usuario_id'], data['total'], json.dumps(data['direccion']), data.get('notas', '')))
        
        pedido_id = cursor.lastrowid
        
        for item in data['items']:
            cursor.execute("""
                INSERT INTO pedido_items (pedido_id, producto_id, cantidad, precio_unitario)
                VALUES (%s, %s, %s, %s)
            """, (pedido_id, item['producto_id'], item['cantidad'], item['precio']))
            
            cursor.execute("""
                UPDATE productos 
                SET cantidad_stock = cantidad_stock - %s,
                    cantidad_vendidos = cantidad_vendidos + %s
                WHERE id = %s
            """, (item['cantidad'], item['cantidad'], item['producto_id']))
        
        cursor.execute("DELETE FROM carrito_temp WHERE session_id = %s", (data['session_id'],))
        
        conn.commit()
        return jsonify({'pedido_id': pedido_id, 'success': True})
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/usuarios/<int:usuario_id>/pedidos', methods=['GET'])
def get_pedidos_usuario(usuario_id):
    """Historial de pedidos de un usuario"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM pedidos 
            WHERE usuario_id = %s 
            ORDER BY fecha DESC
        """, (usuario_id,))
        pedidos = cursor.fetchall()
        return jsonify(pedidos)
    finally:
        cursor.close()
        conn.close()

# ===== API ENDPOINTS PARA SOLICITUDES =====
@app.route('/api/solicitudes', methods=['POST'])
def crear_solicitud():
    """Crea una nueva solicitud de empresa"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id FROM solicitudes_empresa 
            WHERE email = %s AND estado = 'pendiente'
        """, (data['email'],))
        
        if cursor.fetchone():
            return jsonify({'error': 'Ya tienes una solicitud pendiente'}), 400
        
        cursor.execute("""
            INSERT INTO solicitudes_empresa 
            (nombre_negocio, propietario, email, telefono, ciudad, direccion, descripcion, categorias)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['nombre_negocio'],
            data['propietario'],
            data['email'],
            data['telefono'],
            data['ciudad'],
            data['direccion'],
            data['descripcion'],
            json.dumps(data.get('categorias', []))
        ))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Solicitud enviada correctamente'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/solicitudes', methods=['GET'])
def get_solicitudes():
    """Obtiene todas las solicitudes (solo para admin)"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM solicitudes_empresa 
            ORDER BY 
                CASE WHEN estado = 'pendiente' THEN 1 ELSE 2 END,
                creado_en DESC
        """)
        solicitudes = cursor.fetchall()
        
        for s in solicitudes:
            if s['categorias'] and isinstance(s['categorias'], str):
                try:
                    s['categorias'] = json.loads(s['categorias'])
                except:
                    s['categorias'] = []
        
        return jsonify(solicitudes)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/solicitudes/<int:solicitud_id>/aprobar', methods=['PUT'])
def aprobar_solicitud(solicitud_id):
    """Aprueba una solicitud y crea la empresa"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM solicitudes_empresa WHERE id = %s", (solicitud_id,))
        solicitud = cursor.fetchone()
        
        if not solicitud:
            return jsonify({'error': 'Solicitud no encontrada'}), 404
        
        # Crear la empresa
        cursor.execute("""
            INSERT INTO empresa (nombre, direccion, telefono, tipo_producto, activo)
            VALUES (%s, %s, %s, %s, 1)
        """, (
            solicitud['nombre_negocio'],
            solicitud['direccion'],
            solicitud['telefono'],
            'otro'
        ))
        
        empresa_id = cursor.lastrowid
        
        # Buscar si el usuario ya existe
        cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (solicitud['email'],))
        usuario = cursor.fetchone()
        
        temp_password = None
        usuario_id = None
        email_enviado = False
        
        if usuario:
            usuario_id = usuario['id']
            cursor.execute("""
                UPDATE usuarios 
                SET rol = 'socio', empresa_id = %s 
                WHERE id = %s
            """, (empresa_id, usuario_id))
        else:
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            hashed_password = hash_password(temp_password)
            
            cursor.execute("""
                INSERT INTO usuarios (nombre, correo, contrasena_hash, rol, empresa_id)
                VALUES (%s, %s, %s, 'socio', %s)
            """, (
                solicitud['propietario'],
                solicitud['email'],
                hashed_password,
                empresa_id
            ))
            
            usuario_id = cursor.lastrowid
        
        cursor.execute("UPDATE solicitudes_empresa SET estado = 'aprobada' WHERE id = %s", (solicitud_id,))
        conn.commit()
        
        # Intentar enviar email
        try:
            msg = Message(
                subject="✅ ¡Tu solicitud en LocalMarket ha sido APROBADA!",
                recipients=[solicitud['email']]
            )
            
            msg.html = f"""
            <h2>¡Felicidades {solicitud['propietario']}!</h2>
            <p>Tu solicitud ha sido aprobada.</p>
            <p><strong>Email:</strong> {solicitud['email']}</p>
            <p><strong>Contraseña:</strong> {temp_password if temp_password else '[Usa tu contraseña actual]'}</p>
            <p>Accede a: <a href="http://localhost:5000/panel_empresa.html">Panel de Empresa</a></p>
            """
            
            mail.send(msg)
            email_enviado = True
        except Exception as e:
            print(f"Error enviando email: {e}")
        
        return jsonify({
            'success': True,
            'empresa_id': empresa_id,
            'email_enviado': email_enviado
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/solicitudes/<int:solicitud_id>/rechazar', methods=['PUT'])
def rechazar_solicitud(solicitud_id):
    """Rechaza una solicitud"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE solicitudes_empresa SET estado = 'rechazada' WHERE id = %s", (solicitud_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ===== API ENDPOINTS PARA ESTADÍSTICAS =====
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Obtiene estadísticas generales"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) as total FROM empresa WHERE activo = 1")
        empresas = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM productos WHERE activo = 1")
        productos = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM pedidos")
        pedidos = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM solicitudes_empresa WHERE estado = 'pendiente'")
        solicitudes_pendientes = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE rol = 'cliente'")
        clientes = cursor.fetchone()['total']
        
        return jsonify({
            'empresas': empresas,
            'productos': productos,
            'pedidos': pedidos,
            'solicitudes_pendientes': solicitudes_pendientes,
            'clientes': clientes
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ===== INICIALIZACIÓN =====
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 INICIANDO SERVIDOR LOKALMARKET")
    print("=" * 50)
    
    # Crear carpetas necesarias
    os.makedirs(PRODUCTOS_FOLDER, exist_ok=True)
    os.makedirs(PERFILES_FOLDER, exist_ok=True)
    
    print(f"📁 Carpeta de productos: {PRODUCTOS_FOLDER}")
    print(f"📁 Carpeta de perfiles: {PERFILES_FOLDER}")
    
    # Verificar configuración de email
    print("\n📧 Configuración de email:")
    print(f"   MAIL_SERVER: {app.config['MAIL_SERVER']}")
    print(f"   MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
    
    # Verificar conexión a BD
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Verificar si hay usuarios de prueba
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("\n📝 Insertando usuarios de prueba...")
            usuarios_prueba = [
                ('Ana García', 'ana@example.com', hash_password('ana123'), 'cliente', None),
                ('Luis Pérez', 'luis@example.com', hash_password('luis123'), 'administrador', None),
                ('María Socio', 'maria@example.com', hash_password('maria123'), 'socio', 1)
            ]
            
            cursor.executemany("""
                INSERT INTO usuarios (nombre, correo, contrasena_hash, rol, empresa_id)
                VALUES (%s, %s, %s, %s, %s)
            """, usuarios_prueba)
            conn.commit()
            print("✅ Usuarios de prueba insertados")
        
        cursor.close()
        conn.close()
    
    print("\n" + "=" * 50)
    print("🌐 Servidor corriendo en:")
    print("   → http://localhost:5000")
    print("   → http://127.0.0.1:5000")
    print("\n📝 Usuarios de prueba:")
    print("   • ana@example.com / ana123 (cliente)")
    print("   • luis@example.com / luis123 (administrador)")
    print("   • maria@example.com / maria123 (socio)")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)