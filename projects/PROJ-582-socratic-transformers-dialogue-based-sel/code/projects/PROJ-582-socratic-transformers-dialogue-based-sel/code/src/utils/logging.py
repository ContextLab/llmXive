import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Constants for log events
DEGENERATE_DIALOGUE_TRUNCATED = "DEGENERATE_DIALOGUE_TRUNCATED"

class SocraticLogger:
    """
    A structured logger for the Socratic Transformers pipeline.
    
    This logger handles standard logging as well as special JSON-line logging
    for specific edge case events like DEGENERATE_DIALOGUE_TRUNCATED.
    """
    
    def __init__(self, name: str, log_dir: Optional[Path] = None):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Avoid adding handlers multiple times if logger is reused
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            
            # File handler for structured logs (JSON lines)
            if log_dir:
                log_dir.mkdir(parents=True, exist_ok=True)
                file_path = log_dir / f"{name}.log"
                file_handler = logging.FileHandler(file_path)
                file_handler.setLevel(logging.DEBUG)
                # We will handle JSON formatting manually for specific events
                file_handler.setFormatter(logging.Formatter('%(message)s'))
                self.logger.addHandler(file_handler)
        
        self.log_dir = log_dir

    def info(self, message: str):
        self.logger.info(message)

    def debug(self, message: str):
        self.logger.debug(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def log_degenerate_dialogue_truncated(self, dialogue_id: str, 
                                          reason: str, 
                                          original_length: int, 
                                          truncated_length: int,
                                          extra_context: Optional[Dict[str, Any]] = None):
        """
        Logs a DEGENERATE_DIALOGUE_TRUNCATED event as a structured JSON line.
        
        This method specifically handles the edge case requirement where
        n-gram overlap > 0.9 triggers truncation. The log is written as
        a JSON line to facilitate parsing and analysis.
        
        Args:
            dialogue_id: Unique identifier for the dialogue
            reason: Explanation of why truncation occurred
            original_length: Length of the dialogue before truncation
            truncated_length: Length of the dialogue after truncation
            extra_context: Optional dictionary of additional context
        """
        timestamp = datetime.utcnow().isoformat()
        
        log_entry = {
            "event": DEGENERATE_DIALOGUE_TRUNCATED,
            "timestamp": timestamp,
            "dialogue_id": dialogue_id,
            "reason": reason,
            "original_length": original_length,
            "truncated_length": truncated_length,
            "logger": self.name
        }
        
        if extra_context:
            log_entry.update(extra_context)
        
        # Log to console as warning level
        self.logger.warning(f"{DEGENERATE_DIALOGUE_TRUNCATED}: {dialogue_id} - {reason}")
        
        # Write JSON line to file if log_dir is configured
        if self.log_dir:
            log_file = self.log_dir / f"{self.name}.jsonl"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')

def get_logger(name: str, log_dir: Optional[Path] = None) -> SocraticLogger:
    """
    Factory function to get a SocraticLogger instance.
    
    Args:
        name: Name of the logger
        log_dir: Optional directory for log files
        
    Returns:
        SocraticLogger instance
    """
    return SocraticLogger(name, log_dir)