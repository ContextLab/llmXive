import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class JSONLogHandler(logging.Handler):
    """Custom handler that logs to a JSON file."""
    
    def __init__(self, log_file: Path):
        super().__init__()
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize file if it doesn't exist
        if not self.log_file.exists():
            with open(self.log_file, 'w') as f:
                json.dump([], f)
    
    def emit(self, record: logging.LogRecord):
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'level': record.levelname,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            
            # Read existing logs
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    try:
                        logs = json.load(f)
                    except json.JSONDecodeError:
                        logs = []
            else:
                logs = []
            
            logs.append(log_entry)
            
            # Write back
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception:
            self.handleError(record)

def setup_logging(project_root: Optional[Path] = None) -> None:
    """Setup logging infrastructure."""
    if project_root is None:
        project_root = Path(__file__).parent.parent
    
    log_dir = project_root / 'data' / 'processed'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup file handler
    log_file = log_dir / 'mapping_log.json'
    file_handler = JSONLogHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

def log_mapping(mapping_data: Dict[str, Any]) -> None:
    """Log a mapping entry to the JSON log file."""
    logger = logging.getLogger(__name__)
    logger.info(json.dumps(mapping_data))

def get_project_logger(name: str) -> logging.Logger:
    """Get a logger for the project."""
    return logging.getLogger(name)

def get_default_logger() -> logging.Logger:
    """Get the default logger."""
    return logging.getLogger('default')
