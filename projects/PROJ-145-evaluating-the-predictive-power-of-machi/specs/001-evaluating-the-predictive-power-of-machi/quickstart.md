# Quickstart: Evaluating the Predictive Power of Machine Learning for Identifying Novel High‑Entropy Alloy Compositions

## Prerequisites
* Python 3.11+
* Git
* Internet access (to download the placeholder CSV bundled with the repo)

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-145-evaluating-the-predictive-power-of-machi
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Full Pipeline

```bash
python code/run_pipeline.py
```

The script executes the three major stages in order and writes all artifacts under `data/`.

## Manual Stage Execution (optional)

| Stage | Command | Output |
|---|---|---|
| **0 – Data Ingestion & Candidate Generation** | `python code/data_ingestion.py` | `data/processed/heas_train.csv`, `holdout_known.csv`, `true_novel.csv` |
| **1 – Feature Engineering** | `python code/feature_engineering.py` | `data/processed/heas_train_features.csv` |
| **2 – Model Training** | `python code/model_training.py` | `models/rf_model.pkl`, `models/gb_model.pkl` |
| **3 – Evaluation & Report** | `python code/evaluation.py` | `data/results/report.csv` |

## Expected Files
* `data/processed/heas_train.csv`
* `data/processed/holdout_known.csv`
* `data/processed/true_novel.csv`
* `data/processed/heas_train_features.csv`
* `models/rf_model.pkl`, `models/gb_model.pkl`
* `data/results/report.csv`

## Troubleshooting
* **Missing HEA data** – The pipeline aborts with a clear error if the placeholder CSV is absent or its checksum does not match `config.EXPECTED_AFLOW_CHECKSUM`. Replace the file with a correctly formatted CSV and update the checksum in `code/config.py`.  
* **Memory errors** – If `pandas` raises a MemoryError, set `STREAMING=True` in `code/data_ingestion.py` to enable chunked processing.  
* **Insufficient novel samples** – If fewer than 10 novel candidates survive the distance filter, the Spearman test is skipped and the report notes “insufficient samples”.

---
