from __future__ import annotations

import threading
from datetime import timedelta
from typing import List, Optional, Tuple

from agent.qa_agent import QaAgent
from watcher.agent import MarketWatcherAgent
from watcher.models import Event


class Orchestrator:
    """Watcher 이벤트를 로그로 변환하고 QaAgent와 UI/CLI를 중개한다."""

    def __init__(self, watcher: MarketWatcherAgent, qa_agent: QaAgent):
        self._watcher = watcher
        self._qa_agent = qa_agent
        self._latest_event: Optional[Event] = None
        self._latest_summary: Optional[str] = None
        self._history: List[Tuple[Event, str]] = []
        self._history_lock = threading.Lock()
        self._watch_thread: Optional[threading.Thread] = None
        self._stop_signal: Optional[threading.Event] = None

    def run_once(self) -> Optional[str]:
        """단일 이벤트를 처리해 요약 문자열을 반환한다."""
        event = next(self._watcher.watch())
        summary = self._build_event_summary(event)
        self._latest_event = event
        self._latest_summary = summary
        self._record_history(event, summary)
        return summary

    def start(self) -> None:
        if self.is_running():
            return
        self._stop_signal = threading.Event()
        self._watch_thread = threading.Thread(
            target=self._watch_loop, args=(self._stop_signal,), daemon=True
        )
        self._watch_thread.start()

    def stop(self) -> None:
        if self._stop_signal:
            self._stop_signal.set()
        if self._watch_thread:
            self._watch_thread.join(timeout=2)
        self._watch_thread = None
        self._stop_signal = None

    def is_running(self) -> bool:
        return self._watch_thread is not None and self._watch_thread.is_alive()

    def _watch_loop(self, stop_signal: threading.Event) -> None:
        for event in self._watcher.watch(stop_event=stop_signal):
            summary = self._build_event_summary(event)
            self._latest_event = event
            self._latest_summary = summary
            self._record_history(event, summary)
            if stop_signal.is_set():
                break

    def _record_history(self, event: Event, summary: str) -> None:
        with self._history_lock:
            self._history.append((event, summary))

    def event_history(self) -> List[Tuple[Event, str]]:
        with self._history_lock:
            return list(self._history)

    def clear_history(self) -> None:
        with self._history_lock:
            self._history.clear()
        self._latest_event = None
        self._latest_summary = None

    def history_lines(self) -> List[str]:
        with self._history_lock:
            return [summary for _, summary in self._history]

    def latest_event(self) -> Optional[Event]:
        return self._latest_event

    def answer_follow_up(self, question: str) -> str:
        chunks = []
        for chunk in self.answer_follow_up_stream(question):
            chunks.append(chunk)
        return "".join(chunks).strip()

    def answer_follow_up_stream(self, question: str):
        """최근 히스토리를 포함해 QaAgent 스트림을 호출한다."""
        enriched_question = self._inject_history(question)
        yield from self._qa_agent.stream_answer(enriched_question)

    def _inject_history(self, question: str) -> str:
        lines = self.history_lines()
        if not lines:
            return question
        history_text = "최근 이벤트 목록:\n" + "\n".join(lines[-5:])
        return f"{history_text}\n\n사용자 질문: {question}"

    def summaries_text(self) -> str:
        return "\n".join(self.history_lines())

    def _build_event_summary(self, event: Event) -> str:
        timestamp = (event.snapshot.timestamp + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")
        symbol = _format_symbol(event.symbol)
        event_type = event.event_type.value
        change_pct = event.change_metrics.get("price_change_pct")
        volume_mult = event.change_metrics.get("volume_multiple")
        if change_pct is not None:
            direction = "상승" if change_pct > 0 else "하락" if change_pct < 0 else "변동 없음"
            metric_desc = f"직전 대비 {abs(change_pct):.2f}% {direction}했습니다."
        elif volume_mult is not None:
            metric_desc = f"거래량이 직전 대비 {volume_mult:.2f}배 증가했습니다."
        else:
            metric_desc = "조건을 충족한 이벤트입니다."
        return f"[{event_type}] [{timestamp}] [{symbol}] {metric_desc}"


def _format_symbol(symbol: str) -> str:
    symbol = symbol.upper()
    if len(symbol) > 4:
        base = symbol[:-4]
        quote = symbol[-4:]
        return f"{base}/{quote}"
    return symbol
