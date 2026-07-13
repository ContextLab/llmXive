# Implementation Plan: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

**Branch**: `001-phase-change-predictive-power` | **Date**: 2026-07-13 | **Spec**: `specs/001-phase-change-predictive-power/spec.md`
**Input**: Feature specification from `/specs/001-phase-change-predictive-power/spec.md`

## Summary

This project investigates the **associational predictive power** of machine learning (ML) for identifying novel phase-change materials (PCMs). The approach involves retrieving materials data (melting points, heat capacity) from the Materials Project API, computing elemental and structural descriptors (including crystal graphs), and training both black-box baselines (Random Forest, Gradient Boosting) and interpretable models (SHAP, PySR symbolic regression). 

**Critical Methodological Note**: Due to the observational nature of the data, all findings will be framed as **associational predictors** and **statistical correlations**, not causal "governing factors" or "explanatory formulas". The project explicitly avoids causal claims regarding phase-change suitability.

The core research goal is to derive explicit mathematical formulas or ranked feature lists that **correlate** with phase-change properties, validated against an independent set of literature PCMs. All computations are constrained to run on a CPU-only GitHub Actions free-tier runner with limited CPU and memory resources (time limit).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pymatgen`, `scikit-learn`, `pysr`, `shap`, `pandas`, `numpy`, `matplotlib`, `requests`, `pyyaml`  
**Storage**: Local CSV/Parquet files (within `data/`), GitHub Actions ephemeral storage.  
**Testing**: `pytest` (unit tests for data pipelines, integration tests for model training).  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner).  
**Project Type**: Computational research pipeline / CLI.  
**Performance Goals**: Complete data retrieval, feature engineering, model training, and validation within 6 hours; memory usage < 7 GB.  
**Constraints**: No GPU; no deep learning training from scratch; dataset subset to fit RAM; symbolic regression time-bounded.  
**Scale/Scope**: A large set of compounds in the training set; A set of external validation compounds.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Random seeds pinned in `code/`. External datasets fetched via verified URLs or API keys stored in secrets. `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | **Pass** | All dataset URLs in `research.md` are from the verified list (Materials Project API and specific literature DOI). Citations validated against primary sources before analysis. |
| **III. Data Hygiene** | **Pass** | Raw data checksums recorded in `state/`. Transformations produce new files (e.g., `raw.json` -> `features.csv`). No in-place modification. |
| **IV. Single Source of Truth** | **Pass** | Figures/stats in `paper/` will trace to `data/` and `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **Pass** | Content hashes for artifacts. `state` updated on artifact changes. |
| **VI. Numerical Stability** | **Pass** | Explicit checks for `nan`/`inf` in `pymatgen` graph construction. Logging and fallback protocols for unstable features. |
| **VII. Independent Physical Validation** | **Pass** | A held-out set of literature PCMs (external to training) will be used to validate derived rules. |

## Project Structure

### Documentation (this feature)

```text
specs/001-phase-change-predictive-power/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── fetch_materials_project.py
│   ├── compute_descriptors.py
│   └── load_external_validation.py
├── models/
│   ├── train_baselines.py
│   ├── train_symbolic.py
│   └── evaluate.py
├── utils/
│   ├── graph_utils.py
│   ├── stability_checks.py
│   └── collinearity_utils.py
├── config.yaml
└── main.py

tests/
├── contract/
│   ├── test_dataset_schema.py
│   └── test_model_output_schema.py
├── integration/
│   └── test_pipeline.py
└── unit/
    ├── test_descriptors.py
    └── test_stability.py
```

**Structure Decision**: Single project structure (`code/`) is selected to minimize overhead and fit within the 6-hour CI window. The separation of `data/`, `models/`, and `utils/` ensures modularity while keeping the import path simple for the runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Symbolic Regression (PySR)** | Required for explicit mathematical formulas (FR-003, FR-007). | Standard regression (linear/polynomial) cannot discover non-linear, interpretable governing factors without human bias in feature selection. |
| **Crystal Graph Features** | Required to capture structural context (FR-002). | Elemental descriptors alone are insufficient for phase-change properties which depend on bonding topology. |
| **External Validation Set** | Required for Principle VII. | Using the same test set for training and validation would lead to overfitting and invalid scientific claims. |

## Phased Implementation Plan

### Phase 0: Research & Feasibility (Days 1-2)
*Goal: Confirm dataset availability, variable fit, and target consistency.*
1.  **Dataset Verification**: 
    *   **Verify Access**: Confirm access to the **Materials Project API** (primary source) and the specific literature review (DOI: 10.1016/j.matt.2024.01.001) for the external validation set.
    *   **Exclusion**: Explicitly **exclude** the `nist_800_53` and other irrelevant security/LLM datasets from the "Verified datasets" block, as they are out of scope for materials science.
    *   **Variable Fit**: Confirm the presence of `melting_point`, `heat_capacity`, and `latent_heat` (or proxies) in the Materials Project data subset.
2.  **Variable Fit Analysis**: Check if the verified datasets contain the required predictors (atomic number, electronegativity, radius, crystal graph). If `latent_heat` is missing in the primary source, confirm the proxy strategy (US-1).
3.  **Target Consistency Check**: **CRITICAL STEP**. Empirically calculate the Pearson correlation between `melting_point` and `latent_heat` in the overlapping subset of the training data. 
    *   **If r ≥ 0.6**: Proceed with `latent_heat` as the validation target for SC-003.
    *   **If r < 0.6**: Switch the validation target for SC-003 to `melting_point` (ranking accuracy on A selection of high-melting-point PCMs will be identified to address the research question: What are the most promising phase change materials for high-temperature thermal energy storage? The study will employ a systematic literature review and comparative analysis methodology. References: [Citations preserved verbatim].) and flag the limitation. This prevents a logical dead-end where the project fails its own success metric due to a weak proxy.
4.  **Compute Feasibility**: Benchmark `pymatgen` graph generation and PySR on a representative sample of compounds to ensure it fits within the 7 GB RAM / 6h CPU constraint.

### Phase 1: Data Engineering & Model Design (Days 3-5)
*Goal: Build the data pipeline and define the data model.*
1.  **Data Retrieval**: Implement `fetch_materials_project.py` to download compounds with melting points. Handle API rate limits.
2.  **Feature Engineering**: Implement `compute_descriptors.py` to generate elemental and graph features. Implement stability checks (Principle VI).
3.  **Multicollinearity Regularization**: Implement `collinearity_utils.py` to perform Variance Inflation Factor (VIF) analysis. Remove features with VIF > 5 or apply L1 regularization before symbolic regression to prevent spurious formulas from dependent descriptors (FR-006).
4.  **Schema Definition**: Define `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml`.
5.  **Baseline Training**: Implement `train_baselines.py` (Random Forest, Gradient Boosting) with SHAP analysis.
6.  **Symbolic Regression**: Implement `train_symbolic.py` using PySR with a strict time budget and the regularized feature set.

### Phase 2: Validation & Analysis (Days 6-7)
*Goal: Validate findings and perform sensitivity analysis.*
1.  **External Validation**: Load a representative set of literature PCMs. Apply derived rules. 
    *   **Target**: If Phase 0 passed (r ≥ 0.6), validate against `latent_heat` ranking. If Phase 0 failed (r < 0.6), validate against `melting_point` ranking.
    *   **Metric**: Accuracy on the **top 10** highest-value PCMs (resolving SC-003's deferred value).
2.  **Sensitivity Analysis**: Sweep feature importance thresholds (FR-004) and report false-positive/negative rates.
3.  **Collinearity Check**: Final diagnostic check for definitional dependencies (FR-006).
4.  **Report Generation**: Compile results into `research.md` and `paper/` drafts, explicitly framing results as associational.

### Phase 3: Finalization (Day 8)
*Goal: Ensure reproducibility and cleanup.*
1.  **Reproducibility Check**: Run the full pipeline end-to-end on a fresh runner.
2.  **Hygiene**: Verify checksums and artifact hashes.
3.  **Documentation**: Finalize `quickstart.md` and `data-model.md`.

## FR/SC Coverage Matrix

| ID | Requirement | Plan Step Addressing It |
| :--- | :--- | :--- |
| **FR-001** | Retrieve Materials Project data | Phase 1, Step 1: `fetch_materials_project.py` |
| **FR-002** | Compute descriptors & graphs | Phase 1, Step 2: `compute_descriptors.py` |
| **FR-003** | Train baselines & interpretable models | Phase 1, Step 5 & 6: `train_baselines.py`, `train_symbolic.py` |
| **FR-004** | Sensitivity analysis on thresholds | Phase 2, Step 2: Threshold sweep logic |
| **FR-005** | Validate against literature PCMs | Phase 2, Step 1: External validation logic |
| **FR-006** | Flag collinearity | Phase 1, Step 3 & Phase 2, Step 3: VIF analysis |
| **FR-007** | Output explicit formulas/associational framing | Phase 1, Step 6 & Phase 2: PySR output + associational framing |
| **SC-001** | Correlation measurement | Phase 2, Step 1: Pearson correlation calculation |
| **SC-002** | R² comparison (t-test) | Phase 2, Step 1: Model comparison metrics |
| **SC-003** | Generalization accuracy (≥60% on top 10) | Phase 2, Step 1: External ranking accuracy on **top 10** PCMs |
| **SC-004** | Robustness of thresholds | Phase 2, Step 2: Sensitivity report |
| **SC-005** | Compute feasibility | Phase 0, Step 4: Benchmarking & Phase 1 constraints |