from datetime import datetime
from typing import Iterator

from agent.context import ConversationContext
from agent.llm_client import LLMClient, Message


class QaAgent:
    """후속 질문을 받아 LLM 스트리밍 응답을 반환하고 컨텍스트를 갱신한다."""

    def __init__(self, llm_client: LLMClient, context: ConversationContext):
        self._llm = llm_client
        self._context = context

    def answer(self, question: str) -> str:
        chunks = []
        for chunk in self.stream_answer(question):
            chunks.append(chunk)
        return "".join(chunks).strip()

    def stream_answer(self, question: str) -> Iterator[str]:
        """질문을 LLM으로 전달하고 토큰 단위 응답을 스트리밍한다."""
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
