"""
Parse failure logging infrastructure for T008.

Configures logging for AST parsing failures and writes them to
data/parse_failures.csv for downstream analysis and debugging.
"""
import csv
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

# Thread-local storage for logger instances
_logger_local = threading.local()

# Global lock for CSV writes to ensure thread safety
_csv_write_lock = threading.Lock()

# Output file path (relative to project root)
PARSE_FAILURES_PATH = Path("data/parse_failures.csv")

# CSV header columns
CSV_HEADERS = [
    "timestamp",
    "file_path",
    "error_type",
    "error_message",
    "line_number",
    "code_snippet"
]


def _get_logger() -> logging.Logger:
    """Get or create the parse failure logger instance."""
    if not hasattr(_logger_local, 'logger'):
        logger = logging.getLogger('parse_failures')
        logger.setLevel(logging.INFO)

        # Prevent duplicate handlers
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        _logger_local.logger = logger

    return _logger_local.logger


def _ensure_csv_file() -> Path:
    """Ensure the parse failures CSV file exists with proper headers."""
    # Get project root (parent of code/ directory)
    project_root = Path(__file__).parent.parent
    csv_path = project_root / PARSE_FAILURES_PATH

    # Create parent directories if they don't exist
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Write headers if file is empty or doesn't exist
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()

    return csv_path


def init_logger(log_level: int = logging.INFO) -> logging.Logger:
    """
    Initialize the parse failure logging infrastructure.

    Args:
        log_level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = _get_logger()
    logger.setLevel(log_level)
    _ensure_csv_file()
    return logger


def log_parse_failure(
    file_path: str,
    error_type: str,
    error_message: str,
    line_number: Optional[int] = None,
    code_snippet: Optional[str] = None
) -> None:
    """
    Log a parse failure to both the log file and CSV output.

    Args:
        file_path: Path to the file that failed to parse
        error_type: Type of error (e.g., 'SyntaxError', 'IndentationError')
        error_message: Human-readable error message
        line_number: Line number where error occurred (optional)
        code_snippet: Code snippet around the error (optional)
    """
    logger = _get_logger()
    timestamp = datetime.now().isoformat()

    # Log to console/file handler
    log_message = f"Parse failure in {file_path}: {error_type} - {error_message}"
    if line_number:
        log_message += f" (line {line_number})"
    logger.warning(log_message)

    # Write to CSV file
    csv_path = _ensure_csv_file()
    row = {
        'timestamp': timestamp,
        'file_path': file_path,
        'error_type': error_type,
        'error_message': error_message,
        'line_number': str(line_number) if line_number else '',
        'code_snippet': code_snippet or ''
    }

    with _csv_write_lock:
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writerow(row)


def get_parse_failures_path() -> Path:
    """
    Get the absolute path to the parse failures CSV file.

    Returns:
        Path object pointing to data/parse_failures.csv
    """
    project_root = Path(__file__).parent.parent
    return project_root / PARSE_FAILURES_PATH


def clear_parse_failures() -> None:
    """
    Clear the parse failures CSV file (keep headers only).

    Use with caution - this will remove all logged failures.
    """
    csv_path = _ensure_csv_file()
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()


def count_parse_failures() -> int:
    """
    Count the number of parse failures logged (excluding header).

    Returns:
        Number of parse failure records in the CSV
    """
    csv_path = _ensure_csv_file()
    if not csv_path.exists():
        return 0

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return sum(1 for _ in reader)


def main() -> None:
    """
    Main entry point for standalone testing of the logging infrastructure.
    """
    logger = init_logger()
    logger.info("Parse failure logging infrastructure initialized")

    # Log a test failure
    log_parse_failure(
        file_path="test/example.py",
        error_type="SyntaxError",
        error_message="invalid syntax",
        line_number=42,
        code_snippet="def broken("
    )

    logger.info(f"Parse failures logged to: {get_parse_failures_path()}")
    logger.info(f"Total failures: {count_parse_failures()}")


if __name__ == "__main__":
    main()