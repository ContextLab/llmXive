# PROJ-874-llmxive-follow-up-extending-enhancing-tr

## Directory Structure

This project follows the llmXive automated science pipeline structure:

- `code/`: Source code modules and scripts
- `data/`: Data artifacts
 - `raw/`: Original downloaded datasets
 - `processed/`: Intermediate processed data
 - `results/`: Final outputs (videos, metrics, reports)
- `tests/`: Test suites
 - `contract/`: Contract tests for data schemas
 - `integration/`: End-to-end pipeline tests
 - `unit/`: Unit tests for individual functions
- `docs/`: Documentation

## Quick Start

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Run the pipeline (after implementing tasks):
 ```bash
 python code/generate.py --mode baseline-full
 ```