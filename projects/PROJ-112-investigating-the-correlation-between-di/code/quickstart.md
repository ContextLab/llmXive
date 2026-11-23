# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip

## Setup

1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Configure linting and formatting:
 ```bash
./scripts/config_linters.sh
 ```

## Running the Pipeline

Execute the main pipeline:
```bash
python src/main.py
```

## Linting and Formatting

Run linting checks:
```bash
ruff check.
```

Format code:
```bash
black.
```