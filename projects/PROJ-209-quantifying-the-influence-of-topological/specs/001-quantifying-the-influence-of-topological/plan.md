# Implementation Plan: Quantifying the Influence of Topological Defects on 2D Material Properties

**Branch**: `001-quantify-defect-influence` | **Date**: 2024-01-15 | **Spec**: `specs/001-quantify-defect-influence/spec.md`
**Input**: Feature specification from `/specs/001-quantify-defect-influence/spec.md`

## Summary

This project performs **predictive modeling** of how topological defects (dislocations, grain boundaries) in graphene and MoS₂ correlate with changes in electronic conductivity, Young's modulus, and fracture strength. **Crucially, due to the observational nature of the data, all results are framed as associational, not causal.** The study relies on the "2022 supplementary CSV/JSON" (Constitution Principle VI) as the sole source for scientific analysis. If this dataset is unavailable, the scientific analysis phase is **HALTED**, and the project runs a "Pipeline Validation" mode using a strictly synthetic dataset (flagged as `TESTING_ONLY`).

The workflow involves:
1.  Acquiring pristine DFT structures via the Materials Project API.
2.  Validating the presence of the 2022 defect dataset.
3.  Training Random Forest regressors with strict cross-validation (k=5).
4.  Applying permutation-based statistical inference with Benjamini-Hochberg FDR control.
5.  Generating a `Validation_Report.json` that explicitly documents data availability and scope limitations.

The entire workflow is designed to run within GitHub Actions free-tier constraints (CPU-only, ~7GB RAM, ≤6h).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `scikit-learn`, `requests`, `numpy`, `jupyter`, `pyyaml`, `causalml` (for propensity score matching sensitivity analysis).
**Storage**: Local `data/` directory (raw, processed), `data/state/` for logs and checksums.
**Testing**: `pytest` (unit), `nbval` (notebook regression).
**Target Platform**: Linux (GitHub Actions free-tier runner).
**Project Type**: Computational Research / Data Analysis Pipeline.
**Performance Goals**: Complete full analysis (data acquisition, modeling, inference) within 6 hours; memory usage < 7GB.
**Constraints**: No GPU; strict data hygiene (checksums); synthetic data strictly for testing; no external validation if no public dataset exists.
**Scale/Scope**: A set of defect entries (real or synthetic); target properties; A sufficient number of permutation iterations.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | All random seeds pinned (); `requirements.txt` pins versions; data fetched from canonical sources (MP API, 2022 CSV); `data/` checksums recorded. |
| **II. Verified Accuracy** | PASS | All citations in `research.md` verified against the provided `# Verified datasets` block. No fabricated URLs. |
| **III. Data Hygiene** | PASS | Raw data preserved; derivations write to new files; `data/state/exclusion_log.json` tracks missing data with exact flag `[MISSING: requires exclusion]`; PII scan passed (scientific data). |
| **IV. Single Source of Truth** | PASS | Figures/stats trace to `data/processed/` files; no hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | PASS | Content hashes for artifacts; `state/` updated on change. |
| **VI. Defect Dataset Integrity** | PASS | **Strict Gate:** If "2022 supplementary CSV/JSON" is missing, scientific analysis halts. Synthetic data is only for pipeline testing. Provenance metadata stored in `data/state/`. |
| **VII. Modeling Reproducibility** | PASS | `model_config.yaml` records splits/hyperparams; feature matrix saved with checksum; code version-controlled. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-defect-influence/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── defect_entry.schema.yaml
│   ├── model_results.schema.yaml
│   ├── output.schema.yaml
│   ├── processed_data.schema.yaml
│   └── validation_report.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-209-quantifying-the-influence-of-topological/
├── code/
│   ├── 01_data_acquisition.py      # MP API, cache, 2022 CSV check, synthetic gen (test only)
│   ├── 02_feature_engineering.py   # Normalization, encoding, VIF check, confounding control
│   ├── 03_modeling.py              # RF training, CV, permutation tests, hold-out eval
│   ├── 04_analysis.py              # Sensitivity, FDR, Validation_Report.json generation
│   └── run_pipeline.py             # Orchestration with Go/No-Go gates
├── data/
│   ├── raw/
│   │   ├── pristine_structures.csv
│   │   ├── defect_dataset_2022.csv
│   │   ├── synthetic_train.csv
│   │   └── real_holdout.csv
│   ├── processed/
│   │   ├── feature_matrix.csv
│   │   └── target_matrix.csv
│   └── state/
│       ├── exclusion_log.json
│       ├── cache_load_log.json
│       ├── source_validation.json
│       ├── synthetic_config.json
│       └── real_confounding_log.json
├── tests/
│   ├── contract/
│   └── unit/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure (Option 1) chosen. The workflow is linear (Acquisition → Engineering → Modeling → Analysis) and fits within a single Python repository. No frontend/backend split is required for a research pipeline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Permutation Testing (N=1000)** | Required by FR-011 for valid FDR control. | Standard p-values (t-test) assume normality which RF feature importances do not satisfy; permutation is non-parametric and robust. |
| **Synthetic Data Fallback** | Required by US-1 for pipeline testing if real data is missing. | Hard-coding a static "toy" dataset would fail reproducibility (Constitution I) and might not match the schema of the real data. Dynamic generation ensures schema fit. |
| **Cache-Fallback Logic** | Required by US-1 (API failure handling). | Halting on API failure would break CI reliability; a local cache ensures the pipeline can run in air-gapped or rate-limited environments. |
| **Propensity Score Matching** | Required to address confounding (FR-013) and causal limitations. | Simple regression cannot disentangle confounding factors (synthesis method, grain size) from defect effects in observational data. |

## Phase Breakdown

### Phase 0: Data Acquisition & Integrity Gate
- **Step 1**: Download pristine structures from Materials Project API.
- **Step 2**: Check for `data/raw/defect_dataset_2022.csv`.
  - **If Missing**: Log `ERROR: 2022 CSV missing`, generate `Validation_Report.json` with `status: NO_EXTERNAL_DATA`, and **HALT** scientific modeling. Run synthetic pipeline test only.
  - **If Present**: Validate schema and checksums.
- **Step 3**: Flag missing values with `[MISSING: requires exclusion]` and exclude entries. Log count.

### Phase 1: Feature Engineering & Confounding Control
- **Step 1**: Normalize properties by pristine references (σ₀, E₀, σ_f₀).
- **Step 2**: Encode defect types (one-hot).
- **Step 3**: **Confounding Control (FR-013)**: Attempt stratification by 'synthesis_method' or 'grain_size'. If unavailable, include as covariates. Log status.
- **Step 4**: Compute VIF. If VIF > 5, flag collinearity and prepare for sensitivity analysis.

### Phase 2: Modeling & Inference
- **Step 1**: Split data: Train ([deferred]), Validation ([deferred]), Test ([deferred]). The Test set is the **independent hold-out set** (FR-012).
- **Step 2**: Train Random Forest regressors (k=5 CV).
- **Step 3**: Evaluate on Test set (R², MAPE).
- **Step 4**: Permutation testing (N=1000) for p-values.
- **Step 5**: Apply Benjamini-Hochberg FDR control.

### Phase 3: Sensitivity Analysis & Reporting
- **Step 1**: Sensitivity analysis on decision cutoffs (deciles).
- **Step 2**: Collinearity sensitivity (compare models with/without correlated features).
- **Step 3**: Generate `Validation_Report.json` with mandatory fields (`status`, `method`, `scope_limitation`).

## Data Availability & Feasibility

- **Compute**: The datasets are small (<100MB for CSV/Parquet). They fit easily within the 7GB RAM limit.
- **Streaming**: Not required for the expected dataset size (<10k rows). Full load into memory is feasible.
- **Access**: All verified HF datasets are public. Materials Project API is public (requires API key, handled via env var).
- **Real Data Constraint**: The study **requires** the 2022 CSV. If unavailable, no scientific conclusions about "influence" are drawn.