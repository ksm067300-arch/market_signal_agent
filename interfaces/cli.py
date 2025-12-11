"""Minimal CLI helper to prompt for follow-up questions."""

from orchestrator.workflow import Orchestrator


def prompt_follow_up(orchestrator: Orchestrator) -> None:
    """Ask user for follow-up questions until blank line."""
    try:
        while True:
            try:
                question = input("\nFollow-up question (blank to exit): ").strip()
            except EOFError:
                print("\nInput stream closed. Exiting Q&A session.")
                break
            if not question:
                break
            response = orchestrator.answer_follow_up(question)
            print(f"\nAgent response:\n{response}")
    except KeyboardInterrupt:
        print("\nStopping Q&A session.")
