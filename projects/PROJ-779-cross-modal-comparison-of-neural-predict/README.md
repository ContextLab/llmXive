# llmXive: Cross-Modal Comparison of Neural Prediction Error Signals

## Project Overview
This project implements an automated pipeline to compare neural prediction error signals across auditory and visual modalities using real OpenNeuro datasets (ds000246, ds000117). [UNRESOLVED-CLAIM: c_952341b7 — status=not_enough_info]

## Prerequisites
- Python 3.9+
- Virtual Environment (venv)

## Setup

1. **Create and Activate Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

3. **Install Development Tools (Linting & Formatting)**:
 ```bash
./scripts/setup_linting.sh
 ```
 *Alternatively, manually install:*
 ```bash
 pip install black ruff pre-commit
 pre-commit install
 ```

## Development Workflow

- **Formatting**: Code is automatically formatted using Black.
 ```bash
 black code/
 ```

- **Linting**: Code is checked using Ruff.
 ```bash
 ruff check code/
 ```

- **Pre-commit**: Run checks before every commit.
 ```bash
 pre-commit run --all-files
 ```

## Data Policy
**Real Data Only**: This project strictly uses data from OpenNeuro (ds000246, ds000117). No synthetic data is generated. [UNRESOLVED-CLAIM: c_6e343bbf — status=not_enough_info]

## License
MIT