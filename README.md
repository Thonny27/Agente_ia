# Agente Automatizador de Cumpleaños 🎉

Este script en Python lee una base de datos en Excel y envía felicitaciones de cumpleaños de manera automática vía Correo Electrónico (SMTP) y WhatsApp (`pywhatkit`).

## Requisitos previos

1. Tener **Python 3** instalado.
2. Crear un entorno virtual (opcional pero recomendado).

## Instalación

1. Instala las dependencias necesarias ejecutando:
   ```bash
   pip install -r requirements.txt
   ```

2. Configura tus credenciales. 
   - Edita el archivo `.env` e ingresa tu correo y contraseña.
   - Si usas Gmail, necesitas generar una **Contraseña de Aplicación**:
     - Ve a la cuenta de Google > Seguridad.
     - Activa la Verificación en 2 pasos.
     - Busca "Contraseñas de aplicaciones" y crea una nueva (ej. nombre: "Script Cumpleaños"). Esa es la contraseña de 16 letras que debes poner en `EMAIL_PASSWORD`.

## Uso

1. Puedes modificar el archivo `cumpleanos.xlsx` con los datos reales de tus contactos.
   - El formato de `Fecha de Nacimiento` debe ser `DD/MM/YYYY`.
   - El formato de `WhatsApp` debe incluir el código de país (Ej: `+51999999999`).

2. Ejecuta el script principal:
   ```bash
   python main.py
   ```

**Importante sobre WhatsApp:**
La herramienta `pywhatkit` automatizará tu navegador web para enviar el mensaje. 
Por lo tanto, necesitas:
- Tener la sesión de **WhatsApp Web iniciada** en tu navegador predeterminado.
- Tu computadora debe estar encendida y desbloqueada cuando el script se ejecute.
