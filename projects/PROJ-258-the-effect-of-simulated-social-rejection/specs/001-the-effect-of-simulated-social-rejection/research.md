# Research: The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback

## Overview

This research plan details the strategy for a secondary analysis of behavioral data to test the hypothesis that simulated social rejection modulates responses to positive feedback. Given the constraints of the spec and the available verified datasets, this plan addresses the critical challenge of data availability and design adaptation.

**Core Methodological Correction**: The original assumption that ds000208 (Rejection) and ds003392 (Reward) can be merged to test "modulation" is **scientifically invalid**. These are distinct studies with independent participant pools. A Mixed ANOVA requires the *same* participants to be measured under both conditions. Therefore, the "Within-Subjects" path is **ONLY** valid if a **single dataset** is found containing both tasks for the same participants. If no such dataset exists, the study is re-scoped to a Between-Subjects comparison of group differences, and the "modulation" claim is dropped.

## Dataset Strategy

The analysis requires two distinct behavioral components:
1.  **Social Rejection**: Measured via the Cyberball paradigm.
2.  **Positive Feedback**: Measured via reaction times (RT) and mood ratings following positive reinforcement.

### Verified Sources & Feasibility

The spec assumes the availability of a composite dataset. However, the **# Verified datasets** block provided for this project does **not** contain verified URLs for OpenNeuro ds000208, ds003392, or specific Cyberball/Reward behavioral datasets that are single-cohort.

**Critical Constraint**: The spec explicitly states: "If a dataset the spec needs has NO verified source in the block, state that explicitly rather than fabricating one."

**Strategy**:
1.  **Single-Cohort Search**: The `ingest.py` script will search the verified list for a **single dataset** containing both `Condition` (Rejection/Control), `Reaction_Time`, and `Mood_Rating` for the same `Participant_ID`.
    *   *Note*: The verified `openneuro-fslr64k` appears to be imaging data (fSLR64k), not behavioral logs. The `P2SAMAPA` dataset is functional ANOVA results, not raw behavioral logs.
    *   *Action*: If no single-cohort dataset is found, the ingestion script will flag the design as "Data Unavailable for Modulation Hypothesis" and halt or switch to a "Between-Subjects" fallback (if separate datasets for group comparison are available).
2.  **Fallback / Simulation**: Since no verified behavioral dataset for a single-cohort Cyberball/Reward task exists in the provided list, the implementation plan includes a **Mock Data Generator** in `code/ingest.py` (guarded by a `--mock` flag for CI testing).
    *   **Constraint on Mock Data**: The mock generator is **explicitly configured to NOT simulate a Within-Subjects scenario** (no matching IDs across tasks) to reflect the reality of public datasets. It will only generate Between-Subjects data. This prevents the validation of code paths (Mixed ANOVA) that cannot run on real data.
    *   *Real Data Path*: If a real dataset is provided externally (not in the verified block), the ingestion script will validate it. If it fails validation (missing single-cohort structure), the run halts with exit code 1.

**Dataset Variable Fit Check**:
*   **Required**: `Participant_ID`, `Condition` (Rejection/Control), `Reaction_Time`, `Mood_Rating`.
*   **Verified List Check**:
    *   `openneuro-fslr64k`: Likely lacks behavioral RT/Mood. **Mismatch.**
    *   `P2SAMAPA`: Contains ANOVA results, not raw data. **Mismatch.**
    *   `Andyrasika/cat_kingdom`: Irrelevant.
    *   `bhismaperkasa/cerita_panas`: Irrelevant.
*   **Conclusion**: No verified dataset in the provided block satisfies the variable requirements for a Within-Subjects analysis. The plan proceeds with a **Mock Data Strategy** for CI validation (Between-Subjects only) and expects the user to provide a real dataset manually if available, or acknowledges that the specific "Cyberball + Reward" composite dataset is currently unavailable in the verified list.

## Methodological Rigor

### Statistical Approach

The analysis will adapt based on data availability:

1.  **Within-Subjects Design (Ideal - Requires Single-Cohort Dataset)**:
    *   *Condition*: A SINGLE dataset contains both Cyberball and Reward tasks for the same participants.
    *   *Test*: 2×2 Mixed ANOVA (Factors: Rejection [Yes/No] × Feedback [Positive/Negative]).
    *   *Correction*: Benjamini-Hochberg FDR applied to all p-values (FR-004).
    *   *Causal Claim*: None. Results are framed as "associational" (FR-003).

2.  **Between-Subjects Design (Fallback - Distinct Datasets or No Single-Cohort)**:
    *   *Condition*: Data comes from distinct studies or no single dataset contains both tasks.
    *   *Test*: One-Way ANOVA (Factor: Group [Rejection vs. Control]).
    *   *Limitation*: **Cannot test "modulation"**. The report will explicitly state: "This design cannot assess how rejection modulates reward processing within individuals; it only tests for group differences."
    *   *Claim*: Results are framed as "associational group differences".

### Rigor & Corrections

*   **Multiple Comparisons**: If multiple RT or Mood outcomes are tested, FDR correction is mandatory (FR-004).
*   **Power & Sample Size**:
    *   *Mandatory Calculation*: A post-hoc power calculation (or pre-hoc if N is known) is required for the interaction effect (Within-Subjects) or main effect (Between-Subjects).
    *   *Threshold*: If the matched N is < 30 (or power < 0.8), the system will flag a **"Severe Underpowering"** warning.
    *   *Reporting*: The report will explicitly state that the study is underpowered to detect the interaction effect if applicable.
*   **Causal Inference**: The report will explicitly state that this is an observational/secondary analysis of existing data. The word "causal" is banned from the Results section (FR-003). The Limitations section will contain the exact phrase "associational".
*   **Collinearity**: If predictors are derived (e.g., RT normalized by condition), the plan will report them descriptively and acknowledge the dependency.

### Sensitivity Analysis

*   **Scope**: Sweep significance threshold α over {0.01, 0.05, 0.1} (FR-006).
*   **Output**: A table reporting consistency of significance across these thresholds.
*   **Power Reporting**: The sensitivity report will also include the power estimate for each α level.

## Computational Feasibility

*   **Environment**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, 6h).
*   **Data Volume**: Target N ≤ 500. Raw files will be sampled if necessary to stay under 7 GB RAM.
*   **Libraries**: `pandas` (data manipulation), `scipy` (stats), `statsmodels` (ANOVA). All are CPU-tractable and have no GPU dependencies.
*   **No GPU**: No CUDA, no deep learning models.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Single-Cohort Requirement** | Merging distinct studies (ds000208 + ds003392) is scientifically invalid for Mixed ANOVA. The "modulation" hypothesis requires within-subject data. |
| **Mock Data Constraint** | Mock data is configured to ONLY generate Between-Subjects scenarios to prevent false validation of the Mixed ANOVA path. |
| **Power Analysis Mandatory** | To prevent reporting underpowered results as significant, a power calculation is required. |
| **Strict "Associational" Language** | Constitution Principle VI and FR-003 require explicit acknowledgment of the behavioral proxy nature and lack of causal inference. |
| **Inconclusive State** | If no valid single-cohort dataset is found, the research result is marked "Inconclusive" rather than generating a report from mock data. |

