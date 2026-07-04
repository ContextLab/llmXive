# Quickstart: Gut Microbiome and Cognitive Decline Analysis

## Prerequisites

- Python 3.11+
- Git
- 7 GB available RAM (required for pipeline execution)
- **Data Access**: You must have obtained the official American Gut Project (Qiita ID) and Health and Retirement Study (HRS) data files. HRS data requires a Data Use Agreement.

## Setup

1. **Clone the Repository**
 ```bash
 git clone <repo-url>
 cd projects/PROJ-189-investigating-the-correlation-between-gu
 ```

2. **Create Virtual Environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install Dependencies**
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: This includes `scikit-bio`, `sparcc`, and `shap`.*

4. **Download Data**
 The pipeline expects raw data in `data/raw/`. You must manually download the official datasets:
 - **AGP**: Download from `.
 - **HRS**: Download from `https://hrs.isr.umich.edu/data` (after DUA approval).
 - Save files as `agp_taxa.csv` and `hrs_metadata.csv` in `data/raw/`.

## Execution

Run the full pipeline:
```bash
python code/01_data_ingestion.py
python code/02_preprocessing.py
python code/03_correlation_analysis.py
python code/04_predictive_modeling.py
python code/05_sensitivity_analysis.py
```

Or run the orchestrator (if available):
```bash
python code/run_pipeline.py
```

## Verification

1. **Check Outputs**: Verify `data/results/` contains `correlations.json` and `model_metrics.json`.
2. **Contract Tests**:
 ```bash
 pytest tests/contract/
 ```
 This validates that outputs match the schemas in `contracts/`.
3. **Resource Check**: Ensure the process did not exceed 7 GB RAM (monitor via system monitor).

## Troubleshooting

- **Fatal Coverage Gap**: If the pipeline terminates with "No shared participant IDs found", the research question is unanswerable with the current datasets. See `research.md` for scope redefinition options.
- **Memory Error**: If `MemoryError` occurs, reduce the `MAX_TAXA` variable in `code/02_preprocessing.py` or reduce the number of permutations in `04_predictive_modeling.py`.
- **Merge Failure**: If the merge yields < 500 samples, check the column names in `data/raw/` and ensure the `participant_id` column exists in both datasets.