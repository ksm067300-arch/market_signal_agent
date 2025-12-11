from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class EventType(str, Enum):
    PRICE_DROP = "PRICE_DROP"
    PRICE_RISE = "PRICE_RISE"
    VOLUME_SPIKE = "VOLUME_SPIKE"


@dataclass
class MarketSnapshot:
    symbol: str
    price: float
    volume: float
    timestamp: datetime

    def percent_change(self, previous: "MarketSnapshot") -> float:
        if previous.price == 0:
            return 0.0
        return ((self.price - previous.price) / previous.price) * 100

    def volume_ratio(self, previous: "MarketSnapshot") -> float:
        if previous.volume == 0:
            return float("inf")
        return self.volume / previous.volume


@dataclass
class Event:
    symbol: str
    event_type: EventType
    snapshot: MarketSnapshot
    change_metrics: Dict[str, float]
    triggered_at: datetime
    description: Optional[str] = None
