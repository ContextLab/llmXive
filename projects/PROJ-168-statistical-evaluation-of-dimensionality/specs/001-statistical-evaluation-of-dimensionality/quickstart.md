# Quickstart: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

## 1. Prerequisites
- Python 3.11 or newer
- Git
- A GitHub Actions runner **or** a local machine with ≤ 7 GB RAM, ≤ 14 GB disk, and ≤ 2 CPU cores

## 2. Installation
```bash
git clone <repo-url>
cd projects/PROJ-168-statistical-evaluation-of-dimensionality
python -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
```

**Key pinned versions** (see `code/requirements.txt`):
```
scikit-learn==1.5.0
scanpy==1.10.2
umap-learn==0.5.6
leidenalg==0.10.2
pandas==2.2.2
numpy==2.0.0
psutil==6.0.0
statsmodels==0.14.2
pingouin==0.5.4
```

## 3. Pre‑run Specification Check (Phase 0)
Run the data‑gap resolver to **verify that each selected GEO accession contains a `counts` array of raw integers**. If any dataset lacks raw counts, the script aborts and records the status as “Unavailable” in `data/manifest.json`.

```bash
python code/phase0_verify_raw_counts.py
```

- **Exit 0** → manifest created, pipeline can continue.  
- **Exit 1** → raw counts missing; the script logs the reason and the pipeline aborts automatically (Constitution I).

## 4. Execute the Full Pipeline (Snakemake recommended)
```bash
snakemake -j 1 all
```
Snakemake will invoke the phase modules in the correct order:

1. `phase1_preprocess.py` – checksum, sampling, log‑CPM, HVG, write Parquet.  
2. `phase2_embeddings.py` – PCA/t‑SNE/UMAP + Trustworthiness & LCA.  
3. `phase3_fidelity_fixed.py` – Leiden (resolution 0.5), ARI/NMI, **logit‑transform**, store `fidelity_metrics.json`.  
4. `phase4_sensitivity_silhouette.py` – silhouette‑threshold sweep {0.4,0.5,0.6}, recompute ARI/NMI, enforce variance < 0.05, store variance summary.  
5. `phase5_mixed_effects.py` – MixedLM (or permutation ANOVA fallback), VIF (reference level dropped), BH correction, write `statistical_result.yaml`.  
6. `phase6_reporting.py` – aggregate summaries, generate plots, validate contracts.

### Output Locations
- `data/processed/` – processed matrices & geometric descriptors.  
- `data/embeddings/` – CSV files for each embedding.  
- `data/metrics/` – fidelity JSON files (logit‑transformed).  
- `data/results/` – `statistical_result.yaml`, `summary.json`, `sensitivity_plot.png`.  

## 5. Verification
```bash
pytest -v tests/
```
- Contract tests compare each output file against the schemas in `contracts/`.  
- Unit tests validate ARI/NMI on a tiny synthetic dataset.

## 6. Troubleshooting
| Symptom | Remedy |
|--------|--------|
| **MemoryError / RSS > 7 GB** | Reduce the sampling size (edit `code/config.py` → `MAX_CELLS = 3000`). |
| **No raw counts found** | Ensure internet connectivity; the resolver logs the exact missing accession and aborts. |
| **Leiden fails to converge** | The pipeline will automatically retry; if still “Unavailable”, check the log for the dataset ID. |
| **Runtime exceeds 6 h** | Verify that `MAX_CELLS` is honored; large datasets should have been down‑sampled. |
| **Contract validation fails** | Re‑run `pytest`; the failing test will indicate which schema violation to fix. |
| **VIF infinite** | The VIF step drops one dummy level (reference category) before calculation. |
| **Model assumptions violated** | The pipeline will automatically switch to a permutation ANOVA (10 k permutations). |
| **Observed association, not causation** | Remember the analysis is observational; interpret results as associations only. |

---



