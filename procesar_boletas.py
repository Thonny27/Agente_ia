import os
import shutil
import pandas as pd
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Configurar la API de Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY or GEMINI_API_KEY == "tu_clave_de_gemini_api":
    print("[ERROR] Por favor configura GEMINI_API_KEY en el archivo .env")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# Configurar el modelo Vision
model = genai.GenerativeModel('gemini-3.6-flash')

# Carpetas
CARPETA_BOLETAS = "boletas"
CARPETA_PROCESADAS = os.path.join(CARPETA_BOLETAS, "procesadas")
ARCHIVO_EXCEL = "registro_boletas.xlsx"

# Crear carpetas automáticamente si no existen
os.makedirs(CARPETA_PROCESADAS, exist_ok=True)

def inicializar_excel():
    columnas = [
        "Nombres", "Apellidos", "DNI / CE", "Celular / WhatsApp", 
        "Correo Electrónico", "Fecha de nacimiento", "Archivo Boleta",
        "Identificador de comercio", "Fecha de emisión", "Tipo de servicio", 
        "Observaciones", "Código identificador de boleta", "Items comprados", 
        "Total compra", "Total IGV"
    ]
    if not os.path.exists(ARCHIVO_EXCEL):
        df = pd.DataFrame(columns=columnas)
        df.to_excel(ARCHIVO_EXCEL, index=False)
        return df
    return pd.read_excel(ARCHIVO_EXCEL)

def procesar_imagen_con_ia(ruta_imagen):
    try:
        img = Image.open(ruta_imagen)
        
        prompt = """
        Analiza esta boleta de venta o recibo. 
        Quiero que extraigas exactamente los siguientes 8 datos principales:
        1. Identificador de comercio (nombre de la tienda o restaurante)
        2. Fecha de emisión (en formato DD/MM/YYYY o como aparezca)
        3. Tipo de servicio (Por ejemplo: Delivery, Local, Para llevar)
        4. Observaciones (Por ejemplo: Rappi, PedidosYA, o Ninguna si no hay)
        5. Código identificador de boleta (número de ticket, boleta o factura)
        6. Items comprados (resumen detallado en formato "Cantidad x Nombre - Precio", separados por coma. Ejemplo: "1x Gravy Hambagu Bowl - 15.00, 1x Coca Cola - 5.00")
        7. Total compra (monto total)
        8. Total IGV (monto del impuesto, si no hay pon 0.00)
        
        Devuelve la respuesta estrictamente en este formato (separado por el símbolo |):
        Identificador | Fecha | Tipo | Observaciones | Codigo | Items | Total | IGV
        
        No agregues saludos ni explicaciones, solo la respuesta en el formato solicitado.
        """
        
        response = model.generate_content([prompt, img])
        img.close()
        respuesta_texto = response.text.strip()
        
        # Limpiar posibles saltos de linea o asteriscos
        respuesta_texto = respuesta_texto.replace("*", "").split("\n")[0]
        
        # Separar por "|"
        partes = [p.strip() for p in respuesta_texto.split("|")]
        
        if len(partes) >= 8:
            return partes[:8]
        else:
            print(f"[ADVERTENCIA] Respuesta inesperada de la IA: {respuesta_texto}")
            return ["No detectado"] * 8
            
    except Exception as e:
        print(f"[ERROR] Error al procesar la imagen {ruta_imagen}: {e}")
        return [None] * 8

def main():
    print("Iniciando procesamiento de boletas...")
    df = inicializar_excel()
    nuevos_registros = []
    
    # Buscar solo archivos de imagen
    archivos = [f for f in os.listdir(CARPETA_BOLETAS) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    
    if not archivos:
        print(f"No se encontraron boletas nuevas en la carpeta '{CARPETA_BOLETAS}/'.")
        print("¡Pega aquí tus imágenes y vuelve a ejecutar este script!")
        return

    for archivo in archivos:
        ruta_origen = os.path.join(CARPETA_BOLETAS, archivo)
        ruta_destino = os.path.join(CARPETA_PROCESADAS, archivo)
        
        print(f"\n-> Analizando con IA: {archivo} ...")
        
        pedido, cantidad, precio = procesar_imagen_con_ia(ruta_origen)
        
        if pedido:
            print(f"   [ÉXITO] Pedido: {pedido} | Cant: {cantidad} | Precio: {precio}")
            nuevos_registros.append({
                "Archivo": archivo,
                "Pedido": pedido,
                "Cantidad": cantidad,
                "Precio": precio
            })
            
            # Mover archivo a procesadas para no leerlo dos veces
            shutil.move(ruta_origen, ruta_destino)
            
    if nuevos_registros:
        nuevo_df = pd.DataFrame(nuevos_registros)
        df = pd.concat([df, nuevo_df], ignore_index=True)
        df.to_excel(ARCHIVO_EXCEL, index=False)
        print(f"\n✅ ¡Se guardaron {len(nuevos_registros)} boletas en {ARCHIVO_EXCEL}!")

if __name__ == "__main__":
    main()
