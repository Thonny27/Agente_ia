
import pandas as pd
from datetime import datetime
import os

def generar_excel():
    hoy = datetime.now()
    fecha_cumple = hoy.strftime("%d/%m/%Y")

    data = {
        "Nombre": ["Anthony (Prueba)", "Juan Pérez"],
        "Fecha de Nacimiento": [fecha_cumple, "15/01/1990"],
        "Correo": ["tu_correo_de_prueba@ejemplo.com", "juan@ejemplo.com"],
        "WhatsApp": ["+51999999999", "+51999999998"] 
    }

    df = pd.DataFrame(data)
    df.to_excel("cumpleanos.xlsx", index=False)
    print("✅ Archivo 'cumpleanos.xlsx' generado con éxito con fechas de prueba.")

if __name__ == "__main__":
    # Nos aseguramos de que corra en el directorio correcto
    if os.path.exists("requirements.txt"):
        generar_excel()
    else:
        print("⚠️ Por favor ejecuta este script desde el directorio raíz del proyecto (c:/Agente IA)")
