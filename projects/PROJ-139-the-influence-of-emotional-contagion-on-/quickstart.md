# Quick Start Guide

## Prerequisites
- Python 3.11 or higher
- pip package manager

## Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Directory Structure
The project follows a standard research pipeline structure:
- `code/`: Python source modules
- `data/raw/`: Raw data fetched from APIs (e.g., Reddit, Pushshift)
- `data/processed/`: Cleaned, extracted, and annotated data
- `state/`: Logs, execution state, and artifact checksums
- `docs/`: Final reports and paper drafts

## Running the Pipeline
The pipeline is executed via scripts in the `code/data/` directory.
Example:
```bash
python code/data/download.py
python code/data/extract.py
```

## Testing
Run the test suite with:
```bash
pytest code/tests/
```

## Configuration
API keys and dataset paths should be configured via environment variables or a local `config.yaml` (to be created in T006).