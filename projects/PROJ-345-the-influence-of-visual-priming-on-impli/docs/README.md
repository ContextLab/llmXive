# llmXive Project: The Influence of Visual Priming on Implicit Attitudes

## Overview
This project implements an automated scientific pipeline to analyze the influence of visual priming on implicit attitudes towards ambiguous social stimuli. It adheres to strict data integrity principles (Principle V & VI) and reproducibility standards.

## Project Structure
- `code/`: Core Python implementation modules
- `data/`: Raw, processed, and stimulus data
 - `raw/`: Original downloaded datasets
 - `processed/`: Cleaned, linked, and aggregated data
 - `primes/`: Visual prime stimuli images
 - `targets/`: Target stimuli images
- `state/`: Version control and execution logs
- `tests/`: Unit and integration tests
- `docs/`: Documentation
- `reports/`: Generated PDF reports and analysis summaries

## Prerequisites
- Python 3.11+
- Dependencies listed in `requirements.txt`

## Quick Start
1. **Setup Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

2. **Initialize Project State**:
 ```bash
 python code/run_state_init.py
 ```

3. **Run Data Ingestion**:
 ```bash
 python code/data/ingest.py
 ```
 *Note: This downloads real data from verified OSF repositories.*

4. **Run Preprocessing & Modeling**:
 ```bash
 python code/data/preprocess.py
 python code/models/lmm.py
 ```

5. **Generate Report**:
 ```bash
 python code/reports/generate_report.py
 ```

## Data Integrity & Safety
- **Principle V (Versioning)**: All artifacts are tracked in `state/projects/PROJ-345/state.yaml`.
- **Principle VI (Distinct Stimulus Sets)**: Primes and targets are validated to ensure no premature merging.
- **PII Scanning**: Run `python code/main.py --scan-pii` to ensure no personally identifiable information leaks into processed data.

## Limitations
This pipeline produces **associational** findings only. Prime valence is derived via VAD inference models, and human-rated ambiguity is required for valid interaction testing. Synthetic derivation of ambiguity is strictly prohibited per project design constraints.
