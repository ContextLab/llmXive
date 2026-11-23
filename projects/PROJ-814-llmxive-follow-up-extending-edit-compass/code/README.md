# llmXive Follow-up: Extending Edit-Compass & EditReward-Compass

Automated science pipeline for analyzing image editing benchmarks.

## Project Structure

```
.
├── code/
│ ├── src/
│ │ ├── services/ # Core business logic
│ │ ├── models/ # ML model wrappers
│ │ ├── utils/ # Utility functions
│ │ ├── data-models/ # Pydantic models
│ │ └── cli/ # CLI entry points
│ ├── tests/
│ │ ├── unit/ # Unit tests
│ │ └── contract/ # Contract tests
│ ├── tools/ # Utility scripts
│ ├── requirements.txt
│ └── pyproject.toml
├── data/
│ ├── raw/ # Downloaded raw datasets
│ ├── filtered/ # Filtered dataset subsets
│ └── scores/ # Computed scores
├── outputs/ # Analysis reports and figures
└── specs/ # Feature specifications
```

## Setup

1. Install dependencies:
 ```bash
 cd code
 pip install -r requirements.txt
 ```

2. Initialize directory structure:
 ```bash
 python tools/setup_directories.py
 ```

3. Run the pipeline:
 ```bash
 python -m src.cli.main download-filter
 python -m src.cli.main score
 python -m src.cli.main analyze
 ```

## Configuration

- Linting: Ruff (`.ruff.toml`)
- Formatting: Black (`pyproject.toml`)
- Python Version: 3.11+
- Hardware: CPU-only (no CUDA)
