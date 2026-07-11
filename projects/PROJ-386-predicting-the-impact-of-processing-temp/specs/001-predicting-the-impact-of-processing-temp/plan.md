# Implementation Plan: Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys

**Branch**: `001-gene-regulation` | **Date**: 2026-07-02 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project implements a CPU-tractable machine learning pipeline to predict aluminum alloy grain size based on processing temperature and chemical composition. The approach involves strict data validation against schema requirements (FR-001), generation of interaction features (FR-002), baseline linear modeling (FR-003), and non-linear Random Forest modeling with grid search (FR-004). The pipeline includes mandatory sensitivity analysis (FR-005), collinearity diagnostics (FR-006), and confounder assessment (FR-008), all executed within a 5-hour limit on a 2-core CPU runner.

**Critical Feasibility Note**: The project relies on public datasets (NOMAD) that may lack experimental rolling parameters. If the schema pre-check fails, the project halts with `E_DATA_MISSING`, which is treated as a valid scientific conclusion regarding data availability.

## Technical Context

**Language/Version**: Python 3.10 (Standard for scientific stack compatibility)  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `requests`, `pyyaml`, `evalues` (CPU-only, no GPU)  
**Storage**: Local CSV/JSON artifacts in `data/` and `artifacts/`  
**Testing**: `pytest` for unit tests; integration tests via pipeline execution  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, ~7GB RAM, No GPU)  
**Project Type**: Data Science Pipeline / CLI  
**Performance Goals**: Pipeline execution ≤ 5 hours; Peak RAM ≤ 6.5 GB; Grid search timeout fallback ≤ 4h  
**Constraints**: No GPU usage; No large model training; Strict schema pre-checks before download; Observational framing (no causal claims)  
**Scale/Scope**: Public dataset ingestion (NOMAD); Single alloy series stratification; Process Type Filtering  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`. External datasets fetched from canonical URLs only. `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | PASS | All dataset citations in `research.md` will be validated against the "# Verified datasets" block. No fabricated URLs. |
| **III. Data Hygiene** | PASS | Raw data downloaded to `data/raw/` with checksums. Derived data in `data/processed/`. No in-place modification. |
| **IV. Single Source of Truth** | PASS | All metrics (R², MAE) in `paper/` will be generated programmatically from `code/` outputs. No hand-typed numbers. |
| **V. Versioning Discipline** | PASS | **New**: A dedicated `hash_artifacts.py` script will compute SHA-256 hashes for all files in `data/` and update `state/...yaml` with `artifact_hashes` map after every pipeline run. |
| **VI. Composition-Temperature Interaction** | PASS | Plan explicitly includes `Temperature × %Element` feature generation (FR-002) and Random Forest tuning for non-linear effects (FR-004). |
| **VII. Industrial Rolling Context** | PASS | **New**: Data will be filtered by `process_type` (Rolling vs. Casting/SPD) before modeling. Data splits will be stratified by `source_study` (if available) to prevent leakage of processing conditions, not by alloy series. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
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
projects/PROJ-386-predicting-the-impact-of-processing-temp/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, timeouts, seeds
│   ├── data/
│   │   ├── __init__.py
│   │   ├── download.py        # FR-001: Schema pre-check & download (Validates against contracts/dataset.schema.yaml)
│   │   ├── preprocess.py      # FR-002: Interaction features, normalization, Process Type Filtering
│   │   └── validate.py        # FR-006: Collinearity check
│   ├── models/
│   │   ├── __init__.py
│   │   ├── baseline.py        # FR-003: Linear Regression (Stratified by source_study)
│   │   ├── non_linear.py      # FR-004: Random Forest + Grid Search (Stratified by source_study)
│   │   ├── sensitivity.py     # FR-005: Threshold sweep
│   │   └── confounder.py      # FR-008: Confounder analysis & E-value calculation
│   └── main.py                # Orchestrator (timeout handling, versioning)
├── data/
│   ├── raw/                   # Downloaded CSVs (checksummed)
│   └── processed/             # Cleaned, engineered CSVs
├── artifacts/
│   ├── models/                # Pickled models
│   └── reports/               # JSON reports (collinearity, confounders)
├── tests/
│   ├── test_data.py
│   ├── test_models.py
│   └── test_pipeline.py
└── requirements.txt
```

**Structure Decision**: Single project structure (`code/`) selected. The project is a sequential data pipeline, not a web service or mobile app. This minimizes overhead and ensures all scripts run in the same environment, crucial for the 5-hour time limit and memory constraints.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Timeout Fallback Mechanism** | FR-004 requires a fallback if grid search exceeds 4h. | A simple single-pass run might miss optimal hyperparameters; the fallback ensures robustness without risking timeout. |
| **Schema Pre-Check** | FR-001 requires halting if variables are missing *before* download. | Downloading first wastes bandwidth and time on incompatible sources (e.g., Materials Project lacks rolling temp). |
| **Process Type Filtering** | Constitution Principle VII requires 'Industrial Rolling Context'. | Without filtering, the model may learn artifacts from casting or SPD data, invalidating the specific industrial claim. |
| **Conditional Model Selection (N < 100)** | Methodology requires statistical validity. | Running Random Forest on small samples (N < 100) leads to overfitting and invalid R² deltas. |
| **E-value Calculation** | FR-008 requires confounder analysis. | If proxies are missing, 'N/A' is insufficient; E-values provide a theoretical sensitivity bound. |

## Implementation Phases

### Phase 0: Data Ingestion & Validation
1.  **Download**: Fetch NOMAD structure CSV.
2.  **Schema Pre-Check**: Validate presence of `rolling_temperature`, `grain_size`, `composition`, and `process_type` using `contracts/dataset.schema.yaml`.
3.  **Filter**: Exclude non-rolling processes (Casting, SPD).
4.  **Sample Size Check**:
    *   If $N < 50$: Halt with `E_INSUFFICIENT_DATA`.
    *   If $50 \le N < 100$: Disable `non_linear.py` (Random Forest) and proceed only with `baseline.py` (Linear).
    *   If $N \ge 100$: Proceed with full pipeline.
5.  **Hashing**: Compute SHA-256 of raw and processed data, update `state/...yaml`.

### Phase 1: Feature Engineering & Baseline
1.  **Interaction Features**: Generate `Temp × Element` features.
2.  **Normalization**: Scale numeric features.
3.  **Stratified Split**: Split data by `source_study` (or random if missing, with warning) into Train/Val/Test.
4.  **Linear Model**: Train OLS with interaction terms. Log R².

### Phase 2: Non-Linear Modeling (Conditional)
*Only executed if $N \ge 100$.*
1.  **Random Forest**: Train with grid search (n_estimators: 50-100, max_depth: 5-10).
2.  **Timeout**: 4-hour limit. Fallback to default params if exceeded.
3.  **Metrics**: Log R², MAE, RMSE.
4.  **R² Delta**: Calculate $\Delta R^2 = R^2_{RF} - R^2_{Linear}$.

### Phase 3: Diagnostics & Sensitivity
1.  **Collinearity**: Detect $|r| > 0.8$. Report chemical couplings as joint effects.
2.  **Sensitivity**: Sweep thresholds {0.01, 0.05, 0.1}. Calculate stability score.
3.  **Confounder Analysis**:
    *   If proxies exist: Compare R².
    *   If proxies missing: Calculate E-value for the observed effect size.
4.  **Final Hashing**: Update state with final artifact hashes.

## Compute Feasibility
*   **Hardware**: 2 CPU cores, 7GB RAM, No GPU.
*   **Strategy**:
    *   Use `scikit-learn` (CPU optimized).
    *   Limit grid search to small ranges.
    *   Implement a 4-hour timeout for the training step. If exceeded, fallback to default parameters.
    *   Sample data if $N > 10,000$ to ensure fit within 7GB RAM.
    *   **Critical**: If NOMAD lacks required columns, the script exits immediately, saving compute time.