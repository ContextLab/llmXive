# Quickstart Guide: Quantifying the Complexity of Knot Diagrams

This guide documents the end-to-end pipeline execution steps for the Knot Complexity Analysis project. Follow these instructions to reproduce the complete analysis from raw data download through regression modeling and reproducibility verification.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Internet connectivity (for Knot Atlas data download)
- Minimum 2GB available disk space

## 1. Environment Setup

### 1.1 Clone and Navigate

```bash
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr
```

### 1.2 Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages (per T002):
- pandas, numpy, scipy, statsmodels, matplotlib, seaborn, requests, pyyaml
- black, flake8 (for linting per T003)

### 1.3 Verify Project Structure

```bash
# Confirm all directories exist (per T001)
ls code/ tests/ data/ docs/
ls data/raw/ data/processed/ data/plots/
ls docs/reproducibility/
```

## 2. Foundation Verification

### 2.1 Validate Schemas

```bash
# Verify schema files exist (per T004, T005, T005b)
cat specs/001-knot-complexity-analysis/contracts/knot-record.schema.yaml
cat specs/001-knot-complexity-analysis/contracts/regression-model.schema.yaml
cat specs/001-knot-complexity-analysis/contracts/dataset.schema.yaml
```

### 2.2 Verify Reproducibility Framework

```bash
# Test logging framework (per T006)
python -c "from code.reproducibility.logs import get_logger; logger = get_logger(); logger.log('test', 'verification')"
```

### 2.3 Verify Random Seed Pinning

```bash
# Confirm seeds are documented (per T007)
cat docs/reproducibility/random_seeds.md
```

## 3. Data Download and Processing (User Story 1)

### 3.1 Download Knot Atlas Data

```bash
# Execute the Knot Atlas downloader (per T013, T014)
python code/download/knot_atlas_loader.py
```

Expected output:
- Raw data saved to `data/raw/knot_atlas_raw.json`
- Retry logic with exponential backoff (1s → 2s → 4s → 8s → 16s → 32s)
- Partial cache after 3 consecutive failures

### 3.2 Parse and Clean Data

```bash
# Run parser with tie-breaking rules (per T015)
python code/data/parser.py

# Run validator with flagging (per T016, T009, T010, T043a)
python code/data/validator.py
```

Output:
- Cleaned data to `data/processed/knots_cleaned.csv`
- Validation flags recorded in data artifacts

### 3.3 Filter to Hyperbolic Knots

```bash
# Apply hyperbolic volume filter (per T019)
python code/data/filter_hyperbolic.py
```

Expected:
- Excluded knots logged to `docs/reproducibility/excluded_knots.md`
- Filtered dataset ready for analysis

### 3.4 Validate Dataset Completeness

```bash
# Validate against OEIS A002863 and KnotInfo (per T020)
python code/analysis/validate_completeness.py
```

Output:
- Validation results in `docs/reproducibility/validation_scope.md`

## 4. Precision Validation (User Story 2)

### 4.1 Compute Precision Metrics

```bash
# Validate crossing number and braid index precision (per T022)
python code/analysis/precision.py
```

### 4.2 Generate Visualization

```bash
# Create scatter plots stratified by alternating classification (per T023, T024)
python code/analysis/exploratory.py
```

Output:
- `data/plots/crossing_vs_braid.png` (1200x900 pixels)
- Stratified by alternating/non-alternating knots

### 4.3 Data Quality Report

```bash
# Generate null percentage report (per T028, T029)
python code/analysis/data_quality.py
```

Output:
- `docs/reproducibility/data_quality_report.md`
- Application of missing_invariant_flags and data_quality_flags

### 4.4 Tie-Breaking Validation

```bash
# Validate tie-breaking rule consistency (per T030b)
python code/reproducibility/tie_breaking_validator.py
```

Expected: Exit code 0 on success

## 5. Regression Analysis (User Story 3)

### 5.1 Fit Regression Models

```bash
# Fit linear, polynomial, logarithmic models (per T032, T033)
python code/analysis/regression.py
```

Output:
- R², AIC/BIC, MAE metrics for each model
- VIF for multicollinearity assessment (per T037)

### 5.2 Residual Analysis

```bash
# Identify outlier families (per T034, T035)
python code/analysis/residual_analysis.py
```

Output:
- `docs/reproducibility/residual_analysis.md`
- Knots deviating ≥2 standard deviations

### 5.3 Correlation Analysis

```bash
# Compute Spearman and Pearson correlations (per T036)
python code/analysis/correlation.py
```

Note: P-values marked as "not applicable for census data" per FR-006 and Constitution Principle VII

### 5.4 Group Comparisons

```bash
# Compute descriptive metrics for alternating vs. non-alternating (per T039)
python code/analysis/group_comparison.py
```

## 6. Reproducibility Documentation (User Story 4)

### 6.1 Generate Checksums

```bash
# Create SHA-256 checksums for all data files (per T044, T045)
python code/reproducibility/checksums.py
```

Output:
- Checksums recorded in data/ directory
- `docs/reproducibility/checksums.md`

### 6.2 Generate Derivation Notes

```bash
# Document formula citations and transformations (per T046)
python code/reproducibility/derivation_validator.py
```

### 6.3 Operation Logs

```bash
# Review timestamped operation logs (per T049)
cat docs/reproducibility/operation_logs.md
```

### 6.4 Generate Complete Reproducibility Report

```bash
# Run validation status check (per T053)
python code/reproducibility/validation_status.py
```

## 7. Verification Steps

### 7.1 Validate Quickstart Execution

```bash
# Verify end-to-end reproducibility (per T056)
python code/reproducibility/quickstart_validator.py
```

Expected: `docs/reproducibility/quickstart_validation.md` with pass/fail status

### 7.2 Confirm Linting Compliance

```bash
# Run black check (per T055)
black --check code/
```

### 7.3 Verify Random Seeds

```bash
# Confirm all seeds are pinned (per T058)
cat docs/reproducibility/seed_verification.md
```

## 8. Expected Outputs Summary

| Artifact | Path | Description |
|----------|------|-------------|
| Raw Data | data/raw/knot_atlas_raw.json | Downloaded Knot Atlas data |
| Cleaned Data | data/processed/knots_cleaned.csv | Filtered and validated dataset |
| Scatter Plot | data/plots/crossing_vs_braid.png | Crossing vs. braid visualization |
| Data Quality | docs/reproducibility/data_quality_report.md | Null percentages and flags |
| Excluded Knots | docs/reproducibility/excluded_knots.md | Hyperbolic filter exclusions |
| Residual Analysis | docs/reproducibility/residual_analysis.md | Outlier family documentation |
| Checksums | docs/reproducibility/checksums.md | SHA-256 verification hashes |
| Final Report | docs/reproducibility/final_report.md | Synthesized findings |

## 9. Troubleshooting

### API Unavailability

If Knot Atlas is unavailable, the downloader will:
1. Retry with exponential backoff (max 6 attempts)
2. Cache partial results after 3 consecutive failures
3. Log all failures to operation_logs.md

### Missing Invariants

Missing invariants are flagged per FR-009:
- Check `missing_invariant_flags` in validator output
- Review `docs/reproducibility/uncomputable_invariants.md`

### Ambiguous Classifications

Ambiguous alternating/non-alternating classifications:
- Marked as 'unclassifiable' per FR-010
- Logged in `docs/reproducibility/ambiguous_classification_log.md`

## 10. References

- Plan: `plan.md` in project root
- Specification: `specs/001-knot-complexity-analysis/spec.md`
- Data Model: `data-model.md` in project root
- Contracts: `specs/001-knot-complexity-analysis/contracts/`

## 11. Contact

For issues or questions, refer to the project's issue tracker or contact the maintainers listed in `CONTRIBUTING.md`.