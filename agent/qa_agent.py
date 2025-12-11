"""Agent dedicated to handling Q&A with streaming support."""

from datetime import datetime
from typing import Iterator

from agent.context import ConversationContext
from agent.llm_client import LLMClient, Message


class QaAgent:
    """Streams answers for user questions and updates context."""

    def __init__(self, llm_client: LLMClient, context: ConversationContext):
        self._llm = llm_client
        self._context = context

    def answer(self, question: str) -> str:
        chunks = []
        for chunk in self.stream_answer(question):
            chunks.append(chunk)
        return "".join(chunks).strip()

    def stream_answer(self, question: str) -> Iterator[str]:
        user_prompt = Message(role="user", content=question, timestamp=datetime.utcnow())
        messages = self._context.history() + [user_prompt]
        buffer: list[str] = []
        for chunk in self._llm.stream_complete(messages):
            buffer.append(chunk)
            yield chunk
        full_answer = "".join(buffer).strip()
        if full_answer:
            self._context.add(
                Message(role="assistant", content=full_answer, timestamp=datetime.utcnow())
            )
