# llmXive Follow-up: Extending Weak-to-Strong Generalization via Direct On-Policy Distillation

## Project Structure
- `code/`: Source code for data processing, model loading, training, and evaluation.
- `data/`: Raw, processed, and results artifacts.
- `config/`: Configuration files.
- `specs/`: Design documents.
- `docs/`: Documentation.

## Setup
1. Ensure Python 3.11 is installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Run experiments via scripts in `code/scripts/`.

## Constraints
- CPU-only execution (torch CPU index enforced).
- Max RAM 7GB (enforced via `hard_floor_enforcer`).
- No synthetic data fallbacks.