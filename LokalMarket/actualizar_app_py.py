#!/usr/bin/env python3
import re

app_file = 'app.py'

with open(app_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar la función serve_files y reemplazarla
old_route = '''@app.route('/<path:filename>')
def serve_files(filename):
    if filename.endswith('.html'):
        try:
            return render_template(filename)
        except:
            return f"Archivo {filename} no encontrado", 404
    return send_from_directory('static', filename)'''

new_routes = '''@app.route('/<path:filename>')
def serve_files(filename):
    if filename.endswith('.html'):
        try:
            return render_template(filename)
        except:
            return f"Archivo {filename} no encontrado", 404
    return send_from_directory('static', filename)

@app.route('/<page>')
def serve_page(page):
    """Sirve páginas sin extensión .html en la URL"""
    try:
        return render_template(f'{page}.html')
    except:
        return render_template('inicio.html')'''

# Reemplazar
content = content.replace(old_route, new_routes)

# Asegurar que el index esté correcto
old_index = "@app.route('/')\ndef index():\n    return render_template('inicio.html')"
new_index = "@app.route('/')\ndef index():\n    \"\"\"Página de inicio\"\"\"\n    return render_template('inicio.html')"

content = content.replace(old_index, new_index)

with open(app_file, 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ app.py actualizado correctamente')
print('Se agregó la ruta dinámica para páginas sin .html')