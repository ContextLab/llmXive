# Quick Start Guide

This guide walks you through executing the full pipeline on the test dataset.

## Prerequisites

- Python 3.11+
- `pip`
- ~14 GB free disk space
- Internet access (for data download)

## Installation

1. **Clone and Setup**:
```bash
git clone <repo-url>
cd projects/PROJ-252-exploring-the-correlation-between-atmosp
```

2. **Create Virtual Environment**:
```bash
python -m venv.venv
source.venv/bin/activate # On Windows:.venv\Scripts\activate
```

3. **Install Frozen Dependencies** (exact versions are pinned):
```bash
pip install -r requirements.txt
```

## Running the Pipeline

The pipeline is executed via a single command that ensures reproducibility:

```bash
pip install -r requirements.txt && python -m code.seed_init && python -m code.main
```

### Expected output

- The seed initialization script creates `logs/seed_initialization.log` containing the line:
 ```
 Seeds set to 42
 ```
- The script prints `Seed initialization complete.` and exits with code 0.
- `python -m code.main` runs the (currently placeholder) main entry point and exits with code 0.

## Validation

To verify the setup:

```bash
# Verify that the log was created and contains the correct line
grep "Seeds set to 42" logs/seed_initialization.log
```

If the command returns the line without error, the quick‑start setup is successful.
