const express = require('express');
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

const app = express();
app.use(express.json());

const port = 3000;

// Inicializa el cliente de WhatsApp usando autenticación local (guarda la sesión)
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true, // Se ejecuta en segundo plano
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

// Cuando genera el código QR, lo muestra en la terminal
client.on('qr', (qr) => {
    console.log('\n======================================================');
    console.log('¡Escanea este código QR con tu WhatsApp para iniciar!');
    console.log('======================================================\n');
    qrcode.generate(qr, { small: true });
});

// Cuando la sesión esté lista
client.on('ready', () => {
    console.log('✅ Cliente de WhatsApp listo y conectado.');
});

client.on('authenticated', () => {
    console.log('✅ Sesión autenticada correctamente.');
});

client.on('auth_failure', msg => {
    console.error('❌ Error de autenticación:', msg);
});

// Iniciamos el cliente de WhatsApp
client.initialize();

// Endpoint para enviar mensaje
app.post('/send', async (req, res) => {
    try {
        const { numero, mensaje } = req.body;
        
        if (!numero || !mensaje) {
            return res.status(400).json({ error: 'Falta número o mensaje' });
        }

        // whatsapp-web.js requiere el formato: [codigo de pais][numero]@c.us
        // Limpiamos el número de cualquier caracter raro o el signo '+'
        const numeroLimpio = numero.replace(/\D/g, ''); 
        const chatId = `${numeroLimpio}@c.us`;

        console.log(`[API] Enviando mensaje a ${chatId}...`);
        
        const response = await client.sendMessage(chatId, mensaje);
        
        // Simplemente devolvemos éxito para evitar problemas leyendo propiedades
        res.json({ success: true, messageId: "Enviado con éxito" });
    } catch (error) {
        console.error('❌ Error enviando mensaje:', error);
        res.status(500).json({ error: error.message });
    }
});

app.listen(port, () => {
    console.log(`🚀 API Local de WhatsApp corriendo en http://localhost:${port}`);
    console.log('⏳ Esperando a que el cliente de WhatsApp inicie...');
});
