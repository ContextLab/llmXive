# Quickstart: Predicting Gene Expression from Chromatin Accessibility

## 1. Prerequisites
- Python 3.11 or newer
- Git
- On the order of gigabytes of RAM., ~Adequate free disk space (on the order of several gigabytes)
- Internet access (for ENCODE download)

## 2. Installation
```bash
# Clone the repository
git clone 
cd PROJ-211-predicting-gene-expression-from-chromati

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 3. Data Download (real data)
```bash
python code/download_encode.py \
    --cell-lines GM128*, K562, HMEC, IMR90, HepG2 \
    --output-dir data/raw
```
- The script fetches the exact URLs listed in `research.md`, streams the files, computes cryptographic hash checksums, and writes them to `state/projects/…yaml`.  
- If the ENCODE servers are temporarily unreachable, the script aborts (no silent fallback). CI will then run the **optional synthetic fallback** (step 4).

## 4. Optional Synthetic Fallback (CI only)
```bash
python code/generate_synthetic.py --seed 42 --output-dir data/raw
```
Creates deterministic `synthetic_counts.csv` and `synthetic_peaks.bed` (non‑empty) and records their checksums. The main pipeline will automatically detect the presence of real ENCODE files; if absent, it will use the synthetic files. This utility is **not** a functional requirement of the project specification.

## 5. Preprocessing
```bash
python code/preprocess.py \
    --counts data/raw/encode_counts.csv \
    --peaks  data/raw/encode_peaks.bed \
    --tss    data/raw/gene_coords.bed \
    --output-dir data/processed
```
- **Normalization**: RNA‑seq CPM‑scales (library‑size) and ATAC/DNase CPM‑scales before any aggregation (addresses methodology‑602aa220).  
- **Feature selection**: Variance‑based filter retains ≤ N‑1 bins per cell line (applied during modelling, not altering the 200‑bin matrix).  
- **Aggregation**: Peaks are summed into 200 fixed‑width bins within ±50 kb of each gene’s TSS (excluding the promoter ±2 kb).  
- Generates all processed CSVs listed in `data-model.md` and records checksums.

## 6. Model Training
```bash
python code/train.py \
    --features data/processed/binned_matrix.csv \
    --targets  data/processed/imputed_expression.csv \
    --output-dir data/models
```
- Trains Elastic Net per cell line (α = 0.5, l1_ratio via LOOCV).  
- Skips any cell line with fewer than 4 replicates (Sample‑Size Gate).  
- Writes `elastic_net_{cell_line}.pkl` and `cv_scores.json`.

## 7. Cross‑Cell‑Line Validation
```bash
python code/train.py \
    --features data/processed/binned_matrix.csv \
    --targets  data/processed/imputed_expression.csv \
    --hold-out-cell-line HepG2 \
    --output-dir data/models
```
- Trains on four lines, tests on the held‑out line, records results in `external_validation.json` (fulfills SC‑006).

## 8. Analysis & Reporting
```bash
python code/analyze.py \
    --features data/processed/binned_matrix.csv \
    --targets  data/processed/imputed_expression.csv \
    --models   data/models \
    --output-dir data/processed
```
- Extracts non‑zero coefficients (FR‑007), maps bins to TSS distance (FR‑008), **computes % of top‑100 bins within ±10 kb and performs a permutation‑based enrichment test** (SC‑003).  
- Adjusts for gene‑length, GC, and baseline expression covariates, reports partial‑R².  
- Calculates R² for housekeeping genes (FR‑009), ΔR² between gene categories (FR‑010), and external‑validation metrics (SC‑006).  
- Generates markdown reports under `paper/`.

## 9. Testing (CI verification)
```bash
# Unit tests
pytest tests/unit/

# Contract (schema) validation
pytest tests/contract/

# Integration test (runs entire pipeline on synthetic data)
pytest tests/integration/
```
All tests must pass; failures indicate checksum mismatches or schema violations.

## 10. Reproducibility Check
```bash
# Verify raw data checksums
md5sum data/raw/*

# Verify processed data checksums
md5sum data/processed/*

# Compare against hashes stored in state file
cat state/projects/PROJ-211-predicting-gene-expression-from-chromati.yaml
```
Any deviation aborts the pipeline (Constitution III).

