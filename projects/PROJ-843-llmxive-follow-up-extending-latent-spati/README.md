# llmXive: Latent Spatial Memory for Video World Models

## Overview
This project implements a sparse latent spatial memory approach for video world models,
focusing on efficiency and geometric consistency on CPU-only environments.

## Prerequisites
- Python 3.11+
- CPU-only environment (GPU not required)
- Dependencies listed in `requirements.txt`

## Quickstart
1. Install dependencies: `pip install -r requirements.txt`
2. Run the full pipeline: `python code/main.py`
3. Validate results: `python code/eval/quickstart_validation_runner.py`

## Project Structure
- `code/`: Source code
- `data/`: Raw, processed, and results data
- `tests/`: Unit tests
- `specs/`: Design documents

## Validation
To ensure end-to-end reproducibility on CPU, run:
```bash
python code/eval/quickstart_validation_runner.py
```
This will verify all artifacts from T007 to T023.