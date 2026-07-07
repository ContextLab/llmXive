# Implementation Plan: Assessing the Stability of Statistical Model Performance Across Data Subsets

**Branch**: `001-assess-model-stability` | **Date**: 2026-06-27 | **Spec**: `specs/001-assessing-the-stability-of-statistical-m/spec.md`

## Summary

This feature implements a rigorous statistical pipeline to assess the stability of three standard machine learning models (Logistic Regression, Random Forest, Linear SVM) across multiple binary classification datasets. The system executes a repeated k-fold cross-validation protocol (multiple evaluations per model-dataset pair) to generate performance distributions. It then quantifies stability via the Coefficient of Variation (CV), correlates CV with dataset properties (sample size, feature count) using a **log-log transformation** to linearize the power-law relationship, and performs a **paired-difference permutation test** to determine if variance differences between models are statistically significant. The entire pipeline is constrained to run on a GitHub Actions free-tier runner (CPU-only, limited RAM, 6h limit).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `scipy`, `requests`, `pyyaml`, `openml`  
**Storage**: Local filesystem (`data/` for raw datasets, `results/` for outputs); no external DB.  
**Testing**: `pytest` (unit tests for statistical logic, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`).  
**Project Type**: Statistical analysis CLI / Pipeline.  
**Performance Goals**: Complete 15 datasets × 3 models × 100 repeats within 6 hours on 2 CPU cores.  
**Constraints**: CPU-only execution; no GPU; memory footprint < 7GB; strict adherence to data hygiene (checksums); **hardcoded dataset IDs** to eliminate selection bias.  
**Scale/Scope**: A set of binary classification datasets (sample size -100k), 3 models, [deferred] total evaluation runs.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Method |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `code/` will pin `random_seed=42` in all sklearn estimators and numpy. Datasets are cached in `data/` with checksums recorded in `state/`. **Hardcoded dataset IDs** ensure consistent selection. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` are restricted to the verified dataset list provided in the prompt (via OpenML IDs). No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Raw data in `data/` is read-only. All transformations (imputation, scaling) occur in memory or write to new derived files. PII scan passed (binary classification datasets used). |
| **IV. Single Source of Truth** | **PASS** | All metrics (CV, correlations, p-values) will be derived strictly from `results/raw_evaluations.csv` and `results/aggregated_metrics.csv`. No hand-typed stats in `paper/`. |
| **V. Versioning Discipline** | **PASS** | `state/` JSON will track `artifact_hashes` for all data and code artifacts. |
| **VI. Statistical Power Adequacy** | **PASS** | Plan explicitly enforces multiple resampling evaluations (multiple folds × multiple repeats) per model-dataset pair as mandated. |
| **VII. Dataset Diversity** | **PASS** | **Task T005b** explicitly validates that the hardcoded dataset list spans the 100-100k sample size range. If the list fails this check, the pipeline halts. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assess-model-stability/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── evaluation_run.schema.yaml
    └── metrics.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-264-assessing-the-stability-of-statistical-m/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, hyperparameters, HARD CODED DATASET IDS
│   ├── dataset_loader.py      # Fetches/caches specific datasets, validates sample size (Constitution VII)
│   ├── evaluator.py           # Repeated K-Fold logic (FR-002)
│   ├── analyser.py            # CV calculation, Log-Log regression, Spearman Correlation, Permutation tests (FR-003, FR-004, FR-005)
│   └── main.py                # Orchestrator
├── data/
│   ├── raw/                   # Cached datasets (checksummed)
│   └── processed/             # Intermediate derived data (if any)
├── results/
│   ├── raw_evaluations.csv    # 4,500 rows (15*3*100)
│   ├── aggregated_metrics.csv # 45 rows (15*3)
│   └── statistical_tests.json # Correlations and p-values
├── tests/
│   ├── unit/
│   │   ├── test_evaluator.py
│   │   └── test_analyser.py
│   └── integration/
│       └── test_pipeline.py
└── requirements.txt
```

**Structure Decision**: Single project structure selected to minimize overhead. The pipeline is linear: Load -> Evaluate -> Analyze. Separation of `evaluator.py` and `analyser.py` ensures the heavy computation (evaluation) is decoupled from the statistical inference, allowing the analysis to be re-run if parameters change without re-computing the [deferred] folds.

## Storage & Schema Alignment

- `dataset_loader.py` validates downloaded data against `contracts/dataset.schema.yaml` (integer `dataset_id`).
- `evaluator.py` writes `results/raw_evaluations.csv` adhering strictly to `contracts/evaluation_run.schema.yaml` (integer `dataset_id`).
- `analyser.py` reads these schemas to compute metrics, ensuring type consistency throughout the pipeline.

## Implementation Tasks (Phased)

### Phase 1: Data Preparation & Validation
- **T001**: Setup environment and dependencies (`requirements.txt`).
- **T002**: Implement `dataset_loader.py` to fetch specific OpenML IDs (Hardcoded).
- **T003**: Implement checksumming and caching logic (Constitution III).
- **T004**: Implement preprocessing (imputation, scaling) inside CV loop.
- **T005**: **Hard Filter**: Validate that the 15 selected datasets fall within 100-100k samples.
- **T005b**: **Spectrum Validation**: Verify the Multiple datasets collectively span the full 100-100k range. If not, raise error. (Addresses Constitution VII).

### Phase 2: Evaluation Engine
- **T014**: Implement `evaluator.py` for Multiple folds × multiple repeats per model.
- **T015**: Write `raw_evaluations.csv` (Schema: `evaluation_run.schema.yaml`).
- **T016**: Unit test: Verify a representative sample of rows per dataset across multiple models.

### Phase 3: Aggregation & Stability Metrics
- **T018**: Implement `analyser.py` aggregation logic (Mean, Std, CV).
  - *Dependency*: Must wait for T014 (Raw Evaluation). **NOT Parallel**.
- **T019**: Implement **Log-Log transformation** and correlation logic.
  - *Note*: Transformation applied to `log(CV)` vs `log(n_samples)` to linearize power-law.
- **T020**: Extract residuals from the theoretical slope.

### Phase 4: Statistical Inference
- **T021**: Compute **Spearman Rank Correlations** (Primary test).
  - *Note*: Spearman used due to small N=15 and non-normal CV distribution. Pearson on log-transformed data is secondary.
- **T022**: **Deviation Analysis**: Calculate observed slope vs theoretical prediction; compute bootstrap CI.
- **T025**: Implement **Paired-Difference Permutation Test** (Variance of differences between models).
  - *Note*: Tests if variance of `|Acc_A - Acc_B|` differs significantly between model pairs.
  - *Dependency*: Must wait for T020 (Residuals/Variance distributions). **NOT Parallel**.
- **T026**: Apply Benjamini-Hochberg correction to all p-values (Correlations & Permutation Tests).
  - *Dependency*: Must wait for T021 and T025. **NOT Parallel**.
- **T027**: Write `statistical_tests.json`.
  - *Dependency*: Must wait for T026. **NOT Parallel**.
- **T028**: Generate final report.
  - *Dependency*: Must wait for T027. **NOT Parallel**.

### Phase 5: Verification
- **T030**: Run full pipeline on GitHub Actions.
- **T031**: Verify runtime < 6h.
- **T032**: Verify reproducibility (re-run, compare checksums).

## Complexity Tracking

No violations detected. The single-project structure is appropriate for a self-contained statistical pipeline. The separation of concerns (Loading, Evaluation, Analysis) addresses the complexity of managing [deferred] evaluation runs while maintaining code clarity. The strict sequential ordering of Phase 4 ensures statistical dependencies are respected.