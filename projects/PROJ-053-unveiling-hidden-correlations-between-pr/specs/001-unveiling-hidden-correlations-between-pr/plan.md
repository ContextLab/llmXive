# Implementation Plan: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

**Branch**: `001-unveiling-hidden-correlations` | **Date**: 2026-07-14 | **Spec**: `specs/001-unveiling-hidden-correlations/spec.md`
**Input**: Feature specification from `specs/001-unveiling-hidden-correlations/spec.md`

## Summary

This project implements a Gaussian Process Regression (GPR) pipeline to model **associational** non-linear relationships between additive manufacturing (AM) processing parameters (laser power, scan speed, layer thickness) and mechanical properties (yield strength, ductility). The system ingests public or user-provided AM alloy datasets, performs rigorous preprocessing (median imputation, min-max normalization **fit on training data only**, one-hot encoding), trains a GPR model with an RBF kernel using -fold cross-validation, and generates uncertainty-aware visualizations (contour plots, heatmaps) to identify high-priority experimental regimes.

**Critical Scope Note**: This project does **not** claim causal discovery. All claims are framed as associational ("Laser Power is associated with Yield Strength"). The "optimization regimes" identified are statistical suggestions for data-sparse regions, not causal prescriptions. The implementation is constrained to run on free-tier CPU-only CI runners (limited cores, ~7 GB RAM) and adheres strictly to the project constitution regarding reproducibility, data hygiene, and verified accuracy.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `requests`  
**Storage**: Local CSV/JSON artifacts (no external database); raw data cached in `data/raw/`, processed data in `data/processed/`.  
**Testing**: `pytest` (unit tests for preprocessing, integration tests for model training pipeline).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Data Science / Scientific Computing Library  
**Performance Goals**: Total runtime ≤ 6 hours; memory usage ≤ 7 GB; model training time ≤ 30 minutes for N=500 samples.  
**Constraints**: No GPU usage; no deep learning frameworks (PyTorch/TensorFlow); strict adherence to CPU-tractable methods; **no automated download for the primary AM dataset** (requires manual placement due to lack of verified source).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Random seeds are pinned to ensure reproducibility. in `code/`; `requirements.txt` pins all versions; data fetch logic uses canonical URLs (or manual placement). |
| **II. Verified Accuracy** | CONDITIONAL PASS | All external dataset URLs cited in `research.md` are from the verified list. The primary AM dataset has **NO verified source**; the plan explicitly requires manual data placement and user acknowledgment of provenance (see Risks). |
| **III. Data Hygiene** | PASS | Raw data preserved in `data/raw/`; checksums recorded in `state/...yaml`; transformations produce new files in `data/processed/`. |
| **IV. Single Source of Truth** | PASS | All figures/stats in paper trace to `data/processed/` and `code/`; no hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Content hashes used for artifacts; state file updated on artifact changes. |
| **VI. Non-Linear Process-Property Mapping** | PASS | GPR with RBF kernel explicitly selected to capture non-linearities and epistemic uncertainty. |
| **VII. Physical Measurement Independence** | PASS | Plan includes Task 0.2 (Source Independence Validation) to verify predictors and targets are distinct streams and not tautologically derived. |

## Project Structure

### Documentation (this feature)

```text
specs/001-unveiling-hidden-correlations/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-053-unveiling-hidden-correlations-between-pr/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py
│   ├── data/
│   │   ├── download.py        # Dataset ingestion (FR-001) - Validates against contracts/dataset.schema.yaml
│   │   ├── preprocess.py      # Cleaning, imputation, encoding (FR-002) - Validates against contracts/dataset.schema.yaml
│   │   └── schema_validator.py
│   ├── models/
│   │   ├── gpr_trainer.py     # GPR training, CV, hyperparameter opt (FR-003)
│   │   ├── baseline_trainer.py # Linear Regression baseline for SC-001
│   │   └── metrics.py         # R2, RMSE, MAE calculation (FR-004)
│   ├── viz/
│   │   ├── contour_plots.py   # Contour & uncertainty heatmaps (FR-005)
│   │   └── importance.py      # Permutation importance (FR-006)
│   └── main.py                # Orchestration script
├── data/
│   ├── raw/                   # Downloaded raw CSVs
│   └── processed/             # Normalized, encoded CSVs
├── tests/
│   ├── unit/
│   │   ├── test_preprocess.py
│   │   └── test_gpr.py
│   └── integration/
│       └── test_pipeline.py
├── state/
│   └── projects/PROJ-053-.../artifact_hashes.yaml
└── docs/
    └── paper.md
```

**Structure Decision**: Single project structure selected to align with the scientific workflow (download -> preprocess -> model -> viz). No separate frontend/backend required; the output is a set of artifacts (CSV, JSON, PNG) and a report.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **GPR over Linear Regression** | The project constitution (Principle VI) and spec require capturing non-linear microstructural evolution. Linear models would fail to identify actionable optimization regimes. | Linear regression is simpler but scientifically invalid for this specific hypothesis regarding non-linear AM relationships. (Note: Linear Regression is used ONLY as a baseline for SC-001). |
| **Uncertainty Quantification** | Required by FR-007 and US-3 to identify data-sparse regimes. | Point-estimate models (e.g., standard Random Forest without uncertainty) cannot flag regions requiring further experimentation. |
| **CPU-Only Constraint** | Mandatory for free-tier CI execution. | GPU-accelerated libraries (PyTorch, TensorFlow) are excluded to ensure the job completes within 6 hours on 2 cores. |

## Implementation Phases & Tasks

### Phase 0: Data Ingestion & Validation (FR-001, FR-002, FR-007)

**Task 0.1: Dataset Download / Placement**
- **Action**: Check for `data/raw/am_data.csv`. If missing, log error: "No verified source found for AM-Machine-Learning; expecting manual data placement."
- **Validation**: Validate loaded CSV against `contracts/dataset.schema.yaml` (Raw Dataset Schema).
- **Constraint**: If automated download is attempted, it must fail gracefully with instructions for manual placement.

**Task 0.2: Source Independence & Tautology Check**
- **Action**: Verify that predictor variables (process settings) and target variables (mechanical properties) originate from distinct data streams.
- **Check**: Flag if the dataset appears to be a curated list of "successful prints" only (tautological correlation).
- **Check**: Explicitly exclude derived features (e.g., `energy_density = power / (speed * thickness)`) to prevent perfect multicollinearity.

**Task 0.3: Column Verification**
- **Action**: Ensure required columns (`laser_power`, `scan_speed`, `layer_thickness`, `yield_strength`, `ductility`) are present.
- **Action**: If `alloy_type` is present, prepare for one-hot encoding.

### Phase 1: Preprocessing & Data Hygiene (FR-002)

**Task 1.1: Imputation**
- **Action**: Replace `NaN` in numeric columns with column median. Log count of imputed values.

**Task 1.2: Encoding**
- **Action**: Convert `alloy_type` to binary columns (e.g., `is_Ti-6Al-4V`). Drop original column.

**Task 1.3: Training-Set Normalization (CRITICAL)**
- **Action**: **DO NOT** normalize the entire dataset before splitting.
- **Method**: Split data into training and testing subsets with a majority-minority partition. -> Fit MinMaxScaler on **TRAIN** set -> Transform **TRAIN** and **TEST** sets separately.
- **Metadata**: Record `min` and `max` values from the **TRAIN** set in `data/processed/normalization_bounds.json` to enable physical regime mapping later.

**Task 1.4: Zero Variance Check**
- **Action**: Detect columns with `std == 0`. Log warning and drop.

**Task 1.5: Sample Count Check**
- **Action**: If `N < 50`, halt with error: "Insufficient data for GPR training; minimum 50 samples required."

### Phase 2: Modeling & Validation (FR-003, FR-004, FR-006, SC-001, SC-004)

**Task 2.1: GPR Training**
- **Action**: Train GPR with RBF kernel on training set.
- **Optimization**: k-fold CV to maximize log marginal likelihood.

**Task 2.2: Linear Regression Baseline (SC-001)**
- **Action**: Train a Linear Regression model on the same training set.
- **Metric**: Calculate R² and RMSE for baseline.
- **Comparison**: Compare GPR R² vs. Baseline R² to confirm non-linear relationships (SC-001).

**Task 2.3: GPR Evaluation**
- **Action**: Predict on test set.
- **Metric**: Calculate R², RMSE, MAE.
- **Output**: Save results to `results/metrics.json`.

**Task 2.4: Confounder Sensitivity Analysis**
- **Action**: If `alloy_type` is available, perform stratified analysis (train/evaluate per alloy type) to assess if relationships hold across different material classes (proxy for confounders).

**Task 2.5: Importance Baseline Comparison (SC-004)**
- **Action**: Calculate permutation importance.
- **Input**: Load `data/baseline_importance.json` (user-provided or literature-based) if available.
- **Output**: Calculate correlation between model rankings and baseline rankings.

**Task 2.6: Synthetic Data Validation (Power Analysis Proxy)**
- **Action**: Generate synthetic non-linear data with known noise levels and sample size N=50.
- **Goal**: Empirically verify if GPR can recover the signal at N=50. If not, flag high uncertainty in final report.

**Task 2.7: Physical Regime Mapping**
- **Action**: Load `normalization_bounds.json`.
- **Output**: Annotate all visualizations with physical units (e.g., "Laser Power: 100-500W") derived from training set bounds, ensuring interpretability of "parameter regimes".

### Phase 3: Visualization & Reporting (FR-005, FR-007, SC-005)

**Task 3.1: Contour & Uncertainty Plots**
- **Action**: Generate contour plots of predicted properties.
- **Action**: Generate uncertainty heatmaps (σ > 2× median flagged in red).

**Task 3.2: Partial Dependence Plots**
- **Action**: Generate PDPs for top 3 influential parameters.

**Task 3.3: Runtime Instrumentation (SC-005)**
- **Action**: Measure total runtime (preprocessing + training + viz).
- **Output**: Save `total_runtime_seconds` to `results/metrics.json`.
- **Check**: Compare against 6-hour limit.

**Task 3.4: Final Report Generation**
- **Action**: Compile metrics, plots, and data provenance acknowledgment into `docs/paper.md`.
- **Requirement**: Explicitly state data source limitations and the "associational" nature of findings.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Missing AM Dataset** | High (Pipeline cannot run) | Code halts with clear error; user must manually provide `data/raw/am_data.csv`. |
| **Insufficient Samples (N < 50)** | High (Model fails) | Preprocessing script checks N and halts if < 50 (FR-001). |
| **Zero Variance Features** | Medium (Singularity) | `preprocess.py` detects zero-variance columns and excludes them with a warning. |
| **High Uncertainty Regions** | Low (Expected outcome) | These regions are the *output* of the analysis (FR-007), not a failure. |
| **Unverified Data Source** | High (Scientific validity) | Final report MUST include a "Data Provenance Acknowledgment" section detailing the manual data source and its limitations. |
| **Causal Misinterpretation** | High (Scientific validity) | All documentation explicitly states "associational" and "non-causal". |