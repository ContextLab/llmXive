"""
Utility script to validate quickstart artifacts.

Runs the project's quickstart validation tests.
"""

import subprocess
import sys
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def main():
    """Run pytest with the 'quickstart' marker."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-m", "quickstart", "-v"],
            check=False,
        )
        if result.returncode == 0:
            log.info("Quickstart validation passed.")
        else:
            log.error(
                f"Quickstart validation failed with exit code {result.returncode}"
            )
            sys.exit(result.returncode)
    except Exception as e:
        log.exception("Error during quickstart validation")
        sys.exit(1)

if __name__ == "__main__":
    main()