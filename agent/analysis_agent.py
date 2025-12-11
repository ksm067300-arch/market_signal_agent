"""Analysis and Q&A agent that leverages LLM summaries."""

from datetime import datetime

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
        messages = self._context.history() + [
            Message(role="user", content=question, timestamp=datetime.utcnow())
        ]
        answer = self._llm.complete(messages)
        self._context.add(Message(role="assistant", content=answer, timestamp=datetime.utcnow()))
        return answer
