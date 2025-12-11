# market_signal_agent

실시간 시세 변화를 감지해 이벤트화하고, LLM 스타일 분석 에이전트로 요약과 후속 질의응답을 수행하는 프로토타입입니다.

## 프로젝트 구조

```
config/          # 전역 설정
watcher/         # 거래소 클라이언트, 트리거 조건, 워처 에이전트
agent/           # LLM 래퍼, 컨텍스트 저장소, 요약/질의응답 로직
orchestrator/    # 워처 이벤트와 분석 에이전트 사이의 연결
interfaces/      # 사용자 인터페이스(CLI 데모)
main.py          # 전체 흐름을 실행하는 엔트리 포인트
```

## 데모 실행 방법

```bash
pip install -r requirements.txt
python main.py
```

웹 기반 Gradio UI를 사용하려면:

```bash
python main.py --gradio
```

Gradio UI에서 `최신 이벤트 가져오기`를 누르면 워처가 시작되어 중지 명령을 받을 때까지 지속적으로 이벤트를 수집합니다. 히스토리 창은 자동으로 최신 이벤트를 이어서 기록하며, `로그 지우기` 버튼은 화면에 보이는 로그만 초기화합니다(내부 히스토리는 유지). 생성된 이벤트는 누적되어 후속 질문 시 참고 컨텍스트로 제공됩니다.

`config/settings.py`의 `MARKET_DATA_BACKEND` 값을 통해 다음 모드를 선택할 수 있습니다.

- `binance_ws` (기본): 다중 스트림 WebSocket. 자동 재연결하며 라이브러리나 소켓이 준비되지 않으면 REST로 폴백합니다.
- `binance_rest`: `POLL_INTERVAL` 간격으로 `/api/v3/ticker/24hr`를 폴링합니다.
- `mock`: 외부 의존성 없이 오프라인 데모를 위한 의사 난수 생성기를 계속 사용합니다.

어떤 백엔드를 사용하든 조건이 충족되면 오케스트레이터가 이벤트 요약을 출력하고, CLI에서 후속 질문을 이어가면 누적 컨텍스트를 재활용해 답변합니다. 실제 LLM을 붙이려면 `agent/llm_client.py`를 교체하면 됩니다.
