"""Reusable event trigger conditions."""

from typing import Callable, Optional

from config import settings
from watcher.models import Event, EventType, MarketSnapshot

Condition = Callable[[MarketSnapshot, MarketSnapshot], Optional[Event]]


def price_drop_condition(
    current: MarketSnapshot, previous: MarketSnapshot
) -> Optional[Event]:
    """Trigger when current price drops beyond configured threshold."""
    change = current.percent_change(previous)
    if change <= -settings.MAX_PERCENT_DROP:
        return Event(
            symbol=current.symbol,
            event_type=EventType.PRICE_DROP,
            snapshot=current,
            change_metrics={"price_change_pct": change},
            triggered_at=current.timestamp,
        )
    return None


def price_rise_condition(
    current: MarketSnapshot, previous: MarketSnapshot
) -> Optional[Event]:
    """Trigger when current price rises beyond configured threshold."""
    change = current.percent_change(previous)
    if change >= settings.MAX_PERCENT_RISE:
        return Event(
            symbol=current.symbol,
            event_type=EventType.PRICE_RISE,
            snapshot=current,
            change_metrics={"price_change_pct": change},
            triggered_at=current.timestamp,
        )
    return None


def volume_spike_condition(
    current: MarketSnapshot, previous: MarketSnapshot
) -> Optional[Event]:
    """Trigger when current volume multiples exceed configured multiplier."""
    multiple = current.volume_ratio(previous)
    if multiple >= settings.VOLUME_SPIKE_MULTIPLIER:
        return Event(
            symbol=current.symbol,
            event_type=EventType.VOLUME_SPIKE,
            snapshot=current,
            change_metrics={"volume_multiple": multiple},
            triggered_at=current.timestamp,
        )
    return None


DEFAULT_CONDITIONS = [
    price_drop_condition,
    price_rise_condition,
    volume_spike_condition,
]
