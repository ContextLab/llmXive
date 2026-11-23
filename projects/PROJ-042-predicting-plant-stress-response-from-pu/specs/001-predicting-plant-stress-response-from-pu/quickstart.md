# Quickstart: Predicting Plant Stress Response from Publicly Available Transcriptomic Data

## Prerequisites
- **Python** 3.11 or newer (Ubuntu 22.04 recommended).  
- **Memory** ≥ 7 GB, **Disk** ≥ 14 GB, **Internet** access to NCBI GEO FTP.  
- **GitHub Actions** free‑tier runner parameters (2 CPU, ≈ 7 GB RAM, ≤ 6 h) – the pipeline is designed to stay within these limits.

## Installation
```bash
# Clone the repository
git clone https://github.com/your-org/your-repo.git
cd your-repo

# Create a virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Running the Full Pipeline
The entry point is `code/main.py`. Use the `--full-run` flag to execute every stage sequentially.

```bash
python code/main.py --full-run --seed 42 --top_k 50
```

### Individual Stages (optional)
| Stage | Command | Description |
|-------|---------|-------------|
| 0 – Discovery & Verification | `python code/main.py --stage discover` | Queries GEO, verifies plant stress series, writes `data/raw/`. Fails early if < 7 series. |
| 1 – Pre‑processing | `python code/main.py --stage preprocess` | CPM filter, TMM normalization, gene‑ID mapping, writes `data/processed/`. |
| 2 – Feature Selection | `python code/main.py --stage select --top_k 50` | Computes variance, writes `data/processed/feature_space.csv`. |
| 3 – Model Training & Evaluation | `python code/main.py --stage train --top_k 50` | LODO Logistic Regression, permutation tests, writes `results/model_metrics.json`. |
| 4 – Stability Analysis | `python code/main.py --stage stability --bootstrap 100` | Bootstrap coefficient variance, writes `results/robust_biomarkers.csv`. |
| 5 – Unsupervised Validation | `python code/main.py --stage embed --algorithm umap` | UMAP + Silhouette, writes `results/embedding_coords.csv` & plot. |
| 6 – Reporting | `python code/main.py --stage report` | Generates PDF/HTML report, updates state file. |

## Verification Checklist
1. **State file** – `state/projects/PROJ-042-predicting-plant-stress-response-from-pu.yaml` contains `research_complete: true`, a UTC timestamp, and SHA‑256 hashes for all result artefacts.  
2. **Performance metrics** – Open `results/model_metrics.json` and confirm:  
   - Cross‑dataset accuracy ≥ 0.70 *or* a documented post‑hoc power analysis (SC‑001, SC‑005).  
   - Permutation p‑value < 0.05 after FDR correction.  
3. **Biomarker table** – `results/robust_biomarkers.csv` lists at least one gene meeting variance ≤ 0.30 and frequency ≥ 0.70, or a clear “No robust biomarkers” message (SC‑003).  
4. **UMAP plot** – `results/umap_plot.png` shows stress clusters with Silhouette ≥ 0.40 for ≥ 3 classes and Δ ≥ 0.10 vs. dataset Silhouette (SC‑004).  
5. **Resource usage** – `logs/resource_usage.txt` reports peak RAM ≤ 7 GB and total runtime ≤ 6 h (SC‑006).  

Run the test suite to ensure all components behave as expected:

```bash
pytest tests/ -v
```

## Troubleshooting
- **Insufficient datasets**: The discovery stage will abort with `E‑DATA‑INSUFFICIENT`. Verify that GEO contains additional plant stress series or adjust the query terms.  
- **Feature space < 1,500 genes**: Check `data/processed/feature_space.csv`; the abort message will indicate the actual count. Consider relaxing the CPM filter if appropriate.  
- **MemoryError**: Reduce `--top_k` (e.g., to 50) or decrease `n_estimators` in the Logistic Regression config (`config.py`).  
- **Low power**: Review `results/model_metrics.json` for MDES and power; if power < 0.80, the report will flag the result as underpowered (SC‑005).  

All steps are deterministic; re‑running on a fresh CI runner reproduces identical outputs.
