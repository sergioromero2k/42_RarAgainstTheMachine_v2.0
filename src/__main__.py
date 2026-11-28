"""Command-line entry point of the RAG System"""

import sys
import fire

from src.cli import RAGSystem
from src.errors import RagError


def main() -> int:
    """Run the CLI and return the process exit code."""
    try:
        fire.Fire(RAGSystem)
    except RagError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as error:
        print(f"Unexpected error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
