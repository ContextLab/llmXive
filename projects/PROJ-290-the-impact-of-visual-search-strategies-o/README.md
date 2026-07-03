# The Impact of Visual Search Strategies on Attentional Capture by Emotional Faces

**Project ID**: PROJ-290

## Overview
This project investigates how visual search strategies influence attentional capture by emotional faces.
It implements a reproducible pipeline for downloading eye-tracking datasets, extracting features,
classifying search strategies, and performing statistical analysis.

## Requirements
- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Project Structure
- `code/`: Source code modules
- `data/`: Raw and processed data
- `results/`: Analysis outputs and figures
- `tests/`: Unit and integration tests
- `state/`: Artifact hashes and state tracking

## Quick Start
1. Set up the environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```
2. Run the data download and validation pipeline:
 ```bash
 python code/data/download.py
 python code/data/validate.py
 ```
3. Run feature extraction and classification:
 ```bash
 python code/features/extraction.py
 python code/features/classification.py
 ```
4. Run statistical analysis:
 ```bash
 python code/analysis/lmm.py
 ```

## Configuration
Environment variables can be set to override defaults in `code/config.py`.
Key variables:
- `LLMXIVE_DATA_ROOT`: Root directory for data (default: `data/`)
- `LLMXIVE_LOG_LEVEL`: Logging level (default: `INFO`)

## License
Internal research use only.
