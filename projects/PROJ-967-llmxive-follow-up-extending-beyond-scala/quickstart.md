# Quickstart Guide: llmXive Follow-up (Teacher Entanglement vs. Scalar Distillation Loss)

## Project Overview

This project analyzes the relationship between teacher model entanglement (correlated rubric dimensions) and the performance of scalar distillation loss in student models, using the Z-Reward dataset.

**Repository**: `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/`

**Key Findings Goal**: Determine if high entanglement in teacher distributions correlates with higher fidelity loss when training student models on scalar rewards.

## Prerequisites

- Python 3.11+
- pip
- ~14GB disk space (for dataset and processed features)
- ~7GB RAM (minimum for streaming dataset processing)

## Setup

1. **Clone and Navigate**:
 ```bash
 cd projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/
 ```

2. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```
 *Dependencies include: `pandas`, `numpy`, `scikit-learn`, `requests`, `huggingface_hub`, `pyarrow`.*

3. **Verify Environment**:
 Ensure `python --version` returns 3.11.x.

## Pipeline Execution

The pipeline consists of three main stages: Ingestion, Feature Engineering, and Modeling.

### Step 1: Data Ingestion

Downloads the Z-Reward dataset, validates the schema, and aligns teacher/student outputs.

```bash
python code/ingest.py
```

**Outputs**:
- `data/raw/zreward_dataset.csv`: The raw dataset (verified via SHA256).
- Prints a summary of sample counts, missing data flags, and dimension coverage.

*Note: If the dataset is large, this script uses chunked loading to stay within memory limits.*

### Step 2: Feature Engineering

Calculates statistical descriptors (variance, entropy, skewness, kurtosis) and the global entanglement score. Computes the "dimensional fidelity loss" for each sample.

```bash
python code/features.py
```

**Outputs**:
- `data/processed/features.json`: A JSON file containing per-sample statistics and the global entanglement score.

**Key Logic**:
- **Global Entanglement**: Computed via the dominant eigenvalue of the global covariance matrix across all samples.
- **Fidelity Loss**: MAE between the student scalar prediction and the human-annotated score for the *primary* quality dimension (identified via metadata).

### Step 3: Predictive Modeling

Trains a Random Forest regressor to predict fidelity loss using entanglement features. Includes 5-fold cross-validation and a permutation test for statistical significance.

```bash
python code/train.py
```

**Outputs**:
- `results/results.json`: Contains R², MAE, and the permutation test p-value.

**Configuration**:
- Model: `RandomForestRegressor` (CPU-only, `n_jobs=2`).
- Validation: 5-fold stratified cross-validation.
- Significance Test: Non-parametric permutation test comparing model MAE against a null baseline.

## Verification

To ensure the entire pipeline ran correctly and reproduced the expected artifacts:

```bash
python code/validate_quickstart.py
```

This script checks:
- Directory structure (`data/raw`, `data/processed`, `results`).
- Existence and validity of `zreward_dataset.csv`, `features.json`, and `results.json`.
- Correctness of the results content (R² > 0, p-value < 0.05 expected for significance).

## Troubleshooting

- **Memory Errors**: Ensure the dataset is processed in chunks. The `ingest.py` and `features.py` scripts are designed to stream data where possible.
- **Missing Data**: If `validate_quickstart.py` reports missing files, re-run the preceding stage (e.g., run `ingest.py` again if `zreward_dataset.csv` is missing).
- **Schema Mismatch**: If ingestion fails, verify the Z-Reward source URL and checksum in `code/ingest.py`.

## Output Artifacts Summary

| File | Description |
|:--- |:--- |
| `data/raw/zreward_dataset.csv` | Raw Z-Reward dataset with teacher logits and human annotations. |
| `data/processed/features.json` | Engineered features including entanglement scores and fidelity loss. |
| `results/results.json` | Final model metrics (R², MAE, p-value). |
| `code/requirements.txt` | Python dependencies. |
| `quickstart.md` | This guide. |