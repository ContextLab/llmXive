# Quickstart: Single-Cell Trajectories of T-Cell Exhaustion (Full GEO Study)

## Prerequisites
- Python 3.11+  
- R 4.3+ (Seurat v4)  
- Git
- Access to a GitHub Actions runner **or** a local Linux/macOS environment with **2 CPU cores** and **≥ 7 GB RAM**.

## Installation

```bash
# 1️⃣ Clone the repository
git clone <repo-url>
cd projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3️⃣ Install Python dependencies
pip install -r code/requirements.txt
```

## Data Download (Phase 0)

```bash
# Download all four GEO datasets (no authentication required)
python code/download_data.py \
  --datasets GSE136103 GSE127465 GSE111075 GSE138852 \
  --output data/raw/
```

*If the command exits with a non‑zero status, inspect `logs/download.log` for checksum mismatches.*

## Run the Full Pipeline

```bash
# 1️⃣ Preprocess (Seurat QC & normalization)
python code/preprocess.py --input data/raw/ --output data/processed/

# 2️⃣ Subset CD3+ T‑cells (focus on exhaustion‑relevant lineage)
python code/subset_tcells.py --input data/processed/ --output data/processed/

# 3️⃣ Velocity & Pseudotime (CPU‑only)
python code/velocity.py --input data/processed/ --output data/processed/

# 4️⃣ Fork‑Point Identification
python code/forkpoint.py --input data/processed/ --output data/results/fork_points/

# 5️⃣ Enrichment Against Therapy‑Response Signature (GSE138852)
python code/enrichment.py --input data/results/fork_points/ --output data/results/validation/

# 6️⃣ Bootstrap Validation (a sufficient number of iterations)
python code/validate.py --input data/results/validation/ --output data/results/validation/

# 7️⃣ Generate the final HTML report
python code/report.py --input data/results/validation/ --output data/results/report/
```

## Expected Outputs
| Path | Description |
|------|-------------|
| `data/results/fork_points/<dataset>_fork_points.csv` | Ranked list of fork‑point genes (conforms to `fork_point.schema.yaml`; uses `branch_id`). |
| `data/results/validation/<dataset>_enrichment.json` | JSON containing enrichment **corrected p‑value** (< 0.01), confidence interval, and bootstrap iteration count. |
| `data/results/report/final_report.html` | Interactive report with velocity plot, divergence heatmap, gene table, enrichment statistics, and a clear disclaimer. |

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Download script exits 1 | Network glitch or checksum mismatch | Re‑run the command; verify internet connectivity; check `logs/download.log`. |
| QC filter removes **no** cells | Dataset missing mitochondrial gene annotation (`MT-` prefix). | The script falls back to any gene whose name starts with `MT-` **or** uses the `percent.mt` annotation from Seurat; if absent, a warning is logged and the filter is skipped. |
| scVelo fails to converge | High noise or insufficient moments | Increase `n_pcs` or set `scvelo.tl.recover_dynamics(..., max_iter=200)`. |
| No fork‑points detected | Divergence threshold too strict | Lower the threshold in `forkpoint.py` (e.g., `2.0 → 1.5` SD). |
| Enrichment step errors | Signature file not found or malformed | Verify that `code/enrichment.py` points to the bundled therapy‑response signature file (`gse138852_therapy_signature.txt`). |
| Validation step errors | Numeric fields contain `-1` placeholders | Ensure real numeric values are written; re‑run `validate.py` after successful enrichment. |

All scripts are lint‑checked (`ruff check . && black --check .`) as part of CI; failures will be reported in the workflow logs.

---


