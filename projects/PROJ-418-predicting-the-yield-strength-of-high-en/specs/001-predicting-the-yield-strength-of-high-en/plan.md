# Implementation Plan: Predicting the Yield Strength of High‑Entropy Alloys

**Branch**: `feature-predict-yield-strength` | **Date**: 2026-07-30 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/feature-predict-yield-strength/spec.md`

## Summary
The project must predict the yield strength of high‑entropy alloys (HEAs) from compositional descriptors (mixing entropy, atomic size mismatch δ, electronegativity variance Δχ, valence electron concentration VEC, melting‑temperature variance) and additional covariates (phase structure, testing temperature). The workflow consists of:

1. **Descriptor & Covariate Engineering** – deterministic calculation using a locked elemental property table (Principle VI).  
2. **Model Training** – RandomForestRegressor with a lightweight hyper‑parameter grid search (fixed random seed).  
3. **Validation** – 5‑fold outer cross‑validation, reporting mean R².  
4. **Bootstrap Confidence Intervals** – ≥ 1000 bootstrap resamples for R².  
5. **Permutation Importance** – compute importance with **exactly a sufficiently large set of permutations** (hard‑coded) and apply Benjamini‑Hochberg FDR correction.  
6. **SHAP Analysis** – Kernel SHAP on a representative subset (≤ 200 samples).  
7. **Reporting** – reproducible markdown report containing all metrics, CI, importance plots, and a conditional “Data Limitation Warning”.  

All steps are deterministic, checksum‑tracked, and fully reproducible on a GitHub Actions runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `shap==0.45.*`, `matplotlib==3.9.*`, `pyyaml==6.0.*`  
- **Storage**: Files under `data/` (raw CSV, derived descriptor CSV, model artefacts)  
- **Testing**: `pytest==8.2.*` with contract validation via `jsonschema`  
- **Target Platform**: Linux (GitHub Actions Ubuntu‑latest)  
- **Performance Goals**: Complete end‑to‑end run ≤ 5 min on Multiple CPU cores, ≤ 2 GB RAM.  
- **Constraints**: Fixed 1000 permutations for permutation importance; all random seeds pinned.  
- **Scale/Scope**: Expect ≤ 10 k alloy entries (open dataset size ≈ a few MB) – if no suitable open dataset is available the pipeline aborts with a clear error (see Phase 0).

## Execution Phases (deterministic, no undefined FR/SC IDs)

### Phase 0 – Data Acquisition & Validation
- **Task**: `code/download_data.py` fetches the HEA yield‑strength dataset from a verified open source (if available) and validates the raw CSV against `contracts/dataset.schema.yaml`.  
- **Failure Mode**: If the dataset cannot be downloaded or does not meet the schema, the script aborts with an informative error; downstream steps are not executed.  
- **Contract Validation**: Validates against `contracts/dataset.schema.yaml`.

### Phase 1 – Descriptor & Covariate Engineering
- **Task**: `code/compute_descriptors.py` reads the raw data, computes mixing entropy, δ, Δχ, VEC, melting‑temperature variance using `data/element_properties.csv`, and adds `phase` and `testing_temperature`.  
- **Outputs**: `data/derived/descriptors.csv` (validated against `contracts/descriptor.schema.yaml` and `contracts/processed_data.schema.yaml`).  
- **Contract Validation**: 
  - Validate elemental property table against `contracts/elemental_properties.schema.yaml`.  
  - Validate generated descriptor table against `contracts/descriptor.schema.yaml`.  
  - Validate full processed dataset against `contracts/processed_data.schema.yaml`.

### Phase 2 – Model Training & Validation
- **Task**: `code/train_model.py` performs a tiny grid search (`n_estimators` ∈ {[deferred]}, `max_depth` ∈ {10, None}) evaluated via inner 3‑fold CV, selects the best hyper‑parameters, and fits a `RandomForestRegressor` (random_state = 42).
- **Outputs**: `data/derived/model_artifact.pkl` (checksum recorded).  
- **Task**: `code/validate_cv.py` runs 5‑fold outer cross‑validation, computes mean R².  
- **Task**: `code/bootstrap_ci.py` generates 1000‑resample bootstrap CI for R².  
- **Contract Validation**: Model artifact validated against `contracts/model_output.schema.yaml`; performance metrics validated against `contracts/metrics.schema.yaml`.

### Phase 3 – Feature Importance & Uncertainty
- **Task**: `code/perm_importance.py` runs **exactly 1000 permutations**, computes importance, applies Benjamini‑Hochberg FDR correction, writes `data/derived/perm_importance.json`.  
- **Task**: `code/shap_analysis.py` runs Kernel SHAP on ≤ 200 randomly selected samples, saves `data/figures/shap_summary.png`.  
- **Contract Validation**: Permutation results validated against `contracts/model_output.schema.yaml`; SHAP summary plot existence checked in CI tests.

### Phase 4 – Reporting
- **Task**: `code/generate_report.py` assembles `reports/report.md`, embedding:
  - Mean CV R² and its 95 % bootstrap CI.  
  - Permutation‑importance plot and corrected p‑values.  
  - SHAP summary plot.  
  - Conditional “Data Limitation Warning” if any alloy lacks a required descriptor.  
  - The mandatory disclaimer: “Associational analysis only; no causal inference”.  
- **Contract Validation**: Final report checksum recorded; schema‑level checks ensure required sections are present.

## Compute Feasibility
All methods run on the CPU‑first tier; no GPU‑only steps are required. The SHAP KernelExplainer on ≤ 200 samples completes within the GitHub Actions limits (2 CPU cores, ~7 GB RAM, ≤ 6 h).

## Constitution Check
| Principle | Compliance Evidence |
|-----------|---------------------|
| **I. Reproducibility** | Deterministic scripts, pinned seeds, CI workflow. |
| **II. Verified Accuracy** | Placeholder until spec cites a verified dataset; will be enforced once the spec is updated. |
| **III. Data Hygiene** | Checksums recorded, transformations write new files, no PII. |
| **IV. Single Source of Truth** | Every figure/table generated from a single row in `data/` and a single block in `code/`. |
| **V. Versioning Discipline** | Artifact hashes stored in project state YAML. |
| **VI. Deterministic Descriptor Engineering** | Locked `data/element_properties.csv` used by `compute_descriptors.py`. |
| **VII. Statistical Rigor and Uncertainty Quantification** | 5‑fold CV, 1000‑resample bootstrap, permutation importance (1000 permutations), SHAP, all seeds recorded. |

## Project Structure
```text
specs/feature-predict-yield-strength/
├── plan.md                # Updated (this file)
├── research.md            # Updated
├── data-model.md          # Updated with validation notes
├── quickstart.md          # Updated
├── contracts/
│   ├── descriptor.schema.yaml
│   ├── model_output.schema.yaml
│   ├── dataset.schema.yaml
│   ├── elemental_properties.schema.yaml
│   ├── hea_composition.schema.yaml
│   ├── hea_schema.schema.yaml
│   ├── processed_data.schema.yaml
│   ├── metrics.schema.yaml
│   ├── metrics_schema.schema.yaml
│   ├── model_metrics.schema.yaml
│   └── output.schema.yaml
└── tasks.md               # Generated later by /speckit-tasks

code/
├── __init__.py
├── config.yaml            # seeds, paths, constants
├── download_data.py       # pulls open HEA yield‑strength dataset, validates against dataset.schema.yaml
├── compute_descriptors.py
├── train_model.py
├── validate_cv.py
├── bootstrap_ci.py
├── perm_importance.py
├── shap_analysis.py
├── generate_report.py
└── utils/
    ├── checksums.py
    └── io_helpers.py

data/
├── raw/
│   └── hea_yield_strength.csv               # original download (checksumed) – may be absent if no verified source
├── derived/
│   ├── descriptors.csv                      # output of descriptor engineering (checksumed)
│   └── model_artifact.pkl                   # trained model (checksumed)
└── figures/
    ├── perm_importance.png
    └── shap_summary.png

reports/
└── report.md                # generated by generate_report.py

tests/
├── contract/
│   └── test_schemas.py
├── unit/
│   ├── test_descriptors.py
│   ├── test_model.py
│   └── test_report.py
└── integration/
    └── test_end_to_end.py

.state/
└── projects/
    └── PROJ-418-predicting-the-yield-strength-of-high-en.yaml
```

## Complexity Tracking
> No constitution violations identified; no additional complexity justification required.
