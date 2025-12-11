from __future__ import annotations

import gradio as gr

from config import settings
from orchestrator.workflow import Orchestrator


def launch_gradio(orchestrator: Orchestrator) -> None:
    def _apply_thresholds(drop: float, rise: float, volume: float) -> None:
        if drop is not None and drop > 0:
            settings.MAX_PERCENT_DROP = drop
        if rise is not None and rise > 0:
            settings.MAX_PERCENT_RISE = rise
        if volume is not None and volume > 0:
            settings.VOLUME_SPIKE_MULTIPLIER = volume

    def _start_and_fetch(
        drop: float, rise: float, volume: float
    ) -> tuple[str, str, int]:
        _apply_thresholds(drop, rise, volume)
        orchestrator.start()
        lines = orchestrator.history_lines()
        history_text = "\n".join(lines)
        status = "✅ 워처 실행 중입니다."
        return history_text, status, len(lines)

    def _stop_watcher() -> tuple[str, str, int]:
        orchestrator.stop()
        lines = orchestrator.history_lines()
        history_text = "\n".join(lines)
        status = "⏹️ 워처가 중지되었습니다."
        return history_text, status, len(lines)

    def _clear_history() -> tuple[str, int]:
        orchestrator.clear_history()
        return "", 0

    def _poll_history(
        current_text: str, last_index: int
    ) -> tuple[str, int]:
        lines = orchestrator.history_lines()
        if last_index >= len(lines):
            return current_text or "", len(lines)

        new_lines = lines[last_index:]
        new_text = "\n".join(new_lines)
        combined = (current_text + "\n" + new_text).strip() if current_text else new_text
        return combined, len(lines)

    def _handle_question(
        question: str, history: list[dict]
    ):
        question = (question or "").strip()
        history = history or []
        if not question:
            yield history, ""
            return

        updated_history = history + [{"role": "user", "content": question}]
        assistant_entry = {"role": "assistant", "content": ""}
        updated_history.append(assistant_entry)
        yield updated_history, ""

        buffer = ""
        for chunk in orchestrator.answer_follow_up_stream(question):
            buffer += chunk
            assistant_entry["content"] = buffer
            yield updated_history, ""

        yield updated_history, ""

    custom_css = """
    .gradio-container {
        max-width: 960px;
        margin: 0 auto;
        padding: 0 24px;
    }
    """

    with gr.Blocks(title="Market Signal Agent", css=custom_css) as demo:
        gr.Markdown("## MARKET SIGNAL AGENT")

        with gr.Row():
            drop_input = gr.Number(
                label="가격 하락 트리거 (%)",
                value=settings.MAX_PERCENT_DROP,
                precision=4,
            )
            rise_input = gr.Number(
                label="가격 상승 트리거 (%)",
                value=settings.MAX_PERCENT_RISE,
                precision=4,
            )
            volume_input = gr.Number(
                label="거래량 배수 트리거",
                value=settings.VOLUME_SPIKE_MULTIPLIER,
                precision=2,
            )

        summary_box = gr.Textbox(
            label="이벤트 요약 히스토리",
            placeholder="아직 이벤트가 감지되지 않았습니다.",
            lines=16,
        )
        summary_status = gr.Markdown("워처가 중지된 상태입니다.")
        history_index = gr.State(0)

        with gr.Row():
            start_button = gr.Button("Start")
            stop_button = gr.Button("Stop", variant="stop")
            clear_button = gr.Button("Clear")

        start_button.click(
            fn=_start_and_fetch,
            inputs=[drop_input, rise_input, volume_input],
            outputs=[summary_box, summary_status, history_index],
            queue=False,
        )
        stop_button.click(
            fn=_stop_watcher,
            inputs=None,
            outputs=[summary_box, summary_status, history_index],
            queue=False,
        )
        clear_button.click(
            fn=_clear_history,
            inputs=None,
            outputs=[summary_box, history_index],
            queue=False,
        )

        log_timer = gr.Timer(2.0)
        log_timer.tick(
            fn=_poll_history,
            inputs=[summary_box, history_index],
            outputs=[summary_box, history_index],
            queue=False,
        )

        gr.Markdown("토큰 소모를 줄이기 위해 최근 5개의 이벤트 히스토리만 참조합니다. 질문은 아래에 입력하세요.")
        chat_history = gr.Chatbot(label="대화 로그", height=300)
        prompt_box = gr.Textbox(label="질문 입력", placeholder="예) 이게 단기 조정인가요?")
        ask_button = gr.Button("질문 보내기")

        ask_button.click(
            fn=_handle_question,
            inputs=[prompt_box, chat_history],
            outputs=[chat_history, prompt_box],
            queue=True,
        )
        prompt_box.submit(
            fn=_handle_question,
            inputs=[prompt_box, chat_history],
            outputs=[chat_history, prompt_box],
            queue=True,
        )

    demo.launch()
