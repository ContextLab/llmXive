# Quickstart Guide: PROJ-008 Psychology Research

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Access to ClinicalTrials.gov and OSF APIs

## Installation

1. Clone the repository and navigate to the project root:
 ```bash
 cd projects/PROJ-008-psychology-research
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Verification

Run the test suite to verify the environment:
```bash
pytest tests/ -v
```

## Data Collection

The data collector (Task T014) will download raw study metadata from ClinicalTrials.gov and OSF. Ensure network access is available.

## Execution

To run the full pipeline:
```bash
python code/data/collector.py
python code/data/extractor.py
python code/data/cleaner.py
python code/analysis/effect_sizes.py
python code/analysis/meta_analysis.py
python code/viz/plots.py
```

Refer to `docs/analysis-plan.md` for methodological details.
