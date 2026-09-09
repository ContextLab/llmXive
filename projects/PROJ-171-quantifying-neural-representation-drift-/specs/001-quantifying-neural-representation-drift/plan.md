# Implementation Plan: Quantifying Neural Representation Drift During Skill Learning

**Branch**: `001-quantify-neural-drift` | **Date**: 2026-10-27 | **Spec**: `specs/001-quantify-neural-drift/spec.md`
**Input**: Feature specification from `/specs/001-quantify-neural-drift/spec.md`

## Summary

This project implements a reproducible pipeline to quantify the rate of neural representational drift (`b`) during motor skill learning and correlate it with behavioral learning speed. The approach ingests raw or pre-sorted electrophysiology data and behavioral logs, filters for stable units (≥80% session presence), excludes performance-modulated neurons, and computes pairwise Pearson distances to generate Representational Dissimilarity Matrices (RDMs). 

**Dual-Model Strategy**: To satisfy both the Project Constitution (Principle VII) and the Functional Spec (FR-005), the pipeline implements a **Primary** Exponential decay model (`drift(t) = a·exp(−b·t) + c`) and a **Fallback** Linear model (`drift(t) = a + b·t`). The Exponential model is the primary metric per Constitution VII. If the Exponential fit fails to converge, the system falls back to the Linear model to satisfy FR-005. Both models' parameters are reported, with the Exponential 'b' being the primary result and the Linear 'b' being a secondary comparability metric. 

The pipeline includes robust handling of missing behavioral data via linear interpolation (with fallback exclusion), permutation testing for significance, and sensitivity analysis across stability thresholds and distance metrics. All computations are designed for a CPU-first environment (2 cores, 7 GB RAM) using `scikit-learn`, `statsmodels`, and `pandas`.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas>=2.0`, `numpy>=1.24`, `scikit-learn>=1.3`, `statsmodels>=0.14`, `scipy>=1.11`, `openneuro-dataset` (via `datasets`), `matplotlib`, `seaborn`  
**Storage**: Local file system (Parquet for intermediate matrices, CSV for results), no persistent DB.  
**Testing**: `pytest` with `pytest-cov` and `pytest-randomly` for reproducibility.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM).  
**Project Type**: Data analysis pipeline / CLI tool.  
**Performance Goals**: Full pipeline execution < 6 hours; memory footprint < 7 GB; linear fit convergence < 5% error on synthetic ground truth.  
**Constraints**: CPU-only execution; no GPU dependencies; strict adherence to unit stability criteria (≥80%); missing data imputation via linear interpolation; multiple-comparison correction (Bonferroni) for metric sweeps.  
**Scale/Scope**: Up to 50 subjects, 10 training days per subject, ~500 units per day (streamed).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, fixed random seeds, and re-runnable scripts. Synthetic data generation for ground truth validation ensures reproducibility. |
| **II. Verified Accuracy** | **PASS** | All dataset sources (OpenNeuro, HuggingFace) are verified in `research.md`. Citations will be validated by the Reference-Validator Agent. |
| **III. Data Hygiene** | **PASS** | Plan specifies checksumming of raw data, immutable derivations (new filenames for processed matrices), and PII exclusion. |
| **IV. Single Source of Truth** | **PASS** | All figures and statistics will trace back to specific rows in `data/processed/` and code blocks in `src/`. No hand-typed values. |
| **V. Versioning Discipline** | **PASS** | Content hashes will be recorded in `state/` for every artifact. |
| **VI. Neural Data Integrity** | **PASS** | Plan explicitly enforces the ≥80% unit stability criterion and exclusion of performance-modulated neurons as per Constitution VII. |
| **VII. Computational Robustness** | **PASS** | Plan prioritizes CPU-tractable methods. **Hierarchy**: Exponential model is Primary (Constitution VII); Linear model is Fallback (FR-005). This resolves the conflict by satisfying the Constitution's primary requirement while maintaining the Linear model as a mandatory fallback. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-neural-drift/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── neural_population.schema.yaml
│   ├── drift_result.schema.yaml
│   └── correlation_result.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── main.py              # CLI entry point
├── config.py            # Configuration and constants (e.g., STABILITY_THRESHOLD)
├── data/
│   ├── __init__.py
│   ├── loader.py        # Data ingestion (OpenNeuro/HF), streaming, validation
│   ├── preprocessor.py  # Unit filtering, performance-modulated exclusion, alignment
│   └── imputer.py       # Linear interpolation for missing behavioral logs
├── analysis/
│   ├── __init__.py
│   ├── drift.py         # RDM generation, Exponential/Linear fitting, drift rate extraction
│   └── correlation.py   # Pearson correlation, Permutation test, LMM fitting
├── validation/
│   ├── __init__.py
│   ├── sensitivity.py   # Threshold sweeps, metric comparison, exclusion sensitivity
│   └── robustness.py    # Split-half reliability
├── utils/
│   ├── __init__.py
│   ├── metrics.py       # Distance metrics (Pearson, Cosine, Mahalanobis)
│   └── plots.py         # Visualization generation
└── models/
    └── schemas.py       # Pydantic models for validation (optional)

tests/
├── __init__.py
├── contract/            # Schema validation tests
├── integration/         # End-to-end pipeline tests
└── unit/                # Unit tests for specific functions (e.g., imputer, drift_fitter)

data/
├── raw/                 # Downloaded raw data (checksummed)
├── processed/           # Intermediate matrices (NeuralPopulationMatrix, RDM)
└── results/             # Final outputs (drift rates, correlation stats, plots)

docs/
└── paper/               # Generated figures and draft text
```

**Structure Decision**: Single project structure selected to minimize overhead for a data analysis pipeline. All modules are contained within `src/` with clear separation of concerns (data, analysis, validation). This supports the CPU-first constraint by avoiding distributed computing complexity.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed without violations. | N/A |

## Phase Breakdown (Methodological Rigor)

### Phase 0: Data Acquisition & Validation
- **Goal**: Secure open, verified datasets and validate variable availability.
- **FR Coverage**: FR-001, FR-009.
- **Method**: Stream `OpenNeuro` dataset (verified URL) via `datasets` library. Validate presence of `spike_counts`, `trial_success`, `session_id`, `day_index`.
- **Power Check**: **HALT** if N < 15 subjects. Log error: "Insufficient power (N < 15). Analysis cannot proceed."
- **Constraint**: No access-gated data; if missing variables, halt with explicit error. If no ephys dataset is found, reframe study as method validation using synthetic data only.

### Phase 1: Preprocessing & Population Matrix Construction
- **Goal**: Clean data, filter units, handle missing behavior.
- **FR Coverage**: FR-002, FR-003, FR-009 (Imputation).
- **Method**:
  - **Filtering**: Count presence per unit across sessions; exclude if count < 0.8 * total_sessions (Configurable).
  - **Exclusion**: Identify and exclude performance-modulated neurons (Pearson correlation between firing rate and trial success > 0.3, p < 0.05).
  - **Imputation**: Apply linear interpolation for missing `trial_success` logs (as defined in `data-model.md` and `input_schema.schema.yaml`). **Fallback**: If gap > 2 days or at boundaries, flag subject as "insufficient data" and exclude from correlation analysis.
  - **Alignment**: Aggregate spike counts into 20ms bins using raw timestamps from `loader.py` to ensure resolution is maintained in `NeuralPopulationMatrix`.
  - **Dimensionality**: Apply **Global PCA** projection to all daily matrices to ensure a common subspace before distance calculation, addressing varying unit counts.
  - Output: `NeuralPopulationMatrix` (Units × Conditions) per day.

### Phase 2: Drift Quantification (Primary & Fallback)
- **Goal**: Compute RDMs and extract drift rates.
- **FR Coverage**: FR-004, FR-005, FR-007 (Metric sweep).
- **Method**:
  - Compute pairwise Pearson distance (1 - r) between daily population matrices → RDM (upper triangle).
  - **Primary Fit**: Exponential model `drift(t) = a·exp(−b·t) + c`. Extract decay constant `b`.
  - **Fallback**: If Exponential fit fails (non-convergence), fit Linear model `drift(t) = a + b·t`. If Linear also fails, return constant fit with flag "non-drifting".
  - **Validation**: Permutation test (shuffling day labels) on the regression slope to address non-independence of RDM entries.
 - **Sensitivity**: Sweep stability thresholds (70%, 75%, 80%, 85%, [deferred]) and distance metrics (Pearson, Cosine, Mahalanobis). Apply Bonferroni correction (p_corrected = p_raw * n_metrics) if n_metrics > 1.
  - **Circularity Check**: Clarify that Exponential and Linear models are fit independently; Linear is not used to validate Exponential, but reported for comparability. Primary validation is against synthetic ground truth.

### Phase 3: Behavioral Correlation & Hypothesis Testing
- **Goal**: Correlate drift with learning speed.
- **FR Coverage**: FR-006, FR-007.
- **Method**:
  - Calculate "time to reach success" from interpolated behavioral logs.
  - Compute Pearson `r` between drift rate `b` (Exponential) and learning speed.
  - **Permutation Test**: 10,000 shuffles. Null Hypothesis: "No correlation between drift rate and learning speed." Test Statistic: "Pearson r".
  - **LMM**: Fit Linear Mixed-Effects Model (`learning_speed ~ drift_rate + (1 | subject)`) as required by FR-006, despite aggregate data, to account for potential hierarchical structure.
  - **Power Check**: If N < 15, **HALT** (see Phase 0).
  - Output: `CorrelationResult` records as defined in `data-model.md` and `correlation_result.schema.yaml`.

### Phase 4: Robustness & Reporting
- **Goal**: Validate stability and generate outputs.
- **FR Coverage**: FR-008, SC-001 to SC-005.
- **Method**:
  - **Exclusion Sensitivity**: Run analysis with and without excluding performance-modulated neurons. Compare correlations to quantify bias.
  - **Imputation Sensitivity**: Run analysis with and without linear interpolation. Compare results. Acceptance: If sign/significance changes, flag as "Imputation Sensitive".
  - **Threshold Sweep**: Sweep stability threshold across {0.70, 0.75, 0.80, 0.85, 0.90}. Record `stability_threshold` in `DriftResult` entity. Confirm this range covers boundary behaviors required by US-3.
  - **Metric Comparison**: Compare drift rates across Pearson, Cosine, Mahalanobis. Stability Criterion: Sign of correlation with learning speed must remain consistent.
  - **Synthetic Validation**: Generate data with known drift `b_gt` (rotating tuning curves). Verify recovered `b` is within 5% error.
  - **Memory Check**: Use `tracemalloc` to log peak memory usage at 1-second intervals. Fail if peak > 7 GB.
  - **Output**: Generate plots (sensitivity curves, correlation scatter) to `docs/paper/` and write results to `data/results/`.
