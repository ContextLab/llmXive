"""
Dummy script to verify that the structured JSON logger works.

It obtains a logger via ``get_logger`` and emits a single INFO level
message. The console handler in ``code/utils/logging.py`` writes JSON to
stdout, so running this script should produce one JSON line.
"""

from utils.logging import get_logger, log_info

def main():
    logger = get_logger(__name__)
    # Emit a simple info message; the console handler will output JSON to stdout.
    log_info("Dummy logger test successful", logger_name=logger.name)

if __name__ == "__main__":
    main()