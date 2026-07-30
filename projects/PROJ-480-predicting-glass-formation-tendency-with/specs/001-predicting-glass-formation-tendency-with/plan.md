# Implementation Plan: Predicting Glass Formation Tendency with Machine Learning on Public Data

**Branch**: `001-predict-glass-formation` | **Date**: 2026-07-12 | **Spec**: `specs/001-predicting-glass-formation/spec.md`
**Input**: Feature specification from `/specs/001-predicting-glass-formation/spec.md`

## Summary

This feature implements a CPU-constrained machine learning pipeline to predict metallic glass formation tendency. The system ingests composition data from a **verified, static public dataset** (Matbench Glass Formation Benchmark), computes thermodynamic descriptors (atomic size mismatch, mixing enthalpy, electronegativity) using `pymatgen`, and trains an XGBoost model (regressor for critical casting thickness $D_c$, or classifier for binary glass/crystal labels). The plan ensures strict adherence to the multi-core/GB RAM constraint, frames all findings as associational, and includes robust diagnostics for collinearity, threshold sensitivity, and data leakage prevention via group-based cross-validation.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `pymatgen`, `xgboost`, `pandas`, `scikit-learn`, `pyyaml`, `requests`, `matbench`, `statsmodels`, `seaborn`  
**Storage**: Local CSV/Parquet files under `data/` (checksummed)  
**Testing**: `pytest` (unit tests for descriptor computation, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data Science Pipeline / CLI  
**Performance Goals**: Complete training and validation within 6 hours (target < 30 mins) on 2 CPU cores, 7GB RAM.  
**Constraints**: No GPU usage for training; no authentication tokens that expire within 6h; observational data framing.  
**Scale/Scope**: Target dataset size is the count available in the Matbench Glass Formation dataset (minimum 30 for training, as per FR-001 and SC-001). If the dataset size is < 30, the pipeline halts. This scope is defined by the verified data source, not by the unverified FR-001 requirement for MP/Zenodo.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Plan mandates pinned `random_seed=42` for all splits/modeling. External datasets are fetched from a canonical, verified source (Matbench Glass Formation) via the `matbench` library. No dynamic discovery. |
| **II. Verified Accuracy** | **Compliant** | Plan cites ONLY the verified Matbench dataset. All model outputs (accuracy/R²) will be traced to specific data rows in `data/`. No dynamic discovery of unverified sources. |
| **III. Data Hygiene** | **Compliant** | Plan includes checksumming of raw data files AND the processed dataset (`data/processed/composition_records.csv`). No in-place modification; derived datasets written to new files. |
| **IV. Single Source of Truth** | **Compliant** | Figures and statistics in the final report will be generated programmatically from the `data/` artifacts, not hand-typed. |
| **V. Versioning Discipline** | **Compliant** | Artifacts will be content-hashed. `state/` file updated on artifact changes. |
| **VI. Descriptor-Based FE** | **Compliant** | All features are strictly derived from `pymatgen` atomic descriptors (radius, electronegativity, etc.). No latent embeddings. |
| **VII. CPU-Constrained** | **Compliant** | XGBoost is configured for CPU-only execution. Data streaming/sampling strategies used to fit < 7GB RAM. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-glass-formation/
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
projects/PROJ-480-predicting-glass-formation-tendency-with/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── download.py          # Fetches raw data from verified Matbench
│   │   ├── preprocess.py        # Computes descriptors via pymatgen
│   │   └── validate.py          # Checks for missing variables, checksums processed data
│   ├── model/
│   │   ├── train.py             # XGBoost training (regressor/classifier) with GroupKFold
│   │   ├── evaluate.py          # CV, metrics, VIF diagnostics, Power Analysis
│   │   └── interpret.py         # Feature importance, PDP plots, Threshold Sensitivity
│   └── main.py                  # Orchestration script
├── data/
│   ├── raw/                     # Downloaded CSVs (checksummed)
│   └── processed/               # Descriptor-computed CSVs (checksummed)
├── tests/
│   ├── unit/
│   │   ├── test_descriptors.py
│   │   └── test_validation.py
│   └── integration/
│       └── test_pipeline.py
└── state/
    └── projects/PROJ-480-.../
        └── artifacts.yaml       # Checksums and versioning
```

**Structure Decision**: Single `code/` directory with modular sub-packages (`data`, `model`) to ensure isolation and testability. This aligns with the CLI/Data Science pipeline nature of the project.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Phase Execution Order

1.  **Phase 0: Pre-Analysis Power Calculation**
    *   **Task 0.1**: Calculate the Minimum Detectable Effect Size (MDES) for the expected sample size (N) and number of predictors (k) using `statsmodels`. If N is insufficient for a medium effect size (f2=0.15), explicitly flag this limitation in the report and log the calculated MDES. If N < 30, halt immediately.
    *   **Task 0.2**: Verify the availability of the Matbench dataset. If unavailable, check for the UCI Glass Identification dataset as a fallback. If neither is available, halt with `DataValidationError`.

2.  **Phase 1: Data Ingestion**
    *   **Task 1.1**: Download raw data from the **verified** Matbench Glass Formation dataset (or UCI fallback). Validate existence of target variable ($D_c$ or binary label). If the dataset is unavailable, halt immediately.
    *   **Task 1.2**: Verify that the target variable is an **experimental observation** (e.g., measured $D_c$ or experimentally confirmed glass/crystal label) and NOT a calculated function of the descriptors. If the target is derived from the same physics as the features, flag as "Potential Tautology" in the report and halt or proceed with a severe warning.

3.  **Phase 2: Ground Truth Verification**
    *   **Task 2.1**: Check the dataset's metadata for "experimental" or "measured" tags. If the target is found to be a derived proxy for the descriptors, flag this as a "Potential Tautology" and halt or proceed with a severe warning.
    *   **Task 2.2**: **Binary Task Validity Check**: If the target is binary, perform a feature separability analysis (e.g., PCA) and check class balance. If the task is trivial (e.g., perfect separation by a single descriptor), halt with a "Trivial Task" warning.

4.  **Phase 3: Confounding Check**
    *   **Task 3.1**: Inspect dataset for processing conditions (cooling rate). If missing, log a warning that the model learns "associations under mixed processing conditions" and proceed only if the target is binary (less sensitive to rate).
    *   **Task 3.2**: If cooling rate is available, the model will control for it (if continuous) or stratify by it (if categorical).

5.  **Phase 4: Descriptor Computation**
    *   **Task 4.1**: Use `pymatgen` to compute atomic descriptors. Handle "Unknown Element" exclusions. Log excluded samples.

6.  **Phase 5: Data Validation**
    *   **Task 5.1: Variable Presence Check**: Check for missing variables, ensure ≥ 30 samples. **MUST raise `DataValidationError` with message 'Missing required variable: {variable_name} in {dataset_name}'** if any required field is absent. Log the count of missing records and specific missing fields.
    *   **Task 5.2: Error Handling Implementation**: Implement the specific error message format and logging behavior as a distinct, testable step.
    *   **Task 5.3: Processed Data Checksumming**: Calculate the SHA256 checksum of the *processed* dataset (`data/processed/composition_records.csv`) and record it in `state/artifacts.yaml` under the key 'processed_dataset_checksum'. This distinguishes it from raw data checksums.

7.  **Phase 6: Power Analysis (Runtime)**
    *   **Task 6.1**: Re-calculate MDES given the actual sample size (N) and number of predictors (k) using `statsmodels`. If N is insufficient for a medium effect size, explicitly flag this limitation in the report and log the calculated MDES.

8.  **Phase 7: Model Training**
    *   **Task 7.1: Chemical Family Grouping**: Group the data by chemical family (e.g., Zr-based, Cu-based) to prevent data leakage from similar compositions.
    *   **Task 7.2**: Train XGBoost (Regressor or Classifier) with `random_seed=42`. **Use Group K-Fold Cross-Validation** (grouped by chemical family) to prevent data leakage.

9.  **Phase 8: Evaluation**
    *   **Task 8.1**: Compute metrics (R²/AUC), check stability (std dev < 0.05).

10. **Phase 9: Diagnostics**
    *   **Task 9.1: VIF Reporting**: Calculate Variance Inflation Factor (VIF) for top predictors. **Write VIF scores to the `ModelArtifact` JSON** and include in the final report. If VIF > 10, note the physical correlation limitation.

11. **Phase 10: Threshold Sensitivity**
    *   **Task 10.1: Threshold Sensitivity Sweep**: (If Classification) Sweep cutoff values **{0.4, 0.5, 0.6}** and generate a specific artifact `threshold_sensitivity.csv` with a table of False Positive/Negative rates. (Satisfies **FR-005**).

12. **Phase 11: Interpretability**
    *   **Task 11.1**: Generate feature importance rankings and PDP/decision boundary plots.

13. **Phase 12: Associational Framing Validation**
    *   **Task 12.1: Associational Framing Validation**: (Satisfies **FR-007**) Generate a `report_framing_check.txt` file that scans the final report for causal language and confirms the presence of the mandatory disclaimer. Generate the final report using a template that explicitly inserts the required disclaimer: "These findings are associational, not causal, as the data is observational." Validate that no causal language is present in the output.

14. **Phase 13: Reporting**
    *   **Task 13.1**: Generate final summary.

## Compute Feasibility Strategy

- **CPU-First**: XGBoost is native to CPU. The dataset size (≤ 1000 samples) fits easily in 7GB RAM. No GPU is required.
- **Streaming**: If a source dataset is large (> 1GB), the download script will stream and filter for relevant columns before writing to disk to avoid memory spikes.
- **No Synthetic Data**: The plan relies on real, open-source data. If the verified Matbench dataset is unavailable, the plan explicitly halts rather than synthesizing data.

## Risk Assessment

- **Data Scarcity**: If the verified Matbench dataset (or UCI fallback) is unreachable, the project halts. *Mitigation*: None (strict adherence to verified sources).
- **Missing Descriptors**: If `pymatgen` lacks properties for rare earth elements. *Mitigation*: Exclude samples and log.
- **Tautology**: If the target is derived from the same descriptors. *Mitigation*: Flag in report and interpret with caution; halt if severe.
- **Collinearity**: High VIF expected. *Mitigation*: Report VIF scores and caveats.
- **Data Leakage**: Similar compositions in train/test. *Mitigation*: Use Group K-Fold by chemical family.