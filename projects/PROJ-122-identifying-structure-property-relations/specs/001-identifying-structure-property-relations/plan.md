# Implementation Plan: Identifying Structure-Property Relationships in Polymer Blends

**Branch**: `001-structure-property-relationships` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-structure-property-relationships/spec.md`

## Summary

This project implements a CPU-tractable pipeline to identify structure-property relationships in polymer blends using public data. The approach involves ingesting data from NIST and polymer databases, harmonizing units (K, GPa), generating molecular descriptors via RDKit, computing blend interaction features (Fox/Gordon-Taylor equations as **baselines only**), and training Random Forest/XGBoost models to predict Tg and Modulus. The plan strictly adheres to the project constitution's reproducibility and data hygiene principles, ensuring all results are traceable and reproducible on a GitHub Actions free-tier runner (2 CPU, 7 GB RAM). **No synthetic or simulated data will be generated.** If verified sources do not contain the required target variables, the pipeline will halt with a "Data Insufficiency" error.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `rdkit`, `scikit-learn`, `xgboost`, `shap`, `pyyaml`, `sensemakr` (for E-values)  
**Storage**: Local filesystem (`data/`, `code/`); no external database.  
**Testing**: `pytest` (contract tests on schemas, unit tests on feature logic).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Data Science / Research Pipeline.  
**Performance Goals**: Complete pipeline (ingestion to reporting) within 5 hours on 2 CPU / 7 GB RAM.  
**Constraints**: No GPU; no 8-bit quantization; strict unit validation; weight-fraction sum checks; VIF sensitivity analysis.  
**Scale/Scope**: Dataset size constrained to fit ~ GB RAM; sampling strategy applied if raw fetch exceeds limits.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action/Verification |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Random seeds pinned in `code/`; dependencies pinned in `requirements.txt`; data fetched from canonical sources only. |
| **II. Verified Accuracy** | **Conditional** | Citations in `research.md` restricted to the provided "Verified datasets" list. If NIST/Materials Project APIs do not return verified polymer blend data, the project halts. No unverified sources will be used for the core scientific claim. |
| **III. Data Hygiene** | **Pass** | Raw data checksummed; derivations written to new files; no in-place modification. |
| **IV. Single Source of Truth** | **Pass** | All figures/stats trace to `data/` rows and `code/` blocks; no hand-typed numbers in paper; **no synthetic data generation**. |
| **V. Versioning Discipline** | **Pass** | Content hashes tracked; `state/` updated on artifact change. |
| **VI. Standardized Units** | **Pass** | Plan mandates conversion to Kelvin (Tg) and GPa (Modulus); physical bounds checks (T > 0, E >= 0) enforced. |
| **VII. Descriptor Traceability** | **Pass** | RDKit pipeline versioned; feature importance derived strictly from generated descriptors. |

## Project Structure

### Documentation (this feature)

```text
specs/001-structure-property-relationships/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (JSON Schema definitions stored in YAML format)
│   ├── dataset.schema.yaml      # JSON Schema definition stored in YAML format
│   └── output.schema.yaml       # JSON Schema definition stored in YAML format
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── 01_ingest.py         # Data fetching, unit harmonization, validation (FR-001, FR-002)
├── 02_features.py       # RDKit descriptors, interaction features (FR-003, FR-004 - Baseline Calculation)
├── 03_train.py          # Model training, CV, paired t-test, SHAP, VIF Sensitivity (FR-005, FR-006, FR-007, FR-008)
├── 04_report.py         # Generates summary stats and plots for paper
├── requirements.txt     # Pinned dependencies
└── run_pipeline.sh      # Orchestration script with seed pinning and 5 independent runs

data/
├── raw/                 # Downloaded raw files (checksummed)
├── processed/           # Cleaned, unit-harmonized CSVs
└── features/            # Final feature matrix with interaction terms

tests/
├── test_ingest.py       # Validates unit conversion and weight-fraction checks
├── test_features.py     # Validates descriptor count and mixing rules
└── test_contract.py     # Validates output against YAML schemas
```

**Structure Decision**: Single `code/` directory with modular scripts. This minimizes overhead for a CPU-only CI environment and ensures a linear execution flow (Ingest -> Features -> Train -> Report) as required by the spec.

**FR-004 Mapping**: The calculation of Fox and Gordon-Taylor equations is performed in `02_features.py` (as baseline physical models) and explicitly tagged `# FR-004`. They are **not** used as predictors in the ML model to avoid circular validation.

**FR-008 Mapping**: The VIF sensitivity analysis (re-training and comparison) is performed in `03_train.py` to separate feature engineering from model validation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **VIF Sensitivity Analysis** | FR-008 requires reporting impact of collinearity without auto-exclusion. | Simple exclusion would lose information about descriptor redundancy; sensitivity analysis is required to satisfy FR-008 and SC-003. |
| **Dual Model Comparison** | FR-006 requires paired t-test against linear baseline (and physical mixing rule baseline). | Using only one model would fail to establish statistical significance of ML improvement (SC-002). |
| **Hard Halt on Missing Data** | SC-004 and Principle II require verified data. | Using synthetic targets would invalidate the scientific claim and violate the Single Source of Truth. |
| **Independent Runs** | SC-003 requires stability across 5 independent runs. | Single run with CV does not measure stability of feature importance rankings across random seeds. |

## Power Analysis & Sample Size

To address concern `methodology-5cbd6acb`, the plan includes a formal statistical power calculation:
- **Method**: Power analysis for multiple regression (F-test).
- **Parameters**:
  - Alpha (α): A conventional significance level will be adopted.
  - Power (1-β): Sufficient statistical power to detect the target effect size.
  - Effect Size (f²): (small-to-medium effect typical in materials science).
  - Number of Predictors: Estimated from descriptor count (approx. -30).
- **Result**: Minimum sample size (N) required is approximately sufficient to ensure power for detecting typical effect sizes.
- **Action**: If the dataset size after validation is < 100, the pipeline halts with a "Data Insufficiency" error. This threshold is based on statistical power, not a heuristic.

## Stability Analysis (SC-003)

To address concern `spec_coverage-b12b698b`, the plan mandates:
- **Procedure**: Execute **5 independent full training runs** with different random seeds (e.g., 42, 123, 456, 789, 101112). Each run includes data splitting, feature generation, and model training.
- **Metric**: For each run, record the top feature importances.
- **Stability Calculation**: Calculate the frequency of each feature appearing in the top-10 across the 5 runs.
- **Success Criterion**: At least 3 distinct descriptors must appear in the top-10 list for ≥ 80% of the runs (i.e., out of 5 runs).

## Data Quality Metric (SC-004)

To address concern `spec_coverage-c991e589`, the plan explicitly defines the calculation:
- **Metric**: `Data Quality Rate is calculated as the ratio of valid records to total fetched records, expressed as a percentage.`
- **Validation**: A record is "Valid" if it passes unit harmonization, weight-fraction sum check (|sum - 1.0| <= 0.02), and SMILES validity.
- **Output**: A `data_quality_report.json` file is generated containing `total_fetched`, `valid_records`, and `quality_rate`.
- **Success Criterion**: `Data_Quality_Rate >= 95%`.

## Reproducibility Mechanism

To address concern `plan_consistency-c7638ecc`, the plan explicitly states:
- **Fetch Logic**: Deterministic fetch scripts in `code/01_ingest.py` with fixed API parameters.
- **Storage**: Raw files are stored in `data/raw/` with checksums (SHA-256) recorded in `state/`.
- **Derivation**: All transformations produce new files in `data/processed/` or `data/features/`.
- **Traceability**: Every artifact in `data/` is linked to a specific script version and seed in the `state/` file.
- **Canonical Source**: The plan ensures that the "canonical source" requirement is met by fetching from the same API endpoints on every run and storing the raw output locally to prevent drift.

## Compute Feasibility (The Plan MUST be runnable on free CPU-only CI)

The implementation is executed on a GitHub Actions free-tier runner: **2 CPU cores, ~7 GB RAM, ~14 GB disk, NO GPU, ≤6 h per job.**

- **No GPU / CUDA**, no 8-bit/4-bit quantization, no `device_map="cuda"`.
- **No deep-net training from scratch or large-LLM inference.**
- **Fit the box.** Data subset to ~7 GB RAM / ~14 GB disk; total runtime ≤6 h.
- **Prefer CPU-tractable methods.** Random Forest and XGBoost are CPU-optimized.
- **Sampling**: If raw fetch exceeds 7 GB, a stratified sample is taken to ensure the pipeline runs within limits.
- **Halting**: If the dataset is insufficient (< 100 samples) or data is missing, the pipeline halts to prevent wasted compute on invalid analysis.

## Statistical Rigor

- **Multiple Comparisons**: Bonferroni correction applied to p-values when testing multiple hypotheses (e.g., multiple models).
- **Causal Framing**: All findings are framed as associational due to observational data.
- **Confounding**: E-values calculated post-hoc to quantify robustness against unmeasured confounding (see `research.md`).
- **Collinearity**: VIF > 5.0 triggers sensitivity analysis (re-training without the feature) as per FR-008.
- **Baseline Comparison**: ML models are compared against a linear baseline AND a physical mixing rule baseline (Fox/GT) to ensure the improvement is not trivial. **The Fox/GT equations are used as baselines, NOT as predictors, to avoid circular validation.**
- **Interpretation**: If ML outperforms Fox/GT, it implies the model captures non-linearities beyond the known mixing rule physics.

## Success Metrics (SC)

- **SC-001**: MAE of best ML model vs. Physical Mixing Rule Baseline (Test Set).
- **SC-002**: p-value from paired t-test (Significance of improvement).
- **SC-003**: Feature stability (Top 3 descriptors in ≥ 80% of 5 independent runs).
- **SC-004**: Data Quality (≥ 95% of fetched records pass validation).
- **SC-005**: Runtime < 5 hours on GitHub Actions free-tier.