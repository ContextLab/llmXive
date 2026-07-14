# Implementation Plan: llmXive follow-up: extending "ResearchClawBench: A Benchmark for End-to-End Autonomous Scientific Re"

**Branch**: `001-llmxive-scaffold-analysis` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-scaffold-analysis/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-scaffold-analysis/spec.md`

## Summary

This feature implements a comparative analysis of autonomous scientific agents on the ResearchClawBench dataset. The core intervention is the injection of domain-specific procedural templates ("Scaffolds") into the agent's system prompt to address "experimental protocol mismatch" failures. The system executes a set of specific tasks under two conditions (Zero-Shot vs. Scaffolded) using multiple distinct agents, applies a dual-metric rubric (Protocol Alignment, Scientific Core), and performs rigorous statistical analysis (paired t-test/Wilcoxon for alignment; TOST for safety of scientific core) to determine if scaffolding improves protocol adherence without degrading scientific reasoning. All execution is constrained to CPU-only GitHub Actions runners with limited cores and RAM, with strict timeouts.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn` (statistical tests), `pandas` (data manipulation), `pyyaml` (config), `requests` (dataset fetching), `datasets` (HuggingFace loader), `pytest` (testing).  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `results/`). No external database.  
**Testing**: `pytest` with contract tests against `rubric_schema.json` and `constraint_keywords.yaml` (used as fixtures).  
**Target Platform**: GitHub Actions `ubuntu-latest` (CPU-only, 2 cores, 7GB RAM).  
**Project Type**: Research Data Pipeline & Statistical Analysis.  
**Performance Goals**: Complete multiple agent runs (multiple agents × conditions × 10 tasks) within a duration of approximately one day.; individual run timeout set to a fixed duration.  
**Constraints**: No GPU; strict memory limits (<7GB); no external API calls during execution (datasets pre-fetched); reproducible random seeds.  
**Scale/Scope**: A moderate number of tasks, 7 agents, conditions, Multiple executions.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/config.py`; datasets fetched from canonical sources (verified URLs) with checksums; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | T007a implements a blocking gate that logs/report 'Verified Accuracy' status. If dataset sources are unverified, the system aborts (FR-006). |
| **III. Data Hygiene** | **PASS** | Derived datasets (a task subset) written to `data/processed/` with SHA-256 checksums (T008). No in-place modifications; raw data preserved. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final report are derived programmatically from `results/paired_scores.json`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | T007 and T008 ensure all artifacts carry content hashes and the state file is updated on artifact changes. |
| **VI. Experimental Control** | **PASS** | Scaffolded vs. Zero-Shot conditions strictly isolated. Templates derived from open-access manuals, not target papers. `Scientific Core` monitored as a safety control. |
| **VII. Statistical Rigor** | **PASS** | Paired tests (t-test/Wilcoxon) with effect sizes and CIs required. TOST with margin=5 for safety. Power limitations (<0.4 for N=10) explicitly acknowledged and reported as "inconclusive" if not met. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-scaffold-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── rubric_schema.json
│   ├── constraint_keywords.yaml
│   ├── task_metadata.schema.yaml
│   └── score_output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-957-llmxive-follow-up-extending-researchclaw/code/
├── main.py                  # Entry point for orchestration
├── config.py                # Configuration (seeds, paths, timeouts)
├── data/
│   ├── loader.py            # Dataset fetching & filtering
│   ├── filter.py            # Logic to select 10 "protocol mismatch" tasks
│   └── checksum.py          # Checksum generation & verification
├── agents/
│   ├── loader.py            # Agent factory (loads 7 specific agents from agents_config.yaml)
│   └── executor.py          # Execution loop with h timeout & concurrency
├── scaffolding/
│   ├── template_loader.py   # Loads templates from assets/templates/
│   └── validator.py         # Validates template vs. task constraints (FR-007)
├── scoring/
│   ├── engine.py            # Applies rubric_schema.json
│   └── dummy_test.py        # Contract test (FR-008)
├── analysis/
│   ├── stats.py             # TOST, t-test, Wilcoxon, effect sizes
│   └── report.py            # Generates final CSV/JSON reports
└── tests/
    ├── test_contract.py     # Rubric and constraint validation tests
    └── test_integration.py  # End-to-end pipeline test

data/
├── raw/                     # Raw dataset (if fetched)
└── processed/
    └── 10_tasks_protocol_mismatch.json  # Derived dataset with checksum

results/
├── failure_mode_audit.csv   # Audit of dominant failure modes
├── paired_scores.json       # Final analysis dataset
└── logs/                    # Execution logs
```

**Structure Decision**: Selected a modular single-project structure (Option 1) to maintain tight coupling between data loading, agent execution, and analysis, which is critical for reproducible research pipelines. The `agents/` directory isolates the 7 specific agent implementations, while `scaffolding/` and `scoring/` handle the experimental intervention and evaluation logic respectively.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Dual-Condition Execution** | Required by FR-003 to isolate the effect of scaffolding. | A single-condition run would not allow for paired statistical testing (FR-005) or control for agent-specific variance. |
| **TOST Equivalence Test** | Required by FR-005 to establish a "safety bound" for Scientific Core. | Standard null-hypothesis testing cannot prove "no difference" (equivalence); TOST is the statistical standard for non-inferiority. |
| **Constraint Validation (FR-007)** | Required to prevent scaffold-task conflicts. | Blindly injecting templates risks invalidating the scientific core (e.g., conflicting constraints), leading to uninterpretable results. |
| **CPU-Only Execution** | Required by platform constraints (GitHub Actions free tier). | GPU/Quantization methods are unavailable; the design must rely on CPU-tractable agents and sampled data. |

## Phase Breakdown

### Phase 0: Research & Feasibility (Week 1)
- **T001**: Verify ResearchClawBench dataset availability and metadata schema (specifically `failure_mode` field).
- **T002**: Identify and document the 7 CPU-tractable agents from the original study.
- **T003**: Source and verify the "Curated Template Set v1.0" from open-access manuals (specific URLs).
- **T004**: Define the statistical power analysis for N=10 and document limitations.
- **T005**: Draft `rubric_schema.json` and `constraint_keywords.yaml` drafts.

### Phase 1: Data Model & Contracts (Week 2)
- **T006**: Define `config.py` schema (seeds, paths, timeouts).
- **T007**: Implement `checksum.py` for data integrity.
- **T007a**: Implement "Verified Accuracy" blocking gate (logs status, aborts on unverified sources).
- **T008**: Implement `filter.py` to select 10 tasks and **persist** to `data/processed/10_tasks_protocol_mismatch.json` with **SHA-256 checksum**.
- **T009**: Create `template_map.json` and `TEMPLATE-001-v1.0.md` (from verified URL).
- **T009b**: Define, populate, and validate `contracts/constraint_keywords.yaml` (T009b).
- **T009c**: Implement logic to validate template-domain match (T009c).
- **T010a**: Finalize `rubric_schema.json` (Protocol Alignment & Scientific Core).
- **T010b**: Implement scoring engine logic (T010b).
- **T011**: Define `task_metadata.schema.yaml`.
- **T012**: Define `agents_config.yaml` (7 agents) and `agents/loader.py`.
- **T013**: Implement `scaffolding/template_loader.py`.
- **T014**: Implement `scaffolding/validator.py` (FR-007).
- **T015**: Implement `scoring/dummy_test.py` (FR-008).

### Phase 2: Execution Engine (Week 3)
- **T016**: Implement `agents/executor.py` with a configurable timeout..
- **T023a**: Implement 24-hour wall-clock budget enforcement and concurrency controller (limit=7).
- **T024**: Implement `analysis/stats.py` (TOST, t-test, Wilcoxon, effect sizes).
- **T025**: Implement `analysis/report.py`.
- **T026**: End-to-end integration test.

### Phase 3: Experiment Execution (Week 4)
- **T027**: Run Zero-Shot condition (agents × 10 tasks).
- **T028**: Run Scaffolded condition (agents × 10 tasks).
- **T029**: Score all runs and generate `results/paired_scores.json`.
- **T030**: Generate `results/failure_mode_audit.csv`.

### Phase 4: Analysis & Reporting (Week 5)
- **T031**: Perform statistical tests (Shapiro-Wilk check -> t-test/Wilcoxon).
- **T032**: Calculate effect sizes (Cohen's d or rank-biserial r) and CIs.
- **T033**: Generate final report with TOST results (margin=5).
- **T034**: Write discussion on power limitations and interpretation.
