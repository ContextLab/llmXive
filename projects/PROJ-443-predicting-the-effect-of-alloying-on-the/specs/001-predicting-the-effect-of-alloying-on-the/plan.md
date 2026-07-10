# Implementation Plan: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

**Branch**: `001-predict-elastic-modulus` | **Date**: 2024-05-21 | **Spec**: `spec.md`

## Summary

This feature implements a computational pipeline to predict the effect of alloying on the elastic modulus of High-Entropy Alloys (HEAs). The approach involves retrieving HEA composition and elastic constant data from the Materials Project and OQMD APIs, engineering compositional descriptors using Isometric Log-Ratio (ILR) transformation to handle compositional singularity, and training regression models (Random Forest, Gradient Boosting, ElasticNet) to predict residual elastic moduli. The study strictly adheres to a "Residual" strategy, excluding Miedema-derived features when the target is a residual modulus to prevent circular validation. Statistical rigor is enforced via grouped bootstrapping, permutation tests for null hypothesis validation, and multiple-comparison corrections.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `scipy`, `pyyaml`, `requests`, `compositional` (for ILR), `shap` (for interpretability), `materials-project` (for MP API)  
**Storage**: Local files under `data/` (CSV, YAML, Parquet), `results/` (JSON, YAML)  
**Testing**: `pytest` with contract validation against `contracts/` schemas  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7 GB RAM, no GPU)  
**Project Type**: Computational Science Pipeline / CLI  
**Performance Goals**: Complete full pipeline (fetch, engineer, train, evaluate) within 6 hours on CPU-only runner.  
**Constraints**: 
- No GPU/CUDA usage.
- No large-LLM inference or deep net training.
- Memory footprint < 7 GB (data sampling required if raw API output exceeds).
- Strict exclusion of Miedema features for Residual targets.
- Associational framing only (no causal claims).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Details |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seeds in code, and deterministic data fetching from canonical APIs. |
| **II. Verified Accuracy** | **PASS** | The `Reference-Validator Agent` is invoked as a pre-commit hook/CI step. It validates all citations against the `# Verified datasets` block and enforces `CITATION_TITLE_OVERLAP_THRESHOLD` (0.7) via the `validate_citations()` function in `code/`. |
| **III. Data Hygiene** | **PASS** | Pipeline includes checksumming of raw API outputs. The `Repository-Hygiene Agent` is triggered via `scripts/pii_scan.sh` before any data commit to ensure no PII is present. |
| **IV. Single Source of Truth** | **PASS** | All metrics are generated programmatically by `code/report_generator.py` from `results/metrics.yaml`. A CI linting rule prohibits manual entry in the report generation step. |
| **V. Versioning Discipline** | **PASS** | The `code/main.py` script includes an `update_state_file()` function that reads content hashes of all artifacts and writes them to `state/projects/...yaml` upon successful execution, invalidating stale reviews. |
| **VI. Materials Database Provenance** | **PASS** | The `data/fetch.py` script includes a `check_and_update_provenance()` function. If the checksum of fetched data differs from `source_metadata.yaml`, it triggers a re-download and updates the metadata file automatically. |
| **VII. Model Evaluation Transparency** | **PASS** | Plan mandates R², RMSE, MAE, 95% CI via bootstrapping, and permutation tests for all models. While Constitution VII mentions a t-test, this plan uses permutation tests as a statistically valid alternative for non-normal distributions; this choice is documented and validated by the `Reference-Validator Agent`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-elastic-modulus/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── model_output.schema.yaml
│   └── metadata.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-443-predicting-the-effect-of-alloying-on-the/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── main.py                 # Orchestration entry point (includes update_state_file)
│   ├── data/
│   │   ├── fetch.py            # MP/OQMD API retrieval (includes check_and_update_provenance)
│   │   ├── clean.py            # Normalization, filtering
│   │   └── metadata.py         # source_metadata.yaml generation
│   ├── features/
│   │   ├── descriptors.py      # Miedema, ILR, standard descriptors
│   │   └── pipeline.py         # Scikit-learn Preprocessor (includes VIF check)
│   ├── models/
│   │   ├── train.py            # RF, GB, ElasticNet training
│   │   ├── evaluate.py         # Metrics, Bootstrap, Permutation
│   │   └── interpret.py        # SHAP, Partial Dependence
│   ├── utils/
│   │   ├── logging.py
│   │   └── validation.py       # Circular validation checks, validate_citations
│   └── report_generator.py     # Generates report from metrics.yaml (enforces no manual entry)
├── data/
│   ├── raw/                    # Raw API dumps (checksummed)
│   ├── processed/              # Cleaned CSV/Parquet
│   └── source_metadata.yaml
├── results/
│   ├── metrics.yaml
│   ├── plots/                  # Parity, SHAP, PDP
│   └── report.md
├── scripts/
│   └── pii_scan.sh             # Repository-Hygiene Agent trigger
├── tests/
│   ├── contract/               # Schema validation tests
│   ├── integration/            # Pipeline end-to-end tests
│   └── unit/                   # Feature engineering logic
└── specs/001-predict-elastic-modulus/
    └── ...
```

**Structure Decision**: A modular monolithic structure within `code/` is selected to facilitate reproducibility and ease of testing on CI. The separation of `data/`, `features/`, `models/`, and `utils/` ensures clear responsibilities and aligns with the Constitution's requirement for traceability.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **ILR Transformation** | Essential to break the compositional singularity (closure constraint) of alloy percentages. | Standard normalization or simple ratios fail to address the geometric constraints of the simplex, leading to singular matrices in regression. |
| **Miedema Exclusion Logic** | Required to prevent circular validation when predicting *Residual* Moduli. | Including Miedema features as predictors for a target defined as `Observed - Miedema` would mathematically guarantee a perfect or near-perfect correlation, invalidating the study. |
| **Grouped Bootstrap** | Necessary to account for chemical similarity (data leakage) between samples sharing the same constituent elements. | Standard bootstrap would overestimate confidence intervals by resampling chemically similar alloys together, violating statistical independence assumptions. |
| **VIF Check** | Required to ensure 'Standard Descriptors' are orthogonal to the Miedema baseline. | Without VIF, the model may implicitly learn the Miedema baseline through correlated features, inflating R² artificially. |
| **Bootstrap CI for Thresholds** | Required to test non-zero thresholds (e.g., R² > 0.3) correctly. | Shifting the null distribution of a permutation test is mathematically incorrect for non-zero thresholds. |