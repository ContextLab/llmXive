# Plant Disease Susceptibility Prediction Pipeline

This project implements an automated pipeline for predicting plant disease susceptibility
from publicly available genomic and environmental data.

## Setup

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Configure linting and formatting (Task T005):
 ```bash
 python code/src/utils/linting_config.py
 ```

3. Format code:
 ```bash
 black code/
 ```

4. Run linter:
 ```bash
 ruff check code/
 ```

5. Run tests:
 ```bash
 pytest tests/
 ```

## Project Structure

```
.
├── code/
│ ├── src/
│ │ ├── ingestion/
│ │ ├── modeling/
│ │ ├── models/
│ │ └── utils/
│ ├── tests/
│ ├── data/
│ │ ├── raw/
│ │ └── processed/
│ └── models/
├── data/
├── templates/
└── specs/
```

## Linting and Formatting

This project uses:
- **Black** for code formatting
- **Ruff** for linting

Configuration is stored in `pyproject.toml` and `.ruff.toml`.

## Running the Pipeline

See `quickstart.md` for detailed instructions on running the full pipeline.
