# Quickstart: Evaluating Uncertainty Calibration and Extrapolation Error of Machine Learning for High‑Entropy Alloy Compositions

## Prerequisites
* Python 3.11 or newer
* Git
* Internet access (to download the repository; the placeholder CSV is bundled)

## Installation

```bash
git clone <REPO_URL>
cd projects/PROJ-145-evaluating-the-predictive-power-of-machi
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Full Pipeline

```bash
python code/run_pipeline.py
```

The script executes all phases sequentially and writes artifacts under `data/`.  
**Note:** The current run uses a bundled placeholder dataset (`data/raw/hea_placeholder.csv`). A scope‑revision request has been filed to replace this with a verified open HEA dataset (e.g., Materials Project or AFLOW Parquet files). Once the verified dataset is available, re‑run the pipeline to obtain scientifically valid results.

## Manual Stage Execution (optional)

| Stage | Command | Output |
|---|---|---|
| **0 – Data Ingestion & Candidate Generation** | `python code/data_ingestion.py` | `data/processed/heas_train.csv`, `holdout_known.csv`, `true_novel.csv` |
| **1 – Feature Engineering** | `python code/feature_engineering.py` | `data/processed/heas_train_features.csv` |
| **2 – Model Training** | `python code/model_training.py` | `models/rf_model.pkl`, `models/gb_model.pkl` |
| **3 – Evaluation & Report** | `python code/evaluation.py` | `data/results/report.csv` |

## Validation Note
Each generated CSV/JSON file is automatically validated against the corresponding JSON‑Schema in `specs/…/contracts/`. Validation failures will halt execution and print the schema‑error details.

## Testing Infrastructure
The repository includes a minimal test suite:

```
tests/
├── unit/
│   ├── __init__.py
│   └── test_descriptors.py
└── integration/
    ├── __init__.py
    └── test_pipeline.py
```

Run the tests with:

```bash
pytest -q
```

The tests verify checksum validation, exponential backoff logic, and schema conformity for all output artifacts.

## Expected Files
* `data/processed/heas_train.csv`
* `data/processed/holdout_known.csv`
* `data/processed/true_novel.csv`
* `data/processed/heas_train_features.csv`
* `models/rf_model.pkl`, `models/gb_model.pkl`
* `data/results/report.csv`

## Troubleshooting
* **Missing placeholder data** – The pipeline aborts with a clear error if `hea_placeholder.csv` is absent or its checksum does not match `config.EXPECTED_DATASET_CHECKSUM`. Replace the file with a correctly formatted CSV and update the checksum in `code/config.py`.  
* **Memory errors** – If a `MemoryError` occurs, set `STREAMING=True` in `code/data_ingestion.py` to enable chunked processing.  
* **Insufficient novel samples** – If fewer than 10 novel candidates survive the distance filter, the Spearman test is skipped and the report notes “insufficient samples (<10)”.  
