# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Internet connectivity for downloading from Knot Atlas
- Minimum 4GB RAM (recommended 8GB for full ≤13 crossing dataset)
- Minimum 2GB disk space for data and outputs

## Installation

### Step 1: Clone and Navigate

```bash
git clone <repository-url>
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r code/requirements.txt
```

### Step 4: Verify Installation

```bash
python -c "import pandas, numpy, scipy, statsmodels; print('All dependencies installed successfully')"
```

## Running the Pipeline

### Phase 1: Data Download (User Story 1 - P1)

```bash
python code/cli/main.py download --output data/raw/knot_atlas_download.parquet
```

**Expected Output**:
- Download progress logged to console
- File saved to data/raw/knot_atlas_download.parquet
- Checksum recorded in data/raw/.checksums
- Retry logic activated if API unavailable (exponential backoff: 1s → 2s → 4s →... → 60s max)

**Validation**:
- Run `python code/cli/main.py validate --input data/raw/knot_atlas_download.parquet`
- Should report ≥95% completeness on required invariant fields for c≤10

### Phase 2: Invariant Computation (User Story 2 - P2)

```bash
python code/cli/main.py compute-invariants \
 --input data/raw/knot_atlas_download.parquet \
 --output data/processed/knots_with_invariants.parquet
```

**Expected Output**:
- Arc index, Seifert circle count, bridge number computed where diagram representations available
- Records with missing invariants flagged in missing_invariant_flags field
- Summary report at docs/reproducibility/uncomputable_invariants.md

**Validation**:
- Run `python code/cli/main.py validate-algorithms --input data/processed/knots_with_invariants.parquet`
- Should report ≥95% match with KnotInfo reference values where coverage ≥10%

### Phase 3: Exploratory Analysis (User Story 2 - P2)

```bash
python code/cli/main.py exploratory-analysis \
 --input data/processed/knots_with_invariants.parquet \
 --output-dir data/plots/
```

**Expected Output**:
- Scatter plots saved to data/plots/ with minimum resolution 1200x900 pixels
- crossing_vs_braid_alternating.png
- crossing_vs_braid_non_alternating.png
- Summary statistics logged to console

### Phase 4: Regression Modeling (User Story 3 - P3)

```bash
python code/cli/main.py regression \
 --input data/processed/knots_with_invariants.parquet \
 --models linear,polynomial,logarithmic \
 --output-dir code/models/
```

**Expected Output**:
- Three model types fitted and saved to code/models/
- VIF values computed and documented (with mathematical constraint context)
- Residual analysis identifying deviating knot families
- Model metrics (R², AIC/BIC, MAE) logged
- Bonferroni-adjusted p-values for model comparison

### Phase 5: Composite Score Validation (User Story 3 - P3)

```bash
python code/cli/main.py composite-score \
 --input data/processed/knots_with_invariants.parquet \
 --config config/complexity_weights.yaml \
 --validation-split 0.2 \
 --output-dir docs/reproducibility/
```

**Expected Output**:
- Composite complexity scores computed with default 1:1 weights
- Pearson and Spearman correlations reported
- Effect sizes (r, Cohen's d) documented
- Validation results saved to docs/reproducibility/

### Phase 6: Reproducibility Check (User Story 4 - P4)

```bash
python code/cli/main.py reproducibility-check \
 --data-dir data/ \
 --docs-dir docs/reproducibility/ \
 --output docs/reproducibility/validation_status.md
```

**Expected Output**:
- SHA-256 checksums verified for all data files
- Derivation notes completeness validated
- Random seed documentation verified
- Validation status reported
- SC-006 and SC-014 completeness percentages calculated

## Configuration

### Complexity Weights (config/complexity_weights.yaml)

```yaml
crossing_weight: 1.0
braid_weight: 1.0
# Note: Equal weights are exploratory; no theoretical basis for differential weighting
```

### Random Seeds

All random seeds are pinned in code. Current seed values documented in:
- docs/reproducibility/random_seeds.md

### Retry Configuration

Exponential backoff parameters (FR-010):
- Initial delay: 1 second
- Maximum delay: 60 seconds
- Multiplier: 2

## Output Locations

| Output | Location |
|--------|----------|
| Raw downloaded data | data/raw/knot_atlas_download.parquet |
| Processed dataset | data/processed/knots_with_invariants.parquet |
| Exploratory plots | data/plots/*.png |
| Regression models | code/models/*.json |
| Reproducibility docs | docs/reproducibility/*.md |
| Validation status | docs/reproducibility/validation_status.md |

## Troubleshooting

### API Unavailable

If Knot Atlas is unavailable, the download script will:
1. Apply exponential backoff (1s → 2s → 4s →... → 60s max)
2. Cache partial results after 3 consecutive failures
3. Log retry attempts to docs/reproducibility/download_logs.md

**Action**: Check network connectivity, verify API status, review retry logs

### Missing Invariant Data

If invariants cannot be computed for certain knots:
1. Records are flagged with missing_invariant_flags (not silently excluded)
2. Summary report generated at docs/reproducibility/uncomputable_invariants.md
3. SC-006 completeness percentage calculated and reported

**Action**: Review uncomputable_invariants.md to understand which invariants are missing and why

### Algorithm Validation Failure

If algorithm validation against KnotInfo fails (<95% match):
1. Validation results logged to docs/reproducibility/algorithm_validation.md
2. Limitation documented with coverage constraint noted

**Action**: Review algorithm_validation.md; if coverage <10%, validation is skipped per FR-003

### Tie-Breaking Validation Failure

If tie-breaking rules are not applied consistently:
1. Validation script fails with non-zero exit code
2. Error details logged to docs/reproducibility/validation_status.md

**Action**: Re-run invariant computations before proceeding to downstream analysis

## Next Steps

1. Review generated plots in data/plots/
2. Examine regression model metrics in code/models/
3. Read reproducibility documentation in docs/reproducibility/
4. Prepare Phase 1 final report with conclusions limited to validated c≤10 data
5. Plan Phase 2+ for multi-class exploration (torus, satellite, hyperbolic)

## Support

For issues or questions:
1. Check docs/reproducibility/ for detailed logs and derivation notes
2. Review contract tests in tests/contract/
3. Consult spec.md for detailed requirements and acceptance criteria