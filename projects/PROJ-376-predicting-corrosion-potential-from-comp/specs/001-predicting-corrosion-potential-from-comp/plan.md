# Implementation Plan: Predicting Corrosion Potential from Composition and Environment

**Branch**: `001-predict-corrosion-potential` | **Date**: 2026-07-09 | **Spec**: `specs/001-predict-corrosion-potential/spec.md`
**Input**: Feature specification from `/specs/001-predict-corrosion-potential/spec.md`

## Summary

This feature implements a CPU-tractable machine learning pipeline to predict corrosion potential (mV vs SHE) from alloy elemental composition (weight fractions) and environmental conditions (pH, temperature). The approach relies on Random Forest and Gradient Boosting regressors trained on a **GroupKFold (k=5)** strategy to ensure sufficient test set size for statistical validity while preventing alloy-class leakage. The pipeline strictly enforces data hygiene, schema validation, statistical rigor (permutation tests with FDR correction on aggregated predictions), and causal framing (associational only) as mandated by the project constitution and functional requirements.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `requests`, `pytest`, `scipy`  
**Storage**: Local CSV/Parquet files under `data/` (raw and processed), logs under `data/logs/`  
**Testing**: `pytest` (unit tests for data validation, integration tests for pipeline execution)  
**Target Platform**: GitHub Actions `ubuntu-latest` (2 CPU, ~7 GB RAM, no GPU)  
**Project Type**: Computational Research / Data Science Pipeline  
**Performance Goals**: Total runtime ≤ 6 hours; Model training ≤ 30 minutes per model on sample data; Memory usage < 6 GB.  
**Constraints**: No GPU acceleration; No synthetic data fallback; Must halt if < 500 valid records or < 10 specific alloy designations found (unless Nested CV fallback is used).  
**Scale/Scope**: Dataset size estimated based on typical public database intersections (source: NIST public release notes, if available; otherwise deferred to research phase); A set of elemental features.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

### Format Contracts

To ensure internal coherence between storage and contracts:
- **Raw Data**: `data/raw/nist_corrosion.jsonl` MUST conform to `contracts/ingest.schema.yaml`.
- **Processed Data**: `data/processed/corrosion_dataset.parquet` MUST conform to `contracts/dataset.schema.yaml`.
- **Model Output**: `data/processed/model_results.json` MUST conform to `contracts/model_results.schema.yaml`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Strategy |
|-----------|-------------------|-------------------------|
| **I. Reproducibility** | **Compliant** | All random seeds pinned (`random_state=42`); `requirements.txt` pins versions; Docker/GitHub Actions environment isolation enforced. |
| **II. Verified Accuracy** | **Conditional (Pending Data Source Verification)** | All citations in `research.md` will be validated against the "Verified datasets" block. **Critical Note**: The primary dataset (NIST-IR-8200) currently has NO verified URL in the provided block. The pipeline will attempt to fetch from official sources but MUST halt with `DataInsufficientError` if no verified source is found. No fabricated URLs will be used. |
| **III. Data Hygiene** | **Compliant** | Raw data stored immutable in `data/raw/`; processed data in `data/processed/` with checksums recorded in `state/`. No in-place modification. |
| **IV. Single Source of Truth** | **Compliant** | All figures/stats in `paper/` will be generated programmatically from `data/processed/` via `code/` scripts. |
| **V. Versioning Discipline** | **Compliant** | Content hashes for `data/` artifacts tracked in `state/projects/PROJ-376-predicting-corrosion-potential-from-comp.yaml` under the `artifact_hashes` map, as required by the Constitution. |
| **VI. Composition-Environment Feature Integrity** | **Compliant** | Features strictly limited to weight fractions and defined environmental variables (pH, temp). No unverified physical constants. |
| **VII. Leakage-Aware Validation Strategy** | **Compliant** | Split strategy enforced as **GroupKFold (k=5)** to prevent alloy-class leakage while ensuring sufficient test set size for statistical power. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-corrosion-potential-from-comp/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── download_nist.py       # Ingestion script (FR-001, FR-002)
│   ├── preprocess.py          # Cleaning, schema validation, Reference Electrode Normalization (FR-003, FR-011, FR-013)
│   └── split.py               # Group Split logic (FR-004, FR-012)
├── models/
│   ├── train.py               # RF & GB training (FR-005)
│   ├── evaluate.py            # Metrics & Null Baseline (FR-006, FR-014)
│   └── interpret.py           # Permutation importance & PDP (FR-007, FR-008, FR-009)
├── utils/
│   ├── logging.py             # Reproducible logging (FR-010)
│   └── exceptions.py          # DataInsufficientError, SchemaMismatchError
├── tests/
│   ├── test_data_validation.py
│   └── test_pipeline.py
└── requirements.txt

data/
├── raw/
│   └── nist_corrosion.jsonl   # Immutable raw download
├── processed/
│   ├── corrosion_dataset.parquet
│   └── splits/
└── logs/
    └── pipeline.log

state/
└── projects/PROJ-376-predicting-corrosion-potential-from-comp.yaml
```

**Structure Decision**: Single project structure selected to align with the "Computational Research" nature of the feature. All data processing and modeling are contained within `code/` to ensure the `data/` directory remains a clean artifact store. This supports the "Single Source of Truth" principle by making the transformation pipeline explicit and version-controlled.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **GroupKFold (k=5) vs. Single Split** | Required to ensure test set size is large enough for statistical power (R², RMSE, permutation tests) while preventing alloy leakage. A single LOSO split on a limited number of records would yield a test set too small for valid inference.. | Single split would result in < 50 test samples, making R² and permutation p-values unstable and invalid. |
| **Strict Halt on < 500 Records** | **Compliance Requirement (FR-014)**: The spec mandates a halt if < 500 records. This is not a violation but a mandatory constraint to ensure statistical power. | Synthetic data fallback or scope reduction is explicitly forbidden by the spec to maintain scientific integrity. |
| **Permutation Test on Aggregated Predictions** | Required to ensure the null distribution is continuous and p-values are stable. Testing on a single small test set would yield discrete, unstable p-values. | Testing on a single small test set would result in high variance and invalid significance claims. |
| **Compositional Data Handling** | Required due to the sum-to-one constraint of weight fractions (multicollinearity). Standard permutation tests assume independence. | Ignoring compositional constraints would lead to misleading importance scores and inflated false positives. |

## Data Acquisition Strategy

- **Primary Source**: NIST Corrosion Database (NIST-IR-8200).
- **Status**: **NO verified URL** currently exists in the provided "Verified datasets" block.
- **Action**: The `download_nist.py` script will attempt to locate the official NIST public repository. If no verified, reachable source is found, the pipeline MUST halt with a `DataInsufficientError` and a clear message: "Required dataset NIST-IR-8200 not found in verified sources. Pipeline halted."
- **Fallback**: None. Synthetic data is explicitly forbidden.