from enum import Enum
from datetime import datetime
from typing import Optional, List

class MessageType(Enum):
    """Tipi di messaggio supportati."""
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"

class RecurrenceType(Enum):
    """Tipi di ricorrenza per i messaggi programmati."""
    ONCE = "once"      # Una volta sola
    DAILY = "daily"    # Ogni giorno
    WEEKLY = "weekly"  # Settimanale (giorni specifici)

class ScheduledMessage:
    """Modello per i messaggi programmati."""
    def __init__(
        self,
        id: int,
        chat_id: int,
        message_type: MessageType,
        send_time: datetime,
        text: Optional[str] = None,
        media: Optional[str] = None,
        caption: Optional[str] = None,
        pin: bool = False,
        active: bool = True,
        recurrence_type: str = "once",
        recurrence_days: str = "",
        schedule_hour: int = 0,
        schedule_minute: int = 0
    ):
        self.id = id
        self.chat_id = chat_id
        self.message_type = MessageType(message_type)
        self.send_time = send_time
        self.text = text
        self.media = media
        self.caption = caption
        self.pin = pin
        self.active = active
        self.recurrence_type = recurrence_type
        self.recurrence_days = recurrence_days
        self.schedule_hour = schedule_hour
        self.schedule_minute = schedule_minute

    @classmethod
    def from_db_row(cls, row: tuple) -> 'ScheduledMessage':
        """Crea un'istanza da una riga del database."""
        return cls(
            id=row[0],
            chat_id=row[1],
            message_type=row[2],
            send_time=datetime.fromisoformat(row[3]),
            text=row[4],
            media=row[5],
            caption=row[6],
            pin=bool(row[7]),
            active=bool(row[8]),
            recurrence_type=row[9],
            recurrence_days=row[10],
            schedule_hour=row[11],
            schedule_minute=row[12]
        )

    def to_dict(self) -> dict:
        """Converte l'oggetto in dizionario."""
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'message_type': self.message_type.value,
            'send_time': self.send_time.isoformat(),
            'text': self.text,
            'media': self.media,
            'caption': self.caption,
            'pin': self.pin,
            'active': self.active,
            'recurrence_type': self.recurrence_type,
            'recurrence_days': self.recurrence_days,
            'schedule_hour': self.schedule_hour,
            'schedule_minute': self.schedule_minute
        }