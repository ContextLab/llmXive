# Logging Infrastructure and Retention Policy

## Overview

This project uses a centralized logging system defined in `code/logging/pipeline_logger.py`. All scripts in the pipeline (US1-US5) import and utilize this module to ensure a consistent audit trail.

## Log Format

Logs are written in **JSON-lines** format to `logs/run_<timestamp>.log`. Each line is a valid JSON object containing:

- `timestamp`: ISO 8601 formatted timestamp (UTC).
- `level`: Log level (INFO, WARNING, ERROR).
- `module`: Name of the module generating the log.
- `message`: Human-readable message.
- `context`: Optional dictionary of key-value pairs for structured data (e.g., `{"session_id": "123", "score": 0.85}`).

Example:
```json
{"timestamp": "2026-05-25T14:30:00.123Z", "level": "INFO", "module": "compute_scores", "message": "Computed agency score", "context": {"session_id": "S001", "score": 0.85}}
```

## Retention Policy

- **Active Runs**: Logs for the current day are kept in `logs/`.
- **Archival**: Logs older than 30 days are moved to `logs/archive/` (manual or cron job).
- **Deletion**: Logs older than 1 year are permanently deleted to manage storage.

## Verification

The script `code/logging/verify_logging.py` parses all log files in `logs/` and compares them against a predefined list of expected steps (ingestion, detection, aggregation, etc.). It outputs a completeness metric to `logs/completeness_metric.json`.

## Usage

To use the logger in a new script:

```python
from logging.pipeline_logger import get_logger, log_dict

logger = get_logger(__name__)
logger.info("Starting processing", extra={"step": "start"})

# Log structured data
log_dict(logger, "result", {"score": 0.95, "user_id": "U123"})
```
