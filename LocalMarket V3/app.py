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
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'localmarket837@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'ulod idxi bzlm fstc')
app.config['MAIL_DEFAULT_SENDER'] = (os.getenv('MAIL_SENDER_NAME', 'LocalMarket'), 
                                       os.getenv('MAIL_USERNAME', 'localmarket837@gmail.com'))
app.config['MAIL_ASCII_ATTACHMENTS'] = False
app.config['MAIL_SUPPRESS_SEND'] = False

# ===== CONFIGURACIÓN PARA SUBIDA DE ARCHIVOS =====
UPLOAD_FOLDER = 'static/uploads'
PRODUCTOS_FOLDER = os.path.join(UPLOAD_FOLDER, 'productos')
PERFILES_FOLDER = os.path.join(UPLOAD_FOLDER, 'perfiles')
EMPRESAS_FOLDER = os.path.join(UPLOAD_FOLDER, 'empresas')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB máximo

# Crear carpetas necesarias
os.makedirs(PRODUCTOS_FOLDER, exist_ok=True)
os.makedirs(PERFILES_FOLDER, exist_ok=True)
os.makedirs(EMPRESAS_FOLDER, exist_ok=True)

mail = Mail(app)

# ===== CONFIGURACIÓN DE LA BASE DE DATOS =====
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql://3rwEX3bM6GgimVG.root:HxpS7cifPX2bMUJ8@gateway01.us-east-1.prod.aws.tidbcloud.com:4000/IF0_41409995_Local_market')

def get_db_connection():
    """Conecta a la base de datos TiDB Cloud"""
    try:
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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def hash_password(password):
    """Genera un hash SHA-256 de la contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password, hashed_password):
    """Verifica si la contraseña coincide con el hash"""
    return hmac.compare_digest(hash_password(plain_password), hashed_password)

# ============================================
# ===== RUTAS PARA ARCHIVOS ESTÁTICOS ========
# ============================================

@app.route('/static/<path:filename>')
def serve_static_files(filename):
    """Sirve archivos estáticos normales como CSS, JS"""
    return send_from_directory('static', filename)

@app.route('/static/uploads/<path:filename>')
def serve_uploads(filename):
    """Sirve las imágenes subidas a la carpeta uploads"""
    return send_from_directory('static/uploads', filename)

@app.route('/')
def index():
    return render_template('inicio.html')

@app.route('/<path:filename>')
def serve_files(filename):
    """Sirve archivos HTML"""
    if filename.endswith('.html'):
        try:
            return render_template(filename)
        except:
            return f"Archivo {filename} no encontrado", 404
    try:
        return send_from_directory('static', filename)
    except:
        return f"Archivo {filename} no encontrado", 404

# ============================================
# ===== API ENDPOINTS PARA SUBIDA DE IMÁGENES =
# ============================================

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
            return jsonify({'error': 'Tipo de archivo no permitido'}), 400
        
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
        
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        new_filename = f"perfil_{usuario_id}_{int(time.time())}{ext}"
        
        filepath = os.path.join(PERFILES_FOLDER, new_filename)
        file.save(filepath)
        
        foto_url = f"/static/uploads/perfiles/{new_filename}"
        
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

@app.route('/api/upload/empresa/logo', methods=['POST'])
def upload_empresa_logo():
    """Sube un logo de empresa"""
    try:
        if 'logo' not in request.files:
            return jsonify({'error': 'No se envió ninguna imagen'}), 400
        
        file = request.files['logo']
        empresa_id = request.form.get('empresa_id')
        
        if not empresa_id:
            return jsonify({'error': 'ID de empresa requerido'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'Nombre de archivo vacío'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de archivo no permitido'}), 400
        
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        new_filename = f"logo_empresa_{empresa_id}_{int(time.time())}{ext}"
        
        filepath = os.path.join(EMPRESAS_FOLDER, new_filename)
        file.save(filepath)
        
        logo_url = f"/static/uploads/empresas/{new_filename}"
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Error de conexión'}), 500
        
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE empresa SET logo_url = %s WHERE id = %s",
                (logo_url, empresa_id)
            )
            conn.commit()
            
            return jsonify({
                'success': True,
                'logo_url': logo_url
            })
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"❌ Error subiendo logo de empresa: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================
# ===== API ENDPOINTS PARA CATEGORÍAS ========
# ============================================

@app.route('/api/categorias/todas', methods=['GET'])
def get_todas_categorias():
    """Obtiene todas las categorías de todos los productos (para filtros globales)"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT DISTINCT categoria 
            FROM productos 
            WHERE activo = 1 AND categoria IS NOT NULL AND categoria != ''
            ORDER BY categoria
        """)
        
        resultados = cursor.fetchall()
        categorias = [r[0] for r in resultados]
        
        return jsonify(categorias)
    except Exception as e:
        print(f"Error obteniendo categorías: {e}")
        return jsonify([])
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empresas/<int:empresa_id>/categorias', methods=['GET'])
def get_categorias_empresa(empresa_id):
    """Obtiene las categorías que ha usado una empresa en sus productos"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT DISTINCT categoria 
            FROM productos 
            WHERE empresa_id = %s AND activo = 1 
            AND categoria IS NOT NULL AND categoria != ''
            ORDER BY categoria
        """, (empresa_id,))
        
        resultados = cursor.fetchall()
        categorias = [r[0] for r in resultados]
        print(f"📋 Categorías encontradas para empresa {empresa_id}: {categorias}")
        return jsonify(categorias)
    except Exception as e:
        print(f"❌ Error obteniendo categorías de empresa: {e}")
        return jsonify([])
    finally:
        cursor.close()
        conn.close()

# ============================================
# ===== API ENDPOINTS PARA PRODUCTOS =========
# ============================================

@app.route('/api/productos', methods=['GET'])
def get_productos():
    """Devuelve todos los productos activos (para clientes)"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor(dictionary=True)
    categoria = request.args.get('categoria')
    empresa_id = request.args.get('empresa_id')
    
    try:
        query = """
            SELECT p.*, e.nombre as empresa_nombre, e.logo_url as empresa_logo
            FROM productos p
            JOIN empresa e ON p.empresa_id = e.id
            WHERE p.activo = 1 AND e.activo = 1
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

@app.route('/api/productos/todos', methods=['GET'])
def get_todos_productos_admin():
    """Devuelve TODOS los productos (activos e inactivos) - SOLO PARA ADMIN"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.*, e.nombre as empresa_nombre, e.logo_url as empresa_logo
            FROM productos p
            JOIN empresa e ON p.empresa_id = e.id
            ORDER BY p.id DESC
        """)
        productos = cursor.fetchall()
        return jsonify(productos)
    except Exception as e:
        print(f"❌ Error en /api/productos/todos: {e}")
        return jsonify([])
    finally:
        cursor.close()
        conn.close()

@app.route('/api/productos', methods=['POST'])
def crear_producto():
    """Crea un nuevo producto"""
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
            data.get('categoria', ''),
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
            data.get('categoria', ''),
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

# ============================================
# ===== API ENDPOINTS PARA EMPRESAS ==========
# ============================================

@app.route('/api/empresas', methods=['GET'])
def get_empresas():
    """Devuelve SOLO empresas activas (para clientes en inicio.html)"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM empresa WHERE activo = 1 ORDER BY id DESC")
        empresas = cursor.fetchall()
        return jsonify(empresas)
    except Exception as e:
        print(f"❌ Error en /api/empresas: {e}")
        return jsonify([])
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empresas/todas', methods=['GET'])
def get_todas_empresas_admin():
    """Devuelve TODAS las empresas (activas e inactivas) - SOLO PARA ADMIN"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM empresa ORDER BY id DESC")
        empresas = cursor.fetchall()
        return jsonify(empresas)
    except Exception as e:
        print(f"❌ Error en /api/empresas/todas: {e}")
        return jsonify([])
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empresas/buscar', methods=['GET'])
def buscar_empresa():
    """Busca empresa por nombre (solo activas para clientes)"""
    nombre = request.args.get('nombre')
    if not nombre:
        return jsonify({'error': 'Se requiere nombre'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM empresa WHERE nombre LIKE %s AND activo = 1", (f'%{nombre}%',))
        empresa = cursor.fetchone()
        
        if not empresa:
            return jsonify({'error': 'Empresa no encontrada'}), 404
            
        return jsonify(empresa)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empresas/<int:empresa_id>', methods=['GET'])
def get_empresa_by_id(empresa_id):
    """Obtiene empresa por ID (solo activas para clientes)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM empresa WHERE id = %s AND activo = 1", (empresa_id,))
        empresa = cursor.fetchone()
        return jsonify(empresa) if empresa else ('', 404)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empresas/admin/<int:empresa_id>', methods=['GET'])
def get_empresa_by_id_admin(empresa_id):
    """Obtiene empresa por ID (incluyendo inactivas) - SOLO PARA ADMIN"""
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

@app.route('/api/empresas/<int:empresa_id>/completo', methods=['PUT'])
def actualizar_empresa_completo(empresa_id):
    """Actualiza todos los datos de una empresa"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        horario = data.get('horario')
        if isinstance(horario, dict):
            horario = json.dumps(horario)
        
        cursor.execute("""
            UPDATE empresa 
            SET nombre = %s, direccion = %s, telefono = %s, 
                tipo_producto = %s, logo_url = %s, horario = %s,
                latitud = %s, longitud = %s
            WHERE id = %s
        """, (
            data.get('nombre'),
            data.get('direccion', ''),
            data.get('telefono', ''),
            data.get('tipo_producto', 'otro'),
            data.get('logo_url'),
            horario,
            data.get('latitud'),
            data.get('longitud'),
            empresa_id
        ))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Empresa actualizada correctamente'})
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error actualizando empresa: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empresas/<int:empresa_id>/productos', methods=['GET'])
def get_productos_empresa(empresa_id):
    """Productos de una empresa específica (solo activos para clientes)"""
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
        cursor.execute("SELECT COUNT(*) as total FROM productos WHERE empresa_id = %s AND activo = 1", (empresa_id,))
        total_productos = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT SUM(pi.cantidad) as total
            FROM pedido_items pi
            JOIN productos p ON pi.producto_id = p.id
            WHERE p.empresa_id = %s
        """, (empresa_id,))
        result = cursor.fetchone()
        total_ventas = result['total'] or 0
        
        cursor.execute("""
            SELECT COUNT(DISTINCT categoria) as total 
            FROM productos 
            WHERE empresa_id = %s AND activo = 1 AND categoria IS NOT NULL AND categoria != ''
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

@app.route('/api/empresas/<int:empresa_id>/horario', methods=['PUT'])
def actualizar_horario_empresa(empresa_id):
    """Actualiza solo el horario de una empresa"""
    data = request.json
    horario = data.get('horario')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE empresa 
            SET horario = %s
            WHERE id = %s
        """, (json.dumps(horario), empresa_id))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Horario actualizado correctamente'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empresas/<int:empresa_id>/pedidos', methods=['GET'])
def get_pedidos_empresa(empresa_id):
    """Pedidos que contienen productos de esta empresa"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT DISTINCT 
                p.id, 
                p.fecha, 
                p.total, 
                p.estado,
                u.nombre as cliente_nombre
            FROM pedidos p
            JOIN pedido_items pi ON p.id = pi.pedido_id
            JOIN productos prod ON pi.producto_id = prod.id
            JOIN usuarios u ON p.usuario_id = u.id
            WHERE prod.empresa_id = %s
            ORDER BY p.fecha DESC
        """, (empresa_id,))
        pedidos = cursor.fetchall()
        return jsonify(pedidos)
    except Exception as e:
        print(f"❌ Error obteniendo pedidos de empresa: {e}")
        return jsonify([])
    finally:
        cursor.close()
        conn.close()

# ============================================
# ===== API ENDPOINTS PARA USUARIOS ==========
# ============================================

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
                   u.direcciones, u.telefono, u.rol, u.empresa_id, u.activo,
                   e.nombre as empresa_nombre, e.logo_url as empresa_logo
            FROM usuarios u
            LEFT JOIN empresa e ON u.empresa_id = e.id
            WHERE u.correo = %s
        """, (data['email'],))
        usuario = cursor.fetchone()
        
        if usuario:
            if not usuario['activo']:
                return jsonify({'error': 'Cuenta desactivada. Contacta al administrador.'}), 401
            
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
            INSERT INTO usuarios (nombre, correo, contrasena_hash, rol, activo)
            VALUES (%s, %s, %s, 'cliente', 1)
        """, (data['nombre'], data['email'], hashed_password))
        
        conn.commit()
        usuario_id = cursor.lastrowid
        
        cursor.execute("""
            SELECT id, nombre, correo, foto_url, direcciones, telefono, rol, empresa_id, activo
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

@app.route('/api/usuarios/todos', methods=['GET'])
def get_todos_usuarios():
    """Obtiene todos los usuarios (solo para admin)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.id, u.nombre, u.correo, u.foto_url, u.telefono, u.rol, u.empresa_id, u.activo,
                   CAST(u.direcciones AS CHAR) as direcciones,
                   e.nombre as empresa_nombre
            FROM usuarios u
            LEFT JOIN empresa e ON u.empresa_id = e.id
            ORDER BY u.id DESC
        """)
        usuarios = cursor.fetchall()
        
        for u in usuarios:
            if u.get('direcciones'):
                try:
                    if isinstance(u['direcciones'], str):
                        u['direcciones'] = json.loads(u['direcciones']) if u['direcciones'] else []
                except:
                    u['direcciones'] = []
            else:
                u['direcciones'] = []
        
        return jsonify(usuarios)
    except Exception as e:
        print(f"❌ Error obteniendo usuarios: {e}")
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
            SELECT id, nombre, correo, foto_url, direcciones, telefono, rol, empresa_id, activo
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
            SELECT id, nombre, correo, foto_url, direcciones, telefono, rol, empresa_id, activo
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

@app.route('/api/usuarios/<int:usuario_id>/cambiar-password', methods=['PUT'])
def cambiar_password_socio(usuario_id):
    """Cambia la contraseña de un usuario socio"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT contrasena_hash FROM usuarios WHERE id = %s AND activo = 1", (usuario_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        current_hash = result[0]
        
        if not verify_password(data['current_password'], current_hash):
            return jsonify({'error': 'Contraseña actual incorrecta'}), 401
        
        if len(data['new_password']) < 6:
            return jsonify({'error': 'La nueva contraseña debe tener al menos 6 caracteres'}), 400
        
        new_hash = hash_password(data['new_password'])
        cursor.execute("UPDATE usuarios SET contrasena_hash = %s WHERE id = %s", (new_hash, usuario_id))
        
        conn.commit()
        return jsonify({
            'success': True,
            'message': 'Contraseña actualizada correctamente'
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============================================
# ===== ENDPOINTS PARA ADMIN =================
# ============================================

@app.route('/api/usuarios/<int:usuario_id>/actualizar-completo', methods=['PUT'])
def actualizar_usuario_completo(usuario_id):
    """Actualiza usuario incluyendo correo"""
    data = request.json
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM usuarios WHERE correo = %s AND id != %s", 
                       (data.get('correo'), usuario_id))
        if cursor.fetchone():
            return jsonify({'error': 'El correo ya está registrado por otro usuario'}), 400
        
        update_fields = []
        params = []
        
        if 'nombre' in data:
            update_fields.append("nombre = %s")
            params.append(data['nombre'])
        
        if 'correo' in data:
            update_fields.append("correo = %s")
            params.append(data['correo'])
        
        if 'telefono' in data:
            update_fields.append("telefono = %s")
            params.append(data['telefono'])
        
        if 'rol' in data:
            update_fields.append("rol = %s")
            params.append(data['rol'])
        
        if 'empresa_id' in data:
            update_fields.append("empresa_id = %s")
            params.append(data['empresa_id'] if data['empresa_id'] else None)
        
        if not update_fields:
            return jsonify({'error': 'No hay datos para actualizar'}), 400
        
        params.append(usuario_id)
        query = f"UPDATE usuarios SET {', '.join(update_fields)} WHERE id = %s"
        
        cursor.execute(query, params)
        conn.commit()
        
        cursor.execute("""
            SELECT u.id, u.nombre, u.correo, u.foto_url, u.telefono, u.rol, u.empresa_id, u.activo,
                   e.nombre as empresa_nombre
            FROM usuarios u
            LEFT JOIN empresa e ON u.empresa_id = e.id
            WHERE u.id = %s
        """, (usuario_id,))
        
        columns = [column[0] for column in cursor.description]
        usuario = dict(zip(columns, cursor.fetchone()))
        
        return jsonify({
            'success': True,
            'usuario': usuario,
            'message': 'Usuario actualizado correctamente'
        })
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error actualizando usuario: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/usuarios/<int:usuario_id>/eliminar-completo', methods=['DELETE'])
def eliminar_usuario_completo(usuario_id):
    """Elimina un usuario socio y todos sus datos relacionados"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT rol, empresa_id FROM usuarios WHERE id = %s", (usuario_id,))
        usuario = cursor.fetchone()
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        if usuario['rol'] == 'administrador':
            return jsonify({'error': 'No se puede eliminar un administrador'}), 400
        
        empresa_id = usuario.get('empresa_id')
        
        if usuario['rol'] == 'socio' and empresa_id:
            cursor.execute("""
                DELETE ct FROM carrito_temp ct
                JOIN productos p ON ct.producto_id = p.id
                WHERE p.empresa_id = %s
            """, (empresa_id,))
            
            cursor.execute("""
                DELETE pi FROM pedido_items pi
                JOIN productos p ON pi.producto_id = p.id
                WHERE p.empresa_id = %s
            """, (empresa_id,))
            
            cursor.execute("""
                DELETE p FROM pedidos p
                WHERE NOT EXISTS (
                    SELECT 1 FROM pedido_items pi
                    JOIN productos prod ON pi.producto_id = prod.id
                    WHERE pi.pedido_id = p.id AND prod.empresa_id != %s
                )
                AND EXISTS (
                    SELECT 1 FROM pedido_items pi
                    JOIN productos prod ON pi.producto_id = prod.id
                    WHERE pi.pedido_id = p.id AND prod.empresa_id = %s
                )
            """, (empresa_id, empresa_id))
            
            cursor.execute("DELETE FROM productos WHERE empresa_id = %s", (empresa_id,))
            cursor.execute("DELETE FROM empresa WHERE id = %s", (empresa_id,))
        
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Usuario y todos sus datos eliminados correctamente'
        })
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error eliminando usuario completo: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============================================
# ===== ENDPOINT PARA SOCIO ==================
# ============================================

@app.route('/api/socio/<int:usuario_id>/actualizar-perfil', methods=['PUT'])
def actualizar_perfil_socio(usuario_id):
    """Actualiza el perfil del socio incluyendo su correo"""
    data = request.json
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM usuarios WHERE correo = %s AND id != %s", 
                       (data.get('correo'), usuario_id))
        if cursor.fetchone():
            return jsonify({'error': 'El correo ya está registrado por otro usuario'}), 400
        
        update_fields = []
        params = []
        
        if 'nombre' in data:
            update_fields.append("nombre = %s")
            params.append(data['nombre'])
        
        if 'correo' in data:
            update_fields.append("correo = %s")
            params.append(data['correo'])
        
        if 'telefono' in data:
            update_fields.append("telefono = %s")
            params.append(data['telefono'])
        
        if update_fields:
            params.append(usuario_id)
            query = f"UPDATE usuarios SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, params)
        
        conn.commit()
        
        cursor.execute("""
            SELECT id, nombre, correo, foto_url, telefono, rol, empresa_id
            FROM usuarios WHERE id = %s
        """, (usuario_id,))
        
        columns = [column[0] for column in cursor.description]
        usuario = dict(zip(columns, cursor.fetchone()))
        
        return jsonify({
            'success': True,
            'usuario': usuario,
            'message': 'Perfil actualizado correctamente'
        })
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error actualizando perfil socio: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============================================
# ===== API ENDPOINTS PARA CARRITO ===========
# ============================================

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
                e.nombre as empresa_nombre,
                e.telefono as empresa_telefono
            FROM carrito_temp c
            JOIN productos p ON c.producto_id = p.id
            JOIN empresa e ON p.empresa_id = e.id
            WHERE c.session_id = %s AND p.activo = 1 AND e.activo = 1
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

# ============================================
# ===== API ENDPOINTS PARA PEDIDOS ===========
# ============================================

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

# ============================================
# ===== API ENDPOINTS PARA SOLICITUDES =======
# ============================================

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
        
        cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (solicitud['email'],))
        usuario = cursor.fetchone()
        
        temp_password = None
        usuario_id = None
        email_enviado = False
        email_error = None
        
        if usuario:
            usuario_id = usuario['id']
            cursor.execute("""
                UPDATE usuarios 
                SET rol = 'socio', empresa_id = %s 
                WHERE id = %s
            """, (empresa_id, usuario_id))
        else:
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
            hashed_password = hash_password(temp_password)
            
            cursor.execute("""
                INSERT INTO usuarios (nombre, correo, contrasena_hash, rol, empresa_id, activo)
                VALUES (%s, %s, %s, 'socio', %s, 1)
            """, (
                solicitud['propietario'],
                solicitud['email'],
                hashed_password,
                empresa_id
            ))
            
            usuario_id = cursor.lastrowid
        
        cursor.execute("UPDATE solicitudes_empresa SET estado = 'aprobada' WHERE id = %s", (solicitud_id,))
        conn.commit()
        
        try:
            base_url = os.getenv('APP_URL', 'https://localmarket.onrender.com')
            
            msg = Message(
                subject="✅ ¡Tu solicitud en LocalMarket ha sido APROBADA!",
                recipients=[solicitud['email']],
                sender=app.config['MAIL_DEFAULT_SENDER']
            )
            
            msg.html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="color: #0d2922;">¡Felicidades {solicitud['propietario']}!</h2>
                    <p>Tu solicitud para <strong>{solicitud['nombre_negocio']}</strong> ha sido <span style="color: #10b981; font-weight: bold;">APROBADA</span>.</p>
                    
                    <div style="background: #f4a4b4; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #0d2922;">Tus credenciales de acceso:</h3>
                        <p><strong>Email:</strong> {solicitud['email']}</p>
                        <p><strong>Contraseña temporal:</strong> <code style="background: #fff; padding: 5px 10px; border-radius: 4px; font-size: 16px; font-weight: bold;">{temp_password if temp_password else '[Usa tu contraseña actual]'}</code></p>
                        <p style="font-size: 12px; color: #666; margin-top: 10px;">
                            ⚠️ Por seguridad, te recomendamos cambiar esta contraseña en tu primer inicio de sesión.
                        </p>
                    </div>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{base_url}/inicio_secion.html" 
                           style="background: #0d2922; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                            Iniciar Sesión →
                        </a>
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="font-size: 12px; color: #666; text-align: center;">
                        Si no solicitaste esta cuenta, ignora este mensaje.<br>
                        © 2024 LocalMarket - Todos los derechos reservados.
                    </p>
                </div>
            </body>
            </html>
            """
            
            msg.body = f"""
            ¡Felicidades {solicitud['propietario']}!
            
            Tu solicitud para {solicitud['nombre_negocio']} ha sido APROBADA.
            
            TUS CREDENCIALES:
            Email: {solicitud['email']}
            Contraseña temporal: {temp_password if temp_password else '[Usa tu contraseña actual]'}
            
            Accede aquí: {base_url}/inicio_secion.html
            
            © 2024 LocalMarket
            """
            
            mail.send(msg)
            email_enviado = True
            print(f"✅ Email enviado exitosamente a: {solicitud['email']}")
            
        except Exception as e:
            email_error = str(e)
            print(f"❌ Error enviando email: {email_error}")
            import traceback
            traceback.print_exc()
        
        return jsonify({
            'success': True,
            'empresa_id': empresa_id,
            'email_enviado': email_enviado,
            'email_error': email_error if not email_enviado else None,
            'message': 'Solicitud aprobada exitosamente'
        })
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error en aprobar_solicitud: {e}")
        import traceback
        traceback.print_exc()
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

# ============================================
# ===== API ENDPOINTS PARA EMPRESAS (ADMIN) ==
# ============================================

@app.route('/api/empresas', methods=['POST'])
def crear_empresa_admin():
    """Crea una nueva empresa desde el panel de admin"""
    data = request.json
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO empresa (nombre, direccion, telefono, tipo_producto, activo)
            VALUES (%s, %s, %s, %s, 1)
        """, (
            data.get('nombre'),
            data.get('direccion', ''),
            data.get('telefono', ''),
            data.get('tipo_producto', 'otro')
        ))
        
        conn.commit()
        empresa_id = cursor.lastrowid
        
        return jsonify({
            'success': True,
            'id': empresa_id,
            'message': 'Empresa creada exitosamente'
        })
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creando empresa: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empresas/<int:empresa_id>', methods=['PUT'])
def actualizar_empresa_admin(empresa_id):
    """Actualiza una empresa desde el panel de admin"""
    data = request.json
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE empresa 
            SET nombre = %s, direccion = %s, telefono = %s, tipo_producto = %s
            WHERE id = %s
        """, (
            data.get('nombre'),
            data.get('direccion', ''),
            data.get('telefono', ''),
            data.get('tipo_producto', 'otro'),
            empresa_id
        ))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Empresa actualizada'})
    except Exception as e:
        conn.rollback()
        print(f"❌ Error actualizando empresa: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empresas/<int:empresa_id>', methods=['DELETE'])
def eliminar_empresa_admin(empresa_id):
    """Elimina (desactiva) una empresa desde el panel de admin"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) as total FROM productos WHERE empresa_id = %s AND activo = 1", (empresa_id,))
        productos_count = cursor.fetchone()[0]
        
        if productos_count > 0:
            cursor.execute("UPDATE empresa SET activo = 0 WHERE id = %s", (empresa_id,))
            message = "Empresa desactivada (tiene productos activos)"
        else:
            cursor.execute("DELETE FROM empresa WHERE id = %s", (empresa_id,))
            message = "Empresa eliminada permanentemente"
        
        conn.commit()
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        conn.rollback()
        print(f"❌ Error eliminando empresa: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/empresas/<int:empresa_id>/toggle', methods=['PUT'])
def toggle_empresa_estado(empresa_id):
    """Activa o desactiva una empresa"""
    data = request.json
    activo = data.get('activo', False)
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE empresa SET activo = %s WHERE id = %s", (1 if activo else 0, empresa_id))
        conn.commit()
        return jsonify({'success': True, 'message': f'Empresa {"activada" if activo else "desactivada"}'})
    except Exception as e:
        conn.rollback()
        print(f"❌ Error toggling empresa: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/usuarios/<int:usuario_id>/toggle', methods=['PUT'])
def toggle_usuario_estado(usuario_id):
    """Activa o desactiva un usuario"""
    data = request.json
    activo = data.get('activo', False)
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        if not activo:
            cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE rol = 'administrador' AND activo = 1")
            admin_count = cursor.fetchone()[0]
            cursor.execute("SELECT rol FROM usuarios WHERE id = %s", (usuario_id,))
            user_role = cursor.fetchone()
            
            if user_role and user_role[0] == 'administrador' and admin_count <= 1:
                return jsonify({'error': 'No se puede desactivar al único administrador'}), 400
        
        cursor.execute("UPDATE usuarios SET activo = %s WHERE id = %s", (1 if activo else 0, usuario_id))
        conn.commit()
        return jsonify({'success': True, 'message': f'Usuario {"activado" if activo else "desactivado"}'})
    except Exception as e:
        conn.rollback()
        print(f"❌ Error toggling usuario: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/usuarios/<int:usuario_id>', methods=['DELETE'])
def eliminar_usuario_admin(usuario_id):
    """Elimina un usuario (no administradores)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rol FROM usuarios WHERE id = %s", (usuario_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        if user[0] == 'administrador':
            return jsonify({'error': 'No se puede eliminar un administrador'}), 400
        
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Usuario eliminado'})
    except Exception as e:
        conn.rollback()
        print(f"❌ Error eliminando usuario: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============================================
# ===== API ENDPOINTS PARA ESTADÍSTICAS ======
# ============================================

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
        
        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE rol = 'cliente' AND activo = 1")
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

# ============================================
# ===== VERIFICAR EMAIL PARA RECUPERACIÓN ====
# ============================================

@app.route('/api/verificar-email', methods=['POST'])
def verificar_email():
    """Verifica si el email existe y devuelve el user_id"""
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email requerido'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, nombre 
            FROM usuarios 
            WHERE correo = %s AND activo = 1
        """, (email,))
        
        user = cursor.fetchone()
        
        if user:
            return jsonify({
                'found': True,
                'user_id': user['id'],
                'nombre': user['nombre']
            }), 200
        else:
            return jsonify({'found': False}), 404
            
    except Exception as e:
        print(f"❌ Error verificando email: {e}")
        return jsonify({'error': 'Error en el servidor'}), 500
    finally:
        cursor.close()
        conn.close()

# ============================================
# ===== ACTUALIZAR PASSWORD DIRECTO ==========
# ============================================

@app.route('/api/actualizar-password-directo', methods=['POST'])
def actualizar_password_directo():
    """Actualiza la contraseña directamente con user_id"""
    data = request.json
    user_id = data.get('user_id')
    new_password = data.get('new_password')
    
    if not user_id or not new_password:
        return jsonify({'error': 'Datos incompletos'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión'}), 500
    
    cursor = conn.cursor()
    try:
        hashed_password = hash_password(new_password)
        
        cursor.execute("""
            UPDATE usuarios 
            SET contrasena_hash = %s 
            WHERE id = %s AND activo = 1
        """, (hashed_password, user_id))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contraseña actualizada correctamente'
        }), 200
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error actualizando password: {e}")
        return jsonify({'error': 'Error al actualizar contraseña'}), 500
    finally:
        cursor.close()
        conn.close()

# ============================================
# ===== INICIALIZACIÓN =======================
# ============================================

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 INICIANDO SERVIDOR LOKALMARKET")
    print("=" * 50)
    
    os.makedirs(PRODUCTOS_FOLDER, exist_ok=True)
    os.makedirs(PERFILES_FOLDER, exist_ok=True)
    os.makedirs(EMPRESAS_FOLDER, exist_ok=True)
    
    print(f"📁 Carpeta de productos: {PRODUCTOS_FOLDER}")
    print(f"📁 Carpeta de perfiles: {PERFILES_FOLDER}")
    print(f"📁 Carpeta de logos empresas: {EMPRESAS_FOLDER}")
    
    print("\n📧 Configuración de email:")
    print(f"   MAIL_SERVER: {app.config['MAIL_SERVER']}")
    print(f"   MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
    print(f"   MAIL_DEFAULT_SENDER: {app.config['MAIL_DEFAULT_SENDER']}")
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Verificar y agregar columnas faltantes
        cursor.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'empresa' AND column_name = 'logo_url'")
        if cursor.fetchone()[0] == 0:
            print("\n📝 Agregando columna logo_url a tabla empresa...")
            cursor.execute("ALTER TABLE empresa ADD COLUMN logo_url VARCHAR(500) DEFAULT NULL")
            conn.commit()
            print("✅ Columna logo_url agregada")
        
        cursor.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'empresa' AND column_name = 'latitud'")
        if cursor.fetchone()[0] == 0:
            print("\n📝 Agregando columna latitud a tabla empresa...")
            cursor.execute("ALTER TABLE empresa ADD COLUMN latitud DECIMAL(10,8) DEFAULT NULL")
            conn.commit()
            print("✅ Columna latitud agregada")
        
        cursor.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'empresa' AND column_name = 'longitud'")
        if cursor.fetchone()[0] == 0:
            print("\n📝 Agregando columna longitud a tabla empresa...")
            cursor.execute("ALTER TABLE empresa ADD COLUMN longitud DECIMAL(11,8) DEFAULT NULL")
            conn.commit()
            print("✅ Columna longitud agregada")
        
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