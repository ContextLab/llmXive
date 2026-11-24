# Quickstart Guide: Gut Microbiome and Cognitive Decline Analysis

This guide describes how to set up the environment and verify data provenance for the microbiome-cognition analysis pipeline.

## Prerequisites

- Python 3.11+
- 7 GB available RAM (Resource limit enforced during pipeline execution)
- Access to the American Gut Project (AGP) and Health and Retirement Study (HRS) data.

## Setup

1. **Clone the Repository**
 ```bash
 git clone <repo-url>
 cd projects/PROJ-189-investigating-the-correlation-between-gu
 ```

2. **Install Dependencies**
 ```bash
 pip install -r code/requirements.txt
 ```

## Validation

Before running the main analysis, verify that the data sources are reachable and the resource guards are active:

```bash
python code/validate_provenance.py
```

This script:
- Checks connectivity to the **American Gut Project** (via HF `datasets` or the official Qiita portal).
- Checks connectivity to the **HRS data portal**.
- Records system RAM and CPU count to `data/provenance_report.json`.
- Exits with status `0` if all sources are reachable.

## Execution

Run the pipeline in the following order:

```bash
python code/01_data_ingestion.py
python code/02_preprocessing.py
python code/03_correlation_analysis.py
python code/04_predictive_modeling.py
python code/05_sensitivity_analysis.py
```

## Verification

- **Provenance**: Ensure `data/provenance_report.json` exists and `agp_accessible` is `true`.
- **Results**: Check `data/results/` for final summaries and `figures/` for analysis plots.
- **Contracts**: Run `pytest tests/contract/` to validate output schemas.