import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
import pandas as pd
import requests
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

EMAIL_REMITENTE = os.getenv("EMAIL_REMITENTE")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_SERVIDOR = os.getenv("EMAIL_SERVIDOR_SMTP", "smtp.gmail.com")
EMAIL_PUERTO = int(os.getenv("EMAIL_PUERTO_SMTP", 465))

def enviar_correo(destinatario, nombre):
    try:
        msg = EmailMessage()
        msg['Subject'] = f'¡Feliz Cumpleaños, {nombre}!'
        msg['From'] = EMAIL_REMITENTE
        msg['To'] = destinatario
        
        contenido = f"""Hola {nombre},
        
¡Te deseamos un muy feliz cumpleaños! Esperamos que pases un día increíble rodeado de tus seres queridos.
        
Un abrazo grande."""
        
        msg.set_content(contenido)

        with smtplib.SMTP_SSL(EMAIL_SERVIDOR, EMAIL_PUERTO) as server:
            server.login(EMAIL_REMITENTE, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"[EXITO] Correo enviado a {nombre} ({destinatario})")
    except Exception as e:
        print(f"[ERROR] Error enviando correo a {nombre}: {e}")

def enviar_whatsapp(numero, nombre):
    try:
        mensaje = f"¡Hola {nombre}! 🎉 Te deseo un muy feliz cumpleaños, que pases un gran día."
        
        print(f"[INFO] Solicitando envío de WhatsApp a {nombre} al número {numero} vía API Local...")
        
        payload = {
            "numero": str(numero),
            "mensaje": mensaje
        }
        
        # Hacemos la petición a nuestra propia API en Node.js
        response = requests.post("http://localhost:3000/send", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[EXITO] WhatsApp enviado a {nombre}. ID: {data.get('messageId')}")
        else:
            print(f"[ERROR] La API Local respondió con error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] No se pudo conectar a la API Local. ¿Está corriendo el servidor Node.js (whatsapp_server.js) en el puerto 3000?")
    except Exception as e:
        print(f"[ERROR] Error enviando WhatsApp a {nombre}: {e}")

def main():
    correo_habilitado = True
    if not EMAIL_REMITENTE or EMAIL_REMITENTE == "tu_correo@gmail.com":
        print("[ADVERTENCIA] Credenciales de correo no configuradas en .env. Se omitirá el envío de correos, pero se enviarán los WhatsApps.")
        correo_habilitado = False

    archivo_excel = "registro_boletas.xlsx"
    if not os.path.exists(archivo_excel):
        print(f"[ADVERTENCIA] El archivo {archivo_excel} no existe. Aún no hay registros.")
        return

    print("Cargando base de datos de cumpleaños...")
    try:
        df = pd.read_excel(archivo_excel)
    except Exception as e:
        print(f"[ERROR] Error leyendo {archivo_excel}. Asegúrate de tener openpyxl instalado. Detalle: {e}")
        return
    
    hoy = datetime.now()
    # Extraemos día y mes para imprimir al final
    dia_mes_hoy = hoy.strftime("%d/%m")
    
    # Convertimos la columna a datetime de forma segura
    df['Fecha de nacimiento'] = pd.to_datetime(df['Fecha de nacimiento'], dayfirst=True, errors='coerce')
    
    hubo_cumpleanos = False
    
    for index, row in df.iterrows():
        nombre = row.get('Nombres', 'Desconocido')
        apellidos = row.get('Apellidos', '')
        nombre_completo = f"{nombre} {apellidos}".strip()
        fecha_nacimiento = row.get('Fecha de nacimiento')
        correo = row.get('Correo Electrónico', '')
        whatsapp = str(row.get('Celular / WhatsApp', ''))
        
        # Validar que la fecha no sea nula/inválida
        if pd.notna(fecha_nacimiento):
            # Comparamos día y mes numéricamente
            if fecha_nacimiento.day == hoy.day and fecha_nacimiento.month == hoy.month:
                hubo_cumpleanos = True
                print(f"[CUMPLEAÑOS] Hoy es el cumpleaños de {nombre}! Iniciando envíos...")
                
                if correo_habilitado and correo and pd.notna(correo):
                    enviar_correo(correo, nombre)
                
                if whatsapp and whatsapp.lower() != 'nan' and whatsapp.strip() != "":
                    # Excel a veces borra el '+' al guardar. Lo agregamos automáticamente.
                    if not whatsapp.startswith("+"):
                        whatsapp = "+" + whatsapp.strip()
                        print(f"[INFO] Se agregó el '+' automáticamente al número de {nombre} -> {whatsapp}")
                    enviar_whatsapp(whatsapp, nombre)
                
                # Pequeña pausa entre personas
                time.sleep(5)

    if not hubo_cumpleanos:
        print(f"Hoy ({dia_mes_hoy}) no hay cumpleaños registrados en la base de datos.")

if __name__ == "__main__":
    main()
