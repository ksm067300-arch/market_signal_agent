from __future__ import annotations

import json
import logging
import queue
import random
import threading
import time
from datetime import datetime, timezone
from threading import Event as ThreadEvent
from typing import Iterable, Iterator, Optional, Protocol
from urllib import error, request

from config import settings
from watcher.models import MarketSnapshot

try:
    import websocket  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    websocket = None


class MarketDataClient(Protocol):
    def stream_ticker(
        self, symbols: Iterable[str], stop_event: ThreadEvent | None = None
    ) -> Iterator[MarketSnapshot]:
        ...


class MockBinanceClient:
    def __init__(self, *, poll_interval_seconds: float):
        self._poll_interval = poll_interval_seconds

    def stream_ticker(
        self, symbols: Iterable[str], stop_event: ThreadEvent | None = None
    ) -> Iterator[MarketSnapshot]:
        base_prices = {symbol: 30000.0 for symbol in symbols}
        base_volumes = {symbol: 1000.0 for symbol in symbols}

        while True:
            if stop_event and stop_event.is_set():
                return
            for symbol in symbols:
                if stop_event and stop_event.is_set():
                    return
                base_prices[symbol] *= 1 + random.uniform(-0.03, 0.03)
                base_volumes[symbol] *= 1 + random.uniform(-0.3, 0.3)
                yield MarketSnapshot(
                    symbol=symbol,
                    price=round(base_prices[symbol], 2),
                    volume=max(round(base_volumes[symbol], 2), 1.0),
                    timestamp=datetime.utcnow(),
                )

            time.sleep(self._poll_interval)


class BinanceRestClient:
    def __init__(self, *, base_url: str, poll_interval_seconds: float):
        self._base_url = base_url.rstrip("/")
        self._poll_interval = poll_interval_seconds

    def stream_ticker(
        self, symbols: Iterable[str], stop_event: ThreadEvent | None = None
    ) -> Iterator[MarketSnapshot]:
        while True:
            if stop_event and stop_event.is_set():
                return
            for symbol in symbols:
                if stop_event and stop_event.is_set():
                    return
                snapshot = self._fetch_snapshot(symbol)
                if snapshot is not None:
                    yield snapshot
            time.sleep(self._poll_interval)

    def _fetch_snapshot(self, symbol: str) -> Optional[MarketSnapshot]:
        endpoint = f"{self._base_url}/api/v3/ticker/24hr?symbol={symbol.upper()}"
        try:
            with request.urlopen(endpoint, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except error.URLError as exc:
            logging.warning("REST request failed for %s: %s", symbol, exc)
            return None

        try:
            price = float(payload["lastPrice"])
            volume = float(payload["volume"])
        except (KeyError, ValueError) as exc:
            logging.warning("Malformed payload for %s: %s", symbol, exc)
            return None

        return MarketSnapshot(
            symbol=symbol,
            price=price,
            volume=volume,
            timestamp=datetime.utcnow(),
        )


class BinanceWebSocketClient:
    def __init__(self, *, stream_base_url: str, reconnect_delay_seconds: float):
        if websocket is None:
            raise RuntimeError(
                "websocket-client is required for the WebSocket backend. "
                "Install it with `pip install websocket-client`."
            )
        self._stream_base_url = stream_base_url.rstrip("/")
        self._reconnect_delay = reconnect_delay_seconds

    def stream_ticker(
        self, symbols: Iterable[str], stop_event: ThreadEvent | None = None
    ) -> Iterator[MarketSnapshot]:
        symbol_list = [symbol.upper() for symbol in symbols]
        stream = "/".join(f"{symbol.lower()}@ticker" for symbol in symbol_list)
        url = f"{self._stream_base_url}?streams={stream}"

        message_queue: "queue.Queue[dict]" = queue.Queue()
        internal_stop = threading.Event()

        def should_stop() -> bool:
            return (stop_event and stop_event.is_set()) or internal_stop.is_set()

        def on_message(_: object, message: str) -> None:
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                logging.warning("Unable to decode WebSocket payload: %s", message)
                return

            data = payload.get("data") if isinstance(payload, dict) else None
            if not data and isinstance(payload, dict):
                data = payload  # direct stream (single subscription)

            if not isinstance(data, dict):
                return

            message_queue.put(data)

        def on_error(_: object, exc: Exception) -> None:
            logging.warning("WebSocket error: %s", exc)

        def run() -> None:
            while not should_stop():
                ws = websocket.WebSocketApp(
                    url,
                    on_message=on_message,
                    on_error=on_error,
                )
                ws.run_forever()
                if should_stop():
                    break
                logging.info("WebSocket disconnected; retrying in %.1fs", self._reconnect_delay)
                time.sleep(self._reconnect_delay)

        worker = threading.Thread(target=run, daemon=True)
        worker.start()

        try:
            while True:
                if should_stop():
                    break
                try:
                    data = message_queue.get(timeout=1.0)
                except queue.Empty:
                    if should_stop():
                        break
                    if not worker.is_alive():
                        logging.warning("WebSocket worker stopped unexpectedly.")
                        worker = threading.Thread(target=run, daemon=True)
                        worker.start()
                    continue

                symbol = data.get("s")
                price = data.get("c") or data.get("p")
                volume = data.get("v")
                event_time = data.get("E")

                if not symbol or price is None or volume is None:
                    continue

                try:
                    snapshot = MarketSnapshot(
                        symbol=symbol.upper(),
                        price=float(price),
                        volume=float(volume),
                        timestamp=_event_time_to_datetime(event_time),
                    )
                except ValueError:
                    continue

                yield snapshot
        finally:
            internal_stop.set()


def _event_time_to_datetime(event_time: Optional[int]) -> datetime:
    if not event_time:
        return datetime.utcnow()
    return datetime.fromtimestamp(event_time / 1000, tz=timezone.utc).replace(tzinfo=None)


def build_default_client() -> MarketDataClient:
    backend = settings.MARKET_DATA_BACKEND.lower()

    if backend == "binance_ws":
        try:
            return BinanceWebSocketClient(
                stream_base_url=settings.BINANCE_STREAM_BASE_URL,
                reconnect_delay_seconds=settings.STREAM_RECONNECT_DELAY.total_seconds(),
            )
        except Exception as exc:
            logging.warning("Falling back to REST client: %s", exc)
            backend = "binance_rest"

    if backend == "binance_rest":
        return BinanceRestClient(
            base_url=settings.BINANCE_REST_BASE_URL,
            poll_interval_seconds=settings.POLL_INTERVAL.total_seconds(),
        )

    logging.info("Using mock market data backend.")
    return MockBinanceClient(
        poll_interval_seconds=settings.POLL_INTERVAL.total_seconds(),
    )
