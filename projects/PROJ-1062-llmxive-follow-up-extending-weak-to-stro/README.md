# llmXive: Weak-to-Strong Generalization via Direct On-Policy Distillation

## Project Overview
This project implements the automated science pipeline for validating weak-to-strong generalization across different model architectures (Transformer, MoE, SSM).

## Directory Structure
The project follows a standard structure:
- `src/`: Source code for the research pipeline (as per plan)
- `code/`: Implementation code (matching current API surface)
- `data/`:
 - `raw/`: Raw downloaded datasets
 - `processed/`: Preprocessed and cleaned data
 - `results/`: Experiment outputs and metrics
- `tests/`: Unit and integration tests
- `contracts/`: API and data contracts
- `artifacts/`: Final experiment artifacts and hashes

## Setup
1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
2. Initialize project structure:
 ```bash
 python code/setup_project_structure.py
 ```

## Constraints
- **CPU-Only**: All training must run on CPU with <= 7GB RAM.
- **Quantization**: Use int8 quantization for MoE and SSM models.
- **Batch Size**: Hard floor of batch_size=1 with gradient accumulation.
- **Data**: No synthetic data fallbacks; failed real data fetches must raise errors.

## Execution
Run the pipeline using the scripts in `code/scripts/`.
Refer to `tasks.md` for the implementation roadmap.
