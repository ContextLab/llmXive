# Quickstart: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

## 1. Prerequisites

* Python 3.11+
* Git
* Access to a GitHub Actions runner (or local environment with ≤7 GB RAM, ≤14 GB disk)

## 2. Installation

```bash
git clone <repo-url>
cd projects/PROJ-168-statistical-evaluation-of-dimensionality
pip install -r code/requirements.txt
```

**Key Dependencies** (pinned in `code/requirements.txt`):
* `scikit-learn==1.5.0`
* `scanpy==1.10.2`
* `umap-learn==0.5.6`
* `leidenalg==0.10.2`
* `scipy==1.14.0`
* `pandas==2.2.2`
* `numpy==2.0.0`
* `psutil==6.0.0`

## 3. Pre‑run Specification Check (NEW)

Before executing the main pipeline, run the **spec‑gap resolver** to ensure all required raw‑count sources are available:

```bash
python code/spec_gap_resolver.py
```

* This script implements Phase 0 (Data‑Gap Resolution).  
* If it exits with code 0, the spec has been updated to *Case‑Study* mode (or all raw counts were found) and the pipeline may proceed.  
* If it exits with code 1, the pipeline will abort automatically; see the logged error for details.

## 4. Running the Pipeline

```bash
python code/main.py
```

### Configuration (handled automatically)

1. Downloads datasets from verified URLs (or alternatives found in Phase 0).  
2. Skips unavailable datasets with a warning; aborts if **no** dataset provides raw counts.  
3. Applies the **5 000‑cell sampling rule** for any dataset > 10 000 cells.  
4. Computes geometric diagnostics on the sampled high‑dimensional matrix, then generates embeddings.  
5. Runs the Fixed‑Effects ANOVA (descriptive only) and the Leiden‑resolution sensitivity sweep.  
6. Saves results under `data/results/`.

### Output Artifacts

* `data/results/summary.json` – high‑level overview (datasets processed, memory, runtime, exit code).  
* `data/results/statistical_report.yaml` – full model summary, VIFs, adjusted p‑values.  
* `data/results/sensitivity_plot.png` – variance of ARI/NMI across resolution sweep.

## 5. Verification

```bash
pytest -v tests/
```

* **Contract tests** validate JSON/YAML outputs against the schemas in `contracts/`.  
* **Unit tests** verify ARI/NMI calculations on a synthetic mini‑dataset.

## 6. Troubleshooting

* **Memory Error** – If the pipeline hits > 7 GB RSS, it will exit with code 1 (SC‑003). Reduce the sampling size or run on a machine with more RAM.  
* **Dataset Missing** – If `spec_gap_resolver.py` cannot locate raw counts for any required dataset, the pipeline aborts with exit code 1 and logs “No Data”.  
* **Convergence Failure** – If Leiden fails twice, the result is marked “Unavailable” and the pipeline continues.  
* **Time Limit** – If total runtime exceeds 21 600 s, the pipeline aborts with exit code 1 (SC‑004).
