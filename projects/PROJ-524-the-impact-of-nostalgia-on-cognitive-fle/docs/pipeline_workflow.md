# Research Pipeline Workflow

## Phase 1: Setup

1. Create directory structure (`data/raw`, `data/processed`, `data/results`, `data/stimuli`)
2. Initialize configuration and logging
3. Set up schema contracts

## Phase 2: Data Ingestion (US1)

1. **Fetch Data**: Load from OpenML/HuggingFace or local files
2. **Validate Schema**: Check against `dataset.schema.yaml`
3. **Filter Records**:
 - Age ≥ 65
 - Non-null cognitive metrics
 - Valid stimulus_type
4. **Exclusion Logging**: Generate `exclusion_log.json`
5. **MMSE Check**: Set `has_mmse` flag
6. **Output**: `cleaned_dataset.csv`, `validity_metrics.json`

## Phase 3: Statistical Analysis (US2)

1. **Group Separation**: Split by `stimulus_type`
2. **Welch's t-test**: Compare means for each metric
3. **Effect Size**: Calculate Cohen's d with 95% CI
4. **Multiple Comparison Correction**: Bonferroni adjustment
5. **Power Analysis**: Calculate power and MDES
6. **Output**: `statistical_report.json`

## Phase 4: Sensitivity Analysis (US3)

1. **Threshold Sweep**: Test α ∈ {0.01, 0.05, 0.1}
2. **Robustness Check**: Re-run with MMSE < 24 exclusion
3. **Borderline Flagging**: Identify threshold-sensitive results
4. **Stability Metrics**: Compute consistency scores
5. **Output**: `sensitivity_report.json`

## Phase 5: Final Report Generation

1. **Compile Results**: Merge statistical and sensitivity outputs
2. **Citation Validation**: Verify source references
3. **Generate Paper Draft**: `paper/001_results.md`
4. **Archive Artifacts**: Hash and timestamp all outputs

## Data Flow Diagram

```
[Raw Data Source]
 ↓
[Ingestion & Validation]
 ↓
[Exclusion Log]
 ↓
[Cleaned Dataset]
 ↓
[Statistical Analysis] → [Statistical Report]
 ↓
[Sensitivity Analysis] → [Sensitivity Report]
 ↓
[Final Report Compilation]
 ↓
[paper/001_results.md]
```

## Error Handling

- **Missing Age**: Log `ERR_MISSING_AGE_FIELD`, exclude record
- **Missing MMSE**: Log `ERR_MMSE_MISSING`, set flag, skip MMSE filter
- **Zero Variance**: Handle in t-test (skip or warn)
- **Timeout**: Log `WARN_TIMEOUT` if runtime > 6 hours, continue

## Reproducibility

- All random seeds fixed
- All versions pinned in `requirements.txt`
- Checksums verified for all data files
- Complete exclusion logs archived