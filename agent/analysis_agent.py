"""Analysis and Q&A agent that leverages LLM summaries."""

from datetime import datetime
from typing import Iterator

from agent.context import ConversationContext
from agent.llm_client import LLMClient, Message
from watcher.models import Event


class AnalysisAgent:
    """Transforms watcher events into summaries and answers questions."""

    def __init__(self, llm_client: LLMClient, context: ConversationContext):
        self._llm = llm_client
        self._context = context

    def summarize_event(self, event: Event) -> str:
        prompt = (
            "You are a cautious crypto market analyst. "
            "Summarize the situation with context, recent trend, and risks.\n"
            f"Symbol: {event.symbol}\n"
            f"Event type: {event.event_type}\n"
            f"Price change (%): {event.change_metrics.get('price_change_pct', 'n/a')}\n"
            f"Volume multiple: {event.change_metrics.get('volume_multiple', 'n/a')}\n"
            f"Timestamp: {event.snapshot.timestamp.isoformat()}Z\n"
        )
        messages = self._context.history() + [
            Message(role="user", content=prompt, timestamp=datetime.utcnow())
        ]
        summary = self._llm.complete(messages)
        self._context.add(Message(role="assistant", content=summary, timestamp=datetime.utcnow()))
        return summary

    def answer_question(self, question: str) -> str:
        chunks = []
        for chunk in self.answer_question_stream(question):
            chunks.append(chunk)
        return "".join(chunks).strip()

    def answer_question_stream(self, question: str) -> Iterator[str]:
        user_prompt = Message(role="user", content=question, timestamp=datetime.utcnow())
        messages = self._context.history() + [user_prompt]
        buffer: list[str] = []
        for chunk in self._llm.stream_complete(messages):
            buffer.append(chunk)
            yield chunk

        full_answer = "".join(buffer).strip()
        self._context.add(
            Message(role="assistant", content=full_answer, timestamp=datetime.utcnow())
        )
