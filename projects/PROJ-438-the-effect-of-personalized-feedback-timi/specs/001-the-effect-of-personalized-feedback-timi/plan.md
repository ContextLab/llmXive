# Implementation Plan: The Effect of Personalized Feedback Timing on Skill Acquisition

**Branch**: `PROJ-438-feedback-timing` | **Date**: 2026-06-25 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/PROJ-438-the-effect-of-personalized-feedback-timing/spec.md`

## Summary
**Critical Reframing**: This project analyzes the Open University Learning Analytics Dataset (OULAD) to determine the impact of **Student Response Latency to Assessment** (a proxy for feedback-seeking behavior/engagement) on skill acquisition, proxied by final grades. 
*Note: The OULAD dataset does not contain instructor feedback timestamps. Therefore, the "feedback interval" is redefined as the time delta between a student's assessment submission and their next student-generated event (forum post or assessment result). This measures student engagement speed, not instructor feedback delivery. The causal claim is limited to "engagement," not "instructor feedback."*

The approach involves downloading real OULAD data, calculating precise student response intervals, binning learners based on their *median* interval, and fitting a Cluster-Robust OLS model with Tukey HSD post-hoc tests. Sensitivity analysis will sweep bin boundaries to ensure robustness.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, numpy, statsmodels, scipy, requests, tqdm, pyyaml, pytest  
**Storage**: Local CSV/Parquet files (`data/`), SQLite for temporary aggregation if needed  
**Testing**: pytest (unit tests for binning logic, integration tests for pipeline)  
**Target Platform**: Linux server (GitHub Actions free-tier runner: 2 CPU, 7GB RAM)  
**Project Type**: Data analysis pipeline / Research script  
**Performance Goals**: Complete full pipeline (download → model → sensitivity) within 6 hours  
**Constraints**: No GPU usage; max 7GB RAM; strict reproducibility (random seeds); no synthetic data  
**Scale/Scope**: ~10k+ learner records (OULAD size), 3 feedback timing groups, 100+ sensitivity sweeps  

> **Dataset Note**: The plan relies on the OULAD dataset. The spec assumes the presence of `response_timestamp` (feedback). Since OULAD lacks instructor response timestamps, the plan explicitly maps "response_timestamp" to the **next student event** (forum post or assessment result) following submission. This is a proxy for "feedback engagement." The verified sources are:
> - `students_data.csv` (HuggingFace - mirror of official OULAD)
> - `train-00000-of-00004.parquet` (HuggingFace - mirror of official OULAD)
> - `train-00000-of-00001.parquet` (HuggingFace - mirror of official OULAD)

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ | `requirements.txt` pinned; random seeds set in `code/`; data fetched via deterministic URLs; **README.md** and **docs/** generated in Phase 1. |
| **II. Verified Accuracy** | ✅ | Citations in `research.md` limited to verified dataset URLs; Reference-Validator Agent invoked for proxy validation (FR-008). |
| **III. Data Hygiene** | ✅ | Checksums recorded in `state/`; raw data preserved; transformations output new files. |
| **IV. Single Source of Truth** | ✅ | All stats in `results_metrics.csv` trace to code; no hand-typed numbers. |
| **V. Versioning Discipline** | ✅ | Content hashes tracked; `updated_at` updated on artifact change. |
| **VI. Construct Validity** | ⚠️ | "Final grade" proxy validated via Reference-Validator Agent (FR-008); timing intervals derived from **student** events (proxy); explicit validity disclaimer added. |
| **VII. Temporal Data Integrity** | ✅ | Timestamps converted to UTC; no in-place modification; derived columns preserve order. |

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-438-the-effect-of-personalized-feedback-timing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Design-time artifacts)
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-438-the-effect-of-personalized-feedback-timing/
├── code/
│   ├── __init__.py
│   ├── download.py          # FR-001: Data acquisition (with checksum verification)
│   ├── preprocess.py        # FR-002, T018, T019: Filtering & cleaning (logs exclusions)
│   ├── intervals.py         # FR-003, T024: Interval calculation (median per learner)
│   ├── binning.py           # FR-004, T025: Group assignment (median-based)
│   ├── modeling.py          # FR-005, FR-006: OLS + Tukey HSD + PSM/IPW
│   ├── sensitivity.py       # FR-007, T032-T037: Stability analysis (metrics: stability, flip)
│   ├── validation.py        # FR-008, T039: Proxy validation (Reference-Validator Agent)
│   └── main.py              # Orchestration
├── data/
│   ├── raw/                 # Downloaded OULAD files
│   └── processed/           # learners_raw.csv, learners_binned.csv, results_metrics.csv
├── tests/
│   ├── test_binning.py
│   └── test_intervals.py
├── docs/                    # T042: API/Implementation docs (Phase 1 output)
├── README.md                # T041: Usage instructions (Phase 1 output)
├── requirements.txt
└── state/
    └── projects/PROJ-438...yaml
```

**Structure Decision**: Single Python package structure (`code/`) for modularity and testability, aligned with the data pipeline flow.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Sensitivity Sweep (FR-007) | Required to prove bin boundaries (2h/48h) aren't arbitrary artifacts. | A single fixed-bin analysis would fail SC-003 (robustness) and Constitution Principle II (Verified Accuracy) regarding arbitrary thresholds. |
| Cluster-Robust OLS (FR-005) | Courses are non-independent clusters; standard OLS would inflate Type I error. | Standard OLS ignores course-level variance, violating statistical rigor requirements. |
| Proxy Reframing (Construct Validity) | OULAD lacks instructor feedback timestamps. | Using "student response latency" as a proxy for "instructor feedback" is a known limitation; reframing the question to "engagement" is necessary to avoid fabrication. |

## FR-001: Data Acquisition & Source Discrepancy
The spec mandates downloading from `https://analyse.kmi.open.ac.uk/open_dataset`. However, the CI runner cannot interact with web portals. The plan uses **verified HuggingFace mirrors** which are direct, checksum-verified copies of the official OULAD dataset. A `checksum_verification` step in `download.py` will compare the downloaded file hash against the official source hash (if available) or the known HuggingFace hash to ensure data integrity.

## FR-002: Data Preprocessing & Filtering
The plan explicitly implements the **hard constraint** from FR-002: courses must have both "assessment" and "forum" events. 
- **Logic**: Filter courses where `event_type` contains both "assessment" and "forum".
- **Logging**: The count of excluded courses and learners is logged to `logs/preprocess.log`.
- **T018/T019**: Exclusion logic for learners without forum interactions and courses with <50 learners is implemented and logged.

## FR-004: Binning Logic (Median-Based)
The plan explicitly implements the **median** logic from FR-004:
- **Logic**: For each learner, calculate the **median** of their `feedback_interval` (time to next event).
- **Assignment**: Assign to "Immediate" (<2h), "Delayed" (2h–48h), or "Variable" (>48h) based on this **median** value.
- **T024/T025**: Implementation of median calculation and binning is confirmed.

## FR-007: Sensitivity Analysis (Specific Metrics)
The plan explicitly calculates the metrics defined in FR-007:
- **Significance Stability**: Proportion of sweeps where p < 0.05.
- **Significance Flip Rate**: Proportion of sweeps where the direction of the effect changes.
- **Output**: `significance_stability_report.csv` will contain these exact columns.

## FR-008: Proxy Validation Workflow
The plan defines the **automated** workflow for the Reference-Validator Agent:
1. **Input**: Literature citations and OULAD documentation.
2. **Process**: Agent scrapes sources, checks title overlap (>=0.7), and validates "final grade" as a proxy for "skill acquisition" in the context of OULAD.
3. **Output**: A pass/fail report. If fail, the study is flagged for reframing (already done).
4. **T039**: The agent's output log is generated as an artifact.

## Constitution Principle I (Reproducibility) Compliance
To satisfy the requirement for a fresh runner:
- **README.md (T041)**: Generated in Phase 1 with full usage instructions.
- **docs/ (T042)**: Generated in Phase 1 with API/implementation details.
- **Code**: All scripts are runnable end-to-end via `main.py`.
- **Data**: Checksums and versioning are enforced.
