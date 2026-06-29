# Quickstart: Predicting Plant Defense Compound Production from Publicly Available Genomic and Transcriptomic Data

## Prerequisites

- Python 3.11 or higher
- 2+ CPU cores
- 7+ GB available RAM
- 14+ GB available disk space
- Internet connectivity for dataset downloads

## ⚠️ CRITICAL: Dataset Verification Required

**Before proceeding**: This project requires verified plant omics datasets (GEO series and Metabolomics Workbench experiments for herbivore-stress annotated Arabidopsis and Solanum). The current verified datasets block contains ONLY medical data.

**⚠️ IF NO VERIFIED PLANT DATASETS EXIST**: The pipeline will halt with error code **E-DATASET**. This is a research question blocker that cannot proceed without:
1. Verified plant transcriptomic/metabolomic datasets added to verified datasets block
2. Spec modification to use available medical datasets (changes research question)
3. Project pause until plant-specific omics datasets are verified

## Installation

```bash
# Clone repository
git clone <repository-url>
cd projects/PROJ-503-predicting-plant-defense-compound-produc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Quick Start Commands

### Step 0: Verify Dataset Availability (MANDATORY - BLOCKER)

```bash
# Check if required GEO and Metabolomics Workbench datasets are accessible
python code/main.py --check-datasets
```

**Expected Output**: 
- **If verified plant datasets found**: Pairing feasibility report with match rate percentage, sample count, and power analysis
- **If no verified plant datasets**: **ABORT with error code E-DATASET**

**⚠️ If E-DATASET error occurs**: Project cannot proceed without verified plant omics datasets. Options:
1. Add verified plant datasets to verified datasets block
2. Modify spec to use available medical datasets (changes research question)
3. Pause project until plant-specific omics datasets are verified

**⚠️ If E-PAIRING error occurs**: <95% sample-level pairing. Review logs/data_pairing.json and verify GEO/Metabolomics Workbench experiment compatibility.

**⚠️ If E-POWER error occurs**: Sample size <28. Project cannot proceed with adequate statistical power.

### Step 1: Verify Power Requirements (Phase 0)

```bash
# Check sample size meets power requirements (n≥28-30 for r≥0.5)
python code/main.py --check-power
```

**Expected Output**: Power analysis report with required sample size, available sample count, and power calculation. If sample size <28, **ABORT with error code E-POWER**.

**Power Analysis Output**: outputs/power_analysis.json containing:
- Required n for r≥0.5, power=0.80, α=0.05
- Available sample count
- Achieved power with available samples
- PASS/FAIL status

### Step 2: Download and Pair Data (ONLY if Step 0 and Step 1 PASS)

```bash
# Download expression and metabolite data (only after Step 0 passes)
python code/main.py --download
```

**Expected Output**: CSV files in data/paired/ with matched sample IDs; pairing logs in logs/data_pairing.json

**⚠️ Abort if**: Pairing rate <95% (E-PAIRING error)

### Step 3: Preprocess and Select Features

```bash
# Normalize, batch-correct, and select defense pathway + regulatory genes
python code/main.py --preprocess
```

**Expected Output**: data/processed/features.csv with defense pathway genes; logs in logs/feature_filtering.csv

### Step 4: Train and Evaluate Models

```bash
# Train species-specific Ridge Regression models with cross-validation and permutation testing
python code/main.py --train --evaluate
```

**Expected Output**: Model artifacts in outputs/models/; evaluation metrics (RMSE, Pearson r, p-values)

### Step 5: View Results

```bash
# Display summary of model performance
python code/main.py --summary
```

**Expected Output**: Table of metabolites with RMSE, Pearson r, and Bonferroni-corrected p-values

## Expected Runtime

- Total pipeline: ≤4 hours on GitHub Actions free-tier runner
- Data download: [deferred - depends on dataset sizes]
- Preprocessing: [deferred - depends on sample count]
- Modeling: [deferred - depends on feature count and CV folds]

## Troubleshooting

| Error | Cause | Resolution |
|-------|-------|------------|
| E-DATASET | No verified plant omics datasets found | Add verified plant datasets to verified datasets block or modify spec |
| E-PAIRING | <95% sample-level pairing rate | Review logs/data_pairing.json; verify GEO and Metabolomics Workbench experiment compatibility |
| E-POWER | Sample size <28 (insufficient power) | Cannot proceed; project halts. Requires additional data sources |
| MemoryError | Dataset exceeds 7 GB RAM | Reduce sample size or stream data in batches |
| Timeout | Runtime exceeds 4 hours | Optimize I/O operations; reduce permutation iterations |
| KEGG API Error | Pathway annotation unavailable | Use ortholog mapping fallback; check docs/edge_cases.md |

## Data Integrity Notes

- All downloaded files are checksummed (SHA-256) and recorded in data/sources.yaml
- Raw data is preserved unchanged in data/raw/
- All transformations produce new files in data/processed/ or data/paired/
- No data modification in place; all derivations documented

**⚠️ SPEC VS PLAN INCONSISTENCY NOTE**: The spec.md FR-010 still references cross-species model as primary, but this quickstart correctly documents species-specific models as PRIMARY. This requires spec.md revision (flagged for kickback).