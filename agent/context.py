from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Deque, List

from agent.llm_client import Message


@dataclass
class ContextEntry:
    message: Message
    expires_at: datetime


class ConversationContext:

    def __init__(self, ttl: timedelta):
        self._ttl = ttl
        self._entries: Deque[ContextEntry] = deque()

    def add(self, message: Message) -> None:
        self._entries.append(
            ContextEntry(message=message, expires_at=message.timestamp + self._ttl)
        )
        self._prune()

    def history(self) -> List[Message]:
        self._prune()
        return [entry.message for entry in self._entries]

    def _prune(self) -> None:
        now = datetime.utcnow()
        while self._entries and self._entries[0].expires_at < now:
            self._entries.popleft()
