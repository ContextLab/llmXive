# Quickstart: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## Prerequisites
- Python 3.11 or newer  
- Internet access (to stream the open HCP parquet files)  
- Approx. 2 GB RAM and 5 GB free disk space (well within GitHub Actions free‑tier limits)

## Installation

```bash
# Clone the repository (replace <repo-url> with the actual URL)
git clone <repo-url>
cd projects/PROJ-331-investigating-the-influence-of-network-m

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install pinned dependencies
pip install -r code/requirements.txt

# Install pre‑commit hooks (optional but recommended)
pre-commit install
```

## Run the full pipeline

```bash
python code/main.py
```

The script executes the following ordered steps:

1. **Stream‑download** diffusion‑derived streamlines and rsFC parquet files for up to 50 subjects, compute SHA‑256 checksums, and write `manifest.json`.  
2. **Load pre‑computed streamlines** (seed = 42) from the diffusion parquet. No raw DWI tractography is performed.  
3. **Parcellate** streamlines to a binary Schaefer‑100 adjacency matrix (`structural.npy`) per subject; record provenance metadata and generate `structural_connectome.json` (see schema).  
4. **Preprocess rsFC**: regress out global signal and head‑motion parameters, then compute Pearson correlations (`rsfc.npy`).  
   - Compute **mean rsFC strength** as the average absolute off‑diagonal correlation *after* nuisance regression.  
   - Compute **global efficiency** on the binary graph obtained by thresholding |r| > 0.2.  
5. **Aggregate per‑subject metrics** (`subject_metrics.csv`) including rsFC strength, global efficiency, structural global degree, network density, and **optional covariates** (age, sex, head‑motion, scanner site).  
6. **Enumerate all 3‑node & 4‑node motifs** (13 undirected classes), generate ≥ 1000 Maslov–Sneppen degree‑preserving random graphs (seed = 42), compute z‑scores, enforce a **300 s timeout** (fallback to 3‑node‑only if exceeded), and handle zero‑variance gracefully.  
7. **Partial Pearson & Spearman correlations** between each motif and each functional metric (strength, global efficiency), **optionally** controlling for structural global degree and any available covariates, Bonferroni correction across **52 primary tests** (α ≈ 0.00096), VIF ≥ 5 warning, pairwise \|r\| ≥ 0.9 warning, and ≥ 1000 permutation tests.  
8. **Run the power‑analysis module** (target = 0.80, α = 0.05/52). If the effective N after exclusions falls below 30, the module recomputes power with the actual N and suggests remedial actions (increase cohort size or relax α) to retain ≥ 0.80 power.  
9. **Generate `results.pdf`** containing one page per motif with scatter plot, 95 % confidence interval, partial Pearson & Spearman r, raw p, Bonferroni‑corrected p, empirical permutation p, multicollinearity diagnostics, and a power‑analysis summary. The mandatory disclaimer “These findings are associational only and do not imply causation.” is inserted and verified.  
10. **Validate** generated JSON artifacts (`correlation_results.json`, `analysis_results.json`, `results.json`) against their respective schemas in `contracts/`.  

## Inspect results

- **Log**: `data/logs/pipeline.log` – machine‑readable JSON lines with timestamps, step names, warnings, and library versions.  
- **Manifest**: `data/processed/manifest.json` – shows cohort size, checksums, and any subjects skipped.  
- **Subject metrics**: `data/processed/subject_metrics.csv` – contains functional and structural summary metrics plus optional covariates; use the search function to confirm the presence of the disclaimer string “These findings are associational only and do not imply causation.” in the PDF.  
- **PDF report**: `results/results.pdf` – open with any PDF viewer; use the search function to confirm the presence of the disclaimer.  

## Running the test suite

```bash
pytest tests/            # unit, integration, and contract tests
flake8 code/ tests/      # linting (configured via .flake8)
black --check code/ tests/  # formatting check (configured via pyproject.toml)
```

All tests must pass before committing changes.

## Troubleshooting

| Issue | Likely Cause | Remedy |
|-------|--------------|--------|
| **Download failure** | Network glitch or changed URL | Re‑run `python code/main.py`; the script aborts with a clear error if a parquet file cannot be fetched. |
| **Subject missing a modality** | Incomplete record in the source parquet | The pipeline logs a warning and skips the subject; see `pipeline.log` for details. |
| **Streamline loading too slow** | Very large streamline collections | The loading is streamed; if runtime exceeds 60 s per subject, the timeout guard aborts and logs a warning. |
| **Motif enumeration exceeds 300 s** | Dense graph or many null models | The script aborts the subject, logs a timeout warning, and continues with 3‑node‑only enumeration. Use `--synthetic-nodes 200` to trigger the timeout deliberately. |
| **PDF > 5 MB** | High‑resolution figures | The report generator automatically reduces figure DPI and regenerates the PDF. |
| **Missing disclaimer in PDF** | Unexpected PDF generation error | Check `pipeline.log` for the verification step; reinstall `reportlab` if necessary. |
| **Power analysis reports low power** | Cohort size after exclusions < 30 | The pipeline logs remedial suggestions (increase cohort size or relax α) and includes the statement in the PDF. |
| **Linting failures** | Code style violations | Run `black code/ tests/` to auto‑format, then commit. |
| **Contract validation failures** | Schema mismatch in generated JSON | Run `pytest tests/contract/test_schemas.py` to locate the offending file and adjust the generating code. |

## Notes on Optional Covariates
If the HCP metadata CSV includes age, sex, head‑motion metrics, or scanner site, they are automatically incorporated as nuisance covariates in the partial correlation models (step 7). Their inclusion improves robustness but does not alter the core requirement of optionally controlling for structural global degree (which remains optional).

--- 