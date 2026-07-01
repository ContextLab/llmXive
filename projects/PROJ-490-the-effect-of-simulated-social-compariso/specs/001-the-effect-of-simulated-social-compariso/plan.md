# Implementation Plan: Simulated Social Comparison on Self-Esteem in VR

**Branch**: `001-simulated-social-comparison-self-esteem` | **Date**: 2024-01-15 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-simulated-social-comparison-self-esteem/spec.md`

## Summary

This project investigates the effect of simulated social comparison in Virtual Reality (VR) on self-esteem, specifically testing whether individual social comparison tendency moderates this relationship. The implementation is divided into two distinct, mutually exclusive paths based on data availability. The choice of path determines the project's ultimate scientific claim and success metrics.

### Path 1: Primary Path (Real Data - Empirical Answer)
*Goal*: Answer the empirical research question regarding real-world VR effects.
*   **Data Requirement**: Discovery of a real-world dataset containing RSES, INCOM, and longitudinal (pre/post) self-esteem data with N ≥ 100.
*   **Validation**: If found, **verify IRB approval** (Constitution Principle VI). If IRB is absent or unverifiable, discard and fall back to Path 2.
*   **Success Metrics**:
    1.  Statistical significance of the interaction term (with family-wise error correction).
    2.  **Post-hoc Power Analysis**: Must be calculated. If Power < 0.80, results are explicitly labeled **"Preliminary"** and conclusions are framed as such.
    3.  Validity of model assumptions (Shapiro-Wilk, Breusch-Pagan, VIF).

### Path 2: Secondary Path (Synthetic Data - Methodological Validation)
*Goal*: Validate the statistical pipeline (data generation -> MICE -> Regression -> Bootstrap) against known ground truth.
*   **Trigger**: Activated only if no valid real dataset is found (as anticipated) or if the real dataset lacks IRB approval.
*   **Data Generation**: A synthetic dataset is generated with known ground-truth parameters (interaction β = 0.2).
*   **Critical Distinction**: This path **DOES NOT** answer the empirical research question "How does exposure to idealized avatars affect self-esteem?" Synthetic data with arbitrary parameters (β=0.2) has **no external validity** for real-world claims. The output of this path is a **"Validated Pipeline"** report, not an empirical conclusion about VR.
*   **Success Metrics**:
    1.  **Parameter Recovery Bias**: The primary metric is |β_estimated - β_true|. If the pipeline cannot recover the known β=0.2 within a tight tolerance (e.g., ±0.05), the pipeline is deemed **flawed**.
    2.  **No Post-hoc Power Analysis**: This is methodologically invalid for known ground truth. The "Preliminary" label is **NOT APPLICABLE** to this path.
    3.  Assumption validation (Shapiro-Wilk, Breusch-Pagan, VIF) to ensure the statistical engine functions correctly.

The core analysis involves a linear regression model (`self-esteem_change ~ avatar_condition + comparison_tendency + interaction`) with rigorous assumption validation, bootstrap resampling for stability, and family-wise error correction. All methods are constrained to run on CPU-only GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `miceforest` (for MICE), `scipy`, `seaborn`, `matplotlib`, `pyyaml`
**Storage**: CSV/Parquet files in `data/` (raw and processed), JSON/CSV outputs in `data/`
**Testing**: `pytest` (unit tests for data loading, synthetic generation, and statistical assertions)
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM, ~14 GB disk)
**Project Type**: Computational Research / Statistical Analysis Pipeline
**Performance Goals**: Complete pipeline execution (data generation/load -> analysis -> reporting) within ≤ 6 hours. Memory usage < 7 GB.
**Constraints**: No GPU/CUDA; no large LLM inference; no training of deep neural networks. Synthetic data must match ground-truth parameters within statistical tolerance.
**Scale/Scope**: N ≥ 100 participants (synthetic or real). Single regression model with moderation.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action/Verification |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | `requirements.txt` will pin all versions. Random seeds (e.g., `42`) will be set in `code/` scripts. Synthetic data generation will use fixed seeds. |
| **II. Verified Accuracy** | **Pass** | Citations for RSES and INCOM validation will be sourced from primary literature. The **Reference-Validator Agent** will verify all citations against the "Verified datasets" block and primary sources, enforcing a **Title-token-overlap ≥ 0.7** before any review point is awarded. No fabricated URLs. |
| **III. Data Hygiene** | **Pass** | Raw data (if any) will be checksummed. No in-place modification; all transformations (MICE, change score) will create new files. PII will be excluded (synthetic data has no PII). |
| **IV. Single Source of Truth** | **Pass** | All statistics in `paper/` will be derived from `data/` CSV/JSON outputs generated by `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **Pass** | Artifacts will carry content hashes. The **`state/projects/PROJ-490-the-effect-of-simulated-social-compariso.yaml`** file will be explicitly updated on artifact changes to reflect the current state. |
| **VI. Ethical Human Subjects** | **Pass** | **Primary Path**: If a real dataset is found, the system MUST verify IRB approval status. If IRB is missing or unverifiable, the system MUST **discard the real dataset** and proceed to the Synthetic Data path. The Synthetic Data path requires no IRB. |
| **VII. Statistical Analysis Transparency** | **Pass** | `analysis_plan.md` will be generated in `docs/` pre-registration. All model specs and diagnostics will be exported to CSV/JSON. |

## Project Structure

### Documentation (this feature)

```text
specs/001-simulated-social-comparison-self-esteem/
├── plan.md              # This file
├── research.md          # Phase 0 output (Dataset search, synthetic strategy)
├── data-model.md        # Phase 1 output (Schema definitions)
├── quickstart.md        # Phase 1 output (Setup instructions)
├── contracts/           # Phase 1 output (Schemas)
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-490-the-effect-of-simulated-social-compariso/
├── code/
│   ├── __init__.py
│   ├── data_loader.py       # Handles real dataset query or synthetic generation
│   ├── preprocessing.py     # MICE, change score calculation, outlier handling
│   ├── analysis.py          # Linear regression, assumption checks, bootstrap
│   ├── sensitivity.py       # Threshold sweeps, power analysis (Real Data only)
│   └── main.py              # Orchestrator script
├── data/
│   ├── raw/                 # Downloaded raw data (if any) or synthetic raw
│   ├── processed/           # Cleaned, imputed, derived features
│   └── outputs/             # Regression results, diagnostics, plots
├── docs/
│   └── analysis_plan.md     # Pre-registration of the analysis
├── tests/
│   ├── test_data_loader.py
│   ├── test_preprocessing.py
│   └── test_analysis.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `docs/`) selected to align with the computational research nature of the spec. No separate frontend/backend is required as the output is a research report and data artifacts, not a web service.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Synthetic Data Generation** | Real VR longitudinal data with RSES/INCOM is unlikely to exist (FR-001). | Using a generic dataset without the required variables would violate FR-009 and invalidate the research question. Synthetic data allows testing the pipeline with known ground truth. |
| **MICE Imputation** | Spec requires handling missingness < 20% robustly (FR-002). | Simple mean/median imputation biases regression coefficients and underestimates variance, violating statistical rigor requirements. |
| **Bootstrap Resampling** | Required for stability of interaction effects (FR-005). | Relying solely on asymptotic p-values is insufficient for small-to-moderate sample sizes (N=100) and interaction terms. |
| **Dual-Path Logic** | Spec requires attempting real data first, then synthetic. | A single-path approach would either fail to answer the real question (if only synthetic) or fail to run if real data is missing. |