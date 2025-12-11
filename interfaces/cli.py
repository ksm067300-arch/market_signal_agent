from orchestrator.workflow import Orchestrator


def prompt_follow_up(orchestrator: Orchestrator) -> None:
    try:
        while True:
            try:
                question = input("\nFollow-up question (blank to exit): ").strip()
            except EOFError:
                print("\nInput stream closed. Exiting Q&A session.")
                break
            if not question:
                break
            print("\nAgent response:\n", end="", flush=True)
            try:
                for chunk in orchestrator.answer_follow_up_stream(question):
                    print(chunk, end="", flush=True)
                print()
            except KeyboardInterrupt:
                print("\nStreaming interrupted by user.")
    except KeyboardInterrupt:
        print("\nStopping Q&A session.")
