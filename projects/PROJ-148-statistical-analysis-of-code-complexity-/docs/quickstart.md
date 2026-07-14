# Quickstart Guide: Statistical Analysis of Code Complexity

This guide provides the minimal steps to run the full research pipeline: from downloading real Java projects to generating the final bug prediction model and reports.

## Prerequisites

- Python 3.11+
- pip (package installer)
- ~2GB free disk space (for downloaded archives and extracted metrics)

## 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Run the Data Pipeline

This single command executes the full data acquisition, metric extraction, labeling, and preprocessing steps. It will:
1. Download ≥10 Java projects from GHTorrent.
2. Extract source files and commit metadata.
3. Compute complexity metrics (Cyclomatic, LOC, etc.) using `lizard`.
4. Label bug-fix occurrences.
5. Clean and split the data (70% train / 30% test).

**Output**: `data/processed/bug_complexity_dataset.csv`, `data/splits/train.csv`, `data/splits/test.csv`

```bash
python code/data/pipeline.py
```

*Note: The first run may take 10-20 minutes depending on network speed and disk I/O.*

## 3. Train Models

Once the dataset is ready, train the primary (L1 Logistic Regression) and alternative (Random Forest) models.

**Output**: `data/model/primary.pkl`, `data/model/alternative.pkl`, `data/model/metrics.json`

```bash
python code/modeling/pipeline.py
```

## 4. Evaluate and Generate Reports

Evaluate model performance, apply statistical corrections, generate Partial Dependence Plots (PDPs), and compile the final research report.

**Outputs**:
- `data/model/corrected_pvalues.csv`
- `figures/pdp_top3.png`
- `data/model/thresholds.csv`
- `report/research_report.html`

```bash
python code/report/generate_report.py
```

## 5. Verify Results

Run the test suite to ensure all constraints (e.g., ROC-AUC ≥ 0.50, FDR ≤ 0.05) are met:

```bash
python code/run_tests.py
```

## Troubleshooting

- **Missing Data**: If the pipeline fails to download, ensure you have internet access and that GHTorrent mirrors are reachable.
- **Lizard Errors**: Unparsable files are skipped automatically; check logs in `logs/pipeline.log` for warnings.
- **Memory Issues**: The pipeline uses chunked processing; reduce `MAX_FILES_PER_CHUNK` in `code/data/extract_metrics.py` if OOM occurs.

## Citation

If you use this pipeline in your research, please cite the project documentation and the `lizard` complexity analyzer.