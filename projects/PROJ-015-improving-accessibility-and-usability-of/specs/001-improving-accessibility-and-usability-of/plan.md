# Implementation Plan: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

**Branch**: `proj-015-accessibility-usability` | **Date**: 2026-06-25 | **Spec**: `specs/proj-015/spec.md`
**Input**: Feature specification from `specs/proj-015/spec.md`

## Summary
This plan implements a reproducible research pipeline to evaluate the usability of gene regulation interfaces for people with disabilities. The system compares a Traditional interface against an Explainable (XAI) interface using a within-subjects design. The pipeline collects interaction metrics (completion time, errors, SUS scores), validates data against strict schemas, and performs Repeated Measures ANOVA with Holm-Bonferroni correction to test for significant differences. A Streamlit-based simulator enables human participant data collection, ensuring no synthetic data is used for final claims.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `streamlit` (UI/Simulator), `pandas` (Data manipulation), `scipy` (Statistical analysis: ANOVA, Shapiro-Wilk), `statsmodels` (Post-hoc if needed), `pyyaml` (Schema validation), `numpy` (Numerical ops).
**Storage**: Local CSV files (`data/raw/`, `data/processed/`) and JSON logs.
**Testing**: `pytest` for unit tests (schema validation, statistical logic); `streamlit` manual testing for UI.
**Target Platform**: Linux (GitHub Actions runners), Local Desktop (for participant recruitment).
**Project Type**: Research Pipeline / Web Application (Simulator).
**Performance Goals**: Analysis of <1000 sessions must complete in <60s on CPU.
**Constraints**: Must run on GitHub Actions free tier (2 CPU, 7GB RAM). No GPU required for statistical analysis. Strict adherence to Constitution Principle III (Data Hygiene) and Principle VII (Standardized Metrics).
**Scale/Scope**: Target N=40 participants (Constitution Principle VI). Aiming for N=30 initially, but prioritize recruitment to reach N=40 if feasible. If reaching N=40 is not possible due to constraints, this limitation will be explicitly stated in the research report.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**:
  - **Plan**: All random seeds in `code/` will be pinned. `requirements.txt` will pin exact versions. The analysis pipeline will be a single script/notebook runnable end-to-end.
  - **Status**: Satisfied by design.
- **Principle II (Verified Accuracy)**:
  - **Plan**: All citations in `research.md` will be validated against the verified datasets list. No external claims will be made without primary source verification.
  - **Status**: Satisfied by design.
- **Principle III (Data Hygiene)**:
  - **Plan**: Raw data in `data/raw` is immutable. `data/processed` contains derived files (cleaned, metrics). Checksums recorded in `state/`. PII scan enforced via CI.
  - **Status**: Satisfied by design.
- **Principle IV (Single Source of Truth)**:
  - **Plan**: Every figure in the paper will trace back to exactly one row in this project's `data/` and one block in this project's `code/`. Derived numbers MUST NOT be hand-typed into the paper.
  - **Status**: Satisfied by design.
- **Principle V (Versioning)**:
  - **Plan**: Every artifact under this project carries a content hash. The Advancement-Evaluator Agent invalidates stale review records when the hashed artifact changes.
  - **Status**: Satisfied by design.
- **Principle VI (Participant Representation)**:
  - **Plan**: The plan explicitly requires recruitment via disability advocacy orgs. The `power_analysis` module will enforce the N=40 target threshold before accepting data for analysis.
  - **Status**: Satisfied by design.
- **Principle VII (Standardized Usability Metrics)**:
  - **Plan**: The pipeline mandates SUS, Completion Time, and Error Rate. The statistical engine will strictly use Repeated Measures ANOVA (manually implemented) with Holm-Bonferroni correction.
  - **Status**: Satisfied by design.

## Project Structure

### Documentation (this feature)

```text
specs/proj-015/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── session.schema.yaml
│   └── metrics.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── simulator/
│   ├── __init__.py
│   ├── app.py             # Streamlit entry point
│   ├── interfaces.py      # Traditional and XAI rendering logic
│   └── logic.py           # Task logic (gene regulation simulation)
├── analysis/
│   ├── __init__.py
│   ├── data_cleaner.py    # FR-005: Validation, imputation, filtering
│   ├── stats_engine.py    # FR-002: ANOVA, Holm-Bonferroni, Power
│   ├── power_analyzer.py  # FR-006: Power calculation
│   └── visualizer.py      # Plot generation
├── utils/
│   ├── schema_validator.py
│   └── checksum.py
├── main.py                # Orchestration script
└── requirements.txt

data/
├── raw/                   # Immutable raw sessions
└── processed/             # Cleaned sessions, metrics, reports

contracts/
├── session.schema.yaml
└── metrics.schema.yaml
```

**Structure Decision**: Single Python project structure (`code/`) is selected. This aligns with the research pipeline nature, allowing direct import of analysis modules into the Streamlit app and test suites. The separation of `simulator` and `analysis` ensures the UI logic does not pollute the statistical engine.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The current structure is minimal and sufficient. | N/A |

## Phase Mapping to Functional Requirements

- **Phase 1: Data Collection & Schema Definition**
  - Implements **FR-001** (Data Collection), **FR-003** (UI Rendering), **FR-004** (Counterbalancing).
  - *Artifact*: `simulator/app.py`, `contracts/session.schema.yaml`.
- **Phase 2: Data Cleaning & Validation**
  - Implements **FR-005** (Data Cleaning).
  - *Artifact*: `analysis/data_cleaner.py`, `data/processed/cleaned_sessions.csv`.
- **Phase 3: Statistical Analysis**
  - Implements **FR-002** (Statistical Analysis Engine), **FR-006** (Power Analysis).
  - *Artifact*: `analysis/stats_engine.py`, `data/processed/metrics_summary.csv`, `data/processed/power_report.md`.
- **Phase 4: Reproducibility & CI**
  - Implements **NFR-001** (Reproducibility), **NFR-002** (Data Integrity).
  - *Artifact*: `.github/workflows/reproducibility_check.yml`, `requirements.txt`.

## Addressing Unresolved Concerns

1.  **Task Dependency Violations (T032/T033 vs T031)**: The plan ensures `T031-cli` (Schema validation implementation) is a prerequisite for `T032` (Simulator test). The `simulator/app.py` will explicitly load and validate against `contracts/session.schema.yaml` before accepting data.
2.  **Missing Artifacts (T021a, T021c, T023a, T023b, T025b, T026, T036b, T031b, T043)**:
    - The plan mandates the creation of `data/processed/cleaned_sessions.csv` via `data_cleaner.py`.
    - `data/processed/metrics_summary.csv` and `data/processed/descriptive_stats.csv` will be generated by `stats_engine.py`.
    - `data/processed/power_report.md` will be generated by `power_analyzer.py`.
    - `contracts/session.schema.yaml` will be a valid YAML schema file, not a stub.
    - `data/sample_size_verification.json` will be generated by the power analysis step.
3.  **Task Ordering**: The plan enforces `Data Collection` -> `Cleaning` -> `Analysis` -> `Reporting`. No analysis step will run without a verified `cleaned_sessions.csv`.
