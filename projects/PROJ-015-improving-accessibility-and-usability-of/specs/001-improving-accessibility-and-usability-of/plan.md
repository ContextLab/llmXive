# Implementation Plan: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

**Branch**: `015-improving-accessibility-usability` | **Date**: 2026-06-25 | **Spec**: `specs/015-improving-accessibility-usability/spec.md`
**Input**: Feature specification from `specs/015-improving-accessibility-usability/spec.md`

## Summary
This project implements a reproducible research pipeline to evaluate the usability of gene regulation interfaces for people with disabilities. It contrasts a Traditional interface against an Explainable (XAI) interface. The system collects interaction data (time, errors, SUS, explanation engagement) via a Streamlit simulator, validates sessions against strict schemas, and performs Repeated Measures ANOVA (or Friedman Test if non-normal) with Holm-Bonferroni correction to determine statistical significance. The pipeline strictly adheres to the project constitution, forbidding synthetic data for final claims and mandating real participant recruitment via disability advocacy groups.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `streamlit`, `scipy`, `pandas`, `numpy`, `pyyaml`, `pytest`, `seaborn`, `statsmodels`
**Storage**: Local filesystem (`data/raw`, `data/processed`, `figures`)
**Testing**: `pytest` (unit tests for validators, integration tests for pipeline)
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM), Streamlit Web App
**Project Type**: Research Pipeline / Web-based Simulator
**Performance Goals**: < 5 min runtime for full analysis on N=30 dataset; < 2s page load for simulator
**Constraints**: CPU-first execution; no synthetic data in `data/processed`; strict schema validation; Holm-Bonferroni correction mandatory; Pilot Study (N=5) required before full recruitment.
**Scale/Scope**: Single study (N≥30), 2 interface variants, 4 primary metrics (Time, Errors, SUS, Explanation Engagement).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | `requirements.txt` pins all versions. `random.seed(42)` used in **analysis logic only**. The simulator captures real-time human input without seeding (human behavior is stochastic). All analysis scripts runnable end-to-end. |
| **II. Verified Accuracy** | **Compliant** | **Phase 3** explicitly invokes the `Reference-Validator` agent before any artifact write. All citations in `research.md` linked to verified sources. |
| **III. Data Hygiene** | **Compliant** | Raw data in `data/raw` is immutable. Derivations in `data/processed`. Checksums recorded in `state/...yaml`. PII scan enabled. |
| **IV. Single Source of Truth** | **Compliant** | All stats in `paper.md` are generated **exclusively** by `code/analysis.py` reading `data/processed/metrics_summary.csv`. No hand-typed numbers are permitted in the paper. |
| **V. Versioning Discipline** | **Compliant** | Artifacts hashed on write. `state` file updated on any change to `code` or `data`. |
| **VI. Participant Representation** | **Compliant** | Plan includes recruitment strategy via disability advocacy orgs. N=30 minimum enforced. Pilot Study (N=5) included to validate task difficulty. Synthetic data strictly forbidden for claims. |
| **VII. Standardized Metrics** | **Compliant** | SUS, Completion Time, Error Count, and Explanation Engagement Time are the metrics. Statistical analysis uses Repeated Measures ANOVA (or Friedman fallback) and Holm-Bonferroni as mandated. |

## Project Structure

### Documentation (this feature)

```text
specs/015-improving-accessibility-usability/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── session.schema.yaml
│   ├── metrics.schema.yaml
│   └── analysis_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-015-improving-accessibility-and-usability-of/
├── code/
│   ├── __init__.py
│   ├── app.py                 # Streamlit simulator entry point
│   ├── data_loader.py         # Data ingestion and validation
│   ├── validator.py           # Schema validation logic
│   ├── analysis.py            # ANOVA/T-Test, Holm-Bonferroni, Power Analysis
│   ├── visualizer.py          # Plot generation (completion_time, error_count, sus, engagement)
│   └── power_analysis.py      # Sample size verification
├── data/
│   ├── raw/                   # Immutable raw session logs (CSV/JSON)
│   └── processed/             # Derived metrics, summaries (metrics_summary.csv)
├── figures/
│   ├── completion_time.png
│   ├── error_count.png
│   ├── sus_score.png
│   └── explanation_engagement.png
├── docs/
│   └── power_report.md        # Power analysis report
├── tests/
│   ├── test_validator.py
│   ├── test_analysis.py
│   └── test_integration.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Selected a single-project structure (`code/`, `data/`, `figures/`) to align with the research pipeline nature of the project. This ensures a clear separation between the simulator (web app), the analysis engine (scripts), and the data artifacts, facilitating the "Single Source of Truth" principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Repeated Measures ANOVA / Paired T-Test** | Required by FR-002 and Constitution Principle VII. For 2 levels, Paired T-Test is mathematically equivalent (F = t^2) but provides direct Cohen's d effect size, standard in HCI. We use ANOVA for the primary hypothesis test (as mandated) and T-Test for effect size reporting. | Independent T-tests would ignore the paired nature of the data, inflating Type I error. |
| **Holm-Bonferroni Correction** | Required by FR-002 to control family-wise error rate across multiple metrics (Time, Errors, SUS, Engagement). | Simple Bonferroni is too conservative; no correction would inflate false positives. |
| **Friedman Test Fallback** | Required for scientific validity if Shapiro-Wilk indicates severe non-normality (common in small N=30 time/error data). | Proceeding with ANOVA on non-normal data risks invalid Type I error rates. |
| **Schema Validation (Strict)** | Required by FR-005 to prevent "garbage in, garbage out" and ensure data hygiene (Constitution III). | Loose validation would allow incomplete sessions to skew results, violating the "Data Hygiene" and "Reproducibility" principles. |
| **Pilot Study (N=5)** | Required to validate task difficulty and timing mechanisms before full N=30 recruitment. | Without a pilot, there is a high risk of ceiling/floor effects rendering the ANOVA unable to detect effects. |

## Implementation Phases

### Phase 0: Research & Validation
- **T012f-int**: Define Pilot Study protocol (N=5).
- **T016**: Define metrics (Time, Errors, SUS, Engagement).
- **T019d**: Implement `validator.py` with strict schema checks (no PII, complete SUS).
- **T049**: Setup Reference-Validator agent invocation in CI.

### Phase 1: Data Model & Contracts
- **T021a**: Define `session.schema.yaml` and `metrics.schema.yaml`.
- **T021b**: Define `analysis_output.schema.yaml`.
- **T021c-cli**: Implement data loading and validation pipeline.

### Phase 2: Analysis Engine
- **T023a**: Implement `run_anova_rm` (or `run_friedman` if non-normal) and `run_ttest` for effect size.
- **T024**: Implement Holm-Bonferroni correction logic.
- **T024a**: Implement verification logging (Non-blocking dependency for T025c).
- **T025c-orch**: Orchestrate analysis pipeline (Load -> Clean -> Analyze -> Report).

### Phase 3: Power & Reporting
- **T017**: Compute Observed Power (using `statsmodels`) and generate `docs/power_report.md`.
- **T027a-c**: Generate visualization figures (`completion_time.png`, `error_count.png`, `sus_score.png`, `explanation_engagement.png`).
- **T035a-apply**: Apply Reference-Validator before writing `paper.md`.

### Phase 4: Paper Generation
- **T049**: Generate `paper.md` exclusively from `code/analysis.py` output.
- **T012f-main**: Final review and artifact hashing.