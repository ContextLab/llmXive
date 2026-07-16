# Feature Specification

## User Stories

### US1: Data Aggregation and Preprocessing
As a researcher, I want to automatically aggregate ball milling experimental data from public repositories
so that I can have a clean, analysis-ready dataset of at least 500 experiments.

**Acceptance Criteria**:
- Data fetched from Materials Project, NIST, and arXiv
- Minimum 150 experiments, target 500+
- Standardized features and PSD metrics (D10, D50, D90)
- Missing values imputed (excluding targets)
- Unstructured PSD data flagged for manual review

### US2: Predictive Model Training
As a data scientist, I want to train and validate GPR and RF models using Nested Cross-Validation
so that I can robustly predict particle size distribution outcomes.

**Acceptance Criteria**:
- Nested CV with stratified splits by material type
- GPR with ARD kernel, fallback to RF if resource limits exceeded
- R², RMSE, MAE metrics reported
- Statistical significance testing (Nadeau & Bengio t-test)
- Power analysis performed

### US3: Model Interpretability
As a domain expert, I want to generate partial dependence plots and feature importance rankings
so that I can understand how milling parameters influence PSD.

**Acceptance Criteria**:
- Partial dependence plots for key features (speed, time, ratio, Young's modulus, duration)
- Feature importance exported as JSON
- Total plot size ≤ 10MB

## Functional Requirements
- FR-001: Minimum 150 experiments required
- FR-008: Unstructured PSD data detection and OCR fallback
- FR-009: Automatic GPR to RF fallback on resource limits
- SC-004: Halt if dataset < 150 rows
- SC-005: CI job time limit enforcement

## Data Model
- Predictors: milling_speed, milling_time, ball_to_powder_ratio, material_type, Young's modulus, density, process_duration
- Targets: D10, D50, D90 (particle size distribution metrics)

## Non-Functional Requirements
- All data must be real and from verified sources
- Results must be reproducible
- Code must be linted and formatted (black, flake8)
- All findings framed as associational, not causal
