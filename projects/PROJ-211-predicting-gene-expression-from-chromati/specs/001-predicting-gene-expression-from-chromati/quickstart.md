# Quickstart: Predicting Gene Expression from Chromatin Accessibility

## 1. Prerequisites

- Python 3.11+
- Git
- 7GB+ RAM
- ~GB disk space

## 2. Installation

```bash
# Clone the repository
git clone
cd PROJ-211-predicting-gene-expression-from-chromati

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Data Download (First Run)

```bash
# Download ENCODE data (this may take a moderate duration)
python code/download_encode.py --cell-lines GM12878,K562,HMEC,IMR90,HepG2
```

This will populate `data/raw/` with:
- `encode_counts.csv`
- `encode_peaks.bed`
- `gene_coords.bed`

**Note**: The script will verify checksums and record them in `state/projects/PROJ-211-predicting-gene-expression-from-chromati.yaml`.

## 4. Preprocessing

```bash
# Run the full preprocessing pipeline
python code/preprocess.py
```

This will generate:
- `data/processed/filtered_expression.csv`
- `data/processed/binned_matrix.csv` (A fixed number of bins per gene)
- `data/processed/imputed_expression.csv`
- `data/processed/housekeeping_genes.csv`
- `data/processed/cell_type_specific_genes.csv`
- `data/processed/housekeeping_matrix.csv`

## 5. Model Training

```bash
# Train Elastic Net models for all cell lines (with Sample Size Gate)
python code/train.py
```

This will generate:
- `data/models/elastic_net_{cell_line}.pkl`
- `data/processed/cv_scores.json` (LOOCV results)

**Note**: Cell lines with N < 4 samples will be skipped.

## 6. Analysis & Reporting

```bash
# Generate feature importance and TSS mapping
python code/analyze.py
```

This will generate:
- `data/processed/feature_importance.csv`
- `data/processed/sc003_verification.json` (SC-003 check)
- `data/processed/housekeeping_r2.csv` (FR-009)
- `data/processed/performance_gap.csv` (FR-010)
- `data/processed/external_validation.json` (SC-006)
- `paper/results.md`
- `paper/limitations.md`

## 7. Testing

```bash
# Run unit tests
pytest tests/unit/

# Run contract tests (schema validation)
pytest tests/contract/

# Run integration tests (with synthetic data)
pytest tests/integration/
```

## 8. Verification

To verify reproducibility:

```bash
# Checksums for raw data
md5sum data/raw/*

# Checksums for processed data
md5sum data/processed/*
```

Compare with hashes in `state/projects/PROJ-211-predicting-gene-expression-from-chromati.yaml`.