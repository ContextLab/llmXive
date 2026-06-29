# Quickstart Guide

This guide walks you through setting up the **Statistical Analysis of Code Complexity** project and running the full end‑to‑end pipeline, from data acquisition to model evaluation and report generation.

## 1. Prerequisites

- **Python 3.11** (or later) installed and available on `PATH`.
- **Git** (for cloning the repository if you haven't already).
- Internet access (the pipeline downloads Java projects from GHTorrent).

## 2. Clone the Repository

```bash
git clone
cd statistical-analysis-of-code-complexity
```

## 3. Create a Virtual Environment & Install Dependencies

```bash
python -m venv.venv
source.venv/bin/activate # On Windows use `.venv\\Scripts\\activate`
pip install -r requirements.txt
```

The `requirements.txt` file pins the exact versions of all third‑party libraries used in the project (e.g., `pandas`, `scikit-learn`, `lizard`, `statsmodels`, `matplotlib`, `seaborn`, `pymer4`, `pytest`, `black`, `flake8`).

## 4. Run the Data Pipeline

The data pipeline consists of several stages, each implemented as a standalone script under `code/data/`. Run them **in order**:

1. **Download Java projects** (≥10 projects) from GHTorrent:

 ```bash
 python code/data/download_gh.py
 ```

2. **Extract source files and commit metadata**:

 ```bash
 python code/data/extract_commits.py
 ```

3. **Compute code‑complexity metrics** using *lizard* (cyclomatic complexity, LOC, token count, nesting depth, Halstead volume):

 ```bash
 python code/data/extract_metrics.py
 ```

4. **Label bug‑fix vs. non‑bug‑fix units** based on commit messages and issue IDs:

 ```bash
 python code/data/label_bug_fixes.py
 ```

5. **Validate bug‑label reliability** (precision ≥ 85 %):

 ```bash
 python code/data/validate_bug_labels.py
 ```

6. **Preprocess the dataset** (impute missing values, log‑transform skewed metrics, drop rows with excessive missing data):

 ```bash
 python code/data/preprocess.py
 ```

7. **Create a stratified train/test split** (30 % test, stratified by project):

 ```bash
 python code/data/split_dataset.py
 ```

After successful execution, you will find the processed dataset and split files under `data/processed/`:

- `dataset.parquet` – the full cleaned dataset.
- `train.parquet` – training split.
- `test.parquet` – test split.

## 5. Train Predictive Models

Two models are trained for bug prediction:

1. **Primary model** – L1‑regularized logistic regression (converges within 100 iterations):

 ```bash
 python code/modeling/train_primary.py
 ```

2. **Alternative model** – Random Forest (default 100 trees, max depth 10):

 ```bash
 python code/modeling/train_alternative.py
 ```

The trained model objects and evaluation metrics are saved in `data/model/`:

- `primary.pkl`
- `alternative.pkl`
- `evaluation_metrics.json`

## 6. Model Evaluation & Post‑Processing

Run the evaluation script to compute ROC‑AUC, PR‑AUC, and calibration plots:

```bash
python code/modeling/evaluate.py
```

Apply multiple‑hypothesis correction (Benjamini–Hochberg) and export corrected p‑values:

```bash
python code/modeling/correct_pvalues.py
```

Generate Partial Dependence Plots for the three most important metrics:

```bash
python code/modeling/pdp.py
```

Derive practical bug‑probability thresholds and write them to CSV:

```bash
python code/modeling/generate_thresholds.py
```

All visualisations are saved under `figures/` and CSV files under `data/model/`.

## 7. Generate the Research Report

Finally, compile a concise report (HTML) that aggregates tables, plots, and interpretation of the findings:

```bash
python code/report/generate_report.py
```

The report will be written to `reports/report.html`.

## 8. Run the Test Suite

The project includes contract, integration, and unit tests. Ensure everything works:

```bash
pytest -q
```

Expected outcome: all tests pass, and code coverage is ≥ 85 %.

## 9. Clean Up

Temporary files (downloaded archives, intermediate parquet files) can be removed with:

```bash
python code/utils/cleanup.py
```

## 10. Further Reading

- **Design Documents**: See `/specs/001-statistical-analysis-of-code-complexity/` for detailed specifications.
- **Data Model**: Refer to `data-model.md` for schema definitions.
- **Contract Schemas**: `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml`.

---

You now have a reproducible end‑to‑end workflow for analyzing code complexity metrics and predicting bug‑prone code units. Happy researching!