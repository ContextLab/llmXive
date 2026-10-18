# Quickstart: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## Prerequisites
- Python 3.x or newer
- Internet access (to download the OpenNeuro parquet and diffusion files)
- Approx. a few GB RAM, Adequate disk space (CI free‑tier limits)

## Installation

```bash
# Clone the repository (replace <repo-url> with the actual URL)
git clone <repo-url>
cd projects/PROJ-331-investigating-the-influence-of-network-motif

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

The script will:

1. **Stream‑download** the verified OpenNeuro functional parquet **and** the diffusion tractography files for up to 50 subjects, checksum the raw files, and write `manifest.json`.  
2. **Parcellate** the BOLD data to a 100‑node Schaefer atlas, compute rsFC matrices, mean strength, and global efficiency.  
3. **Construct** binary undirected structural connectomes (100 nodes) from the diffusion data.  
4. **Enumerate** 3‑node and 4‑node motifs (with optional weighted counts), compute degree‑preserving null models, and produce z‑scores (timeout > 300 s aborts gracefully).  
5. **Run** partial Pearson & Spearman correlations (controlling for structural global degree, age, sex, and motion), Bonferroni correction across multiple tests, ≥ 1000 permutation tests, VIF & pairwise‑correlation diagnostics (warnings only), and a power‑analysis module (N = 50, α = 0.05/52, power = 0.80).  
6. **Generate** `results/results.pdf` containing per‑motif scatter plots, confidence intervals, effect sizes, corrected and empirical p‑values, multicollinearity diagnostics, the mandatory disclaimer, and the power‑analysis summary.  

## Inspect results

- **Log**: `data/logs/pipeline.log` – machine‑readable log of every step, warnings, and library versions.  
- **Manifest**: `data/processed/manifest.json` – shows cohort size, number of subjects processed/skipped, and covariate inclusion.  
- **PDF report**: `results/results.pdf` – open in any PDF viewer; use the search function to confirm the presence of the disclaimer string “These findings are associational only and do not imply causation.”  

## Running the test suite

```bash
pytest tests/            # unit, integration, and contract tests
flake8 code/ tests/      # linting (configuration removed per spec)
black --check code/ tests/  # formatting check
```

All tests must pass before committing changes.

## Troubleshooting

| Issue | Likely Cause | Remedy |
|-------|--------------|--------|
| **Download failure** | Network glitch or changed URL | Re‑run `python code/main.py`; the script aborts with a clear error if the parquet or diffusion files cannot be fetched. |
| **Subject missing a modality** | Incomplete OpenNeuro record | The pipeline logs a warning and skips the subject; check `pipeline.log` for details. |
| **Motif enumeration exceeds 300 s** | Extremely dense graph or insufficient resources | The script aborts the subject, logs a timeout warning, and suggests limiting to 3‑node motifs only. |
| **PDF > 5 MB** | High‑resolution figures | The report generator automatically reduces figure DPI and regenerates the PDF. |
| **Missing disclaimer in PDF** | Unexpected PDF generation error | Check `pipeline.log` for the verification step; re‑run the pipeline after ensuring `reportlab` is correctly installed. |
| **Over‑control concern** | Results differ between analyses with/without degree covariate | Review the sensitivity analysis pages in the PDF for both versions. |
