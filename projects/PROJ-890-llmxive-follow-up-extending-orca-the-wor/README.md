# PROJ-890: llmXive Follow-up: Extending "Orca: The World is in Your Mind"

## Project Overview
This project implements a follow-up study to "Orca: The World is in Your Mind," focusing on extracting counterfactual reasoning capabilities from a frozen vision-language model without GPU resources.

## Structure
- `specs/`: Feature specifications and design documents
- `code/`: Implementation modules (data, models, utils, analysis)
- `data/`:
 - `raw/`: Original dataset downloads
 - `processed/`: Filtered datasets and extracted latents
 - `validation/`: Physics verification results and benchmarks
- `tests/`: Unit and integration tests
- `figures/`: Generated plots and visualizations

## Prerequisites
- Python 3.11+
- CPU-only environment (no GPU required)
- See `requirements.txt` for dependencies

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Run data download: `python code/data/download_orca.py`
3. Extract latents: `python code/data/extract_latents.py`
4. Train models and compare: `python code/models/train_readout.py`

## Key Constraints
- **CPU-Only**: All operations must run on CPU with dynamic batch sizing.
- **Real Data**: No synthetic data generation; all results must come from real datasets.
- **Audit Logging**: All skipped files and ambiguous prompts must be logged.
