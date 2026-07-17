import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure the src directory is in the path if running as a script
if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

class SocraticLogger:
    """
    Structured logger for the Socratic Transformers project.
    
    Handles special edge-case events (like DEGENERATE_DIALOGUE_TRUNCATED) 
    by writing them as JSON lines to a dedicated log file, while also 
    emitting standard logs to the console.
    """
    
    DEGENERATE_DIALOGUE_TRUNCATED = "DEGENERATE_DIALOGUE_TRUNCATED"
    
    def __init__(self, name: str, log_dir: Optional[Path] = None):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers if logger is re-initialized
        if not self.logger.handlers:
            # Console Handler (Standard logs)
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
            
            # File Handler for Edge Cases (JSON Lines)
            if log_dir is None:
                # Default to data/results/logs if not specified
                log_dir = Path.cwd() / "data" / "results" / "logs"
            
            log_dir.mkdir(parents=True, exist_ok=True)
            self.edge_case_log_path = log_dir / "edge_cases.jsonl"
            
            self.file_handler = logging.FileHandler(
                self.edge_case_log_path, mode='a'
            )
            self.file_handler.setLevel(logging.WARNING) # Log edge cases as warnings or higher
            # Custom formatter for file that just passes the message, 
            # we handle JSON serialization in the specific method
            self.file_handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(self.file_handler)

        self.edge_case_log_path = log_dir / "edge_cases.jsonl"

    def _log_edge_case(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Writes a structured JSON line to the edge case log file.
        
        Args:
            event_type: The specific event identifier (e.g., DEGENERATE_DIALOGUE_TRUNCATED).
            details: A dictionary of metadata describing the event.
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "logger_name": self.name,
            "details": details
        }
        
        try:
            with open(self.edge_case_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
            self.logger.warning(f"Edge case logged: {event_type}")
        except IOError as e:
            self.logger.error(f"Failed to write edge case log: {e}")

    def log_degenerate_dialogue_truncation(
        self, 
        dialogue_id: str, 
        original_length: int, 
        truncated_length: int, 
        ngram_overlap: float,
        truncation_reason: str = "High n-gram overlap detected"
    ) -> None:
        """
        Logs a DEGENERATE_DIALOGUE_TRUNCATED event.
        
        This is the specific implementation for the Edge Case requirement 
        mentioned in T005.
        
        Args:
            dialogue_id: Unique identifier for the dialogue session.
            original_length: Length of the dialogue before truncation.
            truncated_length: Length of the dialogue after truncation.
            ngram_overlap: The calculated n-gram overlap score that triggered this.
            truncation_reason: Optional description of why truncation occurred.
        """
        details = {
            "dialogue_id": dialogue_id,
            "original_length": original_length,
            "truncated_length": truncated_length,
            "ngram_overlap": ngram_overlap,
            "reason": truncation_reason
        }
        
        self._log_edge_case(self.DEGENERATE_DIALOGUE_TRUNCATED, details)

    def info(self, msg: str, *args, **kwargs) -> None:
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self.logger.error(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs) -> None:
        self.logger.debug(msg, *args, **kwargs)

# Global logger instance for convenience
_global_logger: Optional[SocraticLogger] = None

def get_logger(name: str = "socratic") -> SocraticLogger:
    """
    Returns a singleton logger instance or creates a new one if not exists.
    """
    global _global_logger
    if _global_logger is None or name != _global_logger.name:
        _global_logger = SocraticLogger(name)
    return _global_logger

if __name__ == "__main__":
    # Simple test to verify the logger writes JSON lines correctly
    logger = get_logger("test_t005")
    
    # Simulate a degenerate dialogue event
    logger.log_degenerate_dialogue_truncation(
        dialogue_id="demo-001",
        original_length=50,
        truncated_length=20,
        ngram_overlap=0.95,
        truncation_reason="Simulated test event"
    )
    
    logger.info("Test logging completed. Check data/results/logs/edge_cases.jsonl")