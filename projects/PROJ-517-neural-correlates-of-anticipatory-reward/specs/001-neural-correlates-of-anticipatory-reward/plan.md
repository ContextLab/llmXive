# Implementation Plan: Neural Correlates of Anticipatory Reward Processing in Vocal Learning

**Branch**: `001-neural-correlates-anticipatory-reward` | **Date**: 2026-06-28 | **Spec**: `specs/001-neural-correlates-of-anticipatory-reward/spec.md`
**Input**: Feature specification from `/specs/001-neural-correlates-of-anticipatory-reward/spec.md`

## Summary

This project implements a statistical analysis pipeline to regress trial-by-trial neural firing rates in songbird Area X against known reward magnitudes. The primary objective is to determine if anticipatory neural activity (spikes in the pre-reward window) scales with expected reward magnitude. The technical approach involves ingesting pre-processed spike train data and metadata, calculating firing rates, fitting a Negative Binomial Generalized Linear Model (GLM) with permutation-based significance testing, and generating visualizations and summary reports. The pipeline is designed to run entirely on CPU-only CI runners using Python, `pandas`, `statsmodels`, and `scikit-learn`.

**Current Status**: **Pipeline Validation Only**. Due to the absence of a verified real-world songbird electrophysiology dataset in the provided source list, the current execution uses synthetic data to validate the code pipeline (FR-001 to FR-010). **No scientific conclusions regarding neural correlates are drawn from the synthetic run.** The 'Scientific Discovery' phase is blocked until a verified real dataset is ingested.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`
**Storage**: Local filesystem (CSV/Parquet for data, PNG for plots, YAML for schemas)
**Testing**: `pytest` (unit tests for ingestion, model fitting, and validation logic)
**Target Platform**: Linux (GitHub Actions free-tier runner: Multiple CPU, ~7 GB RAM)
**Project Type**: Computational Science / Data Analysis Pipeline
**Performance Goals**: Complete analysis (ingest, model, permute, plot) within 6 hours on CPU; handle dataset sizes up to manageable RAM usage limits.
**Constraints**: No GPU; no deep learning; strict adherence to pre-registered time windows (a baseline period preceding the event); must handle zero-reward trials and silent neurons.
**Scale/Scope**: Single dataset analysis; up to 100 neurons, ~5000 trials.
**Assumptions**:
- **Reward Level Distribution**: Assumes Multiple distinct reward magnitude levels, ensuring >30 trials per level given the A substantial number of trials is estimated to be required., satisfying the >30 trials/level constraint (FR-007).
- **Data Source**: For CI, uses synthetic data strictly adhering to `contracts/dataset.schema.yaml`. Real data ingestion requires a future dataset upload.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (NON-NEGOTIABLE)**:
    *   **Plan Action**: `requirements.txt` will pin exact versions. Random seeds (e.g., `np.random.seed(42)`) will be set at the start of the analysis script. Data fetching will use canonical URLs from the verified dataset list (or synthetic generator for CI).
    *   **Status**: Compliant.

2.  **Verified Accuracy**:
    *   **Plan Action**: For synthetic data, 'Verified Accuracy' applies to **Schema Compliance** (verified against `contracts/dataset.schema.yaml`) and **Reproducibility of the generator**. For real data, all citations will be cross-referenced against the "# Verified datasets" block. No external URLs will be invented.
    *   **Status**: Compliant.

3.  **Data Hygiene**:
    *   **Plan Action**: The ingestion script will verify checksums (if available) or file integrity. Raw data will be read-only; derived firing rates will be saved to new files. No PII is expected in public electrophysiology data.
    *   **Status**: Compliant.

4.  **Single Source of Truth**:
    *   **Plan Action**: The `summary_report.txt` will be generated directly from the `GLM` model object and permutation results, not manually typed.
    *   **Status**: Compliant.

5.  **Versioning Discipline**:
    *   **Plan Action**: The `state` file will be updated by the runtime agent upon artifact completion. Content hashes will be generated for input data and output schemas.
    *   **Status**: Compliant.

6.  **Electrophysiological Signal Integrity**:
    *   **Plan Action**: The code will explicitly define the -500ms to 0ms window relative to reward. Spike counts will be traceable to `trial_id` and `neuron_id`. **Crucially**, the plan requires documentation of the *upstream* spike sorting validation criteria (e.g., SNR > 3, Isolation Distance > 20) that the provided data must have met. If the input data lacks these metadata fields, the pipeline will flag the data as 'unvalidated' or halt.
    *   **Status**: Compliant.

7.  **Statistical Rigor for Neural Analysis**:
    *   **Plan Action**: The plan mandates a permutation test (A sufficient number of iterations will be performed to ensure convergence and statistical stability.) for significance (FR-004, SC-001). Bonferroni correction will be applied if multiple neurons are tested (SC-005). Over-dispersion checks (FR-010) will be performed. A robustness check for non-linearity (categorical vs continuous reward) will be included.
    *   **Status**: Compliant.

## Project Structure

### Documentation (this feature)

```text
specs/001-neural-correlates-of-anticipatory-reward/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 0 output (Defined before implementation)
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-517-neural-correlates-of-anticipatory-reward/
├── data/
│   ├── raw/             # Downloaded raw data (read-only)
│   └── processed/       # Derived firing rates, aligned DataFrames
├── code/
│   ├── __init__.py
│   ├── ingestion.py     # FR-001, FR-002, FR-007, FR-009, Reward Independence Check
│   ├── modeling.py      # FR-003, FR-004, FR-008, FR-010, Power Analysis, Non-linearity Check
│   ├── visualization.py # FR-005
│   ├── reporting.py     # FR-006, Bias Analysis
│   └── main.py          # Orchestration script
├── tests/
│   ├── test_ingestion.py
│   ├── test_modeling.py
│   └── test_visualization.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected. The analysis is a linear pipeline (Ingest -> Process -> Model -> Visualize) best suited for a modular script-based approach rather than a web service or mobile app. This minimizes overhead and fits the CPU-only constraint.

## Implementation Phases

### Phase 1: Data Ingestion & Validation (FR-001, FR-002, FR-007, FR-009)
1.  **Load Data**: Load raw spike timestamps and trial metadata from `data/raw/` or generate synthetic data if `--synthetic` flag is set.
2.  **Validate Schema**: Ensure input strictly matches `contracts/dataset.schema.yaml`.
3.  **Validate Spike Sorting**: Check for upstream spike sorting metadata (e.g., SNR, Isolation Distance). If missing, flag as 'unvalidated' or halt if strict mode is on.
4.  **Calculate Firing Rates**: Count spikes in the [-500ms, 0ms] window relative to reward.
5.  **Validation Checks**:
    *   **Trial Count**: Verify >= 30 trials per reward magnitude level (FR-007). If not, halt and report specific levels.
    *   **Temporal Validity**: Flag trials where cue-reward delay < 500ms (FR-009).
    *   **Data Loss Metric**: Calculate and report `ingestion_rows_total`, `ingestion_rows_valid`, `ingestion_rows_dropped` (SC-004).
    *   **Reward Independence Check**: Validate if `reward_magnitude` is exogenous (fixed) or endogenous (behavior-dependent). If endogenous, flag the analysis as 'correlational of behavioral loop' rather than pure anticipation.

### Phase 2: Statistical Modeling & Robustness (FR-003, FR-004, FR-008, FR-010)
1.  **Dispersion Check**: Calculate dispersion parameter (FR-010). Select Negative Binomial (if > 1.1) or Poisson (if < 1.1).
2.  **Power Analysis (MDES)**: Calculate Minimum Detectable Effect Size (MDES) given current sample size and variance (SC-002). Report `mdes_80_power`. If MDES is too large, flag as 'underpowered'.
3.  **Model Fitting (Primary)**: Fit GLM with `reward_magnitude` as continuous predictor.
4.  **Robustness Check (Non-linearity)**: Fit a secondary model treating `reward_magnitude` as a categorical factor. Compare AIC or perform Likelihood Ratio Test (LRT). If categorical model is significantly better, flag the linear scaling claim as potentially non-linear.
5.  **Model Stability (CV)**: Perform k-fold cross-validation (FR-008) to calculate `cv_score_mean` and `cv_score_std`. **Note**: CV is used here strictly as a diagnostic for coefficient stability and overfitting, not as a measure of predictive performance for the biological hypothesis.
6.  **Significance Testing**: Run a permutation test with a sufficient number of iterations to ensure robust statistical inference. (FR-004) to generate null distribution and p-value.
7.  **Multiple Comparisons**: Apply Bonferroni correction if multiple neurons (SC-005).

### Phase 3: Visualization & Reporting (FR-005, FR-006)
1.  **Generate Plot**: Scatter plot of firing rate vs. reward magnitude with regression line and 95% CI (FR-005).
2.  **Selection Bias Impact Analysis**: Compare reward distribution of included vs. excluded trials (due to FR-009). If excluded trials have systematically different rewards, flag the slope estimate as potentially biased.
3.  **Generate Report**: Summary text file containing coefficient, p-value, MDES, CV scores, data loss metrics, and bias flags (FR-006).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Non-linearity Check | To ensure the "scaling" claim is valid for non-linear relationships. | A simple linear GLM would be biased if the true relationship is saturating. |
| MDES Calculation | To satisfy SC-002 and avoid Type II errors. | Post-hoc power analysis is insufficient; a priori calculation is required to justify sample size. |
| 5-fold CV | To satisfy FR-008 and diagnose overfitting/coefficient stability. | Permutation tests alone do not assess model stability across data splits. |
| Reward Independence Check | To address the confound of endogenous reward generation. | Treating reward as exogenous when it is endogenous leads to circular causal claims. |
| Selection Bias Analysis | To address the bias introduced by excluding short-delay trials. | Excluding trials based on timing may systematically remove specific reward magnitudes, biasing the slope. |