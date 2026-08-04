# Implementation Plan: The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress

**Branch**: `001-impact-of-interoceptive-awareness` | **Date**: 2026-07-31 | **Spec**: `specs/001-impact-of-interoceptive-awareness/spec.md`
**Input**: Feature specification from `/specs/001-impact-of-interoceptive-awareness/spec.md`

## Summary

This project executes a feasibility audit and, contingent on data availability, a statistical analysis of the relationship between behavioral interoceptive accuracy and physiological stress regulation. The primary goal is to determine if open-source datasets (WESAD, OpenNeuro) contain the necessary multimodal data (Schandry task + TSST). 

**Critical Path**: The pipeline is designed to detect a **data gap**. If the behavioral interoception task (Schandry) is missing (the expected outcome per spec), the system generates a `data_audit.md` report explicitly stating the **Feasibility Failure** of the hypothesis. The study does **not** pivot to a different research question (e.g., stress reactivity alone) nor calculate a misleading "detectable effect" for a missing variable. If data exists, it performs an ANCOVA-style linear regression controlling for baseline HRV. The pipeline runs entirely on CPU within GitHub Actions free-tier constraints.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `hrv-analysis`, `pybids`, `requests`, `pyyaml`, `physionet` (for validation)
**Storage**: Local filesystem (`data/`, `results/`)
**Testing**: `pytest` with `random` seed pinning; `pytest.ini` and `conftest.py` configured for fixed seeds.
**Target Platform**: Linux (GitHub Actions Free Runner)
**Project Type**: Data Science Pipeline / Research Script
**Performance Goals**: Complete download, audit, and (conditional) analysis within 45 minutes.
**Constraints**: No GPU required; CPU-only processing; strict adherence to BIDS standards; no modification of raw data.
**Scale/Scope**: Single dataset audit (WESAD ~GB, OpenNeuro subset); regression on N < 100 subjects.
**Validation**: Download and audit scripts validate outputs against `contracts/dataset.schema.yaml` and `contracts/audit.schema.yaml`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Strategy | Status |
| :--- | :--- | :--- |
| **I. Reproducibility** | All random seeds pinned in `code/utils/seeds.py`. External datasets fetched via `requests` with checksum verification logged to `results/checksums.txt`. | ✅ |
| **II. Verified Accuracy** | Citations in `research.md` restricted to URLs in the `# Verified datasets` block. No fabricated URLs. | ✅ |
| **III. Data Hygiene** | Raw data downloaded to `data/raw/` and checksummed. Derived HRV metrics written to `data/derived/`. No in-place edits. | ✅ |
| **IV. Single Source of Truth** | `data_audit.md` and regression outputs generated directly from `code/` scripts. No manual entry. | ✅ |
| **V. Versioning Discipline** | `code/05_update_state.py` hashes all artifacts and updates `state/projects/.../artifact_hashes` post-execution. | ✅ |
| **VI. Physiological Signal Integrity** | Behavioral scores (Schandry) stored in separate CSV from HRV metrics. Cross-modal join performed only by `subject_id` in the analysis script, with explicit logging. | ✅ |
| **VII. Baseline Confounding Control** | Regression model explicitly defined as `Stress_HRV ~ Interoception + Baseline_HRV`. Baseline HRV is a mandatory covariate, never omitted. | ✅ |

## Project Structure

### Documentation (this feature)

```text
specs/001-impact-of-interoceptive-awareness/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── audit.schema.yaml
│   ├── hrv_metrics.schema.yaml
│   ├── output.schema.yaml
│   └── regression_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── 00_validate_hrv.py           # [Step 0] Validates hrv-analysis on PhysioNet MIT-BIH
├── 01_download_data.py          # [Step 1] Downloads WESAD (Zenodo) and OpenNeuro BIDS, verifies checksums
├── 02_audit_metadata.py         # [Step 2] Scans BIDS events.tsv, dataset_description.json, README for Schandry/TSST, generates data_audit.md
├── 03_preprocess_hrv.py         # [Step 3] Extracts RMSSD/SDNN from ECG/PPG (if audit passes)
├── 04_analyze_regression.py     # [Step 4] Runs ANCOVA (if data exists) or terminates with Feasibility Failure
├── 05_update_state.py           # [Step 5] Updates project state YAML with artifact hashes
├── 06_capture_timing.py         # [Step 6] Logs GITHUB_JOB_DURATION and timestamps
├── utils/
│   ├── seeds.py                 # Random seed definitions
│   └── logging.py               # Standardized logging format
└── requirements.txt

data/
├── raw/                         # Downloaded datasets (immutable, BIDS structure)
├── derived/                     # HRV metrics, audit intermediates
└── audit/                       # Final reports

results/
├── checksums.txt
├── logs/
├── timing.log
├── data_audit.md
└── regression_results.json

tests/
├── test_audit.py                # Tests for metadata scanning logic
├── test_hrv.py                  # Tests for HRV calculation on mock data
├── conftest.py                  # Pytest config with random seed
└── pytest.ini                   # Pytest configuration
```

**Structure Decision**: Single-project structure selected. The pipeline is linear (Download -> Audit -> Preprocess -> Analyze -> Report). Separating into microservices is unnecessary for a research script. The `code/` directory contains all executable logic, `data/` holds inputs/outputs, and `tests/` validates the logic.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | The project is a linear pipeline with conditional branching (if data exists -> analyze, else -> Feasibility Failure). No complex architectural patterns are required. | N/A |

## Phase Execution Order

1.  **Phase 0 (Research)**: `research.md` - Verify dataset availability and variable fit.
2.  **Phase 1 (Design)**: `data-model.md`, `quickstart.md`, `contracts/` - Define schemas and data flow.
3.  **Phase 2 (Implementation)**:
    *   **Step 0**: `code/00_validate_hrv.py` - Download PhysioNet MIT-BIH test set and validate `hrv-analysis` output.
    *   **Step 1**: `code/01_download_data.py` - Download WESAD (Zenodo DOI: 10.5281/zenodo.1292932) and OpenNeuro BIDS dataset. Verify checksums against Zenodo/HF hashes.
    *   **Step 2**: `code/02_audit_metadata.py` - Scan `events.tsv`, `dataset_description.json`, and `README` for "Schandry", "heartbeat", and "TSST". Generate `results/data_audit.md`.
        *   *Logic*: If Schandry is missing for all subjects, mark study as **Feasibility Failure** and terminate. Do not calculate UBDE.
    *   **Step 3**: `code/03_preprocess_hrv.py` - (Conditional) If audit passes, preprocess ECG/PPG to extract HRV (RMSSD/SDNN) with <5% artifact rejection. Output `data/derived/hrv_metrics.csv`.
    *   **Step 4**: `code/04_analyze_regression.py` - (Conditional) Run ANCOVA: `Stress_HRV ~ Interoception + Baseline_HRV`. Output `results/regression_results.json`.
    *   **Step 5**: `code/05_update_state.py` - Hash all artifacts and update `state/projects/.../artifact_hashes`.
    *   **Step 6**: `code/06_capture_timing.py` - Log `GITHUB_JOB_DURATION` and start/end timestamps to `results/timing.log`.

## Contract Validation

*   **Download Validation**: `01_download_data.py` validates downloaded files against `contracts/dataset.schema.yaml` (BIDS structure).
*   **Audit Validation**: `02_audit_metadata.py` validates output against `contracts/audit.schema.yaml`.
*   **HRV Validation**: `03_preprocess_hrv.py` validates output against `contracts/hrv_metrics.schema.yaml`.
*   **Regression Validation**: `04_analyze_regression.py` validates output against `contracts/regression_output.schema.yaml`.