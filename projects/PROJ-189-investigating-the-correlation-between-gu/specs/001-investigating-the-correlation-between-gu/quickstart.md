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

### 1. Download raw data & verify provenance
```bash
python code/01_download_and_provenance.py
```
- Downloads `agp.parquet`, `hrs.parquet`, `bmi.csv` into `data/raw/`.  
- Computes SHA‑256 checksums and compares them to `data/provenance/expected_checksums.json`.  
- On success you will see `PROVENANCE CHECK PASSED` and an `observed_checksums.json` file.

### 2. Attempt Merge & Age Filter (may abort)
```bash
python code/02_merge_preprocess.py
```
- Performs an inner join on `participant_id`.  
- **If** the overlap of participant IDs is **≥ 500**, the merged dataframe is written to `data/processed/merged_age60.parquet` and downstream steps proceed.  
- **If** the overlap is **< 500** (the expected case with public AGP/HRS releases), the script logs the count and **exits with a clear “Fatal Coverage Gap” error**. No further steps are run until a truly linked dataset is provided.

### 3. Correlation analysis (Partial Spearman + BH FDR)
```bash
python code/03_correlation.py
```
- Runs only if the merge succeeded.  
- Outputs `data/results/correlations.json`.

### 4. Predictive modeling & permutation null
```bash
python code/04_modeling.py
```
- Runs only if the merge succeeded.  
- Generates `data/results/model.json` (including SHAP and permutation importance).

### 5. Linear Regression (HRS only or linked microbiome data)
```bash
python code/05_linear_regression.py
```
- If a merged microbiome‑cognition dataset is available, this script fits a standard linear regression of cognitive scores on CLR‑transformed genera plus covariates.  
- If no linked dataset is present, this step is skipped (the pipeline has already aborted).  
- Produces `data/results/linear_regression.json`.

### 6. Sensitivity analysis & unified results assembly
```bash
python code/06_sensitivity.py
```
- Runs regardless of merge outcome (uses whatever data are available).  
- Writes `data/results/sensitivity.json`, `data/results/unified_results.json`, and `data/results/summary.md`.

### 7. Verify all outputs
```bash
pytest tests/contract/
```
- All tests should pass (i.e., no schema‑validation failures).  

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **PROVENANCE CHECK FAILED** | Checksum mismatch (file corrupted or source updated) | Update `data/provenance/expected_checksums.json` if the source file has legitimately changed, then re‑run the download step. |
| **Fatal Coverage Gap** (`overlap < 500`) | AGP and HRS IDs do not overlap | The pipeline aborts intentionally; to proceed you must obtain a dataset that contains both microbiome and cognition for the same participants or revise the research question. |
| **MemoryError** | Dataset larger than RAM budget. | The pipeline automatically truncates to the top‑200 genera and/or reduces permutation count; see the log for details. |
| **pytest failures** | Output file does not conform to its JSON schema. | Re‑run the offending script; inspect the log for the specific validation error. |
| **Model R² not significant** | Observed R² ≤ 95th percentile of permutation null. | The result is still reported; interpret as “no predictive advantage over chance”. |
| **Power warning** | Effective N < 100 or detectable effect size unrealistic. | Review the power analysis section in `summary.md`; consider obtaining more data in future work. |

## Re‑run All Steps (clean slate)

```bash
# Remove all generated data
rm -rf data/processed/* data/results/* data/provenance/observed_checksums.json

# Then repeat the pipeline from step 1
python code/01_download_and_provenance.py
python code/02_merge_preprocess.py   # may abort if no overlap
python code/03_correlation.py       # only if merge succeeded
python code/04_modeling.py           # only if merge succeeded
python code/05_linear_regression.py
python code/06_sensitivity.py
pytest tests/contract/
```

---


