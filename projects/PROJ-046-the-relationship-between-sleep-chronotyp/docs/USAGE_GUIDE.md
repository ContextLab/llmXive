# Usage Guide: Sleep Chronotype and Moral Judgement Pipeline

This guide provides step-by-step instructions for running the analysis pipeline, interpreting results, and troubleshooting common issues.

## Quick Start

### 1. Prepare Your Environment

```bash
# Clone and navigate to project
git clone <repository-url>
cd PROJ-046-the-relationship-between-sleep-chronotyp

# Initialize R environment
Rscript code/00_setup_r_env.py

# Set up project structure
python code/setup_project_structure.py
python code/setup_data_structure.py
```

### 2. Prepare Your Data

Place your merged CSV dataset in `data/raw/`. The file must contain:
- `MEQ_score`: Morningness-Eveningness Questionnaire score
- `MFQ_*`: 5 Morality Foundation Questionnaire subscale scores
- `PSQI`: Pittsburgh Sleep Quality Index
- `acute_sleepiness`: Acute sleepiness measure
- `age`: Participant age
- `sex`: Participant sex

Example command to verify data location:
```bash
ls -l data/raw/
```

### 3. Run the Full Pipeline

Execute scripts in sequence:

```bash
# Step 1: Ingestion
Rscript code/01_ingest.R

# Step 2: Classification
Rscript code/02_classify.R

# Step 3: Aggregate Exclusions Check
Rscript code/02.5_aggregate_exclusions.R

# Step 4: Reliability Analysis
Rscript code/02.6_reliability.R

# Step 5: ANCOVA Analysis
Rscript code/03_analysis.R

# Step 6: Regression Test
Rscript code/07_regression_test.R

# Step 7: Generate Report
python code/04_render_report.py

# Step 8: Validate Report
python code/05_validate_report.py
```

### 4. Review Results

- **Main Report**: `reports/chronotype_moral_analysis.html`
- **ANCOVA Results**: `data/derived/ancova_results.csv`
- **Effect Sizes**: `data/derived/effect_sizes.csv`
- **Reliability Metrics**: `data/derived/reliability_metrics.csv`

## Detailed Script Descriptions

### code/01_ingest.R
**Purpose**: Load and clean raw data.

**Actions**:
- Validates required columns
- Excludes rows with missing `acute_sleepiness`
- Logs exclusions to `logs/ingest_exclusions.log`

**Outputs**:
- `data/processed/cleaned_data.csv`
- `data/derived/ingest_exclusion_count.json`

**Expected Runtime**: < 1 minute

### code/02_classify.R
**Purpose**: Classify participants by chronotype.

**Classification Rules**:
- `MEQ >= 59`: "morning"
- `MEQ <= 41`: "evening"
- Otherwise: "intermediate"

**Actions**:
- Excludes rows with NA/non-numeric MEQ
- Excludes rows with out-of-range MFQ scores
- Logs exclusions to `logs/classify_exclusions.log`

**Outputs**:
- `data/derived/classified_data.csv`

**Expected Runtime**: < 1 minute

### code/02.5_aggregate_exclusions.R
**Purpose**: Verify data quality before proceeding.

**Actions**:
- Calculates cumulative exclusion rate
- ABORTS if rate > 20%
- Merges exclusion logs

**Outputs**:
- `data/derived/exclusions.log`
- `data/derived/exclusion_counts.json`

**Expected Runtime**: < 30 seconds

### code/02.6_reliability.R
**Purpose**: Assess internal consistency of MFQ subscales.

**Actions**:
- Calculates Cronbach's alpha for all 5 subscales

**Outputs**:
- `data/derived/reliability_metrics.csv`

**Expected Runtime**: < 1 minute

### code/03_analysis.R
**Purpose**: Perform controlled ANCOVA with multiplicity correction.

**Model Formula**:
```
MFQ_subscale ~ chronotype + PSQI + acute_sleepiness + age + sex
```

**Actions**:
- Runs ANCOVA for all 5 subscales
- Applies Bonferroni correction (α = 0.01)
- Calculates Cohen's d and 95% CI
- Checks VIF (ABORTS if VIF > 2)

**Outputs**:
- `data/derived/ancova_results.csv`
- `data/derived/effect_sizes.csv`

**Expected Runtime**: 2-5 minutes

### code/07_regression_test.R
**Purpose**: Verify analysis reproducibility.

**Actions**:
- Compares p-values against reference values
- Verifies tolerance ≤ 0.01

**Expected Runtime**: < 1 minute

### code/04_render_report.py
**Purpose**: Generate the final analysis report.

**Actions**:
- Renders R-Markdown template
- Includes all required sections:
 - Descriptive statistics
 - ANCOVA results
 - Effect sizes
 - Power analysis
 - Sensitivity sweep

**Outputs**:
- `reports/chronotype_moral_analysis.html`

**Expected Runtime**: 5-10 minutes

### code/05_validate_report.py
**Purpose**: Validate report completeness.

**Actions**:
- Checks for all required sections
- Verifies sensitivity table has ≥3 alpha thresholds

**Expected Runtime**: < 30 seconds

## Interpreting Results

### Chronotype Classification
- **Morning**: MEQ score ≥ 59
- **Evening**: MEQ score ≤ 41
- **Intermediate**: MEQ score 42-58

### ANCOVA Results
- **Significant**: p-value < 0.01 (Bonferroni-corrected)
- **Effect Size**: Cohen's d values:
 - 0.2: Small effect
 - 0.5: Medium effect
 - 0.8: Large effect

### Reliability Metrics
- **Cronbach's Alpha**:
 - > 0.9: Excellent
 - 0.8-0.9: Good
 - 0.7-0.8: Acceptable
 - < 0.7: Questionable

### Sensitivity Analysis
- Results shown for α thresholds: 0.01, 0.0125, 0.015
- Consistency across thresholds indicates robust findings

## Troubleshooting

### Pipeline Aborts with "Exclusion Rate > 20%"
**Cause**: Too many rows excluded during data cleaning.

**Solution**:
1. Check `logs/ingest_exclusions.log` and `logs/classify_exclusions.log`
2. Review data quality
3. Verify data collection procedures

### Pipeline Aborts with "VIF > 2"
**Cause**: Multicollinearity among predictors.

**Solution**:
1. Check `logs/vif_warnings.log` for details
2. Consider removing highly correlated predictors
3. Re-run analysis

### Report Validation Fails
**Cause**: Missing required sections in report.

**Solution**:
1. Check `code/04_report.Rmd` template
2. Verify all sections are included
3. Re-render report

### R Package Installation Errors
**Cause**: Missing or incompatible R packages.

**Solution**:
1. Re-run `code/00_setup_r_env.py`
2. Check R version (must be ≥ 4.3)
3. Manually install missing packages:
 ```r
 install.packages("tidyverse")
 install.packages("lme4")
 ```

## Running Individual Components

### Test Chronotype Classification
```bash
Rscript code/02_classify.R
```

### Run ANCOVA Only
```bash
Rscript code/03_analysis.R
```

### Generate Report Only
```bash
python code/04_render_report.py
```

## Validation and Testing

### Unit Tests
```bash
Rscript -e "testthat::test_dir('tests/')"
```

### Quickstart Validation
```bash
python code/06_validate_quickstart.py
```

### CI Compatibility Check
```bash
python code/07_verify_ci_compatibility.py
```

## Performance Considerations

### Memory Usage
- Maximum expected: ~7 GB RAM
- Monitor with: `top` or `htop`

### Runtime
- Full pipeline: 10-20 minutes
- Individual scripts: < 10 minutes each

### Parallel Execution
- Scripts marked [P] in tasks.md can run in parallel
- Example: Run T009 and T010 (tests) simultaneously

## Data Management

### Raw Data
- Location: `data/raw/`
- **Never modify** raw data files

### Processed Data
- Location: `data/processed/`
- Contains cleaned data after ingestion

### Derived Data
- Location: `data/derived/`
- Contains all analysis outputs

### Logs
- Location: `logs/`
- Contains exclusion records and error messages

## Best Practices

1. **Always validate data** before running the pipeline
2. **Check exclusion logs** to understand data quality issues
3. **Review VIF values** to ensure model assumptions are met
4. **Validate the final report** before publication
5. **Keep raw data separate** from processed data
6. **Document all changes** to the pipeline

## Support

For issues or questions:
1. Check `logs/` directory for error messages
2. Review this usage guide
3. Consult the project README
4. Contact the research team
