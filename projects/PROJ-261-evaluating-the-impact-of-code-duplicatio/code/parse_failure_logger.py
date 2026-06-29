import csv
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
_lock = threading.Lock()
_parse_failures_path = Path("data/parse_failures.csv")

def init_logger():
    """Initialize the parse failure logger."""
    _parse_failures_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def get_parse_failures_path() -> Path:
    """Get the path to the parse failures CSV file."""
    return _parse_failures_path

def log_parse_failure(file_path: str, error_type: str, error_message: str, 
                     line_number: Optional[int] = None, context: Optional[str] = None):
    """
    Log a parse failure to data/parse_failures.csv.
    
    Args:
        file_path: Path to the file that failed to parse
        error_type: Type of error (e.g., 'SyntaxError', 'ASTError', 'ParseError')
        error_message: Description of the error
        line_number: Optional line number where error occurred
        context: Optional code context around the error
    """
    with _lock:
        _parse_failures_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_exists = _parse_failures_path.exists()
        
        with open(_parse_failures_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow([
                    'timestamp', 'file_path', 'error_type', 'error_message',
                    'line_number', 'context'
                ])
            
            writer.writerow([
                datetime.now().isoformat(),
                file_path,
                error_type,
                error_message,
                line_number or '',
                context or ''
            ])
        
        logger.warning(f"Parse failure logged: {file_path} - {error_type}")

def clear_parse_failures():
    """Clear all parse failure logs (for testing)."""
    with _lock:
        if _parse_failures_path.exists():
            _parse_failures_path.unlink()
        logger.info("Parse failures cleared")

def count_parse_failures() -> int:
    """Count the number of parse failures recorded."""
    if not _parse_failures_path.exists():
        return 0
    
    with open(_parse_failures_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        return max(0, len(rows) - 1)  # Subtract header row

def handle_parse_error(file_path: str, error: Exception, line_number: Optional[int] = None):
    """
    Centralized error handler for parse failures.
    Logs the error and returns False to indicate failure.
    
    Args:
        file_path: Path to the file that failed
        error: The exception that was raised
        line_number: Optional line number where error occurred
    
    Returns:
        False (indicating parse failure)
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    log_parse_failure(
        file_path=file_path,
        error_type=error_type,
        error_message=error_message,
        line_number=line_number,
        context=None
    )
    
    return False

def main():
    """Main entry point for parse failure logger."""
    init_logger()
    count = count_parse_failures()
    print(f"Total parse failures recorded: {count}")

if __name__ == "__main__":
    main()
