# Quickstart: Predict Plant Protein‑Protein Interactions from Co‑expression

These instructions assume a fresh GitHub Actions runner (or a local Linux environment with similar resources).

## 1. Clone the repository
```bash
git clone
cd ppi-coexpression
```

## 2. Set up the Python environment
```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt # pins all Python deps
```

## 3. Set up the R environment (DESeq2, org.At.tair.db)
```bash
Rscript scripts/install_bioc.R # installs DESeq2, limma, sva, org.At.tair.db
```

## 4. Configure species and parameters
Edit `config/species.yaml` to list GEO series per species (default includes a few *Arabidopsis* series).
Edit `config/parameters.yaml` to change any defaults (e.g., threshold: a high value, `seed: a fixed deterministic value for reproducibility`).

## 5. Run the full pipeline
```bash
make all
```
* This executes the following Make targets in order: `download → normalize → correlate → map_ids → select_edges → evaluate → enrich → summary → final_report`.
* All major actions are logged to `logs/pipeline.log` (JSON‑Line format).

## 6. Verify outputs
```bash
make verify
```
* Checks schema compliance (`contracts/*.schema.yaml`), checksum integrity, and reproducibility (identical seeds → identical checksums).

## 7. Inspect results
* Predicted edges: `data/processed/predicted_ppi_<species>.tsv`
* Evaluation metrics: `results/evaluation_metrics.json`
* GO enrichment: `data/processed/go_enrichment_<species>.tsv`
* Summary report: `results/summary_<species>.txt` and `results/final_report.txt`

## 8. Re‑run with a different threshold (example)
```bash
make all THRESHOLD=0.85
```
* The threshold is validated to be ≥ 0.75; lower values will abort with a clear error (FR‑012).

## 9. Clean intermediate files (optional)
```bash
make clean
```
* Removes all `data/processed/*` and intermediate logs but retains raw GEO downloads and final reports.

---

