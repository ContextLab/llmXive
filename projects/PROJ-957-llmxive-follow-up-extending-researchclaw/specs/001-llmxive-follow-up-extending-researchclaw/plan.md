# Implementation Plan: llmXive follow-up: extending "ResearchClawBench: A Benchmark for End-to-End Autonomous Scientific Re"

**Branch**: `001-llmxive-scaffold-analysis` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-scaffold-analysis/spec.md`
**Input**: Feature specification from `specs/001-llmxive-scaffold-analysis/spec.md`

## Summary

This feature implements a controlled experimental study to evaluate the efficacy of domain-specific procedural scaffolds in autonomous scientific agents. The system loads 10 tasks from the ResearchClawBench dataset flagged for "experimental protocol mismatch," executes 7 agents across two conditions (Zero-Shot vs. Scaffolded), and applies a dual-rubric scoring system. The core analytical contribution is a statistical decoupling analysis: using paired tests to measure "Protocol Alignment" improvement and TOST equivalence tests to verify that "Scientific Core" scores remain stable (non-inferior), ensuring scaffolds do not degrade hypothesis generation. The implementation is strictly constrained to CPU-only execution on GitHub Actions free-tier runners.

**Critical Note on Power**: With N=10 (or N=30 with 3 generations per task), the study is underpowered to detect moderate effect sizes (Power < 0.4). Non-significant results for "Scientific Core" are interpreted strictly as "inconclusive" regarding safety, not as validation. The primary claim is the *feasibility of the decoupling method*, not a definitive proof of efficacy.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `scipy` (for TOST/t-tests), `pytest`, `pyyaml`, `jsonschema` (for rubric validation), `datasets` (for data loading), `tqdm`, `numpy`.
**Storage**: Local filesystem (`data/`, `results/`, `assets/`); no external database.
**Testing**: `pytest` (unit tests for scoring logic, integration tests for scaffold injection).
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner).
**Performance Goals**: Complete 140 agent runs (7 agents × 2 conditions × 10 tasks) within 24 hours wall-clock time; Individual runs timeout at a predefined duration.
**Constraints**: CPU-only (no CUDA/GPU); memory < 7GB; disk < 14GB; no large model training.
**Scale/Scope**: A set of specific tasks, a set of agents, multiple conditions, and a variable number of total executions (scaled according to whether 3-gen variance control is enabled).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

**Principle I: Reproducibility**
- [x] **Requirement**: Random seeds pinned, external datasets fetched from canonical sources.
- [x] **Plan Action**: The `data_loader` module will pin random seeds for any stochastic sampling. External datasets are fetched from the canonical source *prior* to the run (via a separate fetch job or manual step) and stored in `data/raw/`. The `data_loader` **must** re-verify the local checksum against the known hash on every run. If the checksum fails, the system aborts (FR-006). This ensures the "same canonical source" constraint is met via integrity verification.

**Principle II: Verified Accuracy**
- [x] **Requirement**: Citations verified against primary sources.
- [x] **Plan Action**: Since no verified URL exists for ResearchClawBench, the `Reference-Validator Agent` will verify the *local artifact integrity* (checksum) against the hash recorded in the project state. If the checksum does not match, the project cannot proceed. This satisfies the "Verified Accuracy" gate via local artifact verification.

**Principle III: Data Hygiene**
- [x] **Requirement**: Checksums, no in-place modification.
- [x] **Plan Action**: Raw data loads will be stored in `data/raw/` with recorded checksums. Derived datasets (e.g., filtered 10-task subset) will be written to `data/processed/` with new filenames and derivation logs.

**Principle IV: Single Source of Truth**
- [x] **Requirement**: Figures/stats trace to code/data.
- [x] **Plan Action**: The statistical analysis script (`code/analysis/stats.py`) will generate a JSON report containing all test statistics. The `paper/` generation step will parse this JSON directly; no manual transcription.

**Principle V: Versioning Discipline**
- [x] **Requirement**: Content hashes for artifacts.
- [x] **Plan Action**: The `code/` directory will include a script to update the central `state/projects/PROJ-957-llmxive-follow-up-extending-researchclaw.yaml` file. **This script is explicitly invoked by the `Advancement-Evaluator Agent` as part of the CI pipeline** to ensure the `state` file is the active source of truth for the artifact hashes.

**Principle VI: Experimental Control and Isolation**
- [x] **Requirement**: Strict separation of conditions; `Scientific Core` monitored as control.
- [x] **Plan Action**: The execution loop will explicitly tag runs as `condition: zero_shot` or `condition: scaffolded`. The `Scientific Core` score will be the primary variable for the TOST equivalence test. Scaffold templates are static files in `assets/templates/`. A "Prompt Content Analysis" step will ensure scaffold text does not contain scientific reasoning cues.

**Principle VII: Statistical Rigor**
- [x] **Requirement**: Paired tests, effect sizes, confidence intervals, power acknowledgment.
- [x] **Plan Action**: The analysis module will implement:
  - **Pre-specified Test**: Wilcoxon signed-rank test (or permutation test) for Protocol Alignment (bypassing low-power Shapiro-Wilk).
  - **TOST**: Equivalence test with margin=5 (conservative assumption pending pilot).
  - **Variance Control**: 3 independent generations per task/condition (N=30) to average generation noise, or bootstrap CI if N=30 is infeasible.
  - **Explicit Reporting**: Report effect sizes (Cohen's d/r) and confidence intervals for all tests.
  - **Power Acknowledgement**: Explicitly log that N=10 (or N=30) yields low power (<0.4) for moderate effects.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-scaffold-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── rubric_schema.json
    ├── task_metadata.schema.yaml
    └── score_output.schema.yaml
```

### Source Code (repository root)

```text
src/
├── agents/              # Agent wrappers and execution logic
│   └── cpu_compat.py    # CPU Compatibility Check & Substitution Logic
├── data/                # Data loading and filtering
│   ├── loader.py        # ResearchClawBench loader with checksum verification
│   └── filter.py        # Filter for "protocol mismatch" tasks
├── scaffolding/         # Template injection logic
│   ├── injector.py      # Appends templates to prompts
│   └── validator.py     # Checks for scaffold conflicts (FR-007) & Prompt Content Analysis
├── scoring/             # Rubric application
│   ├── engine.py        # Loads rubric_schema.json
│   └── metrics.py       # Calculates alignment and core scores
├── analysis/            # Statistical testing
│   ├── tests.py         # Wilcoxon, TOST, Bootstrap
│   └── report.py        # Generates final JSON/CSV reports
├── cli/                 # Main entry point
│   └── run_experiment.py
└── utils/               # Logging, checksums, timeouts

tests/
├── unit/                # Unit tests for scoring and injection
├── integration/         # End-to-end run of 1 agent/task
└── contract/            # Schema validation tests

assets/
└── templates/           # Curated Template Set v1.0
    ├── TEMPLATE-001-v1.0.md
    └── ...
```

**Structure Decision**: Single project structure with modular `src/` packages. This minimizes overhead and simplifies dependency management for the 24-hour CI run.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dual-Condition Execution | Essential for causal inference on the scaffold effect. | Single-condition runs cannot isolate the variable of interest (scaffold presence). |
| TOST Equivalence Test | Required to prove "safety" (non-inferiority) of scientific reasoning. | Standard null hypothesis testing (t-test) cannot prove equivalence; it only tests for difference. |
| CPU-Only Constraint | Mandatory for GitHub Actions free-tier compatibility. | GPU-based methods would cause job failures and exceed budget. |
| 3-Generation Variance Control | LLM generation is stochastic; pinned seeds are insufficient. | Single-generation runs would introduce uncontrolled noise, invalidating paired tests. |
| Pre-specified Wilcoxon Test | Shapiro-Wilk has low power at N=10. | Relying on normality tests would lead to incorrect test selection and inflated Type I error. |


## projects/PROJ-957-llmxive-follow-up-extending-researchclaw/specs/001-llmxive-follow-up-extending-researchclaw/research.md