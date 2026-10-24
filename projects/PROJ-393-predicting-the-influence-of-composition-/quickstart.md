# Quickstart Guide: Heusler Alloy Hysteresis Prediction Pipeline

This guide provides instructions to run the full pipeline end‑to‑end.

## Prerequisites

- Python 3.11+
- Virtual environment (recommended)

## Setup

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

The full pipeline can be executed via the main entry point:

```bash
cd code
# The wrapper script runs the library entry point.
python main.py # equivalent to ``python -m src.main --full``
```

For a quick sanity‑check demo on the tiny manual dataset:

```bash
cd code
python -m src.main --demo # produces data/results/demo_metrics.json
```

The help message contains the required phrase:

```bash
cd code
python -m src.main --help # should include “Setup OK”
```

## Individual stages (optional)

```bash
# 1. Manual Curation (creates the template if missing)
python scripts/run_manual_curator.py

# 2. Preprocessing (standardises, normalises and filters)
python scripts/run_preprocessing.py

# 3. Feature Engineering (computes composition descriptors)
python scripts/run_feature_engineering.py

# 4. Model Training (Linear Regression + Random Forest)
python scripts/run_model_training.py

# 5. Final Report Generation
python scripts/run_final_report.py
```

## Output Artifacts

After successful execution, the following files will be generated:

- `data/raw/manual_curated.csv`
- `data/processed/alloys_raw.csv`
- `data/processed/alloys_features.csv`
- `data/results/demo_metrics.json` *(demo only)*
- `docs/reports/final_report.md`
- `docs/reports/statistical_limitations.md`
- `docs/reports/microstructure_note.md`
- `docs/reports/data_scarcity_warning.md`

## Troubleshooting

- **Missing manual file** – run `python scripts/run_manual_curator.py`.
- **Help does not contain “Setup OK”** – ensure you are using the updated
 ``src/main.py`` (the description now includes that phrase).
