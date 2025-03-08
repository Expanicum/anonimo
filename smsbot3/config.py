import os
from dotenv import load_dotenv
from aiogram.fsm.state import State, StatesGroup
import pytz
from typing import Dict, List
from pathlib import Path
import sys

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Configurazione directory
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
MEDIA_DIR = BASE_DIR / "media"
DB_DIR = BASE_DIR / "database"
BACKUP_DIR = BASE_DIR / "backups"

# Crea le directory necessarie
for dir_path in [LOGS_DIR, MEDIA_DIR, DB_DIR, BACKUP_DIR]:
    dir_path.mkdir(exist_ok=True)

# Token del bot e ID amministratore
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# ID e nomi dei gruppi
GRUPPO_1_ID = int(os.getenv('GRUPPO_1_ID'))
GRUPPO_2_ID = int(os.getenv('GRUPPO_2_ID'))
GRUPPO_1_NAME = os.getenv('GRUPPO_1_NAME')
GRUPPO_2_NAME = os.getenv('GRUPPO_2_NAME')

# Configurazione timezone
TIMEZONE = pytz.timezone(os.getenv('TIMEZONE', 'UTC'))

# Configurazione media
MAX_MEDIA_SIZE = int(os.getenv('MAX_MEDIA_SIZE', 20 * 1024 * 1024))  # Default 20MB
MAX_MEDIA_GROUP_SIZE = int(os.getenv('MAX_MEDIA_GROUP_SIZE', 10))

# Tipi di media consentiti
ALLOWED_MEDIA_TYPES = [
    'image/jpeg', 'image/png', 'image/gif',
    'video/mp4', 'video/mpeg',
    'application/pdf', 'application/zip',
    'application/x-rar-compressed',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
]

# Formati datetime accettati
DATETIME_FORMATS = [
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
    '%d/%m/%Y %H:%M:%S',
    '%d/%m/%Y %H:%M'
]

# Giorni della settimana
WEEKDAYS = {
    1: "Lunedì",
    2: "Martedì",
    3: "Mercoledì",
    4: "Giovedì",
    5: "Venerdì",
    6: "Sabato",
    7: "Domenica"
}

# Stati FSM
class States(StatesGroup):
    WAITING_GROUP = State()
    WAITING_MESSAGE = State()
    WAITING_PIN = State()
    SCHEDULE_GROUP = State()
    SCHEDULE_TIME = State()
    SCHEDULE_RECURRENCE = State()
    SCHEDULE_DAYS = State()
    EDIT_MESSAGE = State()
    EDIT_TIME = State()
    EDIT_RECURRENCE = State()
    EDIT_DAYS = State()

# Messaggi di sistema
MESSAGES = {
    'welcome': (
        "👋 Benvenuto nel bot di gestione messaggi!\n\n"
        "🔹 Puoi inviare messaggi immediati o programmarli\n"
        "🔹 Supporta testo, foto, video e documenti\n"
        "🔹 Gestisce ricorrenze giornaliere e settimanali\n"
        "🔹 Permette di pinnare i messaggi\n\n"
        "Seleziona un'opzione:"
    ),
    'unauthorized': "⛔️ Non sei autorizzato ad usare questo bot.",
    'error': "❌ Si è verificato un errore. Riprova.",
    'media_too_large': f"❌ Il file è troppo grande. Dimensione massima: {int(os.getenv('MAX_MEDIA_SIZE', 20*1024*1024)/1024/1024)}MB",
    'invalid_media_type': "❌ Tipo di file non supportato.",
    'backup_success': "✅ Backup completato con successo!",
    'backup_error': "❌ Errore durante il backup.",
    'restore_success': "✅ Ripristino completato con successo!",
    'restore_error': "❌ Errore durante il ripristino.",
    'env_error': "❌ Errore nella configurazione delle variabili d'ambiente. Controlla il file .env"
}

# Validazione configurazione
def validate_config():
    required_vars = ['BOT_TOKEN', 'ADMIN_ID', 'GRUPPO_1_ID', 'GRUPPO_2_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        error_msg = f"Variabili d'ambiente mancanti: {', '.join(missing_vars)}"
        raise ValueError(error_msg)

# Valida la configurazione all'importazione
try:
    validate_config()
except ValueError as e:
    print(f"Errore di configurazione: {e}")
    sys.exit(1)