# The Impact of Ambient Noise on Cognitive Flexibility in Remote Workers

## Overview

This project implements a computational pipeline to test the "coffee shop effect" hypothesis: that moderate ambient noise levels enhance cognitive flexibility in remote workers compared to low (<45dB) or high (>65dB) noise levels [UNRESOLVED-CLAIM: c_a80e2583 — status=not_enough_info].

## Project Structure

```
.
├── code/ # Source code
│ ├── __init__.py
│ ├── config.py # Configuration and logging
│ ├── models.py # Data class definitions
│ ├── data_ingestion.py # Data loading and validation
│ ├── preprocess.py # Data preprocessing
│ ├── model_fitting.py # Statistical modeling
│ ├── sensitivity_analysis.py # Robustness checks
│ ├── robustness.py # Additional robustness utilities
│ ├── requirements.txt # Python dependencies
│ └── scripts/ # Utility scripts
│ ├── generate_synthetic_data.py
│ ├── power_analysis.py
│ ├── validate_calibration.py
│ ├── update_state.py
│ └── setup_linting.py
├── data/ # Data directory
│ ├── raw/ # Raw input data
│ ├── processed/ # Processed/cleaned data
│ └── models/ # Model outputs
├── tests/ # Test suite
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── docs/ # Documentation
│ ├── quickstart.md
│ └── paper_draft.md
├── contracts/ # JSON Schema contracts
│ └── dataset.schema.yaml
├── specs/ # Feature specifications
│ └── 001-ambient-noise-cognitive-flexibility/
│ ├── plan.md
│ ├── spec.md
│ ├── research.md
│ ├── data-model.md
│ └── tasks.md
├── state/ # Project state tracking
│ └── projects/
│ └── PROJ-114-.../
│ └── current_stage.yaml
├── logs/ # Application logs
├── pyproject.toml # Python project metadata
├── setup.cfg # Setup configuration
├── Makefile # Build targets
├──.flake8 # Flake8 configuration
├──.gitignore # Git ignore rules
└── README.md # This file
```

## Setup

1. **Create a virtual environment**:
 ```bash
 python3.11 -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. **Install dependencies**:
 ```bash
 make install
 # or
 pip install -r code/requirements.txt
 ```

3. **Configure linting** (optional):
 ```bash
 python code/scripts/setup_linting.py
 ```

## Running the Pipeline

See `docs/quickstart.md` for detailed instructions on running each phase of the analysis pipeline.

## Development

- **Lint code**: `make lint`
- **Format code**: `make format`
- **Run tests**: `make test`
- **Clean artifacts**: `make clean`

## Key Dependencies

- **Data Processing**: pandas, numpy
- **Statistical Analysis**: scipy, statsmodels, scikit-learn
- **Configuration**: pyyaml, jsonschema
- **Testing**: pytest
- **Code Quality**: flake8, black, isort

## Project Status

- [x] Phase 1: Setup (project structure)
- [ ] Phase 2: Foundational infrastructure
- [ ] Phase 3: User Story 1 (Data Collection Pipeline)
- [ ] Phase 4: User Story 2 (Statistical Analysis)
- [ ] Phase 5: User Story 3 (Robustness & Sensitivity)
- [ ] Phase 6: Reporting & Finalization

## References

- **Specification**: `specs/001-the-impact-of-ambient-noise-on-cognitive/spec.md`
- **Implementation Plan**: `specs/001-the-impact-of-ambient-noise-on-cognitive/plan.md`
- **Tasks**: `specs/001-the-impact-of-ambient-noise-on-cognitive/tasks.md`