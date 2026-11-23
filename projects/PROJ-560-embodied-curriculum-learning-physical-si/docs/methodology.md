# Methodology: Data Processing and Statistical Inference

## Overview

This document details the data processing pipeline, statistical methods, and the
specific framing of results for the Embodied Curriculum Learning project. All
analyses are performed on CPU-only infrastructure with deterministic seed management
to ensure reproducibility.

## Data Processing Pipeline

### Input Sources
The system accepts two primary modes of operation:
1. **Secondary Analysis Mode**: Loads public datasets (CSV/JSON) containing pre-test
 and post-test scores.
2. **Synthetic Mode**: Generates deterministic synthetic datasets for validation
 when public data lacks required fields (specifically `instruction_type`).

### Automatic Fallback (FR-008)
If a public dataset is loaded but lacks the `instruction_type` column, the system
automatically invokes the `SyntheticDataGenerator` to produce a validated dataset
with ground-truth labels. This process is deterministic and requires no manual
intervention.

### Gain Score Calculation
For each record, the learning gain is calculated as:
`gain = post_test_score - pre_test_score`

Records with missing values in either `pre_test_score` or `post_test_score` are
excluded from analysis. These skipped records are logged to
`data/derivation_logs/skipped_records.log` for auditability.

### Synthetic Data Generation
When synthetic data is generated, a `mapping_log.json` is produced in
`data/synthetic/`. This log documents the causal chain:
`Physics_Action` -> `Virtual_Object_State` -> `Abstract_Principle_Inference`,
satisfying Constitution Principle VI.

## Statistical Methods

### Hypothesis Testing
The system performs independent samples t-tests to compare mean gain scores between
instruction groups (e.g., Embodied vs. Static).

**Test Selection**:
- **Levene's Test** is first applied to check for homogeneity of variances.
- If variances are equal, **Student's t-test** is used.
- If variances are unequal, **Welch's t-test** is used to ensure robustness.

### Effect Size and Confidence Intervals
- **Cohen's d** is calculated to quantify the magnitude of the difference between groups.
- **95% Confidence Intervals** are computed for the effect size.

### Multiple Comparison Correction
To control the family-wise error rate when testing multiple concepts, the **Bonferroni
correction** is applied. The significance threshold (alpha) is adjusted by dividing
it by the number of comparisons.

### Power Analysis
Achieved power is calculated for each test. Results with power < 0.80 are flagged
as "underpowered" in the output report.

### Collinearity Diagnostics
The system checks for collinearity between predictors. If the absolute correlation
coefficient |r| > 0.8, a diagnostic warning is issued.

## Sensitivity Analysis

A sensitivity sweep is performed to test the robustness of the headline effect size
across different inclusion thresholds (small, moderate, large significance levels).
If the sample size (N) is less than 30, the sweep is skipped, and a flag
`robustness_warning: true` is set, indicating "insufficient data for robustness check".

## Framing of Results: Associational Nature

### Critical Methodological Caveat (FR-003)
**All statistical findings produced by this system are explicitly framed as "associational".**

The analysis identifies statistical associations between the type of instruction
and learning gains. It does **not** establish causal relationships. The system
deliberately avoids terms such as "causes," "teaching effect," or "training impact"
in its automated output.

Findings should be interpreted as:
> "There is an association between [Instruction Type] and [Learning Gain]..."

rather than:
> "[Instruction Type] causes an increase in [Learning Gain]..."

This framing adheres to the project's methodological constraints and prevents
over-interpretation of observational or quasi-experimental data.

## Reproducibility

All random number generation (numpy, python random) is seeded using a deterministic
seed management system (`code/src/utils.py`). Running the pipeline with the same
`--seed` argument will produce identical results.
