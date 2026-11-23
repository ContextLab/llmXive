# Analysis Pipeline Documentation

## Pipeline Overview

This document provides a detailed walkthrough of the analysis pipeline, including data flow, expected outputs, and troubleshooting guidelines.

## Execution Order

The pipeline must be executed in the following order:

1. **Phase 0**: Data Validation & Feasibility Check (BLOCKING)
2. **Phase 1**: Setup (Parallelizable)
3. **Phase 2**: Foundational (Blocking Prerequisites)
4. **Phase 3**: User Story 1 - Data Ingestion
5. **Phase 4**: User Story 2 - Centrality & Modeling
6. **Phase 5**: User Story 3 - Validation
7. **Phase 6**: Reporting

## Detailed Workflow

### Phase 0: Data Validation

**Tasks**: T001-T004

**Inputs**:
- OpenNeuro dataset URL (from config)

**Outputs**:
- `data/raw/metadata.csv`
- `data/processed/behavioral/retention_metrics.json`

**Process**:
1. Download dataset using `openneuro-cli`
2. Verify required columns: `pre_motor_score`, `post_motor_score`, `age`, `sex`, `subject_id`
3. Calculate retention rate (subjects with valid data / total subjects)
4. **Fatal Gate**: If retention < 80% due to missing behavioral data, exit immediately
5. Check power (N >= 85) and log warning if underpowered

**Failure Conditions**:
- Missing required columns in metadata
- Retention rate < 80% due to missing behavioral data
- Dataset download failure

### Phase 1: Setup

**Tasks**: T005-T008

**Outputs**:
- Directory structure: `code/`, `data/`, `tests/`
- `.gitignore` configuration
- `requirements.txt` with dependencies

### Phase 2: Foundational

**Tasks**: T009-T013

**Outputs**:
- Logging infrastructure (`code/utils/logging.py`)
- Reproducibility reporting utility (`code/utils/metrics.py`)
- Data models (`code/data/subject.py`, `code/data/connectivity_matrix.py`)
- Configuration management (`code/utils/config.py`)

### Phase 3: User Story 1 - Data Ingestion

**Tasks**: T014-T020

**Inputs**:
- `data/raw/metadata.csv`
- fMRIPrep outputs

**Outputs**:
- `data/processed/behavioral/subject_scores.csv`
- `data/processed/behavioral/fd_mean.csv`
- `data/processed/logs/exclusion_log.csv`

**Process**:
1. Run fMRIPrep with memory-efficient settings (float32, batch processing)
2. Extract behavioral metrics: pre/post motor scores, age, sex
3. Calculate improvement score: `post_motor_score - pre_motor_score`
4. Calculate mean Framewise Displacement (FD) per subject
5. Log excluded subjects and reasons

**Key Parameters**:
- FD threshold for motion artifact detection
- Minimum retention rate: 80%

### Phase 4: User Story 2 - Centrality & Modeling

**Tasks**: T021-T032

**Inputs**:
- `data/processed/behavioral/subject_scores.csv`
- fMRIPrep connectivity matrices
- `data/processed/behavioral/fd_mean.csv`

**Outputs**:
- `data/processed/centrality/subject_id_metrics.csv`
- `data/processed/centrality/global_scores.csv`
- `data/processed/centrality/vif_values.csv`
- `data/processed/centrality/model_predictors.csv`
- `data/processed/regression/linear_model_summary.csv`
- `data/processed/regression/nonlinearity_check.csv`
- `data/processed/regression/regional_pvalues.csv` (conditional)
- `data/processed/validation/null_residuals.csv`
- `data/processed/validation/baseline_r2.json`

**Process**:
1. **Centrality Calculation** (T023):
 - Load connectivity matrices for full AAL3 atlas (~90 regions)
 - Compute degree, betweenness, eigenvector centrality for each region
 - Save to `subject_id_metrics.csv`

2. **Global Score Aggregation** (T024):
 - Aggregate regional metrics (mean of all regions or top hub nodes)
 - Save to `global_scores.csv`

3. **Mean FD Calculation** (T025):
 - Read fMRIPrep confounds TSVs
 - Calculate mean FD per subject

4. **VIF Calculation** (T026):
 - Calculate Variance Inflation Factor for degree, betweenness, eigenvector
 - Save to `vif_values.csv`

5. **Model Predictor Selection** (T027):
 - If any VIF > 5: Run PCA, retain first component, set `model_type`='PCA-Adjusted'
 - Else: Use 'Global_Centrality', set `model_type`='Global'
 - Save decision to `model_predictors.csv`

6. **Linear Regression** (T028):
 - Formula: `Improvement ~ [Predictor] + Age + Sex + Mean_FD`
 - Fit using statsmodels
 - Save summary to `linear_model_summary.csv`

7. **Null Model & Baseline** (T029):
 - Fit intercept-only model (`Improvement ~ 1`)
 - Calculate residuals
 - Save baseline R² to `baseline_r2.json`

8. **Non-Linearity Check** (T030):
 - Fit GAM/Polynomial model
 - Compare AIC/BIC with linear model
 - Save to `nonlinearity_check.csv`

9. **Scatter Plot** (T031):
 - Generate visualization with regression line and non-linearity fit

10. **Regional Analysis** (T032 - Conditional):
 - If `config.regional_analysis_flag == true`:
 - Fit separate models for each region
 - Save regional p-values to `regional_pvalues.csv`
 - Else: Skip and log

### Phase 5: User Story 3 - Validation

**Tasks**: T033-T039

**Inputs**:
- `data/processed/validation/null_residuals.csv`
- `data/processed/regression/linear_model_summary.csv`
- `data/processed/centrality/model_predictors.csv`
- `data/processed/behavioral/subject_scores.csv`
- `data/processed/validation/baseline_r2.json`

**Outputs**:
- `data/processed/validation/null_distribution.csv`
- `data/processed/validation/permutation_results.json`
- `data/processed/validation/cv_results.json`
- `data/processed/validation/fdr_corrected_pvalues.csv` (conditional)

**Process**:
1. **Null Distribution** (T035):
 - Permute residuals 1000 times (Freedman-Lane, seed=42)
 - Refit model for each permutation
 - Record primary predictor coefficient
 - Save to `null_distribution.csv`

2. **Empirical P-Value** (T036):
 - Compare observed coefficient to null distribution
 - Calculate empirical p-value
 - Save to `permutation_results.json`

3. **Cross-Validation** (T037):
 - Perform 5-fold CV (seed=42)
 - Calculate out-of-sample R² and RMSE
 - Compare mean R² against baseline R²
 - Save to `cv_results.json`

4. **Null Distribution Histogram** (T038):
 - Generate visualization with observed coefficient overlay

5. **FDR Correction** (T039 - Conditional):
 - If `regional_analysis_flag == true`:
 - Apply Benjamini-Hochberg FDR to regional p-values
 - Save to `fdr_corrected_pvalues.csv`
 - Else: Skip and log

### Phase 6: Reporting

**Tasks**: T040

**Inputs**:
- All validation metrics
- Git commit information
- Resource usage data

**Outputs**:
- `reproducibility_report.json`

**Process**:
1. Calculate checksums for all artifacts
2. Collect wall clock time and RAM usage
3. Aggregate all validation metrics (p-values, R², RMSE)
4. Generate comprehensive report

## Troubleshooting

### Common Issues

#### Dataset Download Fails
- **Cause**: Network issues, authentication errors
- **Solution**: Check OpenNeuro credentials, verify network connectivity

#### Retention Rate < 80%
- **Cause**: Missing behavioral data for many subjects
- **Solution**: Investigate data quality, contact data provider if necessary

#### Memory Errors During Preprocessing
- **Cause**: Insufficient RAM for batch processing
- **Solution**: Reduce batch size, enable float32 precision, increase swap space

#### VIF > 5
- **Cause**: High multicollinearity between centrality metrics
- **Solution**: Pipeline automatically switches to PCA-based model

#### Permutation Test Takes Too Long
- **Cause**: Large number of shuffles or subjects
- **Solution**: Reduce `permutation_shuffles` in config (not recommended for final analysis)

### Debugging Tips

- Enable verbose logging: `config.log_level = 'DEBUG'`
- Check intermediate outputs in `data/processed/`
- Validate data shapes before each processing step
- Use `python code/utils/metrics.py --check` to verify artifact integrity

## Performance Optimization

- **Float32 Precision**: Use float32 for all numerical operations
- **Batch Processing**: Process subjects in batches to manage memory
- **Parallel Execution**: Run independent tasks in parallel where possible
- **Streaming**: Stream large datasets instead of loading entirely into memory

## Configuration Reference

Key configuration parameters:

```python
# config.py
vif_threshold = 5.0 # VIF threshold for model selection
permutation_shuffles = 1000 # Number of permutations for validation
permutation_seed = 42 # Random seed for reproducibility
cv_folds = 5 # Number of folds for cross-validation
min_retention_rate = 0.80 # Minimum retention rate threshold
power_threshold_n = 85 # Minimum subjects for adequate power
regional_analysis_flag = False # Enable regional p-value analysis
```
