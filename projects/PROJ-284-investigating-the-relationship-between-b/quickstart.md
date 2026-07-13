# Quickstart

This document describes the steps to run the full analysis pipeline on a
clean checkout of the repository.

## Prerequisites

* Python 3.11+
* All dependencies installed (`pip install -r requirements.txt`)

## Steps

1. **Download & preprocess** (synthetic validation is performed automatically):
 ```bash
 python code/main.py download_preprocess
 ```

2. **Extract metrics**:
 ```bash
 python code/main.py extract_metrics
 ```

3. **Run analysis** (this will invoke the PCA, factor‑score generation and the
 full‑metrics merge implemented in `code/analysis/correlations.py`):
 ```bash
 python code/main.py analyze
 ```

4. **Generate visualisations and report**:
 ```bash
 python code/main.py viz_report
 ```

After the pipeline finishes, you will find the following artefacts in
`data/analysis/`:

* `pca_loadings.csv`
* `factor_scores.csv`
* `full_metrics.csv`

These files are consumed by the reporting step (`code/report/generate.py`).