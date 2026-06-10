# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-05-31

## Prerequisites

- Python 3.11 or higher
- Stable internet connectivity (for downloading data from Knot Atlas)
- 10GB+ free disk space (for data storage and analysis artifacts)

## Installation

### Step 1: Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

### Step 2: Verify Dependencies

```bash
# Check Python version
python --version  # Should be 3.11+

# Verify key packages
python -c "import pandas; import numpy; import scipy; import statsmodels; print('Dependencies OK')"
```

## Data Download

### Step 3: Download Knot Data

```bash
# Run the download script
python code/download/knot_atlas_downloader.py

# This will:
# - Download prime knot data for crossing number ≤13
# - Apply retry logic with exponential backoff on failures
# - Cache partial results after 3 consecutive failures
# - Output: data/raw/knots_raw.csv
```

**Expected Output**:
- 9988 prime knots at crossing number 13 (source: OEIS A002863)
- Data includes: crossing number, braid index, hyperbolic volume, alternating classification
- Download may take 30-60 minutes depending on network conditions

### Step 4: Verify Data Integrity

```bash
# Check SHA-256 checksums
cat data/checksums.txt

# Validate dataset completeness (Phase 1 benchmark: crossing number ≤10)
python code/compute/validation.py --validate-completeness --crossing-limit 10
```

**Expected Output**:
- Completeness rate ≥95% for required invariant fields (crossing number, braid index, hyperbolic volume)
- Validation report saved to `docs/reproducibility/validation_scope.md`

## Invariant Computation

### Step 5: Compute Additional Invariants

```bash
# Run invariant computation
python code/compute/invariant_computation.py

# This will:
# - Compute arc index via Birman-Menasco method
# - Compute Seifert circle count via Seifert's algorithm
# - Compute bridge number via Schubert's decomposition
# - Flag records with missing invariant data
# - Output: data/processed/knots_with_invariants.csv
```

**Expected Output**:
- Arc index, Seifert circle count, bridge number computed where diagram representations available
- ≥99% of computable invariants populated (per SC-006)
- Uncomputable records logged in `docs/reproducibility/uncomputable_invariants.md`

### Step 6: Validate Algorithm Implementation

```bash
# Validate against KnotInfo reference values
python code/compute/validation.py --validate-algorithms

# Output: docs/reproducibility/algorithm_validation.md
```

**Expected Output**:
- ≥95% match with KnotInfo reference values where coverage ≥10%
- Coverage constraint documented if reference coverage <10%

## Exploratory Analysis

### Step 7: Generate Exploratory Plots

```bash
# Run exploratory analysis
python code/analysis/exploratory_analysis.py

# Output: data/plots/crossing_vs_braid_*.png (1200x900px minimum)
```

**Expected Output**:
- Scatter plot: crossing number vs. braid index (alternating knots)
- Scatter plot: crossing number vs. braid index (non-alternating knots)
- Summary statistics for each knot class

## Regression Modeling

### Step 8: Fit Regression Models

```bash
# Run regression analysis
python code/analysis/regression_models.py

# This will:
# - Fit linear, polynomial, and logarithmic models
# - Compute VIF for multicollinearity assessment
# - Validate composite complexity score on exploratory sample (20% split)
# - Output: data/results/regression_models.json
```

**Expected Output**:
- Three model types compared with R², AIC/BIC, MAE metrics
- VIF values documented for all predictors
- Composite complexity score correlation with hyperbolic volume reported

### Step 9: Run Statistical Tests

```bash
# Run statistical validation
python code/analysis/statistical_tests.py

# This will:
# - Perform ANOVA for group differences (with assumption checks)
# - Compute Pearson AND Spearman correlations (both required)
# - Report effect sizes (Cohen's d, r)
# - Output: data/results/statistical_tests.json
```

**Expected Output**:
- ANOVA results with Levene's test and Shapiro-Wilk test outcomes
- Dual correlation reporting (Pearson + Spearman)
- Effect sizes documented alongside p-values

## Reproducibility Verification

### Step 10: Verify Reproducibility Artifacts

```bash
# Check reproducibility documentation
ls -la docs/reproducibility/

# Verify all required files present:
# - checksums.txt
# - derivation_notes.md
# - algorithm_validation.md
# - excluded_knots.md
# - tie_breaking_rules.md
# - uncomputable_invariants.md
# - validation_scope.md
# - logs/
```

### Step 11: Run Full Reproducibility Check

```bash
# Run reproducibility verification script
python code/tests/reproducibility_check.py

# This verifies:
# - All random seeds pinned
# - All checksums match
# - All derivation notes complete
# - All logs timestamped and traceable
```

## Common Issues

### Issue: Knot Atlas Unavailable

**Symptom**: Download fails with connection error  
**Resolution**: Retry logic automatically applies exponential backoff (1s → 2s → 4s → ... → 60s max). Partial results cached after 3 consecutive failures. Check `data/raw/knots_raw_partial.csv` for cached data.

### Issue: Missing Invariant Data

**Symptom**: Some knots have null values for computed invariants  
**Resolution**: Records are flagged with `missing_invariant_flags` rather than excluded. Check `docs/reproducibility/uncomputable_invariants.md` for details.

### Issue: ANOVA Assumption Violation

**Symptom**: Levene's test or Shapiro-Wilk test indicates assumption violation  
**Resolution**: System automatically uses robust alternatives (Welch's ANOVA, Kruskal-Wallis). Documented in `docs/reproducibility/derivation_notes.md`.

### Issue: Multicollinearity Warning

**Symptom**: VIF > 5 for crossing number or braid index  
**Resolution**: This is expected given braid index ≤ crossing number inequality. VIF values documented in final reports as potential multicollinearity issue affecting coefficient interpretation.

## Next Steps

1. Review exploratory analysis plots in `data/plots/`
2. Examine regression model metrics in `data/results/regression_models.json`
3. Read algorithm validation results in `docs/reproducibility/algorithm_validation.md`
4. Prepare Phase 1 final report with conclusions limited to validated crossing number ≤10 data
5. Plan Phase 2+ for multi-class prime knot exploration (torus, satellite, hyperbolic)
