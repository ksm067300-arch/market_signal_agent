from __future__ import annotations

import argparse
import logging

from dotenv import load_dotenv

load_dotenv()

from agent.context import ConversationContext
from agent.llm_client import LLMClient
from agent.qa_agent import QaAgent
from config import settings
from interfaces.cli import prompt_follow_up
from orchestrator.workflow import Orchestrator
from watcher.agent import MarketWatcherAgent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Market signal agent demo.")
    parser.add_argument("--gradio", action="store_true", help="Gradio UI를 실행합니다.")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    args = parse_args()
    watcher = MarketWatcherAgent(settings.SYMBOLS)
    context = ConversationContext(ttl=settings.SUMMARY_CACHE_TTL)
    llm = LLMClient()
    qa_agent = QaAgent(llm, context)
    orchestrator = Orchestrator(watcher, qa_agent)

    if args.gradio:
        from interfaces.gradio_app import launch_gradio

        launch_gradio(orchestrator)
        return

    backend = settings.MARKET_DATA_BACKEND
    print(f"Watching markets via '{backend}' backend... Press Ctrl+C to stop.")
    try:
        summary = orchestrator.run_once()
        if summary:
            print("\nEvent summary:\n")
            print(summary)
            prompt_follow_up(orchestrator)
    except KeyboardInterrupt:
        print("\nWatcher interrupted by user.")


if __name__ == "__main__":
    main()
