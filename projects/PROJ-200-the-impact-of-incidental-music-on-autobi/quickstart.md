# Quickstart: The Impact of Incidental Music on Autobiographical Memory Retrieval

## Prerequisites
- Python 3.11+
- `pip`

## Installation
1. **Clone the repository** and enter the project root.
2. **Create a virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # Windows: venv\Scripts\activate
 ```
3. **Install pinned dependencies**
 ```bash
 pip install -r requirements.txt
 ```

## Running the Demo
The demo runs a minimal, no‑data pipeline that verifies the codebase can be
executed without errors.

```bash
python -m code.main --demo
```

This command should exit with status 0 and print a short log message. [UNRESOLVED-CLAIM: c_692be648 — status=not_enough_info]

## Full Pipeline (for later phases)
When the full data ingestion and analysis steps are ready, the pipeline can be
executed with:
```bash
python -m code.main --full-run
```

## Project Layout
The repository follows the canonical layout:
```
code/ # Source code
data/
 raw/ # Raw input files
 processed/ # Intermediate parquet files
 final/ # Final CSV/PNG results
tests/ # pytest test suite
```

The `setup_project.py` script (run automatically on first import) ensures these
directories exist.
