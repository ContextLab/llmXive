# Quickstart: Gut Microbiome and Cognitive Decline Analysis

## Prerequisites
- Python 3.11+  
- Git  
- ≤ 7 GB free RAM  
- Internet access (for automated dataset download).  

## Setup

```bash
# 1. Clone the repository
git clone <REPO_URL>
cd projects/PROJ-189-investigating-the-correlation-between-gu

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt
```

## Step‑by‑Step Execution

### 1. Download AGP microbiome data & verify provenance
```bash
python code/01_download_and_provenance.py
```
- Downloads `agp.parquet` from the official Qiita/EBI repository and expects the user‑provided `paired_dataset.parquet` (containing both microbiome and cognition) to be placed in `data/raw/`.  
- Computes SHA‑256 checksums and compares them to `data/provenance/expected_checksums.json`.  
- On success you will see `PROVENANCE CHECK PASSED` and an `observed_checksums.json` file.

### 2. Load paired dataset & apply age filter (may abort)
```bash
python code/02_load_and_filter.py
```
- Loads `paired_dataset.parquet`, filters to `age >= 60`, and checks that the resulting cohort contains **≥ 200 participants**.  
- If the count is < 200, the script logs the count and **exits with a clear “Fatal Coverage Gap” error**; no further steps run.

### 3. Correlation analysis (requires successful load)
```bash
python code/03_correlation.py
```
- Computes covariate‑adjusted partial Spearman correlations and applies Benjamini‑Hochberg FDR (α = 0.05).  
- Output: `data/results/correlations.json`.

### 4. Predictive modeling & permutation null
```bash
python code/04_modeling.py
```
- Trains a CPU‑only Random Forest regressor with nested 5‑fold CV, evaluates against a high‑count permutation null distribution, and generates SHAP & permutation importance artefacts.  
- Output: `data/results/model.json`.

### 5. Linear regression (only if a paired dataset exists)
```bash
python code/05_linear_regression.py
```
- Fits a standard OLS regression of cognitive scores on CLR‑transformed genera plus covariates.  
- Output: `data/results/linear_regression.json`.  
- If the load step failed, this script detects the missing file and exits gracefully.

### 6. Sensitivity analysis & unified results assembly
```bash
python code/06_sensitivity.py
```
- Sweeps rarefaction depth, runs power analyses, enforces RAM guardrails, and writes:
  - `data/results/sensitivity.json`
  - `data/results/unified_results.json`
  - `data/results/summary.md` (human‑readable report with figures).

### 7. Verify all outputs
```bash
pytest tests/contract/
```
- All tests should pass (i.e., every JSON file conforms to its schema).

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **PROVENANCE CHECK FAILED** | Checksum mismatch (file corrupted or source updated) | Update `data/provenance/expected_checksums.json` if the source change is intentional, then re‑run the download step. |
| **Fatal Coverage Gap** (`linked participants < 200`) | No suitable paired dataset provided or dataset too small after age filter | Provide a paired microbiome‑cognition dataset with ≥ 200 participants aged ≥ 60, or revise the research question. |
| **MemoryError** | Dataset larger than RAM budget | The pipeline automatically truncates to the top‑200 genera and/or reduces permutation count; see the log for details. |
| **pytest failures** | Output file does not conform to its JSON schema | Re‑run the offending script; inspect the log for the specific validation error. |
| **Model R² not significant** | Observed R² ≤ 95th percentile of permutation null | The result is still reported; interpret as “no predictive advantage over chance”. |
| **Power warning** | Effective N < 100 or required sample size exceeds observed N | Review the power analysis section in `summary.md`; consider acquiring more data in future work. |

## Re‑run All Steps (clean slate)

```bash
# Remove all generated data
rm -rf data/processed/* data/results/* data/provenance/observed_checksums.json

# Then repeat the pipeline from step 1
python code/01_download_and_provenance.py
python code/02_load_and_filter.py   # may abort if insufficient participants
python code/03_correlation.py       # only if load succeeded
python code/04_modeling.py
python code/05_linear_regression.py
python code/06_sensitivity.py
pytest tests/contract/
```

---



