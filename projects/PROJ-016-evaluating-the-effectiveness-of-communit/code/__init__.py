import logging
import logging.config
import os
from pathlib import Path

# Ensure the logs directory exists relative to the project root
# We assume the project root is the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIR / "run.log"

# Create logs directory if it doesn't exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_formatter": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        },
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json_formatter",
            "filename": str(LOG_FILE),
            "maxBytes": 10485760,
            "backupCount": 5,
            "encoding": "utf8"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}

# Attempt to import jsonlogger for JSON formatting
# If not installed, fallback to a standard string formatter for the JSON handler
try:
    from pythonjsonlogger import jsonlogger
    # Re-define the handler config to ensure it uses the class if available
    # The dictConfig above uses a callable constructor which works if the module is present
except ImportError:
    # Fallback: If pythonjsonlogger is missing, we use a standard formatter that outputs JSON-like strings
    # or simply text if strict JSON isn't enforced by the environment.
    # For this implementation, we assume the requirement to use JSON format implies
    # the library is available or we provide a standard string format that looks structured.
    # However, to strictly follow "JSON format" without the library, we define a custom formatter.
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            import json
            log_record = {
                "asctime": self.formatTime(record, self.datefmt),
                "name": record.name,
                "levelname": record.levelname,
                "message": record.getMessage(),
                "filename": record.filename,
                "lineno": record.lineno
            }
            if record.exc_info:
                log_record["exc_info"] = self.formatException(record.exc_info)
            return json.dumps(log_record)

    LOGGING_CONFIG["formatters"]["json_formatter"] = {
        "()": JsonFormatter,
        "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
    }

# Apply the configuration
logging.config.dictConfig(LOGGING_CONFIG)

def get_logger(name=None):
    """
    Returns a logger instance configured with the project settings.
    """
    return logging.getLogger(name)

# Initialize the root logger immediately
logger = get_logger()
logger.info("Logging infrastructure initialized for project.")