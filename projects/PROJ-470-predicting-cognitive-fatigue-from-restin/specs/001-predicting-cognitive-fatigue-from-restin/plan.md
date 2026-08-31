# Implementation Plan: Predicting Cognitive Fatigue from Resting-State EEG Complexity

**Branch**: `001-cognitive-fatigue-eeg-complexity` | **Date**: 2026-06-28 | **Spec**: `specs/001-predicting-cognitive-fatigue-from-restin/spec.md`
**Input**: Feature specification from `specs/001-predicting-cognitive-fatigue-from-restin/spec.md`

## Summary

This project implements a computational pipeline to predict cognitive fatigue by analyzing the complexity of resting-state EEG signals. The approach involves retrieving a **single public dataset** containing both resting-state EEG and paired subjective fatigue ratings (or PVT-derived proxies) from the same participants. The pipeline preprocesses signals using MNE-Python (1–40 Hz bandpass, 50 Hz notch, artifact rejection at ±100 µV), extracts Lempel-Ziv Complexity (LZC) and Permutation Entropy (PE) features, and performs correlational analysis between **Delta Complexity** (Post - Pre) and **Delta Fatigue** (Post - Pre). 

The primary analysis is a Spearman/Pearson correlation of deltas (per FR-004). A secondary ANCOVA model (`Post_Complexity ~ Fatigue_Delta + Pre_Complexity + Covariates`) is used for robustness and confound control. The pipeline strictly enforces SC-001: if the validated dataset yields N < 30, the system halts immediately with a specific error code. Multiple-comparison correction (Benjamini-Hochberg) and collinearity diagnostics (VIF < 5) are mandatory. The pipeline is designed to run entirely on CPU within the -hour/7GB RAM constraints.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mne`, `numpy`, `scipy`, `pandas`, `scikit-learn`, `nolds` (for LZC), `pyentropy` (for PE), `pyyaml`, `requests`  
**Storage**: Local file system (GitHub Actions runner ephemeral storage) for `data/raw`, `data/processed`, `data/analysis`  
**Testing**: `pytest` with `pytest-cov`  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner)  
**Project Type**: Data Science Pipeline / CLI  
**Performance Goals**: Runtime ≤ 6 hours for N=30 participants; Memory ≤ 7 GB  
**Constraints**: CPU-only execution; no external authentication for data; strict adherence to spec-defined metrics (LZC, PE only); no topological metrics (TDA) or cross-sectional fallbacks.  
**Scale/Scope**: N=30 participants (Hard Gate); 2 resting-state segments per participant; ~14 GB disk usage (streaming/processing).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Random seeds pinned in `code/`. External datasets fetched from verified Hugging Face URLs. `requirements.txt` pins versions. `nolds` and `pyentropy` are explicitly selected for deterministic behavior. |
| **II. Verified Accuracy** | **Compliant** | Task T001 performs citation validation against the "Verified datasets" block before analysis. No fabricated URLs. |
| **III. Data Hygiene** | **Compliant** | Raw data checksummed. Derivations write to new files (`data/processed/`). PII scan enforced. |
| **IV. Single Source of Truth** | **Compliant** | All figures/stats in final report trace to `data/analysis` CSVs. Contracts map to specific output files. |
| **V. Versioning Discipline** | **Compliant** | Artifacts carry content hashes. State file updated on change. |
| **VI. EEG Signal Processing** | **Compliant** | Pipeline: MNE-Python, 1–40 Hz bandpass, notch filter, average re-reference, artifact rejection (±100 µV). `code/config.yaml` values derived directly from FR-002/FR-003. |
| **VII. Statistical Correlation** | **Compliant** | Primary: Delta-Delta correlation (FR-004). Secondary: ANCOVA for confounds. BH correction (FR-005). VIF diagnostics (SC-004). |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-cognitive-fatigue-from-restin/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── processed_eeg.schema.yaml
│   ├── analysis_output.schema.yaml
│   ├── vif_diagnostics.schema.yaml   # NEW: Maps to vif_diagnostics.log
│   └── sensitivity_table.schema.yaml # NEW: Maps to sensitivity_table.csv
└── tasks.md             # Generated (see Task List below)
```

### Source Code (repository root)

```text
projects/PROJ-470-predicting-cognitive-fatigue-from-restin/
├── code/
│   ├── __init__.py
│   ├── config.yaml          # Locked parameters: filters, thresholds, seeds, LZC/PE params
│   ├── download.py          # Data retrieval and validation (FR-001, T002)
│   ├── preprocess.py        # EEG cleaning (FR-002, T011)
│   ├── features.py          # LZC & PE calculation (FR-003, T012)
│   ├── analysis.py          # Correlation, VIF, BH correction (FR-004, FR-005, FR-006, T005, T006)
│   └── report.py            # Report generation
├── data/
│   ├── raw/                 # Downloaded raw files (checksummed)
│   ├── processed/           # Cleaned .fif files (conforms to processed_eeg.schema.yaml)
│   └── analysis/            # CSVs of metrics, results, and diagnostics
│       ├── complexity_metrics.csv
│       ├── fatigue_scores.csv
│       ├── correlation_results.csv
│       ├── vif_diagnostics.log        # Conforms to vif_diagnostics.schema.yaml
│       └── sensitivity_table.csv      # Conforms to sensitivity_table.schema.yaml
├── tests/
│   ├── unit/                # Unit tests for feature extraction
│   ├── integration/         # Pipeline integration tests
│   └── contract/            # Schema validation tests
└── requirements.txt
```

**Structure Decision**: Single project structure selected. This aligns with the data-science nature of the task, keeping data, code, and analysis tightly coupled for reproducibility on a CI runner. No web/mobile components are required.

## Tasks

*Explicit mapping of FR/SC to implementation tasks.*

- **T001**: **Verified Accuracy Check**. Validate all citations in `research.md` against the "Verified datasets" block. Fail if any citation is unreachable or mismatched. (Constitution II)
- **T002**: **Data Validation**. Download dataset. Check for presence of both `eeg_data` and `fatigue_rating` variables. If N < 30, halt with error code 1 and list available variables. (FR-001, SC-001)
- **T003**: **Preprocessing**. Apply 1–40 Hz bandpass, 50 Hz notch, re-reference, and artifact rejection (±100 µV). Write to `.fif` conforming to `processed_eeg.schema.yaml`. (FR-002, T011)
- **T004**: **Feature Extraction**. Calculate LZC (median quantization) and PE (dim=3, lag=1) for segments ≥ 120s. (FR-003)
- **T005**: **Collinearity Diagnostics**. Calculate VIF for predictors. Verify VIF < 5. Output `vif_diagnostics.log` conforming to `vif_diagnostics.schema.yaml`. (SC-004)
- **T006**: **Sensitivity Analysis**. Run discrete significance checks at p ≤ 0.05 and p ≤ 0.01. Output `sensitivity_table.csv` conforming to `sensitivity_table.schema.yaml`. (FR-006)
- **T007**: **Correlation Analysis**. Compute Delta-Delta correlation (primary) and ANCOVA (secondary). Apply BH correction. (FR-004, FR-005)
- **T008**: **Report Generation**. Compile results into final report.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The project strictly follows the spec's defined metrics (LZC, PE) and excludes unauthorized scope creep (TDA, topological metrics) identified in previous reviews. | Tasks T040-T042 (Topological Stability Metrics) were removed as they violate FR-003 and constitute scope creep. |
| **None** | The plan enforces paired-data analysis only, rejecting the "cross-sectional fallback" (T019) which violated FR-004. | A fallback would weaken the mandatory requirement for paired pre/post recordings. The spec demands paired data; if unavailable, the system must halt (FR-001). |
| **None** | VIF diagnostics (SC-004) and Sensitivity Analysis (FR-006) are explicitly backed by Tasks T005 and T006. | Omitting these would fail the success criteria. The plan now explicitly maps these requirements to tasks. |
| **None** | The hard halt on N < 30 enforces SC-001. | Proceeding with N < 30 would violate the Success Criterion and invalidate the study's power. |

## Data Flow to Contract Mapping

1.  **Download** → `data/raw/` → Validated by `dataset.schema.yaml`.
2.  **Preprocess** → `data/processed/` → Validated by `processed_eeg.schema.yaml`.
3.  **Extract** → `data/analysis/complexity_metrics.csv` → Validated by `complexity_metric.schema.yaml`.
4.  **Analyze** → `data/analysis/correlation_results.csv` → Validated by `analysis_output.schema.yaml`.
5.  **Diagnostics** → `data/analysis/vif_diagnostics.log` → Validated by `vif_diagnostics.schema.yaml`.
6.  **Sensitivity** → `data/analysis/sensitivity_table.csv` → Validated by `sensitivity_table.schema.yaml`.

## Compute Feasibility

-   **CPU-First**: All operations (filtering, LZC, PE, correlation) are computationally lightweight and run efficiently on CPU.
-   **Memory**: Streaming data processing ensures memory usage stays < 7 GB.
-   **Time**: N=30 participants with 120s segments is well within the 6-hour limit.
-   **GPU**: Not required. No deep learning models are used.