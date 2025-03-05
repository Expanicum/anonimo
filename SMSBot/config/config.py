import os
from dotenv import load_dotenv
from dataclasses import dataclass

# Carica le variabili d'ambiente dal file .env
load_dotenv()

@dataclass
class Config:
    token: str
    admin_id: int
    gruppo_clienti_id: int
    gruppo_reseller_id: int
    gruppo_clienti_name: str
    gruppo_reseller_name: str

# Carica i valori dalle variabili d'ambiente
config = Config(
    token=os.getenv('BOT_TOKEN'),
    admin_id=int(os.getenv('ADMIN_ID', 0)),
    gruppo_clienti_id=int(os.getenv('GRUPPO_CLIENTI_ID', 0)),
    gruppo_reseller_id=int(os.getenv('GRUPPO_RESELLER_ID', 0)),
    gruppo_clienti_name=os.getenv('GRUPPO_CLIENTI_NAME', 'Gruppo Clienti'),
    gruppo_reseller_name=os.getenv('GRUPPO_RESELLER_NAME', 'Gruppo Reseller')
)

# Validazione delle configurazioni
def validate_config():
    if not config.token:
        raise ValueError("BOT_TOKEN non impostato nel file .env")
    if config.admin_id == 0:
        raise ValueError("ADMIN_ID non impostato nel file .env")
    if config.gruppo_clienti_id == 0:
        raise ValueError("GRUPPO_CLIENTI_ID non impostato nel file .env")
    if config.gruppo_reseller_id == 0:
        raise ValueError("GRUPPO_RESELLER_ID non impostato nel file .env")

# Esegui la validazione all'importazione
validate_config()