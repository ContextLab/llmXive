"""Initialize the logging infrastructure (T004).

Runs setup_logging() from code/config.py and writes a timestamped
startup entry to code/logs/app.log, creating the file on first run.
"""
from config import setup_logging, LOG_FILE, LOGS_DIR, RANDOM_SEED


def main() -> None:
    logger = setup_logging()
    logger.info("Logging infrastructure initialized (T004)")
    logger.info("Log file: %s", LOG_FILE)
    logger.info("Random seed: %d", RANDOM_SEED)
    logger.info("Logs directory: %s", LOGS_DIR)
    # Flush handlers so the file exists on disk before the process exits.
    for handler in logging.getLogger().handlers:
        handler.flush()


if __name__ == "__main__":
    import logging

    main()
