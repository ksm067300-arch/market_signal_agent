"""Market watcher agent that translates ticker data into events."""

from __future__ import annotations

import logging
from typing import Iterable, Iterator, List, Optional
from threading import Event as ThreadEvent

from watcher.clients import build_default_client
from watcher.conditions import DEFAULT_CONDITIONS, Condition
from watcher.models import Event, MarketSnapshot

logger = logging.getLogger(__name__)


class MarketWatcherAgent:
    """Evaluates incoming market snapshots and emits triggered events."""

    def __init__(
        self,
        symbols: Iterable[str],
        conditions: Iterable[Condition] | None = None,
    ) -> None:
        self._symbols = list(symbols)
        self._client = build_default_client()
        self._cache: dict[str, MarketSnapshot] = {}
        self._conditions = list(conditions) if conditions else list(DEFAULT_CONDITIONS)

    def watch(self, stop_event: Optional[ThreadEvent] = None) -> Iterator[Event]:
        """Stream events as they are triggered."""
        for snapshot in self._client.stream_ticker(self._symbols, stop_event=stop_event):
            if stop_event and stop_event.is_set():
                break
            previous = self._cache.get(snapshot.symbol)
            self._cache[snapshot.symbol] = snapshot
            if previous is None:
                logger.info(
                    "첫 스냅샷 수신: %s price=%.2f volume=%.2f",
                    snapshot.symbol,
                    snapshot.price,
                    snapshot.volume,
                )
                continue

            change_pct = snapshot.percent_change(previous)
            volume_ratio = snapshot.volume_ratio(previous)
            logger.info(
                "틱 업데이트: %s price=%.2f volume=%.2f Δ%%=%.5f volume×=%.3f",
                snapshot.symbol,
                snapshot.price,
                snapshot.volume,
                change_pct,
                volume_ratio,
            )

            for event in self._evaluate(snapshot, previous):
                logger.info("이벤트 발생: %s (%s)", event.symbol, event.event_type.value)
                yield event

    def _evaluate(
        self, current: MarketSnapshot, previous: MarketSnapshot
    ) -> List[Event]:
        """Run all configured conditions and collect triggered events."""
        events: List[Event] = []
        for condition in self._conditions:
            event = condition(current, previous)
            if event:
                events.append(event)
        return events
