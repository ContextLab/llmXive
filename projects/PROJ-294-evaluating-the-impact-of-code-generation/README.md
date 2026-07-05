# PROJ-294: Evaluating the Impact of Code Generation Models on Code Testability

## Project Overview
This project investigates how different code generation models (specifically CodeGen variants) impact the testability, complexity, and functional correctness of generated code.

## Directory Structure
- `code/`: Python implementation modules
- `data/`: Raw datasets and generated analysis outputs
- `state/`: Artifact tracking and hash verification
- `results/`: Generated figures and final reports
- `tests/`: Unit and integration tests
- `specs/`: Feature specifications and design documents

## Prerequisites
- Python 3.9+
- See `code/requirements.txt` for dependencies

## Quick Start
1. Install dependencies: `pip install -r code/requirements.txt`
2. Run data acquisition: `python code/download_data.py`
3. Generate code: `python code/generate_code.py`
4. Analyze metrics: `python code/analyze_metrics.py`
5. Run statistical tests: `python code/statistical_tests.py`
6. Generate report: `python code/report_generator.py`
