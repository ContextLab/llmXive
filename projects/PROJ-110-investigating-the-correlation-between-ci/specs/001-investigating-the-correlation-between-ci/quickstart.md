# Quickstart: Investigating Circadian Gene Expression & Metabolic Syndrome Risk

This guide shows how to run the full exploratory analysis on a fresh GitHub Actions runner (or locally) using only open datasets.

## Prerequisites
- Python 3.11
- Internet access (to download HF and Zenodo datasets)
- 2 CPU cores, ≥ 6 GB RAM (default GH Actions free tier)

## Setup

```bash
# 1️⃣ Clone the repository
git clone https://github.com/your-org/circadian-metabolic-correlation.git
cd circadian-metabolic-correlation

# 2️⃣ Create a virtual environment and install pinned dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions
```

## Run the Pipeline

```bash
# Execute the end‑to‑end pipeline
python src/pipelines/run_pipeline.py \
    --seed 42 \
    --log-level INFO
```

The script follows the ordered steps described in `plan.md`:

1. **Download GTEx expression (TPM)** and **public metabolic‑trait datasets** (BMI, HDL, ATP‑III components) – validated against their schemas.
2. **Validate** each raw file against its JSON schema (`contracts/*.schema.yaml`).  
3. **Merge** expression with phenotype data **only for donors where IDs overlap**.
4. **Compute** a continuous MetS risk score (z‑score sum of the five ATP‑III components).  
5. **Power analyses** for DE and correlation (and optional high‑risk grouping); log actual overlap sample size; issue exploratory warning if power < 0.80.  
6. **Differential expression (ANCOVA)** per tissue (≥ 20 donors); tissues failing the threshold are excluded (warning). Optional exploratory pooling of similar tissues is performed only if explicitly requested.  
7. **Global Benjamini‑Hochberg** correction across all gene‑tissue tests.  
8. **Tissue‑specific gene‑trait correlations**; meta‑analysis across tissues; global BH correction.  
9. **Reporting & Figures** – heatmaps of DE βs, scatter plots of significant correlations, forest plots of meta‑analysis, and summary tables.  
10. **Schema validation** – any failure aborts the run (`pytest -q tests/contract`).  

## CI Workflow (CPU‑only enforcement)

A GitHub Actions workflow file **`.github/workflows/ci.yml`** is included in the repository. It installs dependencies, asserts a CPU‑only environment, runs the pipeline, and validates contracts. The critical step:

```yaml
- name: Verify CPU‑only environment
  run: |
    python - <<'PY'
    import torch, sys
    if torch.cuda.is_available():
        sys.exit("GPU detected! This pipeline must run CPU‑only.")
    print("CPU‑only check passed.")
    PY
```

This satisfies the T060 requirement that the pipeline explicitly checks `torch.cuda.is_available() == False`.

## Expected Outputs

| Directory | Content |
|-----------|---------|
| `data/raw/` | Streamed GTEx TPM parquet, phenotype parquet, and trait CSV/parquet files (not persisted). |
| `data/processed/` | Cleaned expression matrix, donor phenotype table, risk‑score CSV, DE results, correlation results, power summary CSV. |
| `src/results/figures/` | `de_heatmap.png`, `gene_trait_scatter_{gene}_{trait}.png`, `meta_forest_{gene}_{trait}.png`. |
| `state/projects/PROJ-110...yaml` | Checksums, artifact hashes, timestamps for reproducibility. |

All outputs are automatically validated against the contracts in `contracts/`; any schema violation aborts the pipeline.

---


