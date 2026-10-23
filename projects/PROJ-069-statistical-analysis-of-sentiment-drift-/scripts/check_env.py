"""
Sanity‑check script for required environment variables.

This script loads variables from the project's ``.env`` file using
``python‑dotenv`` and verifies that both ``FRED_API_KEY`` and
``TWITTER_BEARER_TOKEN`` are present.  On success it prints the names
of the variables and exits with status 0; otherwise it prints an error
message and exits with status 1.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def main() -> None:
    """
    Load the ``.env`` file located at the repository root and validate
    required keys.
    """
    env_path = paths.root / ".env"
    if not env_path.is_file():
        print(f"Error: .env file not found at {env_path}", file=sys.stderr)
        sys.exit(1)

    # Load variables – do not overwrite existing OS env vars
    load_dotenv(dotenv_path=env_path, override=False)

    required_vars = ["FRED_API_KEY", "TWITTER_BEARER_TOKEN"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(
            f"Error: Missing required environment variables: {', '.join(missing)}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Success – print the variable *names* as required by the verification step
    for var in required_vars:
        print(var)

    sys.exit(0)

if __name__ == "__main__":
    main()
