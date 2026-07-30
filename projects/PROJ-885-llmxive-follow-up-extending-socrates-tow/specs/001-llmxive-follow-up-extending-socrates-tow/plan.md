# Implementation Plan: llmXive Follow-up: Dynamic Socio-Cognitive State Injection

**Branch**: `001-dynamic-state-injection` | **Date**: 2026-07-14 | **Spec**: `specs/001-dynamic-state-injection/spec.md`
**Input**: Feature specification from `/specs/001-dynamic-state-injection/spec.md`

## Summary

This feature implements a dynamic socio-cognitive state injection adapter to improve consensus gap closure in LLM-mediated conflict resolution. The system generates synthetic conflict trajectories with targeted oversampling of high-emotion/cultural diversity scenarios, infers socio-cognitive states via a lightweight logistic regression classifier (trained on dynamic text features), and injects dynamic style instructions into the the LLM context. The implementation compares this dynamic adapter against a static baseline across eight LLMs in a CPU-only environment (repeated measures design), followed by rigorous statistical analysis (paired t-test/Wilcoxon with Holm-Bonferroni correction) to determine significance.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `datasets`, `scikit-learn`, `torch` (CPU-only), `pandas`, `numpy`, `statsmodels`, `pyyaml`, `sentence-transformers`
**Storage**: Local file system (JSON/CSV/Parquet)
**Testing**: `pytest`
**Target Platform**: Linux (GitHub Actions Free Tier: vCPU, 7GB RAM)
**Project Type**: Research Pipeline / CLI
**Performance Goals**: ≤45s per trajectory inference; ≥40 trajectories/hour throughput on CPU
**Constraints**: No GPU/CUDA; ≤7GB RAM; ≤14GB disk; no external API credentials required (local models or public APIs); strict data hygiene (checksums).
**Scale/Scope**: N=500 trajectories (repeated measures across 8 LLMs); Multiple conditions (Adapter vs. Static).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ | Random seeds pinned; `requirements.txt` provided; data fetched from canonical sources. |
| **II. Verified Accuracy** | ✅ | All citations to SoCRATES and datasets verified against primary sources. |
| **III. Data Hygiene** | ✅ | Checksums recorded; no in-place modification; PII scan enforced. |
| **IV. Single Source of Truth** | ✅ | All stats trace to `data/results/` CSVs; no hand-typed numbers. |
| **V. Versioning** | ✅ | Artifacts carry content hashes; state file updated on change. |
| **VI. Low-Resource Feasibility** | ✅ | Logistic regression, sentence-transformers, and GGUF/CPU inference planned; no CUDA dependencies. |
| **VII. Dynamic State Injection Isolation** | ✅ | Strict separation of Adapter vs. Static conditions; **statistical analysis explicitly excludes 'neutral-monitoring' logs from the primary effect calculation** to ensure valid comparison. |

## Project Structure

### Documentation (this feature)

```text
specs/001-dynamic-state-injection/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── trajectory.schema.yaml
│   ├── experiment_log.schema.yaml
│   └── statistical_report.schema.yaml
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/code/
├── src/
│   ├── data/
│   │   ├── generate_trajectories.py      # SoCRATES pipeline wrapper
│   │   └── classifier_training.py        # Logistic regression training
│   ├── models/
│   │   ├── state_classifier.py           # Inference logic
│   │   └── evaluator.py                  # Consensus gap calculator
│   ├── experiments/
│   │   ├── runner.py                     # Adapter vs. Static execution
│   │   └── prompts.py                    # Prompt templates
│   └── analysis/
│       ├── stats_utils.py                # Normality, t-test, correction
│       └── report_generator.py           # Final JSON/Markdown report
├── tests/
│   ├── unit/
│   │   ├── test_classifier.py            # FR-002 logic tests (Planned)
│   │   ├── test_evaluator.py             # FR-005 logic tests (Planned)
│   │   └── test_data_flow.py             # Reproducibility assertions (Planned)
│   ├── integration/
│   │   └── test_full_pipeline.py         # End-to-end run (Planned)
│   └── contract/
│       └── test_schemas.py               # JSON Schema validation (Planned)
├── data/
│   ├── raw/                              # Downloaded datasets
│   ├── processed/                        # Derived datasets
│   └── results/                          # Experiment outputs & stats
└── requirements.txt
```

**Structure Decision**: Single project structure chosen to minimize I/O overhead and simplify dependency management for a research pipeline. All components are scriptable and testable. *Note: `tests/unit/` files are planned deliverables to be created in Phase 2.*

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Dual Condition (Adapter vs. Static)** | Required by FR-003 and FR-007 to isolate the "dynamic injection" variable. | A single condition would fail to establish causality or improvement over baseline. |
| **Statistical Correction (Holm-Bonferroni)** | Required by FR-007 to control family-wise error rate across 8 LLMs. | Uncorrected p-values would inflate Type I error rates, invalidating the study. |
| **CPU-Only Constraint** | Required by Constitution Principle VI and Assumption 2. | GPU reliance would violate the "low-resource feasibility" goal and CI runner limits. |
| **Repeated Measures Design** | Required to maintain power (N=500 per model) with limited total trajectories. | Splitting N across models would result in N<65 per model, making the study underpowered. |

## Unresolved Panel Concerns (Addressed)

The following concerns from the previous iteration have been resolved in this plan:

1.  **T043 (Unit Tests)**: **Resolved**. Task T043 is split into **T043a** (`tests/unit/test_classifier.py` - tests for FR-002 logic) and **T043b** (`tests/unit/test_evaluator.py` - tests for FR-005 logic). Specific function names and assertions are defined in the task list below.
2.  **T044 (Quickstart Validation)**: **Resolved**. Task T044 now explicitly requires generating `data/results/quickstart_validation_log.txt` containing the string "SUCCESS" and exiting with code 0.
3.  **T047 (Reproducibility)**: **Resolved**. Task T047 is now explicitly defined as `tests/unit/test_reproducibility.py` to verify statistical reproducibility (variance < tolerance).
4.  **T049 (Power Analysis)**: **Resolved**. Task T049 logic is updated: if power is insufficient, it writes an "underpowered" flag to the report and **continues** (no exit code 1), aligning with Assumption 4.
5.  **T020 (Classifier Parallelism)**: **Resolved**. The [P] tag is removed. T020 is now explicitly marked as **Sequential** and dependent on T019.
6.  **T045 (Refactor)**: **Resolved**. Split into **T045a** (Refactor split logic) and **T045b** (Add unit test in `tests/unit/test_data_flow.py`).
7.  **T038 (Statistical Workflow)**: **Resolved**. Split into **T038a** (Data Ingestion), **T038b** (Normality Test & Recording), **T038c** (Statistical Test & Holm-Bonferroni Correction), **T038d** (Report Generation).
8.  **T028 (Logging Neutral State)**: **Resolved**. Task T028 is updated to explicitly mandate that "neutral-monitoring" logs are **excluded** from the primary "Adapter Effect" calculation in T038c to preserve validity.
9.  **T050 (Threshold Sensitivity)**: **Added**. New task T050 explicitly covers the confidence threshold sweep (SC-005).
10. **T051 (Throughput Measurement)**: **Added**. New task T051 explicitly covers measuring inference time and throughput (SC-003).
11. **T015 (Oversampling Verification)**: **Added**. New task T015 explicitly verifies the >40% oversampling distribution (FR-001).
12. **T033b (Evaluator Independence)**: **Added**. New task T033b explicitly audits the evaluator logic for independence from state labels (FR-005).
13. **T028b (Injection Validation)**: **Added**. New task T028b explicitly validates that logged `injected_state` matches the injected instruction template (US-2).
14. **T020b (Feature Independence)**: **Added**. New task T020b explicitly verifies training features are distinct from evaluation metrics (FR-002).
15. **Dataset/Methodology Validity**: **Resolved**. Research.md updated to clarify that trajectories are derived/synthesized from SoCRATES prompts if a direct dataset is unavailable, and that the evaluator uses a CPU-compatible sentence-transformer. The classifier uses dynamic text features, not static metadata, for prediction.
16. **T054 Reference**: **Resolved**. All references to the non-existent task ID T054 have been removed from the plan.

## Detailed Task List (Phase 0 - Phase 2)

### Phase 0: Data & Feasibility
- **T014**: Generate filtered trajectories (oversampling).
- **T015**: **NEW** Verify >40% oversampling distribution. *Deliverable: `data/results/oversampling_report.json` with counts. Gate: Must pass >40%.*
- **T019**: Derive training data for classifier (dynamic text features).
- **T020**: Train logistic regression classifier. *Dependency: T019. Status: **Sequential**. (No [P] tag).*
- **T020b**: **NEW** Verify feature independence (classifier features vs. evaluator logic). *Deliverable: `data/results/feature_independence_audit.json`.*

### Phase 1: Implementation
- **T033**: Implement evaluator (sentence-transformer based).
- **T033b**: **NEW** Audit evaluator for independence from state labels. *Deliverable: `data/results/evaluator_independence_audit.json`.*
- **T045a**: Refactor runner to reuse split logic. *Status: Sequential (must complete before T024).*
- **T045b**: Add unit test in `tests/unit/test_data_flow.py`.
- **T043a**: Add unit tests in `tests/unit/test_classifier.py` (FR-002). *Specific functions: `test_classifier_predicts_correct_label`, `test_classifier_handles_low_confidence`.*
- **T043b**: Add unit tests in `tests/unit/test_evaluator.py` (FR-005). *Specific functions: `test_evaluator_independence`, `test_gap_score_calculation`.*
- **T047**: Add unit tests in `tests/unit/test_reproducibility.py` (statistical variance). *Specific logic: Verify variance < tolerance across runs.*

### Phase 2: Execution & Analysis
- **T028**: Run experiments (Adapter vs. Static). *Log `injected_state`. **Mandate**: Logs with `injected_state='neutral-monitoring'` are explicitly excluded from the primary 'Adapter Effect' calculation in T038c.*
- **T028b**: **NEW** Validate logged `injected_state` matches template. *Deliverable: `data/results/injection_validation_log.txt`.*
- **T038a**: Ingest data and determine active LLMs.
- **T038b**: Run normality test (Shapiro-Wilk) and **record p-value** in report.
- **T038c**: Run statistical test (t-test/Wilcoxon) and **apply Holm-Bonferroni**. *Logic: Exclude 'neutral-monitoring' logs from primary effect calculation.*
- **T038d**: Generate final statistical report.
- **T049**: Power analysis. *Logic: If underpowered, write flag to report and **continue** (no exit code 1).*
- **T050**: Threshold sensitivity sweep (SC-005). *Deliverable: `data/results/threshold_sensitivity_report.json`.*
- **T051**: Throughput measurement (SC-003). *Deliverable: `data/results/throughput_report.json`.*

### Phase 3: Validation
- **T044**: Run quickstart validation. *Deliverable: `data/results/quickstart_validation_log.txt` containing "SUCCESS". Exit code 0.*
