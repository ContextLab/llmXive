# Quickstart: Gut Microbiome – PD Progression Pipeline

## Prerequisites
* Python 3.11 (available on the CI runner)
* Internet access (only needed to fetch `pip` packages; **no automatic dataset download**).

## Setup
```bash
# 1. Create a fresh virtualenv (CI does this automatically)
python -m venv .venv
source .venv/bin/activate

# 2. Install pinned dependencies
pip install -r requirements.txt
```

## Prepare Input Data
1. **Microbiome ASV table** – place a CSV file named `ppmi_asv.csv` in `data/raw/`. The file must contain at least the columns `sample_id`, `patient_id`, `visit_date`, plus one column per taxon with raw count values.
2. **Clinical metadata** – place a Parquet file named `ppmi_clinical.parquet` in `data/raw/`. Required columns are `patient_id`, `visit_date`, `age`, `sex`, `levodopa_eq_dose`, and `MDS_UPDRS_Total` (the exclusive clinical outcome for this study).

The ingest step aborts with a clear error message if any required file or required column is missing. If the file parses but the `MDS_UPDRS_Total` column is absent, the pipeline does NOT abort: it logs a warning and sets a skip flag so the slope, correlation, and mixed-effects steps are skipped downstream (graceful degradation). The pipeline never falls back to synthetic or placeholder data.

## Validate Inputs (Phase 0)
```bash
# Verify presence, parseability, and provenance of the raw inputs
python -m code.src.pipeline.ingest
```
This logs the row/column counts of both tables and whether `MDS_UPDRS_Total` is present, and writes a validation record with downstream skip flags to `data/raw/ingest_validation.json`. It exits non-zero with a descriptive error if an input file is missing or malformed; it exits zero with a logged warning if only the outcome column is missing.

## Run the Full Pipeline
```bash
# Execute the end‑to‑end analysis (all phases 0‑6)
python -m code.src.pipeline \
    --seed 42 \
    --max_taxa 100 \
    --perm_iterations 1000
```

### Flags
| Flag | Meaning |
|------|-------------------|
| `--seed` | Random seed for reproducibility |
| `--max_taxa` | Upper bound on taxa to retain (default 100) |
| `--perm_iterations` | Number of permutation iterations (default 1000) |

All deliverables are written under `data/results/`: `taxa_correlations.csv`, `mixed_effects_summary.csv`, `permutation_pvalues.csv`, and `PD_microbiome_progression_report.pdf`.

## Verify Outputs
```bash
# Unit and contract tests (pytest)
pytest -q code/tests

# Spot‑check a result file
head -n 5 data/results/taxa_correlations.csv
```

## Expected Runtime (benchmark on CI)
| Step | Approx. Wall‑time |
|------|-------------------|
| Data validation & loading | < 2 min |
| Filtering + CLR | < 5 min |
| Slope computation | < 3 min |
| Correlation + BH | < 2 min |
| Mixed‑effects fitting (raw data) | < 12 min |
| Permutation (1 000 iterations, ≤ 100 taxa) | 3–4 h |
| PDF report generation | < 1 min |
| **Total** | **≤ 4 h** (well under the 6 h limit) |

**Important:** The clinical outcome is exclusively `MDS_UPDRS_Total`. If that column is absent from the clinical metadata, the slope, correlation, and mixed-effects steps are skipped with a logged warning (the pipeline still completes the remaining steps); if a required input file or required metadata column is missing or malformed, the pipeline aborts with an informative error and the researcher must supply the real PPMI files before re-running.