# Quickstart: Predicting Gene Expression from Chromatin Accessibility

## 1. Prerequisites
- Python 3.11+  
- Git  
- ~7 GiB RAM, ~14 GiB free disk space  
- Internet access (for ENCODE download)

## 2. Installation
```bash
# Clone the repository
git clone https://github.com/your-org/PROJ-211-predicting-gene-expression-from-chromati.git
cd PROJ-211-predicting-gene-expression-from-chromati

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 3. Data Download (real ENCODE data)
```bash
python code/download_encode.py \
    --cell-lines GM12878 K562 HMEC IMR90 HepG2 \
    --output-dir data/raw
```
- The script queries the ENCODE REST API for the exact file IDs listed in `research.md`, streams each file, computes a SHA‑256 checksum, and aborts on mismatch.  
- If a file exceeds 2 GB, the script automatically restricts processing to chromosome 1 (still a genuine ENCODE slice).  
- On failure (e.g., network outage) the script retries up to three times before exiting with a clear error message.

## 4. Optional Synthetic Fallback (CI only)
```bash
python code/generate_synthetic.py --seed 42 --output-dir data/raw
```
Creates deterministic small synthetic `synthetic_counts.tsv` and `synthetic_peaks.bed`. The main pipeline detects the presence of real ENCODE files; if they are missing, the synthetic files are used **only** to allow CI to run end‑to‑end. This is **not** a scientific requirement.

## 5. Preprocessing
```bash
python code/preprocess.py \
    --counts data/raw/rna_counts.tsv \
    --peaks  data/raw/atac_peaks.bed \
    --tss    data/raw/gene_tss.bed \
    --output-dir data/processed
```
- CPM normalisation of RNA‑seq and ATAC/DNase counts.  
- Log‑pseudocount (`log(count + 1)`).  
- Median imputation per bin.  
- Aggregation of peaks into 200 fixed‑width bins within ±50 kb of each TSS (promoter ±2 kb set to 0).  
- Writes all processed CSVs listed in `data-model.md` and records checksums.

## 6. Model Training
```bash
python code/train.py \
    --features data/processed/binned_matrix.csv \
    --targets  data/processed/imputed_expression.csv \
    --output-dir data/models
```
- Trains Elastic Net per cell line (α = 0.5, l1_ratio tuned via LOOCV).  
- Applies variance‑based filter (≤ N‑1 bins) and zero‑pads coefficients to maintain 200 entries.  
- Computes Pearson r, R², raw p‑values, and Bonferroni‑corrected p‑values.  
- Stores model pickle and `cv_scores.json`.

### Cross‑Cell‑Line Validation (external validation)
```bash
python code/train.py \
    --features data/processed/binned_matrix.csv \
    --targets  data/processed/imputed_expression.csv \
    --hold-out-cell-line HepG2 \
    --output-dir data/models
```
- Trains on the other four lines, tests on the held‑out line, writes `external_validation.json` (fulfills SC‑006).

## 7. Analysis & Reporting
```bash
python code/analyze.py \
    --features data/processed/binned_matrix.csv \
    --targets  data/processed/imputed_expression.csv \
    --models   data/models \
    --output-dir data/processed
```
- Extracts non‑zero coefficients, maps bins to TSS distance, ranks bins, computes % of top‑100 bins within ±10 kb, runs a 1 000‑draw permutation enrichment test (SC‑003).  
- Calculates R² for housekeeping genes (FR‑009) and ΔR² between gene categories (FR‑010).  
- Generates `paper/results.md` and `paper/limitations.md`.

## 8. Testing (CI verification)
```bash
# Unit tests
pytest tests/unit/

# Contract (schema) validation
pytest tests/contract/

# Integration test (runs full pipeline on synthetic data)
pytest tests/integration/
```
All tests must pass; failures indicate checksum mismatches, schema violations, or runtime errors.

## 9. Reproducibility Check
```bash
# Verify raw data checksums
cat state/projects/PROJ-211-predicting-gene-expression-from-chromati.yaml | grep checksum

# Verify processed data checksums
md5sum data/processed/*

# Compare against recorded hashes – any mismatch aborts the pipeline (Constitution III)
```

---
