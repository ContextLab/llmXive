# Implementation Plan: Investigating the Predictive Power of Brain Network Metrics for Schizophrenia Diagnosis

**Branch**: `001-gene-regulation` | **Date**: 2026-07-08 | **Spec**: `specs/001-investigating-the-predictive-power-of-br/spec.md`
**Input**: Feature specification from `/specs/001-investigating-the-predictive-power-of-br/spec.md`

## Summary

This project implements a computational pipeline to determine if graph theory metrics derived from resting-state fMRI (rs-fMRI) can differentiate between individuals diagnosed with schizophrenia and healthy controls. The technical approach involves downloading rs-fMRI data from OpenNeuro, preprocessing it (motion correction, normalization, bandpass filtering), constructing functional connectivity matrices using the AAL atlas, computing network metrics (efficiency, modularity, centrality), and training Logistic Regression and SVM classifiers with nested cross-validation and permutation testing for statistical validation. The entire pipeline is constrained to run on a free-tier GitHub Actions runner (2 CPU, 7GB RAM) within 6 hours.

**Critical Constraint**: The pipeline will **abort** if the required `ds000030` dataset (or a verified equivalent with Schizophrenia/Control labels) is not found in the verified source list. Synthetic data is used **only** for unit testing the pipeline logic, not for hypothesis validation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel`, `numpy`, `pandas`, `scikit-learn`, `networkx`, `bctpy`, `scipy`, `huggingface_hub`, `nilearn`, `pydantic`  
**Storage**: Local filesystem (temporary processing), CSV/Parquet for intermediate matrices, JSON for metadata.  
**Testing**: `pytest` (unit tests for metric calculations, integration tests for pipeline stages).  
**Target Platform**: Linux (GitHub Actions runner).  
**Project Type**: Data analysis pipeline / Computational neuroscience study.  
**Performance Goals**: Complete end-to-end analysis for N=60 subjects within 6 hours on 2 vCPU.  
**Constraints**: No GPU; no CUDA; no 8-bit/4-bit quantization; strict memory limit (limited RAM); strict disk limit (moderate capacity).  
**Scale/Scope**: N=60 subjects (assumed), ROIs (AAL), -20 features per subject.

> **Dataset Variable Fit Warning**: The spec assumes the OpenNeuro ds000030 dataset contains the necessary rs-fMRI data and diagnostic labels. The verified dataset URLs provided in the research phase (HuggingFace mirrors) must be inspected to confirm they contain the specific `ds000030` data with Schizophrenia/Control labels. If the verified URLs point to a different dataset (e.g., NSCLC radiomics or generic test NIfTIs), the plan **must abort** with a `DATA_GAP` error. *Note: The verified URLs listed in the prompt input do not explicitly confirm `ds000030` content; the research phase addresses this by defining a strict stop condition.*

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. `requirements.txt` pins all versions. Data fetched from canonical HuggingFace URLs. |
| **II. Verified Accuracy** | **PASS** | All citations (AAL atlas, OpenNeuro) will be validated against primary sources in `research.md`. |
| **III. Data Hygiene** | **PASS** | Raw data checksummed in `state/`. Preprocessing outputs new files; no in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in `paper/` will be generated programmatically from `data/` artifacts. |
| **V. Versioning Discipline** | **PASS** | **Mechanism**: `scripts/hash_artifacts.sh` generates SHA-256 hashes for all `data/` and `code/` files and updates `state/projects/PROJ-072-...yaml` `artifact_hashes` map automatically on every run. |
| **VI. Neuroimaging Standardization** | **PASS** | Pipeline uses FSL/AFNI logic (via `nilearn`) for motion correction, normalization, 0.01-0.1Hz bandpass. AAL atlas strictly enforced. |
| **VII. Statistical Significance** | **PASS** | Plan includes FDR-corrected t-tests and permutation tests. CI calculation and Cohen's d included. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-072-investigating-the-predictive-power-of-br/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   └── pipeline.py       # FR-001: Download, motion correction, bandpass. Enforces dataset.schema.yaml via Pydantic.
│   ├── graph_metrics/
│   │   ├── __init__.py
│   │   └── calculator.py     # FR-002, FR-003: Efficiency, centrality, feature extraction. Includes collinearity checks.
│   ├── classification/
│   │   ├── __init__.py
│   │   ├── models.py         # FR-004: LR, SVM, nested CV with Stability Selection. Enforces output_schema.yaml.
│   │   └── validation.py     # FR-005: Permutation tests, FDR, Sensitivity Analysis.
│   └── main.py               # Orchestrator with runtime monitoring and stop conditions.
├── data/
│   ├── raw/                  # Downloaded NIfTI (if cached) or pointers
│   ├── processed/            # Connectivity matrices, feature vectors
│   └── metadata/             # Subject labels, checksums
├── scripts/
│   └── hash_artifacts.sh     # Updates state/ YAML with content hashes (Constitution V).
├── tests/
│   ├── unit/
│   │   └── test_graph_metrics.py
│   └── integration/
│       └── test_pipeline.py
└── docs/
    └── figures/
```

**Structure Decision**: Single `code/` directory with modular sub-packages (`preprocessing`, `graph_metrics`, `classification`) to ensure separation of concerns and easy unit testing. This aligns with the "Single project" option in the template, optimized for a data pipeline rather than a web service.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Nested Cross-Validation** | Required by FR-004 to prevent data leakage during feature selection/hyperparameter tuning. | Simple train-test split would overestimate performance and fail the "statistical validation" requirement. |
| **Permutation Testing** | Required by FR-005 and SC-003 to establish significance against chance without distributional assumptions. | Standard t-test on accuracy is insufficient for small N and non-normal distributions; permutation is the gold standard here. |
| **FDR Correction** | Required by FR-005 for multiple comparisons across 15-20 metrics. | Bonferroni is too conservative for 20 tests; FDR balances Type I/II errors appropriately. |
| **Stability Selection** | Required to mitigate overfitting in N=60 with ~20 features (Methodology concern). | Simple RFE is unstable in small samples; Stability Selection ensures robust feature selection. |
| **Threshold Sensitivity** | Required to address global signal confounds in proportional thresholding (Scientific Soundness concern). | Single threshold may bias results; sensitivity analysis ensures robustness. |

## Statistical Rigor & Methodological Notes

### Power Analysis & Sample Size (Addressing Methodology Concern)
- **Current N**: 60 subjects (30 per group).
- **Power Limitation**: For binary classification with small effect sizes (Cohen's d indicates a small to medium effect size.), N=60 is underpowered to detect significant accuracy above chance.
- **Mitigation**:
  1.  **Exploratory Framing**: The study is explicitly framed as exploratory.
  2.  **Minimum Detectable Effect (MDE)**: The `validation.py` module will calculate and report the MDE for the observed sample size and a target power level.
  3.  **Significance Definition**: Primary significance is defined by permutation p-value < 0.05 (SC-003). The An accuracy threshold sufficient to demonstrate model viability. (SC-001) is treated as a **target metric** for this specific sample size, not a universal scientific standard.

### Feature Selection & Collinearity (Addressing Scientific Soundness Concerns)
- **Collinearity Check**: Before model training, a correlation matrix of features is computed. If Global and Local Efficiency are correlated (r > 0.8), PCA is applied to create a single 'Efficiency' component, or one is dropped.
- **Stability Selection**: Instead of RFE, the pipeline uses Stability Selection (Meinshausen & Bühlmann) within the inner CV loop. Features are retained only if selected in >60% of folds.
- **Global Signal Control**: Mean connectivity strength is included as a covariate in all models to control for global signal differences.

### Data Availability & Stop Conditions (Addressing Data Resource Concerns)
- **Stop Condition**: The `main.py` script checks for the presence of a verified equivalent dataset within the initial phase of the search.
- **Action**: If not found, the job fails with `DATA_GAP` error and does not proceed. Synthetic data is **not** used for hypothesis validation.
- **Sensitivity Analysis (FR-006)**: If medication status is missing, a simulated covariate (Bernoulli distributed) is added to the model to estimate the potential impact of unmeasured confounding. This is a sensitivity analysis, not data fabrication.

### Runtime & Constraints (Addressing Spec Coverage Concerns)
- **Monitoring**: `main.py` records start/end timestamps.
- **Constraint**: If runtime > 6 hours, the job is terminated, and `constraints_met` is set to `false` in the output.
- **Threshold Check**: The output includes a boolean `meets_accuracy_threshold` (CI lower bound >= 0.65).
