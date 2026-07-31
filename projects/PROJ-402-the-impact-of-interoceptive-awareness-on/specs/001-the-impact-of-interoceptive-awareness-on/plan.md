# Implementation Plan: The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress

**Branch**: `001-impact-of-interoceptive-awareness` | **Date**: 2026-07-31 | **Spec**: `specs/001-impact-of-interoceptive-awareness/spec.md`
**Input**: Feature specification from `/specs/001-impact-of-interoceptive-awareness/spec.md`

## Summary

This project investigates whether behavioral interoceptive accuracy (Schandry task) predicts physiological emotional regulation (HRV changes) during acute psychosocial stress, controlling for baseline HRV. The primary technical approach is a feasibility-first pipeline: (1) audit open-source datasets (WESAD, OpenNeuro) for the specific presence of a behavioral heartbeat perception task and stress paradigms; (2) if data exists, extract and compute HRV metrics (RMSSD, SDNN) using `hrv-analysis`; (3) perform an ANCOVA-style linear regression. 

**Feasibility Fallback**: If the required behavioral data (Schandry task) is absent (as hypothesized), the pipeline proceeds to generate a **Data Gap & Sensitivity Report**. This report includes a **Minimum Detectable Effect Size (MDES)** calculation. 
* **Methodology**: Since the predictor is missing, the regression residual variance cannot be estimated. Instead, the MDES is calculated using the **Total Variance of the Outcome** (Stress HRV observed in WESAD) and a **Best-Case Scenario Assumption**: that the missing predictor would explain a conservative [deferred] of the variance (R² = 0.10).
*   **Interpretation**: This MDES represents the smallest effect size a *hypothetical* predictor would need to have to be detectable in this sample size, given the observed noise of the outcome. It is explicitly framed as a **Theoretical Sensitivity Bound**, not an empirical test of the hypothesis, avoiding the category error of estimating effects from missing data.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `hrv-analysis`, `pybids`, `requests`, `pyyaml`, `jsonschema`  
**Storage**: Local filesystem (`data/`, `code/`, `results/`)  
**Testing**: `pytest` (unit tests for HRV calculation, integration tests for pipeline flow, schema validation)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: data-analysis-pipeline  
**Performance Goals**: Complete audit and preprocessing within 45 minutes; full regression (if data exists) within 60 minutes.  
**Constraints**: Must run on a minimal CPU core configuration, with limited RAM, no GPU. Must not require authentication or credentials for data access.  
**Scale/Scope**: Analysis of a cohort of subjects (typical for WESAD/OpenNeuro stress studies).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: **SATISFIED**. The plan mandates pinning `requirements.txt`, using random seeds, and fetching data from canonical URLs (Zenodo/HuggingFace/OpenNeuro API) on every run. No manual steps are allowed.
- **Principle II (Verified Accuracy)**: **SATISFIED**. All dataset URLs and methodological citations will be verified against the provided `# Verified datasets` block. No fabricated URLs will be used. The OpenNeuro search uses the official GraphQL API.
- **Principle III (Data Hygiene)**: **SATISFIED**. Raw data will be downloaded to `data/` and checksummed. Derived HRV metrics will be written to new files in `data/derived/`. No in-place modification.
- **Principle IV (Single Source of Truth)**: **SATISFIED**. The `data_audit.md` and regression/MDES outputs will be the sole source for the final report. No hand-typed statistics.
- **Principle V (Versioning)**: **SATISFIED**. Step 4 (`04_update_state.py`) explicitly updates the `state/projects/...yaml` file. It computes **SHA-256** hashes for all files in `data/` and `results/`, populates the `artifact_hashes` map, updates `last_modified` to the current UTC timestamp, and increments the `version` minor number. This ensures the state file reflects the exact content of the artifacts as required.
- **Principle VI (Physiological Signal Integrity)**: **SATISFIED**. The plan explicitly separates the behavioral predictor (Schandry score) from the physiological outcome (HRV). The pipeline will not conflate these data sources.
- **Principle VII (Baseline Confounding Control)**: **SATISFIED**. The regression model is defined as `Stress_HRV ~ Interoception_Accuracy + Baseline_HRV`. Baseline HRV is a mandatory covariate.

## Project Structure

### Documentation (this feature)

```text
specs/001-impact-of-interoceptive-awareness/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Implementation Inputs (not outputs)
    ├── dataset.schema.yaml
    ├── hrv_metrics.schema.yaml
    └── regression_output.schema.yaml
```
*Note: The `contracts/` directory contains schemas authored during the planning phase to guide the implementation. They are **inputs** to the scripts (e.g., `01_audit_data.py` validates against `dataset.schema.yaml`), not outputs generated by the pipeline.*

### Source Code (repository root)

```text
code/
├── 01_audit_data.py         # FR-001, FR-002: Scan metadata for Schandry/TSST (Validates against dataset.schema.yaml)
├── 02_preprocess_hrv.py     # FR-003, FR-004: Extract RMSSD/SDNN from ECG/PPG (Validates against hrv_metrics.schema.yaml)
├── 03_analyze_regression.py # FR-005, FR-006: Run ANCOVA or MDES calculation (Validates against regression_output.schema.yaml)
├── 04_update_state.py       # FR-006, Constitution V: Hash artifacts (SHA-256) and update state YAML
├── utils/
│   ├── hrv_utils.py         # Artifact rejection, signal validation
│   └── data_loader.py       # WESAD/OpenNeuro download logic
└── main.py                  # Pipeline orchestrator

tests/
├── test_audit.py            # Maps to FR-001, FR-002, US-1
├── test_hrv.py              # Maps to FR-003, FR-004, US-2
├── test_regression.py       # Maps to FR-005, FR-006, US-3 (Tests MDES logic)
└── test_versioning.py       # Maps to Constitution V

data/
├── raw/                     # Downloaded datasets (checksummed)
├── derived/                 # HRV metrics, cleaned events
└── audit/                   # data_audit.md, MDES report
```

**Structure Decision**: Single project structure (`code/`) selected to align with the data-analysis nature of the feature. This minimizes overhead and ensures the pipeline runs sequentially on a single runner. Contracts are treated as validation inputs for the scripts.

## Test Coverage Matrix

| Test File | Functional Requirements | User Stories | Contract Validated |
| :--- | :--- | :--- | :--- |
| `test_audit.py` | FR-001, FR-002 | US-1 | `dataset.schema.yaml` |
| `test_hrv.py` | FR-003, FR-004 | US-2 | `hrv_metrics.schema.yaml` |
| `test_regression.py` | FR-005, FR-006 | US-3 | `regression_output.schema.yaml` |
| `test_versioning.py` | Constitution V | N/A | N/A (State YAML) |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations found. | The pipeline is linear and modular, fitting within the constrained RAM environment. |