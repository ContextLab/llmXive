# The Impact of Ambient Noise on Cognitive Flexibility in Remote Workers

**Project ID**: PROJ-114

## Overview
This project implements an automated research pipeline to analyze the impact of ambient noise levels on cognitive flexibility in remote workers. It includes data ingestion, calibration, statistical modeling (Linear Mixed Effects), and sensitivity analysis.

## Prerequisites
- Python 3.11+
- pip

## Installation
1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure
- `code/`: Source code for data ingestion, modeling, and analysis.
- `data/`: Raw, processed, and model artifacts.
- `contracts/`: JSON Schema definitions for data validation.
- `docs/`: Documentation, including power analysis and paper drafts.
- `tests/`: Unit and integration tests.
- `state/`: Project state tracking and artifact hashes.

## Quick Start
See `docs/quickstart.md` for instructions on running the synthetic data generation and ingestion pipeline.

## License
MIT
