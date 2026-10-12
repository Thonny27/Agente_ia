import os
import shutil
import re
import requests
from flask import Flask, request, jsonify, send_from_directory, session, redirect, send_file
import pandas as pd
from datetime import datetime
from io import BytesIO

# Importamos la lógica de IA que ya creamos
from procesar_boletas import procesar_imagen_con_ia, inicializar_excel, ARCHIVO_EXCEL, CARPETA_BOLETAS, CARPETA_PROCESADAS

app = Flask(__name__, static_folder='landing_page', template_folder='landing_page')
app.secret_key = 'super_secret_bento_key_2026'

CLIENTES_EXCEL = "cumpleanos.xlsx"

os.makedirs(CARPETA_BOLETAS, exist_ok=True)
os.makedirs(CARPETA_PROCESADAS, exist_ok=True)

def generar_detalle_items(df):
    if df.empty or 'Items comprados' not in df.columns:
        return pd.DataFrame(columns=[
            'Código identificador de boleta', 'Fecha de emisión', 'Identificador de comercio',
            'Nombres', 'Apellidos', 'DNI / CE', 'Celular / WhatsApp',
            'Cantidad', 'Producto / Item', 'Precio', 'Item Completo', 'Total compra'
        ])
    
    registros_detalle = []
    for _, row in df.iterrows():
        items_str = str(row.get('Items comprados', ''))
        if not items_str or items_str.lower() in ['nan', 'none', 'ninguno', '']:
            continue
            
        items_lista = [it.strip() for it in items_str.split(',') if it.strip()]
        for it in items_lista:
            cantidad = '1'
            precio = ''
            producto = it
            
            m_qty = re.match(r'^(\d+)\s*[xX]\s*(.*)$', producto)
            if m_qty:
                cantidad = m_qty.group(1)
                producto = m_qty.group(2).strip()
                
            m_price = re.search(r'\s*-\s*(?:S/?\.?\s*)?([\d\.,]+)$', producto)
            if m_price:
                precio = m_price.group(1)
                producto = producto[:m_price.start()].strip()
                
            registros_detalle.append({
                'Código identificador de boleta': row.get('Código identificador de boleta', ''),
                'Fecha de emisión': row.get('Fecha de emisión', ''),
                'Identificador de comercio': row.get('Identificador de comercio', ''),
                'Nombres': row.get('Nombres', ''),
                'Apellidos': row.get('Apellidos', ''),
                'DNI / CE': row.get('DNI / CE', ''),
                'Celular / WhatsApp': row.get('Celular / WhatsApp', ''),
                'Cantidad': cantidad,
                'Producto / Item': producto,
                'Precio': precio,
                'Item Completo': it,
                'Total compra': row.get('Total compra', '')
            })
            
    return pd.DataFrame(registros_detalle)

def autoajustar_columnas(writer):
    for sheetname in writer.sheets:
        ws = writer.sheets[sheetname]
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 55)

# Usuarios multi-empresa. El key es el usuario y el value es la contraseña.
# El 'username' se usará para buscar dentro del "Identificador de comercio" de la boleta.
# 'admin' es el superusuario que ve todo.
USUARIOS_SISTEMA = {
    'bentobox': 'bento123',
    'kfc': 'kfc123',
    'starbucks': 'starbucks123',
    'admin': 'admin123'
}

@app.route('/')
def index():
    return send_from_directory('landing_page', 'index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').lower().strip()
        password = request.form.get('password')
        
        if username in USUARIOS_SISTEMA and USUARIOS_SISTEMA[username] == password:
            session['logged_in'] = True
            session['username'] = username
            return redirect('/admin')
        else:
            return redirect('/login?error=1')
    return send_from_directory('landing_page', 'login.html')

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect('/login')
    return send_from_directory('landing_page', 'admin.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/login')

@app.route('/api/boletas')
def api_boletas():
    if not session.get('logged_in'):
        return jsonify({"error": "No autorizado"}), 401
    
    df = inicializar_excel()
    df = df.fillna('')
    
    username = session.get('username', '')
    if username != 'admin' and not df.empty and 'Identificador de comercio' in df.columns:
        # Filtra las boletas donde el identificador contenga el nombre de usuario (ej: 'bentobox')
        df = df[df['Identificador de comercio'].str.contains(username, case=False, na=False)]
        
    data = df.to_dict('records')
    data.reverse() # Invertir para que los más nuevos salgan primero
    return jsonify(data)

@app.route('/api/exportar')
def exportar_boletas():
    if not session.get('logged_in'):
        return redirect('/login')
        
    df = inicializar_excel()
    username = session.get('username', '')
    
    if username != 'admin' and not df.empty and 'Identificador de comercio' in df.columns:
        df = df[df['Identificador de comercio'].str.contains(username, case=False, na=False)]
        
    if df.empty:
        return "No hay datos para exportar", 404

    # Generar el Excel en memoria con las tres hojas
    output = BytesIO()
    
    df_detalle = generar_detalle_items(df)
    
    df_usuarios = df.groupby('DNI / CE').agg(
        Nombres=('Nombres', 'first'),
        Apellidos=('Apellidos', 'first'),
        Celular=('Celular / WhatsApp', 'first'),
        Total_Compras=('DNI / CE', 'count'),
        Producto_Mas_Pedido=('Items comprados', lambda x: x.mode()[0] if not x.mode().empty else "Ninguno")
    ).reset_index()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Boletas', index=False)
        df_detalle.to_excel(writer, sheet_name='Detalle_Productos', index=False)
        df_usuarios.to_excel(writer, sheet_name='Resumen_Usuarios', index=False)
        autoajustar_columnas(writer)
        
    output.seek(0)
    return send_file(output, download_name=f"boletas_{username}.xlsx", as_attachment=True)

@app.route('/submit', methods=['POST'])
def submit():
    try:
        nombres = request.form.get('nombres')
        apellidos = request.form.get('apellidos')
        dni = request.form.get('dni')
        telefono = request.form.get('telefono')
        correo = request.form.get('correo')
        cumpleanos = request.form.get('cumpleanos')
        boleta = request.files.get('boleta')

        if not all([nombres, apellidos, dni, telefono, correo, boleta]):
            return jsonify({"error": "Faltan datos obligatorios en el formulario"}), 400

        # Formatear fecha
        fecha_corta = ""
        if cumpleanos:
            if "-" in cumpleanos:
                partes = cumpleanos.split("-")
                fecha_corta = f"{partes[2]}/{partes[1]}"
            else:
                fecha_corta = cumpleanos

        # Asegurar que las carpetas existan (por si el usuario las borró manualmente)
        os.makedirs(CARPETA_BOLETAS, exist_ok=True)
        os.makedirs(CARPETA_PROCESADAS, exist_ok=True)

        # Guardar la boleta físicamente
        filename = boleta.filename.replace(" ", "_")
        ruta_boleta = os.path.join(CARPETA_BOLETAS, filename)
        boleta.save(ruta_boleta)

        # Procesar con IA
        datos_ia = procesar_imagen_con_ia(ruta_boleta)
        identificador, fecha, tipo, observaciones, codigo, items, total, igv = datos_ia

        df_boletas = inicializar_excel()

        # Validación de duplicado
        if codigo != "No detectado" and "Código identificador de boleta" in df_boletas.columns:
            if not df_boletas[df_boletas["Código identificador de boleta"].astype(str) == str(codigo)].empty:
                os.remove(ruta_boleta) # Limpiar archivo
                return jsonify({"error": "Esta boleta ya fue registrada anteriormente."}), 400

        compras_previas = 0
        if "DNI / CE" in df_boletas.columns:
            compras_previas = df_boletas[df_boletas["DNI / CE"] == dni].shape[0]
        num_compra = compras_previas + 1

        estado_satisfaccion = request.form.get('estado_satisfaccion', 'Excelente (100%)')

        nuevo_registro = pd.DataFrame([{
            "Nombres": nombres,
            "Apellidos": apellidos,
            "DNI / CE": dni,
            "Celular / WhatsApp": telefono,
            "Correo Electrónico": correo,
            "Fecha de nacimiento": fecha_corta,
            "Archivo Boleta": filename,
            "Identificador de comercio": identificador,
            "Fecha de emisión": fecha,
            "Tipo de servicio": tipo,
            "Observaciones": observaciones,
            "Código identificador de boleta": codigo,
            "Items comprados": items,
            "Total compra": total,
            "Total IGV": igv,
            "Satisfacción Servicio": estado_satisfaccion
        }])
        
        df_boletas = pd.concat([df_boletas, nuevo_registro], ignore_index=True)
        
        # Agrupar por DNI para resumen de usuarios
        df_usuarios = df_boletas.groupby('DNI / CE').agg(
            Nombres=('Nombres', 'first'),
            Apellidos=('Apellidos', 'first'),
            Celular=('Celular / WhatsApp', 'first'),
            Total_Compras=('DNI / CE', 'count'),
            Producto_Mas_Pedido=('Items comprados', lambda x: x.mode()[0] if not x.mode().empty else "Ninguno")
        ).reset_index()

        df_detalle = generar_detalle_items(df_boletas)
        with pd.ExcelWriter(ARCHIVO_EXCEL, engine='openpyxl') as writer:
            df_boletas.to_excel(writer, sheet_name='Boletas', index=False)
            df_detalle.to_excel(writer, sheet_name='Detalle_Productos', index=False)
            df_usuarios.to_excel(writer, sheet_name='Resumen_Usuarios', index=False)
            autoajustar_columnas(writer)

        # Lógica de mensajes WSP según número de compra
        mensaje_wsp = ""
        if num_compra == 1:
            mensaje_wsp = f"¡Hola {nombres}! Gracias por tu primera compra. Como agradecimiento, tienes un descuento del 20% en tu próximo pedido. ¡Solo es canjeable si nos pides por este medio (WhatsApp)!"
        elif num_compra == 2:
            mensaje_wsp = f"¡Hola {nombres}! Queremos agradecerte por tu segunda compra. ¡Valoramos mucho tu preferencia y confianza en nosotros!"
        elif num_compra == 5:
            mensaje_wsp = f"¡Hola {nombres}! ¡Has alcanzado tu 5ta compra! Como recompensa, te regalamos una nueva promoción especial. ¡Escríbenos por aquí para canjearla!"

        if mensaje_wsp and telefono:
            num_wsp = str(telefono).strip()
            # Quitar posibles espacios u otros caracteres, dejando solo números y el +
            num_wsp = "".join(c for c in num_wsp if c.isdigit() or c == "+")
            
            if not num_wsp.startswith("+"):
                # Si el número tiene 9 dígitos (formato estándar de Perú) le agregamos el código +51
                if len(num_wsp) == 9:
                    num_wsp = "+51" + num_wsp
                else:
                    num_wsp = "+" + num_wsp
            try:
                requests.post("http://localhost:3000/send", json={"numero": num_wsp, "mensaje": mensaje_wsp}, timeout=5)
            except Exception as e:
                print(f"[ERROR] No se pudo enviar WhatsApp: {e}")
        
        # Mover a procesadas
        shutil.move(ruta_boleta, os.path.join(CARPETA_PROCESADAS, filename))

        return jsonify({"success": True, "message": "Promoción activada."})

    except Exception as e:
        print(f"[ERROR] API Web: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Iniciando Servidor Web Bentobox en http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
