# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-05-31

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git (for version control)
- Internet connectivity (for downloading Knot Atlas data)
- Minimum 4GB RAM (for processing ~10,000 knot records)
- Minimum 1GB free disk space (for data and derived files)

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/<your-org>/llmXive.git
cd llmXive/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt contents**:
```
pandas==2.2.2
numpy==1.26.4
scipy==1.13.1
matplotlib==3.9.0
seaborn==0.13.2
pyyaml==6.0.1
requests==2.32.3
retry==0.9.2
datasets==2.20.0
pytest==8.2.2
pytest-cov==5.0.0
```

### 4. Verify Installation

```bash
python -c "import pandas; import scipy; print('Dependencies installed successfully')"
```

## Data Download and Processing

### 1. Download Knot Atlas Data

```bash
python code/data/download_knot_atlas.py
```

**Output**: `data/raw/knot_atlas_2026-05-31.json` (with SHA-256 checksum)

**Expected behavior**:
- Downloads all prime knots with crossing number ≤13
- Implements retry logic with exponential backoff (1s → 2s → 4s → ... → 60s max)
- Caches partial results after 3 consecutive failures
- Records checksum in `data/checksums.txt`

### 2. Parse and Clean Data

```bash
python code/data/parse_and_clean.py
```

**Output**: `data/derived/knots_cleaned.parquet`

**Expected behavior**:
- Extracts consistent representations of crossing number, braid index, hyperbolic volume
- Flags records with missing invariant data
- Documents excluded knots in `docs/reproducibility/excluded_knots.md`

### 3. Compute Additional Invariants

```bash
python code/data/compute_invariants.py
```

**Output**: `data/derived/knots_with_invariants.parquet`

**Expected behavior**:
- Computes arc index, Seifert circle count, bridge number where diagram representations available
- Flags records where invariants cannot be computed
- Validates algorithms against KnotInfo (if coverage ≥10%)
- Documents validation results in `docs/reproducibility/algorithm_validation.md`
- Documents uncomputable invariants in `docs/reproducibility/uncomputable_invariants.md`

## Exploratory Analysis

### 1. Generate Scatter Plots

```bash
python code/analysis/exploratory_analysis.py
```

**Output**: `data/derived/plots/crossing_vs_braid_*.png` (1200x900 pixels minimum)

**Expected behavior**:
- Generates scatter plots of crossing number vs. braid index
- Stratifies by alternating/non-alternating classification
- Saves PNG files to `data/derived/plots/`

### 2. Fit Regression Models

```bash
python code/analysis/regression_models.py
```

**Output**: `data/derived/regression_models.parquet`

**Expected behavior**:
- Fits linear, polynomial, and logarithmic regression models
- Computes VIF for multicollinearity assessment
- Identifies residual outliers (specific knot families)
- Documents model metrics (R², AIC/BIC, MAE)

### 3. Run Statistical Tests

```bash
python code/analysis/statistical_tests.py
```

**Output**: `data/derived/statistical_results.parquet`

**Expected behavior**:
- Computes Pearson AND Spearman correlations
- Performs ANOVA with assumption checks (Levene's, Shapiro-Wilk)
- Reports effect sizes (Cohen's d, r²) alongside p-values
- Uses robust alternatives if assumptions violated

## Reproducibility Verification

### 1. Check Checksums

```bash
python code/utils/reproducibility.py verify-checksums
```

**Output**: Verification report in `docs/reproducibility/checksums.md`

### 2. Verify Tie-Breaking Rules

```bash
python docs/reproducibility/validate_tie_breaking.py
```

**Output**: Validation status in `docs/reproducibility/validation_status.md`

### 3. Review Derivation Notes

```bash
cat docs/reproducibility/derivation_notes.md
```

**Expected contents**:
- Formula citations with page/section references
- Step-by-step transformation logic
- All parameter values used
- Justification for non-standard choices

## Running Tests

### Unit Tests

```bash
pytest tests/unit/ -v
```

### Integration Tests

```bash
pytest tests/integration/ -v
```

### Contract Tests

```bash
pytest tests/contract/ -v
```

### Full Test Suite with Coverage

```bash
pytest tests/ -v --cov=code --cov-report=html
```

## Configuration

### Complexity Score Weights

Edit `config/complexity_weights.yaml` to configure composite complexity score weights:

```yaml
# Default equal weights (1:1 ratio)
weight_crossing_number: 0.5
weight_braid_index: 0.5

# Example: Custom weights
# weight_crossing_number: 0.7
# weight_braid_index: 0.3
```

### Random Seeds

Random seeds are pinned in code at module level:

```python
# code/__init__.py
import random
import numpy as np

RANDOM_SEED = 42  # Configurable via environment variable
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
```

## Output Artifacts

After successful execution, the following artifacts should be present:

```
data/
├── raw/
│   └── knot_atlas_2026-05-31.json       # Raw download
├── derived/
│   ├── knots_cleaned.parquet            # Cleaned dataset
│   ├── knots_with_invariants.parquet    # Dataset with computed invariants
│   ├── plots/
│   │   ├── crossing_vs_braid_alternating.png
│   │   └── crossing_vs_braid_non_alternating.png
│   ├── regression_models.parquet        # Fitted models
│   └── statistical_results.parquet      # Statistical test results
└── checksums.txt                        # SHA-256 checksums

docs/reproducibility/
├── checksums.md                         # Checksum documentation
├── derivation_notes.md                  # Transformation documentation
├── logs/
│   └── execution_2026-05-31.log         # Execution logs
├── validation_scope.md                  # Phase 1 scope documentation
├── algorithm_validation.md              # Algorithm validation results
├── uncomputable_invariants.md           # Uncomputable invariant records
├── excluded_knots.md                    # Excluded knot documentation
├── tie_breaking_rules.md                # Tie-breaking rules
└── validation_status.md                 # Validation status
```

## Troubleshooting

### Knot Atlas Unavailable

**Symptom**: Download script fails after 3 consecutive retries

**Solution**:
- Check network connectivity
- Verify Knot Atlas URL is accessible
- Partial results cached to disk after 3 failures (FR-010)
- Review `docs/reproducibility/logs/execution_*.log` for error details

### Missing Invariant Data

**Symptom**: High number of records flagged with `missing_invariant_flags`

**Solution**:
- Review `docs/reproducibility/uncomputable_invariants.md` for specific reasons
- Check if diagram representations (DT codes, braid words) are available in source data
- Verify algorithm implementations in `code/data/compute_invariants.py`

### ANOVA Assumption Violations

**Symptom**: Levene's test or Shapiro-Wilk test indicates assumption violation

**Solution**:
- System automatically switches to robust alternatives (Welch's ANOVA, Kruskal-Wallis)
- Documentation notes the deviation from standard ANOVA
- Review `docs/reproducibility/derivation_notes.md` for assumption check results

### Multicollinearity Warning

**Symptom**: VIF > 5 for any predictor

**Solution**:
- Document multicollinearity issue in final reports (FR-005)
- Consider alternative model specifications
- Acknowledge that braid index ≤ crossing number for most knots (known inequality)

## Next Steps

After completing the quickstart:

1. Review results in `data/derived/`
2. Examine reproducibility documentation in `docs/reproducibility/`
3. Run full test suite to verify all components
4. Proceed to implementation phase (`/speckit-tasks` command)

## Support

- **Constitution Principles**: See `projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/.specify/memory/constitution.md`
- **Feature Specification**: See `specs/001-knot-complexity-analysis/spec.md`
- **Implementation Plan**: See `specs/001-knot-complexity-analysis/plan.md`
