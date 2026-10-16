"""
Minimal trainer placeholder.

The full training logic is implemented elsewhere; this file exists so that
the project compiles and the CLI can import ``models.trainer`` without
raising import errors.
"""

import logging

def main() -> int:
    """
    Entry point used by the CLI. Currently performs no training
    (placeholder) but returns a success code so that the script can be
    invoked without error.
    """
    logger = logging.getLogger(__name__)
    logger.info("Trainer placeholder invoked – no training performed.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
