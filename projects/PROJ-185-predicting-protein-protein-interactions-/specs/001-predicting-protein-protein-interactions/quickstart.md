# Quickstart: Predict Plant PPIs from Co‑expression

## Prerequisites
```bash
# Clone the repository
git clone
cd ppi-coexpression

# Create a virtualenv and install dependencies
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt

# Install R packages (run once)
Rscript scripts/install_bioconductor.R # installs DESeq2, org.At.tair.db, limma, sva
```

## Configuration
Edit `src/config/species.yaml` to list GEO series per species (default includes Arabidopsis GSE152416).
Edit `src/config/parameters.yaml` to change thresholds, normalization mode, or random seed.

## Run the Full Pipeline
```bash
make all SEED=12345 NORM=vst THRESHOLD=0.80
```
*What happens*:
1. Downloads GEO series, skips those with < 30 samples, checks total ≥ 50.
2. Normalizes (VST), filters low‑expression genes, keeps the most variable genes (high‑variance genes).
3. Batch‑corrects across series, regresses out expression‑level and gene‑length confounds.
4. Computes Pearson correlations, writes `raw_correlations_Arabidopsis.tsv.gz`.
5. Maps genes to STRING proteins, writes edge list `predicted_ppi_Arabidopsis.tsv`.
6. **Evaluation** uses a [deferred]/A train‑test split proportion will be determined based on standard practice.; the test set is scored against STRING experimental + database edges (combined ≥ 700). Baseline random‑graph results and `baseline_p` are reported.
7. Runs GO enrichment → `go_enrichment_Arabidopsis.tsv`.
8. Generates per‑species summary and `final_report.txt`.
9. All per‑species metrics are collated into `master_results.json`, the project’s Single Source of Truth.

## Individual Targets
| Target | Description |
|--------|-------------|
| `make evaluate` | Runs only the evaluation phase (FR‑006‑FR‑019) on the held‑out test set. |
| `make enrich` | Runs GO enrichment (FR‑008‑FR‑023). |
| `make summary` | Generates summary reports (FR‑021‑FR‑028). |
| `make clean` | Removes all intermediate files. |

## Validation
After any target, the verification step runs automatically:
```bash
python scripts/verify_outputs.py
```
It checks all contract files (`predicted_edges.schema.yaml`, `evaluation.schema.yaml`, etc.) and aborts on failure, satisfying FR‑017, FR‑019, FR‑030, FR‑034.
