import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union
from .models import ScheduledMessage, MessageType

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestisce le operazioni del database."""
    
    DB_PATH = Path(__file__).parent / "messages.db"
    
    @classmethod
    def init_db(cls) -> None:
        """Inizializza il database e crea le tabelle necessarie."""
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Creazione tabella messaggi programmati
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scheduled_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER NOT NULL,
                        message_type TEXT NOT NULL,
                        send_time TIMESTAMP NOT NULL,
                        text TEXT,
                        media TEXT,
                        caption TEXT,
                        pin BOOLEAN NOT NULL DEFAULT 0,
                        active BOOLEAN NOT NULL DEFAULT 1,
                        recurrence_type TEXT NOT NULL DEFAULT 'once',
                        recurrence_days TEXT DEFAULT '',
                        schedule_hour INTEGER DEFAULT 0,
                        schedule_minute INTEGER DEFAULT 0
                    )
                """)
                
                conn.commit()
                logger.info("Database inizializzato con successo")
                
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione del database: {e}")
            raise

    @classmethod
    def add_scheduled_message(cls, message_data: dict) -> int:
        """Aggiunge un nuovo messaggio programmato al database."""
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO scheduled_messages (
                        chat_id, message_type, send_time, text, media, 
                        caption, pin, active, recurrence_type, recurrence_days,
                        schedule_hour, schedule_minute
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    message_data['chat_id'],
                    message_data['message_type'].value,
                    message_data['send_time'].isoformat(),
                    message_data.get('text'),
                    message_data.get('media'),
                    message_data.get('caption'),
                    message_data['pin'],
                    message_data['active'],
                    message_data['recurrence_type'],
                    message_data.get('recurrence_days', ''),
                    message_data['schedule_hour'],
                    message_data['schedule_minute']
                ))
                
                message_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Aggiunto nuovo messaggio programmato con ID: {message_id}")
                return message_id
                
        except Exception as e:
            logger.error(f"Errore nell'aggiunta del messaggio programmato: {e}")
            raise

    @classmethod
    def get_pending_messages(cls) -> List[ScheduledMessage]:
        """Recupera tutti i messaggi programmati attivi."""
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM scheduled_messages 
                    WHERE active = 1 
                    ORDER BY send_time ASC
                """)
                
                return [ScheduledMessage.from_db_row(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Errore nel recupero dei messaggi programmati: {e}")
            return []

    @classmethod
    def get_filtered_messages(cls, chat_id: Optional[int] = None) -> List[ScheduledMessage]:
        """Recupera i messaggi filtrati per gruppo."""
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                
                if chat_id:
                    cursor.execute("""
                        SELECT * FROM scheduled_messages 
                        WHERE chat_id = ? 
                        ORDER BY send_time DESC
                    """, (chat_id,))
                else:
                    cursor.execute("""
                        SELECT * FROM scheduled_messages 
                        ORDER BY send_time DESC
                    """)
                
                return [ScheduledMessage.from_db_row(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Errore nel recupero dei messaggi filtrati: {e}")
            return []

    @classmethod
    def get_message_by_id(cls, message_id: int) -> Optional[ScheduledMessage]:
        """Recupera un messaggio specifico per ID."""
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM scheduled_messages 
                    WHERE id = ?
                """, (message_id,))
                
                row = cursor.fetchone()
                return ScheduledMessage.from_db_row(row) if row else None
                
        except Exception as e:
            logger.error(f"Errore nel recupero del messaggio {message_id}: {e}")
            return None

    @classmethod
    def toggle_message(cls, message_id: int) -> bool:
        """Attiva/disattiva un messaggio programmato."""
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE scheduled_messages 
                    SET active = NOT active 
                    WHERE id = ?
                """, (message_id,))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Errore nel toggle del messaggio {message_id}: {e}")
            return False

    @classmethod
    def delete_message(cls, message_id: int) -> bool:
        """Elimina un messaggio programmato."""
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM scheduled_messages 
                    WHERE id = ?
                """, (message_id,))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Errore nell'eliminazione del messaggio {message_id}: {e}")
            return False

    @classmethod
    def update_send_time(cls, message_id: int, new_time: datetime) -> bool:
        """Aggiorna l'orario di invio di un messaggio."""
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE scheduled_messages 
                    SET send_time = ? 
                    WHERE id = ?
                """, (new_time.isoformat(), message_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento dell'orario per il messaggio {message_id}: {e}")
            return False

    @classmethod
    def mark_as_sent(cls, message_id: int) -> bool:
        """Marca un messaggio come inviato (disattivandolo)."""
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE scheduled_messages 
                    SET active = 0 
                    WHERE id = ? AND recurrence_type = 'once'
                """, (message_id,))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Errore nella marcatura come inviato del messaggio {message_id}: {e}")
            return False