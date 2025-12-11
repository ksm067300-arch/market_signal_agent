"""Gradio UI for monitoring summaries and running follow-up Q&A."""

from __future__ import annotations

import gradio as gr

from orchestrator.workflow import Orchestrator


def launch_gradio(orchestrator: Orchestrator) -> None:
    """Start a Gradio Blocks app backed by the orchestrator."""

    def _start_and_fetch() -> tuple[str, str, int]:
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
        length = len(orchestrator.history_lines())
        return "", length

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
        question: str, history: list[tuple[str, str]]
    ) -> tuple[list[tuple[str, str]], str]:
        question = (question or "").strip()
        if not question:
            return history, ""
        answer = orchestrator.answer_follow_up(question)
        updated_history = history + [(question, answer)]
        return updated_history, ""

    with gr.Blocks(title="Market Signal Agent") as demo:
        gr.Markdown("## 실시간 마켓 이벤트 요약 + Q&A")

        summary_box = gr.Textbox(
            label="이벤트 요약 히스토리",
            placeholder="아직 이벤트가 감지되지 않았습니다.",
            lines=16,
        )
        summary_status = gr.Markdown("워처가 중지된 상태입니다.")
        history_index = gr.State(0)

        with gr.Row():
            start_button = gr.Button("최신 이벤트 가져오기")
            stop_button = gr.Button("요약 가져오기 중지", variant="stop")
            clear_button = gr.Button("로그 지우기")

        start_button.click(
            fn=_start_and_fetch,
            inputs=None,
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

        gr.Markdown("### 후속 질문")
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
