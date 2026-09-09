# Research: Pipeline Validation for Gut Microbiome & Cognitive Function Analysis

## Problem Statement

This study validates the **analysis pipeline** for investigating the association between gut microbiome composition (ILR-transformed 16S rRNA data) and cognitive function (reaction time, numeric memory, reasoning) in aging populations. 

**Critical Distinction**: The original research question ("Investigating the Correlation...") requires real human data. However, the available data source (UK Biobank) is access-gated and cannot be downloaded on the CI runner. **No open-access proxy dataset exists.** Therefore, this phase uses a **deterministic synthetic data generator** to validate the *statistical methodology* (ILR, regression, BH correction) and *code logic*. The biological hypothesis (that specific taxa correlate with cognition) **cannot be tested** in this phase and is deferred to a future phase requiring real data access.

## Dataset Strategy

### Feasibility Assessment

**Critical Constraint**: The UK Biobank (UKB) is an **access-gated** resource. It requires registration, ethical approval, and a data access agreement. **It cannot be downloaded automatically by the GitHub Actions free-tier runner.**

**Resolution**:
1.  **No Verified Open UKB Microbiome Dataset**: The provided "Verified datasets" block contains `IL_Replay` and `il-reasoning-responses` datasets, which are **not** microbiome data. These are irrelevant to the biological question.
2.  **No Open Proxy**: A search for open-access datasets with matched 16S microbiome + cognitive + confounder data (age, sex, BMI, diet, activity, meds) yielded **no results**.
3.  **Synthetic Data Strategy**: To satisfy the "CPU-first, real data" constraint and the "Reproducibility" principle, the implementation will use a **deterministic synthetic data generator** (`code/pipelines/download.py`). This generator will create a dataset that **strictly mimics the UKB schema** (Field IDs 20400, 20002, antibiotic use, etc.) with realistic distributions.
4.  **Rationale**:
    *   **Reproducibility**: Every CI run generates the same data from the same seed.
    *   **Feasibility**: The synthetic data fits within the disk limit and can be streamed.
    *   **Validity**: The pipeline logic (ILR, regression, BH correction) is tested against known distributions.
    *   **Transparency**: The `data-model.md` explicitly documents the synthetic nature and the schema mapping.

**Scientific Validity Disclaimer**: A synthetic dataset with pre-defined correlations cannot validate the *scientific* hypothesis (microbiome-cognition link) or the *methodological* robustness against real-world confounding, as the confounding structure is also synthetic and defined by the researcher. The 'validation' of the method against synthetic data only proves the code runs, not that the statistical approach is valid for the biological question. This limitation is explicitly acknowledged.

### Data Schema (Synthetic Proxy)

| Variable | Source (UKB Field) | Synthetic Generation Method |
| :--- | :--- | :--- |
| `participant_id` | - | UUID or sequential integer (deterministic seed) |
| `age` | 21022 | Normal distribution (mean=65, sd=8), truncated [40, 85] |
| `sex` | 31 | Binary (0/1) with [deferred] split |
| `bmi` | 21001 | Normal (mean=27, sd=5), truncated [15, 45] |
| `diet_quality` | 1338 | Score 0-100, beta distribution |
| `physical_activity` | 900 | Continuous (MET-min/week), log-normal |
| `medication_use` | 6153 | Binary (0/1) based on age/sex correlation |
| `antibiotic_use` | 20002 (subset) | Binary (0/1), correlated with age |
| `microbiome_counts` | 20400 | Dirichlet-Multinomial distribution (simulating 16S counts) |
| `reaction_time` | 20002 (subset) | Normal (mean=600ms, sd=150), correlated with age |
| `numeric_memory` | 20002 (subset) | Integer 0-100, correlated with age/education |
| `reasoning` | 20002 (subset) | Integer 0-100, correlated with age/education |
| `validation_reference` | - | Cites UK Biobank validation papers for cognitive instruments (FR-009) |

*Note: The "Verified datasets" block URLs are **not used** as they do not contain the required variables. The synthetic generator is the only feasible path for CI execution.*

## Methodological Rigor

### Compositional Data Analysis (ILR)

Microbiome data is compositional (sums to 1). Standard regression on raw proportions is invalid due to the "sum-to-zero" constraint (spurious correlations).
*   **Method**: Isometric Log-Ratio (ILR) transformation.
*   **Justification**: ILR maps the simplex to Euclidean space, producing orthonormal coordinates that break the dependency between taxa. This allows the use of standard linear models without multicollinearity artifacts.
*   **Reference**: Gloor et al. (2017) "Microbiome datasets are compositional: and this is not optional." (To be verified by Reference-Validator Agent).

### Statistical Modeling

1.  **Primary Model**: Multivariate Linear Regression (OLS).
    *   **Outcome**: Cognitive Score (Reaction Time, Memory, Reasoning).
    *   **Predictor**: ILR-transformed taxon coordinates.
    *   **Covariates**: Age, Sex, BMI, Diet Quality, Physical Activity, Medication Use.
    *   **Equation**: $Y = \beta_0 + \beta_1(ILR_{taxon}) + \sum \gamma_i(Covariate_i) + \epsilon$

2.  **Multiple Testing Correction**: Benjamini-Hochberg (BH).
    *   **Justification**: Controls False Discovery Rate (FDR) across thousands of taxon-cognitive tests.
    *   **Threshold**: $\alpha = 0.05$.

3.  **Robustness Checks**:
    *   **Lasso/Ridge**: To handle potential multicollinearity among taxa.
    *   **Reduced Models**: Excluding diet/medication to check for over-control bias (FR-010).

### Causal Claims

*   **Status**: **Associational only**.
*   **Justification**: Observational study with no randomization. The plan explicitly sets `causality_claim: false` in all outputs (FR-008).
*   **Assumptions**: Confounders are measured without error; no unmeasured confounding.

## Statistical Power & Sample Size

*   **Limitation**: The study relies on a synthetic dataset. The power analysis will be performed on a **synthetic dataset with a known effect size ($\beta = 0.1$)**.
*   **Method**: Simulation-based power analysis.
    1.  Generate data with known $\beta$.
    2.  Run the full pipeline.
    3.  Measure the proportion of times the null hypothesis is rejected (Power).
*   **Goal**: Confirm the pipeline detects $\beta=0.1$ with >80% power given the simulated cohort size.
*   **Critical Distinction**: This is a **Code Correctness Test**, not a true statistical power analysis. A valid power analysis for an observational study requires estimating effect sizes from prior literature or pilot data, not generating them. The synthetic generator's injected effects are for *testing code logic*, not for *validating statistical power* against real-world noise. The true power analysis is **deferred** to the real-data phase.

## Confounding Limitations

The synthetic data generation includes confounders (age, sex, BMI, etc.) with linear relationships to the outcome. However, real-world confounding in the UK Biobank may involve complex non-linear interactions and unmeasured confounders. The "control" in the synthetic case is trivial because the relationships are defined by the generator. This limitation is acknowledged, and the reduced model analysis (FR-010) is included to validate the *code's* ability to compare models, even if the *bias* estimation is synthetic.

## Decision Rationale: CPU vs. GPU

*   **Choice**: **CPU-First**.
*   **Rationale**: The analysis uses classical statistics (OLS, Lasso) and ILR transformation. These are computationally efficient and scale linearly with sample size. No deep learning or large-model training is required.
*   **GPU Escape Hatch**: Not needed. The entire pipeline fits within the limited CPU and memory constraints of the GitHub Actions runner.

## Addressing Spec Constraints

*   **FR-001 to FR-010**: All functional requirements are addressed in the pipeline design. FR-001 and FR-009 are implemented with synthetic data and deferred for real data.
*   **SC-001 to SC-006**: Success criteria are measured via the code correctness tests on synthetic data. Real-world measurements are deferred.
*   **Dataset Mismatch**: The plan explicitly acknowledges the lack of open UKB data and uses a **deterministic synthetic generator** as the only feasible, reproducible alternative for CI.