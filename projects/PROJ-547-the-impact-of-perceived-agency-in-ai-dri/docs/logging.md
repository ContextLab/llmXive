# Logging Documentation

## Overview

The project uses a centralized logging system implemented in `code/logging/pipeline_logger.py`.
All pipeline scripts import the logger via:

```python
from logging.pipeline_logger import get_logger, log_dict
```

The logger writes **JSON‑Line** (`.log`) files to the `logs/` directory.
Each line is a valid JSON object representing a single log entry, making the logs easy to parse
with standard tools (e.g., `jq`, Python `json` module, or log aggregation platforms).

---

## Log File Naming

- Files are created per pipeline run with the pattern:
 `logs/run_<YYYYMMDD_HHMMSS>.log`
 where the timestamp reflects the start time of the run.
- Example: `logs/run_20240629_143210.log`

---

## Log Entry Format

Each log entry is a JSON object with the following fields:

| Field | Type | Description |
|---------------------|--------|-------------|
| `timestamp` | string | ISO‑8601 datetime with timezone, e.g., `"2024-06-29T14:32:10+00:00"` |
| `level` | string | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `module` | string | Python module name that emitted the log |
| `function` | string | Function name within the module |
| `message` | string | Human‑readable log message |
| `extra` (optional) | object | Additional key‑value pairs supplied via `log_dict` |

The logger is configured in `pipeline_logger.py` as follows:

```python
logger = logging.getLogger("pipeline")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
formatter = logging.Formatter('%(message)s') # raw JSON string
handler.setFormatter(formatter)
logger.addHandler(handler)
```

All helper functions (`log_dict`, `get_logger`) ensure that the JSON structure is respected.

---

## Logging Levels and Usage

- **DEBUG** – Detailed internal state, useful during development.
 Emitted via `logger.debug(json.dumps(entry))`.
- **INFO** – Normal operation messages (e.g., start/end of a pipeline step).
 Emitted via `logger.info(json.dumps(entry))`.
- **WARNING** – Non‑critical issues that do not stop the pipeline (e.g., missing optional data).
 Emitted via `logger.warning(json.dumps(entry))`.
- **ERROR** – Critical problems that cause the pipeline to abort.
 Emitted via `logger.error(json.dumps(entry))`.
- **CRITICAL** – Severe failures (e.g., inability to write logs).
 Emitted via `logger.critical(json.dumps(entry))`.

Use `log_dict` to add structured data:

```python
logger = get_logger()
log_dict(logger, level="INFO", module=__name__, function="run", message="Step completed", extra={"step": "ingest_transcripts"})
```

---

## Retention Policy

To balance auditability with storage constraints, the following retention policy is enforced:

1. **Maximum Age**: Log files older than **30 days** are automatically deleted.
2. **Maximum Size**: The total size of the `logs/` directory is limited to **5 GB**.
 When this limit is exceeded, the oldest log files are removed until the total size falls below the threshold.
3. **Archiving**: Before deletion, log files may be compressed (`.log.gz`) to reduce storage usage.
 Compression is performed by the utility script `code/logging/verify_logging.py` during the cleanup step.
4. **Backup**: Critical logs (e.g., those containing `ERROR` or `CRITICAL` levels) are copied to a backup location
 defined by the environment variable `LOG_BACKUP_PATH`. If the variable is unset, backups are skipped.

### Automated Cleanup

The cleanup routine is invoked at the start of each pipeline run:

```python
from logging.pipeline_logger import get_logger
import os, pathlib, gzip, shutil

def cleanup_logs(retention_days: int = 30, max_total_bytes: int = 5 * 1024**3):
 log_dir = pathlib.Path("logs")
 now = pathlib.Path().stat().st_mtime
 # Delete files older than retention_days
 for file in log_dir.glob("run_*.log*"):
 age_days = (pathlib.Path().stat().st_mtime - file.stat().st_mtime) / 86400
 if age_days > retention_days:
 file.unlink()
 # Enforce size limit
 total = sum(f.stat().st_size for f in log_dir.iterdir())
 while total > max_total_bytes:
 oldest = min(log_dir.iterdir(), key=lambda f: f.stat().st_mtime)
 total -= oldest.stat().st_size
 oldest.unlink()

cleanup_logs()
logger = get_logger()
logger.info("Log cleanup completed")
```

The above snippet is illustrative; the actual implementation resides in
`code/logging/verify_logging.py` and is executed automatically by the pipeline entry points.

---

## Accessing Logs

- **Interactive Exploration**: Use tools such as `jq`:
 ```bash
 jq. logs/run_20240629_143210.log | less
 ```
- **Programmatic Access**: Load logs into a Pandas DataFrame:
 ```python
 import pandas as pd
 df = pd.read_json("logs/run_20240629_143210.log", lines=True)
 ```
- **Search**: Filter by level or module:
 ```python
 df[df["level"] == "ERROR"]
 ```

---

## Versioning

The logging format is version‑controlled via the `log_format_version` field added to each entry
(currently set to `"1.0"`). Future changes to the schema will increment this version and maintain
backward compatibility where possible.

---

## References

- Python `logging` module documentation: https://docs.python.org/3/library/logging.html
- JSON Lines (Wikidata Q111841144, https://www.wikidata.org/wiki/Q111841144) format: https://jsonlines.org/
- Project’s logging implementation: `code/logging/pipeline_logger.py`

---

*This document is part of the project’s documentation suite and is tracked in version control.*