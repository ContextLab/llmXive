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
python code/validate_provenance.py
```
- Downloads `agp.parquet`, `hrs.parquet`, `bmi.csv` into `data/raw/`.  
- Computes SHA‑256 checksums and compares them to the values in `data/provenance/expected_checksums.json`.  
- On success you will see `PROVENANCE CHECK PASSED` and an `observed_checksums.json` file.

### 2. Merge, age filter, rarefaction, CLR, BMI imputation, VIF
```bash
python code/02_merge_preprocess.py
```
- Produces `data/processed/merged_age60.parquet` and `data/processed/dataset.json` (validated against `contracts/dataset.schema.yaml`).  
- Writes `clr_normalized.parquet` and `imputed.parquet`.

### 3. Correlation analysis (Spearman + BH FDR)
```bash
python code/03_correlation.py
```
- Outputs `data/results/correlations.json` (validated against `contracts/correlation.schema.yaml`).

### 4. Predictive modeling & permutation null
```bash
python code/04_modeling.py
```
- Generates `data/results/model.json` (validated against `contracts/model.schema.yaml`).  
- Includes SHAP rankings and VIF flags.

### 5. Sensitivity analysis over rarefaction depth
```bash
python code/05_sensitivity.py
```
- Writes `data/results/sensitivity.json` and assembles `data/results/unified_results.json` (validated against `contracts/results.schema.yaml`).  
- Produces `data/results/summary.md` with key tables and figures.

### 6. Verify all outputs
```bash
pytest tests/contract/
```
- All tests should pass (i.e., no failures).  

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **PROVENANCE CHECK FAILED** | Checksum mismatch (file corrupted or version changed) | Update `data/provenance/expected_checksums.json` if the source file has legitimately changed, then re‑run the download step. |
| **Fatal Coverage Gap** (`overlap < 500`) | AGP and HRS IDs do not overlap enough after age filter. | Verify that the correct URLs are used; if the public datasets truly lack sufficient overlap, the analysis cannot proceed (spec‑mandated). |
| **MemoryError** | Dataset larger than RAM budget. | The pipeline will automatically down‑sample taxa to the top‑200 and/or reduce permutations; see logs for the adjustment. |
| **pytest failures** | Output file does not conform to its JSON schema. | Re‑run the offending script; check the log for schema‑validation error details. |
| **Model R² not significant** | Observed R² ≤ 95th percentile of permutation null. | The result is still reported; interpret as “no predictive advantage over chance”. |

## Re‑run All Steps (clean slate)

```bash
# Remove all generated data
rm -rf data/processed/* data/results/* data/provenance/observed_checksums.json

# Then repeat the pipeline from step 1
python code/01_download_and_provenance.py
python code/validate_provenance.py
python code/02_merge_preprocess.py
python code/03_correlation.py
python code/04_modeling.py
python code/05_sensitivity.py
pytest tests/contract/
```

---
