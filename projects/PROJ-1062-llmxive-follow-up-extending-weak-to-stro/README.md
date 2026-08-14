# llmXive Follow-up: Extending Weak-to-Strong Generalization

Research pipeline for validating cross-architecture signal transfer via Direct On-Policy Distillation.

## Setup

1. Ensure Python 3.11 is installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Run data download scripts in `code/data/`.
4. Execute training scripts in `code/scripts/`.

## Structure

- `code/`: Source code
 - `core/`: Training, evaluation, memory monitoring
 - `data/`: Data loading and preprocessing
 - `models/`: Model loaders
 - `scripts/`: Experiment runners
 - `tests/`: Test suite
- `data/`: Raw and processed data (generated at runtime)
- `projects/`: Project-specific configuration and structure
