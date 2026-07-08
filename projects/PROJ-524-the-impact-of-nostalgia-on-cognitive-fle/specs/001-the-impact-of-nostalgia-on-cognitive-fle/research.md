# Research: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

## Overview

This document outlines the research strategy for investigating whether exposure to nostalgic stimuli is associatively linked to improved cognitive flexibility in adults aged 65+, as measured by Wisconsin Card Sorting Test (WCST) performance metrics. Given the observational nature of available datasets, all findings will be framed as associational, not causal.

**Critical Design Clarification**: The study is **between-subjects** (participants are exposed to either nostalgia or control stimuli, not both). Therefore, the primary statistical test is **Welch's independent samples t-test**, not a paired t-test. The spec's mention of "paired t-tests" (FR-002) and "pre/post measures" (US-2) is identified as a contradiction to the observational design and is addressed by using the statistically valid independent test.

## Dataset Strategy

### Real Data Acquisition Strategy
We will attempt to source real data from the following repositories, prioritizing those with verified WCST and demographic data:
- **OpenNeuro**: Search for datasets containing "WCST" and "aging" or "elderly".
- **ICPSR**: Query for studies on "cognitive flexibility" and "nostalgia" or "emotional regulation" in older adults.
- **UK Biobank**: Check for available cognitive task data and self-reported emotional states (if nostalgia proxies exist).
- **HuggingFace Datasets**: Search for "WCST" or "executive function" datasets.

### Gap Analysis & Fallback
**Current Status**: No verified public dataset exists that combines **WCST metrics** + **Age ≥ 65** + **Nostalgia/Control labels** in a single schema.
**Fallback Plan (Methodological Simulation)**:
If no real dataset is found, the project will proceed with a **Methodological Simulation** using synthetic data generated to match the required schema.
- **Purpose**: To validate the **pipeline code** (ingestion, cleaning, statistical logic, reporting).
- **Limitation**: Synthetic data **cannot** validate the empirical hypothesis (the actual impact of nostalgia). Results from this path will be explicitly labeled as "Simulation Results" and will not claim empirical validity.
- **Distinction**: The final report will clearly separate "Pipeline Validation Results" (from synthetic data) from "Empirical Results" (from real data, if found).

### Dataset Table

| Dataset | Source URL | Variables Needed | Validation Status | Notes |
|---------|------------|------------------|-------------------|-------|
| WCST Performance Data | NO verified source found | `participant_id`, `age`, `stimulus_type`, `perseverative_errors`, `categories_completed` | ⚠️ Requires manual curation or synthetic generation | No verified public dataset exists. Will use synthetic data for pipeline validation. |
| Nostalgia Induction Stimuli | NO verified source found | `stimulus_id`, `type` (nostalgia/control), `source_url`, `checksum` | ⚠️ Requires manual curation | Stimuli must be validated for emotional elicitation; checksums required for fidelity. |
| MMSE Scores (for exclusion) | NO verified source found | `participant_id`, `mmse_score` | ⚠️ May not be available | If unavailable, sensitivity analysis will proceed without exclusion flag (see Fallback Logic). |

> **Critical Note**: The spec assumes availability of WCST data with age ≥ 65 and nostalgia/control labels. No verified public dataset currently exists for this specific combination. The implementation will either:
> 1. Use a synthetic dataset generated to match the schema (for testing pipeline integrity), OR
> 2. Await contribution of a real dataset from collaborators.
>
> If a real dataset is used, it MUST be verified for:
> - Presence of `age` field (≥ 65 filtering)
> - Presence of `stimulus_type` (nostalgia vs. control)
> - Presence of WCST metrics (`perseverative_errors`, `categories_completed`)
> - Absence of PII

## Statistical Methodology

### Primary Analysis
- **Design**: Between-subjects (observational exposure).
- **Test**: **Welch's independent samples t-test** comparing `perseverative_errors` and `categories_completed` between nostalgia and control conditions. (Paired t-test is invalid for independent groups).
- **Correction**: Bonferroni correction applied for two primary outcomes (errors, categories).
- **Effect Size**: Cohen's d with 95% CI calculated for each comparison.
- **Power/MDES**: **Minimum Detectable Effect Size (MDES)** calculated based on the observed sample size and variance, framed as a study limitation. *Post-hoc power analysis is excluded due to statistical controversy.*
- **Confounding Control**:
  - If covariates (age, education, baseline cognitive score, depression scores) are available, a **linear regression** or **ANCOVA** will be used to adjust for them.
  - If covariates are missing, the analysis will be unadjusted, and the report will flag the result as "Unadjusted - High Confounding Risk".

### Sensitivity Analysis
- **Threshold Sweep**: Re-run primary tests at α = {0.01, 0.05, 0.1} and report significance status changes.
- **Robustness Check**: Exclude participants with MMSE < 24 (if data available) and compare effect sizes to full cohort.
  - **Fallback**: If MMSE is missing, proceed with full cohort and log "ERR_MMSE_MISSING".
- **Flagging**: Results with p ≈ 0.05 (e.g., 0.04–0.06) flagged as "sensitive to threshold choice".

### Assumptions & Limitations
- **Observational Design**: No random assignment; findings are associational only.
- **Collinearity**: If predictors are definitionally related (e.g., errors and categories), independent effects will not be claimed; descriptive reporting only.
- **Sample Size**: Power may be limited if N < 50; this will be explicitly reported via MDES.
- **Measurement Validity**: WCST metrics assumed valid proxies for cognitive flexibility per established literature (citations required).
- **Data Availability**: If no real dataset is found, results are limited to pipeline validation (simulation).

## Compute Feasibility

- **Environment**: GitHub Actions free-tier (2 CPU, 7GB RAM, 14GB disk, no GPU).
- **Libraries**: `pandas`, `scipy`, `statsmodels`, `numpy` — all CPU-tractable.
- **Runtime**: Expected < 1 hour for typical dataset sizes (< 100k rows).
- **Memory**: Peak usage < 2GB for data processing and statistical modeling.

## Citations & Validation

All citations in the final report will be validated against primary sources. Title overlap ≥ 0.7 enforced by the `reference_validator` script. No fabricated URLs or datasets.

**Validation Citation Check**:
- If a real dataset is used, the system will parse its metadata for a 'citation' field.
- If no citation exists, the report will flag "Stimulus Validity: Unverified" and exclude SC-006 from the final success metrics for that run.