# PROJ-1062: llmXive Follow-up: Extending Weak-to-Strong Generalization via Direct On-Policy Distillation

## Overview
This project implements and validates the "Weak-to-Strong Generalization" hypothesis across different model architectures (MoE and SSM) using Direct On-Policy Distillation (Direct-OPD) with Transformer teachers.

## Project Structure
- `code/`: Source code for data processing, model loading, training, and evaluation
- `data/`: Raw and processed datasets, experiment results
- `docs/`: Documentation and research notes
- `tests/`: Unit, integration, and contract tests
- `specs/`: Feature specifications and design documents

## Prerequisites
- Python 3.11+
- CPU-only execution environment (≤7GB RAM constraint)
- HuggingFace Hub access for dataset/model downloads

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Download and verify datasets: `python code/scripts/download_aime_verified.py`
3. Preprocess data: `python code/data/preprocess.py`
4. Run experiments: See user story scripts in `code/scripts/`

## Key Constraints
- All training must run on CPU with ≤7GB RAM
- No synthetic data fallbacks - real data only
- Strict memory monitoring and hard floor enforcement (batch_size=1)
- Statistical significance testing with multiple-comparison correction

## License
Research use only. See LICENSE file for details.
