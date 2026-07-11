# Research: The Effect of Sensory Deprivation on Dream Recall and Bizarreness (Simulation Study)

## 1. Research Question & Hypotheses

**Primary Question**: Does experimentally induced brief sensory deprivation immediately before sleep increase the likelihood of dream recall and the subjective bizarreness of recalled dream content compared to a control condition?

**Hypotheses**:
- **H1**: Sensory deprivation increases dream recall odds (OR > 1).
- **H2**: Sensory deprivation increases dream bizarreness scores (β > 0).
- **H3**: Effects are robust across varying definitions of "sensory deprivation" (threshold sweep).

## 2. Dataset Strategy

### 2.1 Verified Datasets

The following dataset was verified for potential real-world data ingestion. However, it **lacks explicit sensory deprivation metadata**, necessitating the synthetic data path.

| Dataset Name | URL | Status | Notes |
|--------------|-----|--------|-------|
| DreamBank (annotated) | https://huggingface.co/datasets/gustavecortal/DreamBank-annotated/resolve/main/train.csv | **Verified** | Contains dream reports and bizarreness scores, but **no experimental condition tags** for sensory deprivation. |
| DreamBank (parquet) | https://huggingface.co/datasets/DReAMy-lib/DreamBank-dreams/resolve/main/data/train-00000-of-00001-612108f52c64b64f.parquet | **Verified** | Same as above; no sensory deprivation metadata. |
| DreamBank (en) | https://huggingface.co/datasets/DReAMy-lib/DreamBank-dreams-en/resolve/main/data/train-00000-of-00001-24937aef854be1c9.parquet | **Verified** | English subset; no sensory deprivation metadata. |

**Decision**: Since no verified dataset contains the required `condition` (sensory deprivation vs. control) variable, the project will **default to synthetic data generation** as the primary mechanism. The real datasets will be used only for validating the *bizarreness score distribution* and *recall rates* in the synthetic generator to ensure ecological validity.

### 2.2 Synthetic Data Generation Strategy

The synthetic generator will create datasets with **N=200 participants (clusters)**, each contributing exactly **3 dream records** (repeated measures), resulting in 600 total observations. The generator reads parameters from `data/protocols/protocol.yaml`.

**Latent Variables (Stored in CSV)**:
- `deprivation_intensity`: Continuous (0.0-1.0), representing the degree of sensory deprivation.
- `latent_bizarreness`: Continuous, representing the underlying propensity for bizarre content.
- `participant_id`: Unique identifier.

**Derived Variables (Computed at Runtime)**:
- `condition`: Binary (0=Control, 1=Sensory Deprivation), derived by applying a threshold (e.g., >0.5) to `deprivation_intensity`.
- `recall`: Binary (0=No, 1=Yes), derived via logistic function of `condition` + noise.
- `bizarreness`: Ordinal (1-7), derived by discretizing `latent_bizarreness` using a **latent variable threshold model** (probit link) to ensure the ground truth is truly ordinal.

**Ground Truth Scenarios**:
- **Scenario A (Positive)**: High intensity correlates with high recall/bizarreness.
- **Scenario B (Null)**: No correlation.
- **Scenario C (Negative)**: Negative correlation.

**Validation Strategy (Non-Circular)**:
The generator introduces specific **noise and structural misspecification** to test the model's robustness, rather than simply recovering parameters:
1.  **ICC Misspecification**: The generator simulates data with a specific **true ICC** (e.g., 0.5) but the analysis model is configured to **assume** a different ICC (e.g., 0.2) or estimates it. The pipeline is validated on its ability to recover the *fixed effect* correctly despite this mismatch in the random effects structure.
2.  **Noise Injection**: Random noise is added to the latent variables such that the *observed* correlation is weaker than the *generated* ground truth, testing if the model can detect the signal amidst noise.
3.  **Coverage Probability**: The bootstrap validation (Section 3.2) will generate **50 independent synthetic datasets** (each with new seeds). The metric is whether the confidence interval contains the true parameter in approximately the nominal proportion of these datasets. This validates the method's reliability, not just the stability of a single dataset.

## 3. Statistical Methodology

### 3.1 Primary Models

1.  **Dream Recall (Binary)**:
    -   **Model**: Mixed-effects logistic regression.
    -   **Formula**: `recall ~ condition + (1 | participant_id)`
    -   **Estimator**: Maximum Likelihood (Laplace approximation) via `statsmodels`.
    -   **Output**: Odds Ratio (OR), 95% CI, p-value.

2.  **Dream Bizarreness (Ordinal/Continuous)**:
    -   **Model A (Primary)**: Linear Mixed-Effects (LME).
        -   **Formula**: `bizarreness ~ condition + (1 | participant_id)`
        -   **Assumption**: 1-7 Likert scale approximates interval data.
    -   **Model B (Robustness)**: Fixed-effects Ordinal Regression (`statsmodels.OrderedModel`).
        -   **Formula**: `bizarreness ~ condition`
        -   **Implementation**: `statsmodels` (OrderedModel).
        -   **Output**: Cumulative log-odds ratio, p-value.
        -   **Limitation**: This model does not account for clustering (random effects) due to the lack of CPU-tractable mixed-effects ordinal libraries in pure Python. It serves only as a check for the distributional shape assumption, not for the full mixed-effects structure. **This is a known limitation of FR-008 implementation.**

### 3.2 Robustness & Sensitivity Analysis

1.  **Threshold Sweep (Single-Distribution Sensitivity)**:
    -   The binary `condition` is derived from the continuous `deprivation_intensity` variable.
    -   **Mechanism**: The analysis script applies different thresholds (Strict: >0.8, Moderate: >0.5, Partial: >0.2) to the **same** raw data file.
    -   **Scientific Validity**: This tests the sensitivity of the *result* to the *arbitrary definition* (cut-off) of the predictor variable within a single population distribution. It does not test robustness across different populations, but rather the stability of the conclusion to the operational definition of "deprivation".

2.  **Bootstrap Validation (Coverage Probability)**:
    -   **Process**: The `sensitivity.py` script will generate **50 independent synthetic datasets** internally (each with new random seeds for noise and latent variables).
    -   **Thresholding**: For *each* of the 50 datasets, the binary `condition` is derived using the specific threshold being tested.
    -   **Resampling**: 1,000 bootstrap resamples are applied to *each* dataset.
 - **Metric**: **Coverage Probability**. Do the 95% CIs contain the true ground-truth parameter in [deferred] of the 50 datasets? This validates the statistical method's reliability.

### 3.3 Statistical Rigor & Limitations

-   **Multiple Comparisons**: Since only two primary hypotheses (recall, bizarreness) are tested, Bonferroni correction will be applied (α=0.025) to control family-wise error rate.
-   **Power Justification**: N=200 **participants** (clusters), with **3 records per participant** (600 total observations), is sufficient for detecting medium effects (d=0.5) with [deferred] power in mixed-effects models (α=0.05), assuming a moderate ICC (0.2). The effective sample size for the fixed effect is determined by the number of clusters (200), not the total observations.
-   **Causal Claims**: All results framed as **associational**. No randomization is confirmed in real data (synthetic only); causal language avoided.
-   **Collinearity**: No collinearity expected as `condition` is the sole fixed effect.
-   **Zero Counts**: Firth correction (penalized likelihood) will be applied if a condition has zero recall events.
-   **Ordinal Model Limitation**: The robustness check uses a fixed-effects ordinal model because `statsmodels` does not support mixed-effects ordinal regression. This limits the validity of the robustness check regarding clustering, but it remains the best available pure-Python approximation.

## 4. Compute Feasibility

-   **Environment**: GitHub Actions free-tier (multiple CPU cores, several GB RAM).
-   **Methods**: All models (`statsmodels`, `scikit-learn`) are CPU-tractable.
-   **Data Size**: N=200 participants * 3 records = 600 rows; negligible memory footprint.
-   **Runtime**: Estimated < 30 minutes for full pipeline (generation + modeling + bootstrap).
-   **No GPU**: No deep learning or GPU-accelerated methods used.
-   **Dependencies**: `rpy2` and `lme4` excluded to avoid R runtime complexity. Pure Python stack enforced.

## 5. Decision Log

| Decision | Rationale | Alternative Rejected |
|----------|-----------|----------------------|
| Synthetic Data Primary | No real dataset has required `condition` metadata. | Using real data without tags would require imputation, violating data hygiene. |
| Mixed-Effects Models | Accounts for within-subject correlation (repeated measures). | Fixed-effects models would inflate Type I error. |
| Dynamic Thresholding | Allows a single raw data file to support multiple threshold sweeps. | Storing fixed `condition` would require regeneration for every threshold. |
| Ordinal Robustness Check (Fixed-Effects) | `statsmodels` lacks mixed-effects ordinal support. | Using `rpy2`/`lme4` violates pure-Python/CPU constraints. |
| Bootstrap Coverage Probability | Validates the method's reliability across multiple datasets. | Single-dataset bootstrap only checks stability, not coverage. |
| Protocol as SSoT | Ensures simulation parameters are versioned and auditable. | Hardcoding parameters in scripts makes reproducibility difficult. |
| ICC Misspecification Test | Validates model robustness to structural mis-specification. | Perfect match only validates arithmetic. |
| Latent Threshold Model | Ensures ground truth is truly ordinal. | Continuous + discretization does not test ordinal model failure modes. |