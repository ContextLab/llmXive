# Pipeline Walkthrough

This document details the end-to-end pipeline for PROJ-037.

## Step 1: Data Ingestion
**Script**: `code/ingestion.py`
**Inputs**:
- AGP 16S rRNA data (BIOM format)
- AGP metadata (TSV)
- OpenHumans sleep metadata (TSV)

**Process**:
1. Download data from canonical URLs.
2. Parse BIOM table and metadata.
3. Merge on Participant ID.
4. Filter missing values.
5. Cap outliers (sleep duration <2h or >16h).
6. Impute covariates (median/mode).
7. Save to `data/processed/cohort_merged.csv`.

**Outputs**:
- `data/processed/cohort_merged.csv`
- `logs/ingestion.log`

## Step 2: Diversity Calculation
**Script**: `code/diversity.py`
**Inputs**:
- `data/raw/agp.biom`
- `data/raw/agp_metadata.tsv`

**Process**:
1. Load BIOM table and metadata.
2. Calculate alpha diversity (Shannon, Simpson).
3. Calculate beta diversity (Bray-Curtis).
4. Merge with sleep metadata.

**Outputs**:
- Updated cohort with diversity metrics.

## Step 3: Associational Analysis
**Script**: `code/analysis.py`
**Inputs**:
- `data/processed/cohort_merged.csv`

**Process**:
1. Calculate correlations (Spearman/Pearson).
2. Apply FDR correction.
3. Run dbRDA for non-linear relationships.
4. Run GLM adjusted for confounders.
5. Run PERMANOVA for categorical variables.
6. Save results to `data/outputs/correlation_results.csv`.

**Outputs**:
- `data/outputs/correlation_results.csv`
- `data/outputs/heatmap.png`
- `data/outputs/pcoa_sleep_quality.png`

## Step 4: Validation
**Script**: `code/validation.py`
**Inputs**:
- `data/outputs/correlation_results.csv`

**Process**:
1. Bootstrap resampling (1000 iterations) for top 5 correlations.
2. Sensitivity analysis on thresholds [0.01, 0.05, 0.1].
3. Save status and report.

**Outputs**:
- `data/outputs/validation_status.json`
- `data/outputs/sensitivity_report.csv`

## Step 5: Report Generation
**Script**: `code/report.py`
**Inputs**:
- `data/outputs/correlation_results.csv`
- `data/outputs/validation_status.json`
- `data/outputs/sensitivity_report.csv`

**Process**:
1. Load all results.
2. Generate sections for bootstrap stability and sensitivity.
3. Frame all findings as "associational".
4. Save to `data/outputs/final_report.md`.

**Outputs**:
- `data/outputs/final_report.md`

## Execution Order
1. `ingestion.py`
2. `diversity.py`
3. `analysis.py`
4. `validation.py`
5. `report.py`

## Notes
- All steps must use real data.
- If any step fails, the pipeline stops.
- All outputs are associational.
