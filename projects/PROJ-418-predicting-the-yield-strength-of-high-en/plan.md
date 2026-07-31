# Plan: Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

## Project Overview
This project aims to predict the yield strength of High-Entropy Alloys (HEAs) using compositional descriptors as features. The pipeline will download verified HEA composition data, engineer descriptors (atomic size difference, electronegativity difference, VEC, mixing entropy, melting temperature variance), train and evaluate machine learning models (Linear Regression, Random Forest, Gradient Boosting), and perform rigorous statistical validation.

## User Stories

### US1: Data Acquisition and Descriptor Engineering
**Goal**: Download HEA data from verified repositories, calculate compositional descriptors (δ, Δχ, VEC, entropy, melting var), and filter to single-phase room-temperature alloys.

**Acceptance Criteria**:
- Data downloaded from verified sources or open repositories (Materials Project, NIST, Zenodo) if verified sources fail.
- Descriptors calculated: δ (atomic size difference), Δχ (electronegativity difference), VEC (valence electron concentration), mixing entropy, melting temperature variance.
- Data filtered to single-phase, room-temperature alloys with yield strength values.
- Output: `data/processed/hea_descriptors.csv` with complete descriptor values.
- Status written to `output/data_status.json` with count, warnings, and power status.

### US2: Model Training and Predictive Performance Evaluation
**Goal**: Train Random Forest and Gradient Boosting models (5-fold CV, hyperparameter tuning ≤50 trees, depth ≤10), evaluate on hold-out test set, and compare against Linear Regression baseline.

**Acceptance Criteria**:
- Data split 80/20 using stratified splitting by elemental ratios (replaces "disjoint elemental sets").
- Linear Regression baseline trained.
- Random Forest trained with 5-fold CV and grid search (trees: 10-50, depth ≤10).
- Gradient Boosting trained with 5-fold CV and grid search (trees: 10-50, depth ≤10).
- Models evaluated on held-out test set with R², MAE, RMSE.
- Best model selected and metrics written to `output/metrics.json`.
- Total pipeline runtime tracked and validated against 6-hour limit.

### US3: Statistical Validation and Significance Reporting
**Goal**: Perform permutation testing, bootstrap resampling, multiple-comparison correction, sensitivity analysis on α, and VIF diagnostics.

**Acceptance Criteria**:
- Power analysis performed based on sample size (N < 50 triggers low_power warning but proceeds).
- VIF calculated for Linear Regression baseline only; remediation applied if VIF > 10.
- Permutation importance tested with a **large number of permutations (fixed at 1000)** for all models (FR-006 compliance).
- Multiple-comparison correction applied (Bonferroni and Benjamini-Hochberg).
- Bootstrap resampling performed for Linear Regression and best tree-based model to calculate R² confidence intervals.
- Sensitivity analysis performed over α ∈ {0.01, 0.05, 0.1}.
- Final report generated at `output/report.md` with all results and mandatory disclaimers.

## Functional Requirements

### FR-001: Data Source Fallback
If verified dataset URL is missing or fails, attempt to fetch from open repositories (Materials Project, NIST, Zenodo) in order. If all fail, report N=0 and continue with `NO_DATA` status.

### FR-004: Model Constraints
Random Forest and Gradient Boosting models must use ≤50 trees and max_depth ≤10 during hyperparameter tuning.

### FR-005: Stratified Splitting (Updated)
Data must be split 80/20 using stratified splitting by elemental ratios, replacing the previous "disjoint elemental sets" requirement.

### FR-006: Permutation Testing (Updated)
Permutation importance tests must use a **large, fixed number of permutations (1000)** for all models, regardless of dataset size. Adaptive permutation counts are NOT permitted.

### FR-009: VIF Diagnostics
VIF must be calculated within the full multiple regression model for the Linear Regression baseline only. If VIF > 10, remediation (PCA or L1-regularization) must be applied.

### FR-012: Documentation
README.md must include installation steps, usage instructions, and data source requirements.

### FR-013: Quickstart Guide
quickstart.md must provide a step-by-step walkthrough of pipeline execution.

## Technical Constraints

- **Reproducibility**: All random seeds must be pinned (numpy, random, torch if used).
- **Runtime**: Total pipeline runtime must not exceed 6 hours (21600 seconds).
- **Memory**: Pipeline must run within ~7 GB RAM / ~14 GB disk constraints.
- **Data Integrity**: All artifacts must have SHA256 checksums recorded in project state.
- **Validation**: All JSON/YAML artifacts must conform to schemas in `contracts/`.

## Implementation Phases

### Phase 1: Setup
- Create directory structure: `code/`, `data/raw`, `data/processed`, `output/`, `tests/`, `output/plots`
- Create `__init__.py` files in all `code/` and `tests/` subdirectories
- Create `requirements.txt` and `README.md` scaffolding

### Phase 2: Foundational
- Setup deterministic logging and random seed management (`code/utils/logging.py`)
- Create base data schemas and validation logic (`code/data/__init__.py`)
- Implement unit normalization utility (`code/utils/unit_utils.py`)
- Setup environment configuration management (`code/utils/config.py`)
- Implement plot disclaimer injector (`code/utils/plot_utils.py`)
- Implement report disclaimer injector (`code/utils/report_utils.py`)

### Phase 3: User Story 1 - Data Acquisition and Descriptor Engineering
- Implement data downloader (`code/data/download.py`) with fallback logic
- Implement data preprocessor (`code/data/preprocess.py`) for filtering and normalization
- Implement elemental property loader (`code/data/descriptors.py`)
- Implement descriptor calculator (`code/data/descriptors.py`)
- Implement composition filter (`code/data/descriptors.py`)
- Implement pipeline orchestrator (`code/data/pipeline.py`)
- Generate processed data and status file (`code/data/status_writer.py`)

### Phase 4: User Story 2 - Model Training and Evaluation
- Implement data splitter (`code/models/train.py`) with stratified splitting
- Implement Linear Regression baseline trainer
- Implement Random Forest trainer with grid search
- Implement Gradient Boosting trainer with grid search
- Implement evaluation runner (`code/models/evaluate.py`)
- Write metrics to `output/metrics.json` (`code/models/metrics_writer.py`)
- Track total pipeline runtime (`code/models/runtime_tracker.py`)

### Phase 5: User Story 3 - Statistical Validation
- Implement power analysis checker (`code/models/power_analysis.py`)
- Implement VIF calculator and remediation (`code/models/evaluate.py`)
- Implement permutation importance tester with fixed 1000 permutations
- Implement multiple-comparison correction
- Implement bootstrap resampling
- Implement sensitivity analysis
- Generate final report (`code/models/report_generator.py`)

### Phase 5a: Data Hygiene, Provenance, and Versioning
- Compute SHA256 checksums for raw and processed data
- Generate provenance metadata
- Compute content-hashes for all major artifacts

### Phase 6: Polish & Cross-Cutting Concerns
- Update README.md with full documentation
- Create quickstart.md with step-by-step guide
- Run linting and formatting (ruff, black)
- Write unit tests for descriptor math
- Write integration tests for full pipeline
- Validate quickstart.md execution

### Phase 7: Execution & Verification
- Verify data acquisition returns SUCCESS or NO_DATA
- Verify data processing produces valid status file
- Verify model training produces valid metrics
- Verify statistical validation produces all required JSON files
- Verify final report contains disclaimers and warnings

### Phase 8: Documentation & Specification Alignment
- Update spec.md to reflect stratified splitting (replacing disjoint sets)
- Update plan.md to reflect fixed 1000 permutations (removing adaptive logic)
- Add note to spec.md clarifying adaptive permutation count is not permitted

## Dependencies
- Python 3.8+
- pandas, numpy, scikit-learn, matplotlib, seaborn
- datasets (Hugging Face) for data loading
- pyyaml for configuration
- ruff, black for code quality

## Success Metrics
- Pipeline executes end-to-end without errors
- All output artifacts generated with correct schemas
- Models achieve R² > 0.5 on held-out test set (target)
- Statistical validation confirms model significance (p < 0.05)
- Documentation complete and validated