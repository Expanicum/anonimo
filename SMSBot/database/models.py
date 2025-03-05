from enum import Enum
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

class RecurrenceType(Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"

class MessageType(Enum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    VOICE = "voice"
    ANIMATION = "animation"

@dataclass
class ScheduledMessage:
    id: int
    chat_id: int
    text: Optional[str]
    file_id: Optional[str]
    message_type: MessageType
    caption: Optional[str]
    send_time: datetime
    pin: bool
    recurrence_type: RecurrenceType
    recurrence_days: Optional[str] = None
    sent: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db(cls, row):
        """Crea un'istanza da una riga del database."""
        return cls(
            id=row[0],
            chat_id=row[1],
            text=row[2],
            file_id=row[3],
            message_type=MessageType(row[4]),
            caption=row[5],
            send_time=datetime.fromisoformat(row[6]),
            pin=bool(row[7]),
            recurrence_type=RecurrenceType(row[8]),
            recurrence_days=row[9],
            sent=bool(row[10]),
            created_at=datetime.fromisoformat(row[11]) if row[11] else None,
            updated_at=datetime.fromisoformat(row[12]) if row[12] else None
        )