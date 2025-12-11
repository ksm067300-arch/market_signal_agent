# MARKET SIGNAL AGENT

실시간 거래소 API(WebSocket/REST)를 자체 백엔드처럼 활용해 **시세 변동 감지 → 이벤트 로그 → LLM 기반 Q&A** 전체 흐름을 실험하는 스터디용 프로젝트입니다. 데이터베이스나 복잡한 백엔드 없이도 상태 모니터링 로직과 AI 응답 경험을 빠르게 검증할 수 있으며, Python과 AI Agent Service 개발 패턴을 학습하는 것이 주된 목적입니다.

## 개발 배경  
- “준비된 거래소 API를 마치 사내 서비스처럼 쓰면 변동 감지와 AI 응답 흐름만 집중적으로 연습할 수 있다”는 아이디어에서 시작.
- Python 기반 AI Agent 서비스의 구조와 스트리밍 Q&A 패턴을 연습하기 위한 스터디 목적.

## 기술 스택
- **언어/런타임**: Python 3.11  
- **데이터 소스**: Binance WebSocket/REST (또는 Mokup)  
- **UI**: Gradio 4 (웹), CLI  
- **AI**: OpenAI Chat Completions API, python-dotenv  
- **그 외**: threading, websocket-client, logging

## 프로젝트 구조 및 역할
```
config/            설정 및 트리거 값
watcher/           거래소 클라이언트, 조건, MarketWatcher
agent/llm_client.py  OpenAI/목업 LLM 래퍼
agent/qa_agent.py     스트리밍 Q&A 담당
orchestrator/      이벤트 로그·히스토리 관리 + Q&A 연결
interfaces/        CLI 및 Gradio UI
main.py            엔트리 포인트
```

## AI 서비스 흐름
1. **MarketWatcher**: 거래소 스트림 감시, 가격/거래량 조건을 평가.  
2. **Orchestrator**: 조건 충족 시 즉시 요약 텍스트(고정 포맷)를 생성해 히스토리에 저장.  
3. **QaAgent**: 사용자가 질문하면 OpenAI LLM에 스트리밍으로 질의해 바로 출력.  
4. **UI/CLI**:  
   - Gradio: 조건 조정, 이벤트 로그, 스트리밍 Q&A 표시.  
   - CLI: 간단한 이벤트 확인과 스트리밍 응답.  
5. LLM은 **후속 질문에만** 사용하며, 이벤트 히스토리에는 시그널 5개만 포함해 토큰 사용을 제한.

## 어플리케이션 아키텍처
```
┌──────────┐     WebSocket/REST      ┌────────────┐
│ settings │ ─────────────────────▶ │ watcher     │
│ config   │     (Binance/mock)     │ (MarketWatcher)
└──────────┘                         └────┬───────┘
                                         │ 이벤트(Event)
                                         ▼
                               ┌─────────────────────┐
                               │ Orchestrator        │
                               │ - 이벤트 요약         │
                               │ - 히스토리 관리       │
                               │ - QaAgent 연결      │
                               └──────┬──────────────┘
             질문/응답 스트림        │
   ┌───────────────────────┐         ▼
   │ Gradio UI / CLI       │ ◀──── QaAgent + LLMClient
   │ - 조건조정/로그/Q&A   │         │
   │ - 스트리밍 Q&A        │         │ OpenAI API
   └───────────────────────┘         ▼
                                 LLM Provider
```

## 주요 기능
- 실시간 변동 감지(가격 상승/하락, 거래량 급증)  
- 이벤트 로그 자동 생성
- 조건 값 UI에서 실시간 변경  
- OpenAI 스트리밍 Q&A (CLI·Gradio 공통)  
- `.env` 기반 LLM 설정, `config/settings.py`로 백엔드 모드 및 트리거 제어

## 개발 이슈 및 배운 점
- 이벤트 발생 시 요약 Summary Agent로 인해 Websocket 틱 조회가 Blocking되어 Watcher 스레드가 막혀 성능 저하 → 고정된 포맷의 이벤트 히스토리여서 **고정 포맷 요약**으로 전환해 해결.  
- Gradio Chatbot은 OpenAI 형식(dict)을 요구 → 스트리밍 중에도 dict 업데이트 방식으로 수정.  
- 첫 OpenAI 호출이 느려 “워밍업” 또는 짧은 히스토리 유지 전략이 필요함.  
- `.env` 로드가 늦어지면 LLM 키가 인식되지 않는 이슈를 겪어, 프로그램 시작 시 `load_dotenv()`를 호출하도록 구조화.  
- Gradio Chatbot에서 `type="pairs"`가 지원되지 않아 messages 포맷(dict)을 그대로 반환하도록 스트리밍 제너레이터를 재구성.  

## 확장 방향성
- Redis/Postgres 등 외부 스토리지 추가해 이벤트를 장기 보관.  
- Slack/이메일 알림 연동으로 실서비스에 가까운 워크플로 구축.  
- 온체인 지표나 다른 자산 조건을 추가해 감지 로직 확장.  
- Docker/CI 등 배포 자동화 검토.

Gradio UI는 `MARKET_DATA_BACKEND`(binance_ws / binance_rest / mock)와 트리거 입력값을 조정해 다양한 시나리오를 실험할 수 있습니다.
