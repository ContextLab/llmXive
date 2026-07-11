# Research: The Impact of Ambient Noise on Cognitive Flexibility in Remote Workers

## Executive Summary

This research plan outlines the methodology for testing the non-linear relationship between ambient noise and cognitive flexibility. The study uses a **Within-Subject Randomized Design** to control for confounds: participants complete the task-switching battery under multiple, randomized noise conditions (Low, Moderate, High) across different sessions. This design allows for within-subject comparison, controlling for time-invariant individual differences (e.g., baseline cognitive ability, motivation). The analysis uses linear mixed-effects modeling (LMM) for hypothesis testing. All methods are CPU-tractable and fit within GitHub Actions free-tier constraints.

**Critical Distinction**: Synthetic data is used to verify that the code runs and handles data correctly. It **cannot** validate the scientific hypothesis (the "coffee shop effect") because synthetic noise lacks the complex spectral properties of real environments. The scientific conclusion will be drawn **only** from the final real-world dataset collected via the within-subject randomized design.

## Dataset Strategy

### Verified Datasets

| Dataset Name | Description | Verified URL | Usage |
|--------------|-------------|--------------|-------|
| CFI (jsonl) | High-quality Cognitive Flexibility Index data (simulated task-switching metrics) | https://huggingface.co/datasets/jumplander/J6-CFI-HQ-20K/resolve/main/j6_cfi_hq_20k.jsonl | Primary source for task performance metrics (reaction times, error counts) **for pipeline validation**. |

> **Note**: No verified dataset currently contains *both* real-time decibel logs and task-switching metrics for remote workers. The plan relies on:
> 1.  **Pipeline Validation**: Synthetic acoustic logs merged with CFI data (from J6-CFI-HQ-20K) to test ingestion and model fitting logic.
> 2.  **Hypothesis Testing**: Real data collected via the custom app (User Story 1) using a **within-subject randomized design** will be merged with real task logs.
>
> **Dataset Verification Step**: Before using the J6-CFI-HQ-20K dataset, the pipeline will programmatically verify that it contains the required columns (`trial_type`, `reaction_time_ms`, `error_flag`) AND the specific `switch`/`repeat` trial structure.
> *   **If the structure matches**: Use for pipeline validation.
> *   **If the structure does NOT match** (e.g., only aggregate scores): The pipeline will fail with a clear error. **Fallback**: Use synthetic data ONLY for ingestion logic validation. The hypothesis test will be deferred until real data is collected. Synthetic data will **not** be used to test the hypothesis.

### Dataset-Variable Fit

| Required Variable | Source | Fit Status | Notes |
|-------------------|--------|------------|-------|
| Decibel levels (dB) | Real Data (Future) / Synthetic (Dev) | **Real: Pending / Sim: Synthetic** | Real data requires custom logging app; synthetic data mimics distribution (Low/Moderate/High) for code testing only. |
| Reaction times (ms) | CFI (jsonl) | **Verified** | Directly mapped from `J6-CFI-HQ-20K` (after schema check). |
| Error counts | CFI (jsonl) | **Verified** | Directly mapped from `J6-CFI-HQ-20K` (after schema check). |
| Participant ID | Synthetic | **Simulated** | Unique identifiers for mixed-effects model. |
| Noise sensitivity | Synthetic | **Simulated** | Covariate for robustness check (US-3). |
| Demographics | Synthetic | **Simulated** | Covariates (age, job type) for model control. |
| Session ID | Synthetic | **Simulated** | Required for within-subject design (multiple sessions per participant). |

> **Critical Gap**: No verified dataset contains *both* objective acoustic logs and task-switching metrics. The plan relies on synthetic acoustic data for development and assumes real-world data collection via a custom app (as per User Story 1) using a within-subject design. The analysis pipeline is designed to handle real data once collected.

## Statistical Methodology

### Primary Analysis: Linear Mixed-Effects Model (LMM)

**Design**: Within-Subject Randomized Design. Each participant completes the task under Low, Moderate, and High noise conditions in randomized order across sessions.

**Model Formula**:
```
CFI ~ noise_level + I(noise_level^2) + noise_variability + (1 | participant_id)
```

- **Dependent Variable**: Cognitive Flexibility Index (CFI). **Note**: CFI is computed only after a correlation check between z-scored RT difference and error counts. If correlation > 0.7, RT difference alone is used to avoid redundancy.
- **Fixed Effects**:
  - `noise_level`: Continuous decibel level (mean per session).
  - `I(noise_level^2)`: Quadratic term to test for non-linearity (inverted-U).
  - `noise_variability`: Standard deviation of noise within the session.
- **Random Effects**: Random intercept for `participant_id` to account for repeated measures (within-subject design).

**Hypothesis Tests**:
1.  **Non-linearity**: Likelihood-ratio test (LRT) comparing the quadratic model vs. linear-only model.
2.  **Post-hoc**: Tukey HSD adjusted p-values for pairwise comparisons between Low, Moderate, High noise categories.
3.  **FWER Check (SC-004)**: Explicitly calculate the observed family-wise error rate from the Tukey results and report it against nominal alpha (0.05).

### Predictor Collinearity & Structural Dependency
- **Issue**: `noise_level` (mean) and `noise_variability` (SD) are often structurally correlated in time-series data (higher mean often implies higher variance).
- **Mitigation**:
  1.  Compute VIF. If VIF > 5, report warning.
  2.  **Residualized Variability Approach**: If structural dependency is confirmed (variability is a function of mean), regress `noise_variability` against `noise_level` and use the residuals as the predictor in the model. This isolates the unique variance of variability not explained by the mean.
  3.  **Alternative**: If residualization is not feasible, the model will be re-run with only `noise_level` and `I(noise_level^2)` to isolate the non-linear effect without the confounding variability term.
  4.  The interpretation of the LRT for the quadratic term will explicitly note if this structural dependency was addressed and how it affects the inference.

### Robustness & Sensitivity Analysis

1.  **Threshold Sweeps**: Re-run model with noise categories defined as:
    - Set A: Low <40, Moderate 40-50, High >50
    - Set B (Baseline): Low <45, Moderate 45-65, High >65
    - Set C: Low <50, Moderate 50-70, High >70
2.  **Exclusion Checks**: Re-fit model excluding participants with extreme noise sensitivity (top [deferred] of self-reported scores).
3.  **Collinearity Diagnostic**: Compute Variance Inflation Factor (VIF) for `noise_level` and `noise_variability`; if VIF > 5, report collinearity and interpret cautiously.

### Power Analysis & Sample Size

- **Target N**: 150 participants (justified by FR-008).
- **Effect Size Assumption**: Literature suggests a small-to-medium effect size for environmental noise on cognition (Cohen's d in the small-to-medium range for linear effects). However, detecting a **quadratic** effect in a mixed-effects model typically requires larger sample sizes or more repeated measures.
- **Calculation**: Based on a conservative linear effect size (d=0.3), 150 participants with 3 repeated measures each (Low, Mod, High) provides [deferred] power to detect a linear trend. Power to detect the quadratic term specifically is lower and may be underpowered.
- **Fallback**: If the real data yields insufficient power to detect a quadratic term (e.g., wide confidence intervals), the analysis will be re-framed to focus on linear trends or descriptive statistics. A post-hoc power analysis will be conducted to quantify this limitation. The study will explicitly report the power limitations for the quadratic hypothesis.

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| Use synthetic acoustic data (Dev only) | No verified dataset contains real-time decibel logs + task metrics; synthetic data enables pipeline validation (ingestion, schema, code logic) but **not** scientific hypothesis validation. |
| Within-Subject Randomized Design | Controls for time-invariant confounds (motivation, baseline ability) by comparing the same participant across different noise conditions, strengthening causal inference compared to purely observational designs. |
| LMM with quadratic term | Directly tests the non-linear "inverted-U" hypothesis (Constitution Principle VII). |
| Residualized Variability | Addresses the structural dependency between mean and SD of noise, ensuring the quadratic term is not confounded by variability. |
| Tukey HSD correction | Controls family-wise error rate for multiple pairwise comparisons (FR-006). |
| CPU-only methods | Ensures feasibility on GitHub Actions free tier (no GPU, <7GB RAM). |
| Threshold sweeps | Addresses US-3 robustness requirement; prevents data dredging claims. |
| Associational Framing (if observational) | If real data collection fails to achieve randomization, findings will be framed as associational. However, the primary design is randomized within-subject. |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Model convergence failure | Fallback to simpler linear model; report diagnostic stats. |
| Insufficient valid logs (<80%) | Exclude participant (US-1); re-calculate power. |
| High collinearity (VIF > 5) | Apply Residualized Variability approach; interpret effects descriptively; do not claim independence. |
| Synthetic data not representative | Validate synthetic distribution against literature; update generator parameters. **Note**: Synthetic data does not validate the scientific hypothesis. |
| CFI Redundancy | Check correlation between RT and Error; use RT only if high correlation. |
| Power limitations for quadratic term | Explicitly report confidence intervals; re-frame analysis if power is insufficient. |
| Dataset structure mismatch | If J6-CFI-HQ-20K lacks required columns, pipeline fails with clear error; fallback to synthetic data for code validation only. |