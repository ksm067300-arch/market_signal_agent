"""Data models used by the Market Watcher agent."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class EventType(str, Enum):
    """Enumeration of supported event triggers."""

    PRICE_DROP = "PRICE_DROP"
    PRICE_RISE = "PRICE_RISE"
    VOLUME_SPIKE = "VOLUME_SPIKE"


@dataclass
class MarketSnapshot:
    """Represents a single observed point in time for a market."""

    symbol: str
    price: float
    volume: float
    timestamp: datetime

    def percent_change(self, previous: "MarketSnapshot") -> float:
        """Return percent price change vs. previous snapshot."""
        if previous.price == 0:
            return 0.0
        return ((self.price - previous.price) / previous.price) * 100

    def volume_ratio(self, previous: "MarketSnapshot") -> float:
        """Return volume multiple relative to previous snapshot."""
        if previous.volume == 0:
            return float("inf")
        return self.volume / previous.volume


@dataclass
class Event:
    """Structured event emitted when a trigger condition is met."""

    symbol: str
    event_type: EventType
    snapshot: MarketSnapshot
    change_metrics: Dict[str, float]
    triggered_at: datetime
    description: Optional[str] = None
