# PROJ-913: llmXive Follow-up - OPD Generalization Gap in Unified Diffusion

## Project Overview
This project investigates the "Out-of-Distribution (OOD) Generalization Gap" in unified diffusion models, specifically comparing a base model against an RL-unified variant. The research focuses on whether Reinforcement Learning (RL) fine-tuning improves performance on In-Distribution (ID) data while degrading performance on OOD data (the generalization gap).

## Structure
- `code/`: Python source code for data acquisition, inference, and analysis.
- `data/`: Storage for prompts, models, and generated outputs.
- `tests/`: Unit and integration tests.
- `specs/`: Research design documents and user stories.

## Prerequisites
- Python 3.9+
- PyTorch (CPU-only version recommended for this pipeline)
- Hugging Face `diffusers`, `transformers`, `datasets`
- `scikit-learn`, `pandas`, `numpy`, `statsmodels`

## Quick Start
1. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
2. Set up data directories:
 ```bash
 python code/utils/setup_data_dirs.py
 ```
3. Run the pipeline (see `code/` scripts for specific stages).

## Execution Order
Refer to `tasks.md` for the strict dependency graph (T015a -> T016 -> T020a -> T034 -> T015b ->...).
