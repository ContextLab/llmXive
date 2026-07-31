# Quickstart: Predicting Plant PPIs from Co‑expression

These instructions assume a fresh GitHub Actions runner or a local Linux environment with Docker (optional).

## 1. Clone the repository
```bash
git clone https://github.com/yourorg/ppi-coexpression.git
cd ppi-coexpression
```

## 2. Set up the Python environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Set up the R environment (renv)
```R
# In R console
install.packages("renv")
renv::restore()   # installs DESeq2, org.At.tair.db, limma, sva, edgeR
```

## 4. Configure the run (optional)
Edit `src/config/species.yaml` to add or modify GEO accession lists.  
Edit `src/config/parameters.yaml` to change thresholds or seed.

## 5. Run the full pipeline
```bash
make all SEED=12345
```
- `make all` executes the targets `download → normalize → correlate → map_ids → select_edges → evaluate → enrich → summary → final_report`.  
- The `SEED` variable sets the global random seed (FR‑012).

## 6. Inspect results
- Predicted edges: `data/processed/predicted_ppi_<species>.tsv`  
- Evaluation metrics: `results/evaluation_metrics.json` (validated against `contracts/evaluation.schema.yaml`)  
- GO enrichment: `results/go_enrichment_<species>.tsv`  
- Summary report: `results/final_report.txt`  
- Log file (JSON‑Line): `logs/pipeline.log` (validated against `contracts/pipeline_log.schema.yaml`)

## 7. Run verification only
```bash
make verify
```
This step validates all output files against the contracts; any violation aborts with a clear error (FR‑[relevant contract], FR‑013, FR‑019, FR‑030, FR‑034).

## 8. Clean intermediate files (optional)
```bash
make clean
```

All commands are reproducible; re‑running with the same `SEED` yields identical outputs (SC‑).

---



