"""Thin wrapper around an LLM provider (mocked for demo)."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime


class LLMClient:
    """Mock LLM client that emits simple Korean summaries/answers."""

    def complete(self, messages: List[Message]) -> str:
        last_user = _latest_user_message(messages)
        if last_user is None:
            return "대화 내용이 없습니다."

        content = last_user.content
        if "Event type:" in content and "Symbol:" in content:
            info = _parse_event_prompt(content)
            return _format_event_summary(info)

        return _format_question_response(content, messages)


def _latest_user_message(messages: List[Message]) -> Optional[Message]:
    for message in reversed(messages):
        if message.role == "user":
            return message
    return None


def _parse_event_prompt(prompt: str) -> dict[str, Optional[str]]:
    key_map = {
        "symbol": "symbol",
        "event type": "event_type",
        "price change (%)": "price_change_pct",
        "volume multiple": "volume_multiple",
        "timestamp": "timestamp",
    }
    parsed: dict[str, Optional[str]] = {value: None for value in key_map.values()}

    for line in prompt.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        normalized_key = key.strip().lower()
        mapped_key = key_map.get(normalized_key)
        if mapped_key:
            parsed[mapped_key] = value.strip() or None

    return parsed


EVENT_TYPE_LABELS = {
    "EventType.PRICE_DROP": "가격 급락",
    "EventType.PRICE_RISE": "가격 급등",
    "EventType.VOLUME_SPIKE": "거래량 급증",
}


def _format_event_summary(info: dict[str, Optional[str]]) -> str:
    symbol = info.get("symbol") or "알 수 없는 심볼"
    event_type = info.get("event_type") or ""
    event_label = EVENT_TYPE_LABELS.get(event_type, "시장 이벤트")
    price_change = _safe_float(info.get("price_change_pct"))
    volume_multiple = _safe_float(info.get("volume_multiple"))
    timestamp = info.get("timestamp") or "알 수 없는 시각"

    parts = [f"{symbol}에서 {event_label}이 감지되었습니다. (관측 시각: {timestamp})"]

    if price_change is not None:
        direction = "상승" if price_change > 0 else "하락" if price_change < 0 else "변동 없음"
        parts.append(f"직전 대비 {abs(price_change):.2f}% {direction}했습니다.")
    else:
        parts.append("가격 변동률 정보가 없습니다.")

    if volume_multiple is not None and volume_multiple != 0:
        parts.append(f"거래량은 직전 대비 약 {volume_multiple:.2f}배 수준입니다.")

    parts.append("리스크: 고변동 구간이므로 포지션 크기와 손절 기준을 명확히 하세요.")
    parts.append("추세 확인용으로 상위 타임프레임과 온체인 지표도 함께 검토해 보세요.")
    return "\n".join(parts)


def _safe_float(value: Optional[str]) -> Optional[float]:
    if value is None or value.lower() == "n/a":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _format_question_response(question: str, messages: List[Message]) -> str:
    recent_summary = _latest_assistant_message(messages)
    response_lines = [
        f"질문 요약: {question}",
    ]
    if recent_summary:
        headline = recent_summary.splitlines()[0]
        response_lines.append(f"최근 이벤트 힌트: {headline}")
    response_lines.append(
        "정확한 매매 판단은 본인 전략과 리스크 허용도에 맞춰야 합니다. "
        "지지/저항, 거래량 추이, 거시 지표 등을 함께 검토하고 분할 접근을 고려하세요."
    )
    return "\n\n".join(response_lines)


def _latest_assistant_message(messages: List[Message]) -> Optional[str]:
    for message in reversed(messages):
        if message.role == "assistant":
            return message.content
    return None
