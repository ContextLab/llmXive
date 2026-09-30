# Quick Start Guide for PROJ-485

## Prerequisites
- Python 3.11+
- pip

## Installation
1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline
The main orchestrator handles the full execution flow:
```bash
python code/main.py
```

This command will:
1. Validate configuration
2. Seed elemental properties (if missing)
3. Ingest real data and generate descriptors
4. Train models and perform LOSO cross-validation
5. Generate visualizations and fidelity reports

## Output Artifacts
Upon successful completion, the following files will be generated:
- `data/raw/elemental_properties.csv`
- `data/processed/descriptors.csv`
- `data/artifacts/baseline_comparison.json`
- `data/artifacts/fidelity_report.json`
- `data/artifacts/tcs_report.json`
- `data/artifacts/resource_log.json`
- `data/artifacts/plots/*.png`
