import os
import logging
import json
from datetime import datetime

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Sets up logging with a JSON formatter.
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # For JSON logs, we might want a custom formatter, but standard format is fine for now.
        # The task T008 mentions JSON logs to stdout.
        # Let's create a JSON formatter.
        
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_record = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage()
                }
                if record.exc_info:
                    log_record["exc_info"] = self.formatException(record.exc_info)
                return json.dumps(log_record)

        json_handler = logging.StreamHandler()
        json_handler.setFormatter(JsonFormatter())
        logger.addHandler(json_handler)
        
        # Also add a standard handler if needed, but the requirement is JSON.
        # We will stick to JSON.
        
    return logger
