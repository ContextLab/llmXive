# Quickstart: Investigating the Relationship Between Gut Microbiome Composition and Resting-State EEG Alpha Power (Virtual Cohort & Distributional Analysis)

## Overview

This guide provides step-by-step instructions to set up and run the Virtual Cohort Matching and Distributional Comparison pipeline. The pipeline processes independent microbiome (American Gut Project) and EEG (OpenNeuro ds000246) datasets, attempts to match individual subjects, and tests for associations between gut microbiome composition and resting-state EEG alpha power. If matching fails, it falls back to distributional comparisons.

## Prerequisites

- **Python**: 3.11+
- **System Dependencies**: `git`, `wget`, `curl`
- **Memory**: ≥7 GB RAM
- **Disk**: ≥14 GB free space
- **CPU**: 2+ cores (GPU not required)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo/projects/PROJ-039-investigating-the-relationship-between-g
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r code/requirements.txt
```

**Note**: All dependencies are CPU-only. No GPU/CUDA required.

### 4. Verify Installation

```bash
python -c "import pandas, numpy, scipy, mne, qiime2; print('All imports successful')"
```

## Data Setup

### 1. Download Datasets

**Important**: The American Gut Project and OpenNeuro ds000246 have NO verified URLs in the dataset list. You must manually download these datasets:

- **American Gut Project**: Download from the official AGP repository (v2.0 release). Record the commit hash or release tag in `data/metadata.json`.
- **OpenNeuro ds000246**: Download from OpenNeuro. Record the dataset version in `data/metadata.json`. (Note: Corrected from ds000248).

Place raw data in:
- `data/raw/agp_microbiome/`
- `data/raw/openneuro_eeg/`

### 2. Generate Checksums

```bash
cd data/raw
sha256sum agp_microbiome/* > ../checksums.txt
sha256sum openneuro_eeg/* >> ../checksums.txt
```

Update `artifacts/checksums.txt` with the generated hashes.

## Running the Pipeline

### 1. Preprocess Microbiome Data

```bash
python code/preprocess_microbiome.py
```

**Output**: `data/processed/microbiome_features.csv` (≥100 rows)

### 2. Preprocess EEG Data

```bash
python code/preprocess_eeg.py
```

**Output**: `data/processed/eeg_features.csv` (≥50 subjects)

### 3. Virtual Cohort Matching

```bash
python code/match_cohorts.py
```

**Output**: `data/processed/matched_pairs.csv` (if ≥10 pairs) OR `data/processed/distribution_groups.csv` (if <10 pairs)

**Note**: If <10 pairs are found, the pipeline automatically switches to Distributional Comparison mode.

### 4. Run Correlation/Comparison Analysis

```bash
python code/correlation_analysis.py
```

**Output**: `artifacts/analysis_results.json` (correlation results, permutation test flags)

### 5. Generate Visualizations

```bash
python code/visualization.py
```

**Output**: 
- `artifacts/visualization/scatter_*.png` (if matched pairs)
- `artifacts/visualization/distribution_*.png` (if distributional test)

### 6. Generate Final Report

```bash
python code/main.py
```

**Output**: `docs/report.md` (includes associational disclaimer)

## Testing

### Run Contract Tests

```bash
pytest tests/contract/
```

### Run Integration Tests

```bash
pytest tests/integration/
```

### Run Unit Tests

```bash
pytest tests/unit/
```

## Expected Outputs

| File | Description |
|------|-------------|
| `data/processed/microbiome_features.csv` | Genus-level abundances + demographics (≥100 rows) |
| `data/processed/eeg_features.csv` | Alpha power + demographics (≥50 subjects) |
| `data/processed/matched_pairs.csv` | Matched individual pairs (if ≥10 found) |
| `data/processed/distribution_groups.csv` | Grouped data for distributional tests (if <10 pairs) |
| `artifacts/analysis_results.json` | Correlation results, permutation test flags |
| `artifacts/visualization/scatter_*.png` | Scatter plots for matched pairs |
| `artifacts/visualization/distribution_*.png` | Distributional comparison plots |
| `docs/report.md` | Final research report with associational disclaimer |

## Troubleshooting

### Issue: "ERROR: Insufficient matched pairs (<10)"

**Cause**: Demographic matching between AGP and OpenNeuro ds000246 yields <10 pairs.

**Resolution**:
- The pipeline automatically switches to **Distributional Comparison** mode.
- Verify that AGP and OpenNeuro data have sufficient demographic overlap (Age, Sex, BMI).
- If BMI is missing in OpenNeuro, the pipeline will match on (Age, Sex) only.

### Issue: "Log(0) error in CLR transformation"

**Cause**: Zero abundances not handled.

**Resolution**: Ensure pseudocount=0.5 is applied before CLR transformation (handled automatically in `correlation_analysis.py`).

### Issue: "Memory limit exceeded"

**Cause**: Data too large for 7 GB RAM.

**Resolution**: 
- Subset data to relevant taxa/subjects.
- Use streaming/chunked processing for large files.

### Issue: "Dataset not found"

**Cause**: AGP or OpenNeuro ds000246 not downloaded.

**Resolution**: Manually download datasets and place in `data/raw/` as described in "Data Setup".

## Success Criteria

The pipeline is successful if:
1. **SC-001**: ≥10 matched pairs are found OR ≥25 subjects per group in distributional test.
2. **SC-002**: All taxa with q<0.1 (Path A) or significant groups (Path B) are correctly counted and reported.
3. **SC-003**: Permutation test results are validated against a high-percentile null distribution.
4. **SC-004**: FDR correction is applied to all tests.
5. **SC-005**: Visualization outputs include appropriate plots (scatter or distribution).

## Notes

- **Associational Only**: All results are framed as associational; no causal inference is made.
- **Exploratory Nature**: Low power due to potential small sample sizes; results require replication.
- **Reproducibility**: Random seeds are pinned; all datasets are fetched from canonical sources (or manually downloaded with checksums).