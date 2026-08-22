# Implementation Plan: Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

**Branch**: `001-evaluating-llm-docs-impact` | **Date**: 2024-05-21 | **Spec**: `specs/001-evaluating-the-impact-of-llm-generated-c/spec.md`
**Input**: Feature specification from `specs/001-evaluating-the-impact-of-llm-generated-c/spec.md`

## Summary

This project implements a controlled feasibility pilot to evaluate the impact of LLM-generated documentation versus human-written and no documentation on developer onboarding time and effort. The technical approach involves three core pipelines: (1) a **Documentation Generation Pipeline** that ingests open-source repositories, pins them to specific commits, and generates Markdown documentation using a state-of-the-art LLM with a fallback to a quantized local `phi` model; (2) an **Experiment Execution System** that manages participant assignment, logs task start/end times, counts clarification questions, and enforces stop-loss mechanisms; and (3) a **Statistical Analysis Pipeline** that performs robust estimation (Welch's ANOVA with bootstrapped confidence intervals) and sensitivity analysis (permutation tests), strictly adhering to CPU-only constraints (≤7GB RAM, ≤6h runtime).

**Critical Methodological Shift**: Given the feasibility pilot nature (N=15-20), the primary analysis goal is **variance estimation and effect size description**, not binary hypothesis testing. P-values are treated as exploratory only. The analysis pipeline pre-specifies robust methods (Welch's ANOVA) to avoid the statistical invalidity of assumption-based test selection in low-power settings.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (HuggingFace), `scikit-learn`, `scipy`, `statsmodels`, `psutil`, `requests`, `pyyaml`, `rich` (for CLI), `transformers` (for local fallback), `torch` (CPU-only), `gitpython`, `ruff` (for linting).  
**Storage**: Local file system (`data/raw/`, `data/processed/`), JSON for logs, YAML for schemas.  
**Testing**: `pytest` (unit), `pytest-cov` (coverage), manual mock study for integration.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 vCPU, 7GB RAM).  
**Project Type**: CLI / Research Pipeline.  
**Performance Goals**: Analysis pipeline completes in ≤6 hours; peak memory ≤7GB. Documentation generation per repo ≤15 minutes (with retries).  
**Constraints**: No local GPU; strict reproducibility via pinned seeds and commit hashes; IRB compliance for human data.  
**Scale/Scope**: N=15-20 participants; ≤500 files per repository; 3 experimental conditions.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Evidence/Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Plan includes `requirements.txt` pinning, random seed enforcement, and commit-hash pinning for repositories. |
| **II. Verified Accuracy** | **Pass** | Plan includes a dedicated task T070b to implement and execute `Reference-Validator` logic as a blocking gate before analysis. |
| **III. Data Hygiene** | **Pass** | Plan enforces checksumming of raw data (`data/raw/`), immutable transformations, and PII removal before analysis. |
| **IV. Single Source of Truth** | **Pass** | All figures/statistics will be generated programmatically from `data/processed/` via scripts; no hand-typed numbers. |
| **V. Versioning Discipline** | **Pass** | Artifacts will carry content hashes; state updates will trigger on artifact changes. |
| **VI. Human Subjects Compliance** | **Pass** | Plan includes IRB protocol reference in `data/`, anonymization scripts, and consent record archiving. |
| **VII. Generation Traceability** | **Pass** | LLM config (model, temp, prompt) will be logged and checksummed alongside generated docs. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-llm-docs-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── participant.schema.yaml
    ├── repository.schema.yaml
    ├── task_log.schema.yaml
    ├── statistical_results.schema.yaml
    ├── analysis_output.schema.yaml
    └── ...
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── raw/             # Raw logs, repo metrics, generated docs
│   └── processed/       # Anonymized data, statistical inputs
├── scripts/
│   ├── generate_docs.py # LLM pipeline (API + fallback)
│   ├── run_experiment.py# Participant flow, logging, monitoring
│   ├── analyze.py       # Statistical tests (Welch, Permutation)
│   ├── validate_refs.py # Reference validator for citations
│   ├── repo_metrics.py  # LOC, CC calculation
│   └── anonymize.py     # PII removal
├── models/
│   └── schemas.py       # Pydantic models for validation
├── utils/
│   ├── monitor.py       # psutil/time context manager (FR-010)
│   └── repo_metrics.py  # LOC, Cyclomatic Complexity calculation
└── main.py              # Entry point for CLI
tests/
├── unit/
├── integration/
└── contract/
requirements.txt
```

**Structure Decision**: Single-project structure selected to minimize overhead for a research pilot. All logic is encapsulated in `code/scripts/` with a clear separation between data generation, execution, and analysis.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Robust Statistical Suite** | FR-005 requires handling non-normality AND unequal variance (Welch-James/Permutation). | Standard ANOVA alone would violate statistical rigor and produce invalid p-values if assumptions fail. |
| **Dual-Mode LLM Pipeline** | FR-008 requires API fallback to local `phi` (int4) for reproducibility. | Relying solely on an API risks failure (rate limits) and breaks reproducibility if the API changes. |
| **Real-time Monitoring** | FR-010 requires `psutil`/`time` monitoring during the *actual* analysis run. | A separate stress test (T087) does not guarantee constraints are met during the real data path. |

## Unresolved Panel Concerns Resolution

1.  **FR-007/SC-005 Constraint Verification**: The plan explicitly includes `utils/monitor.py` as a context manager wrapper around the `analyze.py` execution (Task T010b). This ensures that *during* the actual analysis run, wall-clock time and peak memory are logged and validated against the 6h/7GB thresholds, rather than relying on a separate stress test.
2.  **Reference-Validator Implementation**: A new task T070b is added to implement `scripts/validate_refs.py` and execute it as a blocking gate before the analysis phase.
3.  **Methodological Rigor**: The plan now explicitly states that the study is a **Feasibility Pilot** focused on variance estimation and effect sizes. The "decision tree" for test selection based on low-power assumption tests is removed; Welch's ANOVA is pre-specified as the primary robust method.

## Phased Implementation Plan

### Phase 0: Research & Data Strategy
*   **Goal**: Define the statistical methodology, verify dataset availability, and establish the repository selection rubric.
*   **Deliverables**: `research.md` (with Statistical Methodology Appendix), `data-model.md`.
*   **Key Steps**:
    *   Identify -5 open-source repositories with high-quality human docs (verified via rubric).
    *   Confirm availability of `datasets` or `openml` sources for any synthetic/auxiliary data.
    *   Draft the statistical protocol (Welch's ANOVA + Bootstrapped CIs) in `research.md`.

### Phase 1: Data Model & Contracts
*   **Goal**: Define schemas for participants, repositories, and analysis outputs.
*   **Deliverables**: `contracts/*.schema.yaml`, `quickstart.md`.
*   **Key Steps**:
    *   Define `Participant` schema (condition, timestamps, question counts).
    *   Define `Repository` schema (URL, commit, LOC, CC, doc status).
    *   Define `AnalysisOutput` schema (test statistics, p-values, CI).
    *   **T030a**: Generate `data/raw/schema_temp.json` for validation.

### Phase 2: Core Implementation (Documentation & Experiment)
*   **Goal**: Build the generation pipeline and experiment runner.
*   **Deliverables**: `scripts/generate_docs.py`, `scripts/run_experiment.py`.
*   **Key Steps**:
    *   **T021a**: Implement `calculate_cyclomatic_complexity` and write to `data/raw/repo_cc_raw.json`.
    *   **T021b**: Implement `cloc` execution and write to `data/raw/repo_loc_raw.json`.
    *   **T021c**: Implement doc quality rubric and write to `data/raw/doc_quality_scores.json`.
    *   **T021d/T021e**: Generate `repo_selection_rubric.json` and `repo_matching_report.json`.
    *   **T016/T018/T019/T020**: Implement participant logging, incomplete record handling, stop-loss, and anonymization to produce `data/raw/participant_logs.json` and `data/processed/anonymized_logs.json`.
    *   **T028**: Implement LLM generation with API fallback to `phi` (int4), pinning to a specific commit, and logging config/checksum.

### Phase 3: Analysis & Validation
*   **Goal**: Implement statistical tests and verify constraints.
*   **Deliverables**: `scripts/analyze.py`, `scripts/validate_refs.py`.
*   **Key Steps**:
    *   **T010b**: Integrate `monitor.py` as a context manager wrapper around `analyze.py` execution to enforce FR-007.
    *   **T070b**: Execute `validate_refs.py` as a blocking gate before analysis begins.
    *   Implement Welch's ANOVA, Games-Howell, and Permutation tests.
    *   Generate final report with effect sizes and confidence intervals.

### Phase 4: Reporting
*   **Goal**: Generate the final report.
*   **Deliverables**: `paper.md` (draft), final `analysis_report.json`.
*   **Key Steps**:
    *   Aggregate results.
    *   Generate visualizations (via `matplotlib`/`seaborn`).
    *   Write conclusion based on SC-001 to SC-005, emphasizing effect size estimation.

