# llmXive Follow-up: Extending Multi-LCB to Multiple Programming Languages

**Project ID**: PROJ-869
**Status**: Active Research Pipeline

## Overview
This project implements an automated research pipeline to evaluate logic transfer capabilities of LLMs across multiple programming languages (Rust, Kotlin, Go) by extending the LiveCodeBench dataset.

## Directory Structure
- `code/`: Core Python implementation modules
- `data/`: Raw and processed datasets, logs, and results
 - `raw/`: Original dataset downloads
 - `processed/`: Filtered and enriched data
- `tests/`: Unit and integration tests
- `specs/`: Feature specifications and design documents
- `figures/`: Generated plots and visualizations
- `scripts/`: Utility scripts for data management

## Prerequisites
- Python 3.10+
- See `requirements.txt` for dependencies

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Setup data directories: `python code/setup_data_structure.py`
3. Run feasibility gate: `python code/feasibility_gate.py`
4. Execute pipeline: `python code/main.py`

## Data Sources
- Primary Dataset: Multi-LiveCodeBench (HuggingFace)
- Model: GGUF quantized models via `llama-cpp-python`

## License
Research use only.
