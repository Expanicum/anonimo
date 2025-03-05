import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from .models import ScheduledMessage, RecurrenceType, MessageType

class DatabaseManager:
    DB_NAME = "messages.db"

    @classmethod
    def init_db(cls):
        """Inizializza il database creando le tabelle necessarie."""
        conn = sqlite3.connect(cls.DB_NAME)
        c = conn.cursor()
        
        c.execute('DROP TABLE IF EXISTS scheduled_messages')
        
        c.execute('''
        CREATE TABLE scheduled_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            text TEXT,
            file_id TEXT,
            message_type TEXT NOT NULL,
            caption TEXT,
            send_time TIMESTAMP NOT NULL,
            pin BOOLEAN NOT NULL DEFAULT 0,
            recurrence_type TEXT NOT NULL DEFAULT 'none',
            recurrence_days TEXT,
            sent BOOLEAN NOT NULL DEFAULT 0,
            active BOOLEAN NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()

    @classmethod
    def add_scheduled_message(cls, chat_id: int, send_time: datetime, 
                            message_type: MessageType, text: Optional[str] = None,
                            file_id: Optional[str] = None, caption: Optional[str] = None,
                            pin: bool = False, recurrence_type: RecurrenceType = RecurrenceType.NONE,
                            recurrence_days: Optional[str] = None) -> ScheduledMessage:
        """Aggiunge un nuovo messaggio programmato al database."""
        conn = sqlite3.connect(cls.DB_NAME)
        c = conn.cursor()
        
        c.execute('''
        INSERT INTO scheduled_messages 
        (chat_id, send_time, message_type, text, file_id, caption, pin, 
         recurrence_type, recurrence_days)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (chat_id, send_time, message_type.value, text, file_id, caption, 
              pin, recurrence_type.value, recurrence_days))
        
        message_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return ScheduledMessage(
            id=message_id,
            chat_id=chat_id,
            text=text,
            file_id=file_id,
            message_type=message_type,
            caption=caption,
            send_time=send_time,
            pin=pin,
            recurrence_type=recurrence_type,
            recurrence_days=recurrence_days,
            sent=False,
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    @classmethod
    def get_all_scheduled_messages(cls) -> List[ScheduledMessage]:
        """Recupera tutti i messaggi programmati."""
        conn = sqlite3.connect(cls.DB_NAME)
        c = conn.cursor()
        
        c.execute('''
        SELECT * FROM scheduled_messages 
        WHERE (recurrence_type != 'none' OR sent = 0)
        ORDER BY send_time
        ''')
        messages = c.fetchall()
        
        conn.close()
        
        return [
            ScheduledMessage(
                id=msg[0],
                chat_id=msg[1],
                text=msg[2],
                file_id=msg[3],
                message_type=MessageType(msg[4]),
                caption=msg[5],
                send_time=datetime.fromisoformat(msg[6]),
                pin=bool(msg[7]),
                recurrence_type=RecurrenceType(msg[8]),
                recurrence_days=msg[9],
                sent=bool(msg[10]),
                active=bool(msg[11]),
                created_at=datetime.fromisoformat(msg[12]),
                updated_at=datetime.fromisoformat(msg[13])
            )
            for msg in messages
        ]

    @classmethod
    def get_pending_messages(cls) -> List[ScheduledMessage]:
        """Recupera i messaggi programmati da inviare."""
        conn = sqlite3.connect(cls.DB_NAME)
        c = conn.cursor()
        
        current_time = datetime.utcnow()
        weekday = str(current_time.isoweekday())
        
        # Recupera messaggi non ricorrenti non inviati e messaggi ricorrenti
        c.execute('''
        SELECT * FROM scheduled_messages 
        WHERE active = 1 
        AND (
            (sent = 0 AND send_time <= ?) 
            OR (recurrence_type = 'daily' AND sent = 1 AND time(send_time) <= time(?))
            OR (
                recurrence_type = 'weekly' 
                AND sent = 1 
                AND time(send_time) <= time(?)
                AND recurrence_days LIKE ?
            )
        )
        ORDER BY send_time
        ''', (current_time, current_time, current_time, f'%{weekday}%'))
        
        messages = c.fetchall()
        conn.close()
        
        return [
            ScheduledMessage(
                id=msg[0],
                chat_id=msg[1],
                text=msg[2],
                file_id=msg[3],
                message_type=MessageType(msg[4]),
                caption=msg[5],
                send_time=datetime.fromisoformat(msg[6]),
                pin=bool(msg[7]),
                recurrence_type=RecurrenceType(msg[8]),
                recurrence_days=msg[9],
                sent=bool(msg[10]),
                active=bool(msg[11]),
                created_at=datetime.fromisoformat(msg[12]),
                updated_at=datetime.fromisoformat(msg[13])
            )
            for msg in messages
        ]

    @classmethod
    def mark_as_sent(cls, message_id: int):
        """Marca un messaggio come inviato e aggiorna la prossima data di invio se ricorrente."""
        conn = sqlite3.connect(cls.DB_NAME)
        c = conn.cursor()
        
        # Recupera le informazioni del messaggio
        c.execute('SELECT recurrence_type, send_time FROM scheduled_messages WHERE id = ?', 
                 (message_id,))
        result = c.fetchone()
        
        if not result:
            conn.close()
            return
            
        recurrence_type, send_time = result
        current_time = datetime.utcnow()
        send_time = datetime.fromisoformat(send_time)
        
        if recurrence_type == RecurrenceType.NONE.value:
            # Per messaggi non ricorrenti, marca solo come inviato
            c.execute('''
            UPDATE scheduled_messages
            SET sent = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (message_id,))
        else:
            # Per messaggi ricorrenti, aggiorna la data di invio
            if recurrence_type == RecurrenceType.DAILY.value:
                # Se l'orario di invio è passato, passa al giorno successivo
                if send_time.time() <= current_time.time():
                    next_send_time = datetime.combine(
                        current_time.date() + timedelta(days=1),
                        send_time.time()
                    )
                else:
                    next_send_time = datetime.combine(
                        current_time.date(),
                        send_time.time()
                    )
            else:  # WEEKLY
                # Passa alla prossima settimana mantenendo lo stesso orario
                next_send_time = send_time + timedelta(days=7)
            
            c.execute('''
            UPDATE scheduled_messages
            SET send_time = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (next_send_time, message_id))
        
        conn.commit()
        conn.close()

    @classmethod
    def toggle_message_active(cls, message_id: int) -> bool:
        """Attiva/disattiva un messaggio programmato."""
        conn = sqlite3.connect(cls.DB_NAME)
        c = conn.cursor()
        
        c.execute('''
        UPDATE scheduled_messages 
        SET active = NOT active,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (message_id,))
        
        conn.commit()
        result = c.rowcount > 0
        conn.close()
        return result

    @classmethod
    def delete_old_messages(cls, days: int = 30):
        """Elimina i messaggi non ricorrenti già inviati più vecchi di X giorni."""
        conn = sqlite3.connect(cls.DB_NAME)
        c = conn.cursor()
        
        c.execute('''
        DELETE FROM scheduled_messages
        WHERE recurrence_type = 'none'
        AND sent = 1
        AND datetime(updated_at) < datetime('now', ?)
        ''', (f'-{days} days',))
        
        conn.commit()
        conn.close()