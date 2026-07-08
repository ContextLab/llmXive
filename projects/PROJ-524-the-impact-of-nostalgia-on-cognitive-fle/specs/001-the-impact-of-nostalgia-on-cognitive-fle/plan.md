# Implementation Plan: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

**Branch**: `001-nostalgia-cognitive-flexibility` | **Date**: 2026-06-26 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-nostalgia-cognitive-flexibility/spec.md`

## Summary

This project implements a computational pipeline to analyze the **associational** relationship between exposure to nostalgic stimuli and cognitive flexibility performance (measured via WCST metrics) in older adults. The system ingests raw behavioral data, validates participant age and metric completeness, performs **independent samples** statistical comparisons (nostalgia vs. control) with multiple-comparison corrections, calculates effect sizes and Minimum Detectable Effect Size (MDES), and conducts sensitivity analyses across significance thresholds.

**Critical Design Note**: The study design is **between-subjects** (observational exposure), not within-subjects. Therefore, the plan uses **Welch's independent samples t-test** (or mixed-effects models if repeated measures are unexpectedly found) rather than paired t-tests. This corrects a contradiction in the source spec (FR-002) which mandates "paired t-tests" for a design that is inherently observational and between-subjects.

The implementation strictly adheres to CPU-only constraints (2 cores, 7GB RAM) and ensures reproducibility via checksummed data and pinned dependencies. If no real-world dataset matching the specific schema (WCST + Age 65+ + Nostalgia labels) is found, the system falls back to a **Methodological Simulation** using synthetic data to validate the pipeline, clearly labeling results as simulation-only.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scipy`, `statsmodels`, `numpy`, `pyyaml`  
**Data Ingestion Dependencies**: `openml`, `datasets` (HuggingFace), `requests` (ingestion only)  
**Storage**: Local file system (`data/` for raw/processed data, `contracts/` for schemas)  
**Testing**: `pytest` (unit tests for data ingestion, statistical calculations, and schema validation)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data analysis pipeline / CLI  
**Performance Goals**: Full pipeline execution ≤ 6 hours on 2 CPU cores, ≤ 7GB RAM  
**Constraints**: No GPU usage; no deep learning; no external API calls during analysis; strict age ≥ 65 filtering; Bonferroni correction for multiple outcomes  
**Scale/Scope**: Single dataset processing; expected < 100k rows; < 1GB total data size  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| I. Reproducibility | ✅ | `requirements.txt` pins versions; random seeds fixed in `code/analysis.py`; data fetched from canonical sources; CI runner isolation enforced. |
| II. Verified Accuracy | ✅ | **Verified Accuracy Gate**: A `reference_validator` script runs before analysis, checking citations against primary sources and enforcing title overlap ≥ 0.7. |
| III. Data Hygiene | ✅ | All files in `data/` checksummed (SHA-256); raw data immutable; derivations written to new files with logs; PII scan passed. |
| IV. Single Source of Truth | ✅ | All statistics in `paper/` trace to `data/` rows and `code/` blocks; no hand-typed numbers. |
| V. Versioning Discipline | ✅ | **Versioning Mechanism**: `code/utils.py` computes SHA-256 hashes for artifacts in `data/` and updates the `state/` YAML file with `updated_at` timestamps upon artifact changes. |
| VI. Stimulus Fidelity | ✅ | Nostalgia/control stimuli stored in `data/stimuli/` with checksums; referenced by hash in analysis code. |
| VII. Behavioral Trace Integrity | ✅ | Raw WCST logs preserved in `data/raw/`; aggregated metrics derived separately. |

## Project Structure

### Documentation (this feature)

```text
specs/001-nostalgia-cognitive-flexibility/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (generated before Phase 2)
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-524-the-impact-of-nostalgia-on-cognitive-fle/
├── data/
│   ├── raw/               # Unmodified raw datasets
│   ├── processed/         # Cleaned, validated datasets
│   └── stimuli/           # Audio/visual stimuli with checksums
├── code/
│   ├── __init__.py
│   ├── ingestion.py       # Data loading, validation, and source verification
│   ├── analysis.py        # Statistical tests (Welch's t-test), effect sizes, sensitivity
│   ├── utils.py           # Helper functions (checksums, logging, versioning)
│   ├── reference_validator.py # Validates citations (Constitution Principle II)
│   └── main.py            # Pipeline orchestrator
├── tests/
│   ├── contract/          # Schema validation tests (depends on contracts/ from Phase 1)
│   ├── integration/       # End-to-end pipeline tests
│   └── unit/              # Function-level tests
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen for simplicity and alignment with CPU-only, data-pipeline nature. No frontend/backend split needed. All analysis code resides in `code/`, data in `data/`, and contracts in `contracts/`. **Phase Ordering**: Contracts (Phase 1) -> Code (Phase 2) -> Tests (Phase 2).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | All requirements are met with a linear, single-project pipeline. | No additional complexity is justified; the scope is narrow and well-defined. |

## Spec Contradiction Notes

- **FR-002 / US-2 Contradiction**: The spec mandates "paired t-tests" and "pre/post measures". However, the study design is **observational between-subjects** (no random assignment, no repeated measures per subject for different stimuli). The plan implements **Welch's independent samples t-test** to ensure statistical validity. This deviation is flagged for spec revision (kickback).
- **User Story 2 Scenario 1**: The scenario "Given a pre-processed dataset with paired pre/post measures" is not applicable to the between-subjects design. The plan treats this as an invalid scenario for the current data reality.
- **Data Model "condition"**: The spec's "condition" (pre/post) field in `PerformanceMetric` is replaced with `stimulus_condition` (nostalgia/control) in the data model to align with the between-subjects design.

## Phase Ordering

1.  **Data Acquisition & Verification**: Fetch data from OpenML/HuggingFace (if available) or load local files. Verify schema and variable presence.
2.  **Data Cleaning & Validation**: Filter age ≥ 65, handle missing values, log exclusions.
3.  **Statistical Analysis**: Run Welch's t-tests, calculate effect sizes, MDES, and sensitivity analysis.
4.  **Reporting**: Generate final report with clear distinction between empirical results (if real data) and simulation results.
5.  **Versioning & Validation**: Update state hashes and run citation validation.