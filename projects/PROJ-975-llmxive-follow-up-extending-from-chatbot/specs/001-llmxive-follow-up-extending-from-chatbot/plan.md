# Implementation Plan: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

**Branch**: `001-gene-regulation` | **Date**: 2026-07-12 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This feature implements a synthetic experimental environment to test the "Digital Colleague" hypothesis. The system generates a deterministic dataset of 500 multi-step tasks and a configurable library of 100 Python skills with controlled semantic overlap. It executes a minimal agent across library sizes (10, 30, 50, 100) to measure task success rates, latency, and retrieval fidelity. The core analysis identifies a "tipping point" via Piecewise Linear Regression and evaluates a "Skill Pruning" heuristic to mitigate performance degradation. All results are measured against ground-truth solution paths and validated via contract schemas.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `sentence-transformers` (CPU), `pandas`, `numpy`, `pyyaml`, `pytest`, `jsonschema`  
**Storage**: Filesystem (JSON for data, YAML for state)  
**Testing**: `pytest` (unit, contract, integration)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7 GB RAM)  
**Project Type**: Research CLI / Simulation Engine  
**Performance Goals**: Complete 500 tasks x 4 library sizes x 2 pruning states within 6 hours; Memory < 7 GB during embedding calculation.  
**Constraints**: No GPU training; embeddings computed on CPU; synthetic data must be reproducible (seeded).  
**Scale/Scope**: 500 tasks, 100 skills, 4 experimental configurations.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `code/generate_data.py` will pin `random.seed` and `numpy.random.seed`. `requirements.txt` will pin versions. CI runs against `data/raw`. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` will reference only verified sources (or synthetic generation logic). No external URLs invented. |
| **III. Data Hygiene** | **PASS** | `code/generate_data.py` will generate checksums (SHA-256) for `tasks.json` and `skills.json` and record them in `state/...yaml`. Raw data immutable. |
| **IV. Single Source of Truth** | **PASS** | Metrics in `data/results/` will be the sole source for `paper/`. No manual typing of numbers. |
| **V. Versioning Discipline** | **PASS** | All artifacts (code, data, state) will carry content hashes. State YAML updated on every run. |
| **VI. Synthetic Environment Validity** | **PASS** | Ground-truth paths generated independently of retrieval logic (FR-001). Semantic overlap controlled via cosine similarity constraints (FR-002). |
| **VII. Pruning Intervention Fidelity** | **PASS** | Pruning logic (FR-004) strictly follows "every 10 tasks" rule. Baseline comparison (pruning off) implemented for direct contrast (SC-003). |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── task.schema.yaml
    ├── skill.schema.yaml
    └── experiment_log.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/
├── data/
│   ├── raw/
│   │   ├── tasks.json
│   │   └── skills.json
│   └── results/
│       └── metrics.csv
├── code/
│   ├── __init__.py
│   ├── generate_data.py       # Synthetic data generation (FR-001, FR-002)
│   ├── agent.py               # Agent execution loop (FR-003)
│   ├── pruning.py             # Pruning heuristic (FR-004)
│   ├── analysis.py            # PLR, VIF, Metrics (FR-005, FR-006, FR-007)
│   ├── logging_config.py      # Logger setup (T007 fix)
│   └── requirements.txt
├── tests/
│   ├── unit/
│   │   └── test_pruning.py
│   ├── contract/
│   │   └── test_schemas.py    # Validates data against contracts (T011, T012 fix)
│   └── integration/
│       └── test_full_run.py
├── state/
│   └── projects/
│       └── PROJ-975-llmxive-follow-up-extending-from-chatbot.yaml
└── contracts/
    ├── task.schema.yaml       # Contract for tasks.json (T011 fix)
    ├── skill.schema.yaml      # Contract for skills.json (T012 fix)
    └── experiment_log.schema.yaml # Contract for metrics.csv (T007 fix)
```

**Structure Decision**: Single-project structure selected to simplify the data flow from generation to analysis. `contracts/` placed at the root of the feature directory to ensure schema visibility to the test runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations detected. | N/A |

## Unresolved panel concerns (addressed)

- **Task T001 Ambiguity**: The directory structure explicitly defines `contracts/` at the feature root (not root of repo) to align with `tasks.md` paths. The plan clarifies `contracts/` is a sibling to `code/` and `data/` within the feature scope.
- **Task T035 Sensitivity Analysis**: The `analysis.py` module will implement a sensitivity sweep but will report the **primary** tipping point derived from the standard configuration (10, 30, 50, 100) as the main result for SC-004. The sweep results will be stored as a secondary artifact (`data/results/sensitivity_analysis.json`) to ensure SC-004 remains measurable against a single, defined breakpoint.

## Tasks an independent verifier REJECTED (redo these)

- **T007 (Logging)**: `code/logging_config.py` will be implemented to fully construct the logger and include the `edge_case` column in the CSV header as defined in `LOG_COLUMNS`. `contracts/experiment_log.schema.yaml` will be created to validate the output.
- **T011 (Task Schema)**: `contracts/task.schema.yaml` will be created. `tests/contract/test_schemas.py` will load `data/raw/tasks.json` and validate it against this schema.
- **T012 (Skill Schema)**: `contracts/skill.schema.yaml` will be created. `tests/contract/test_schemas.py` will load `data/raw/skills.json` and validate overlap metrics.
- **T015 (Data Generation)**: `code/generate_data.py` will include full serialization logic, checksum generation, and state update logic to produce `tasks.json`, `skills.json`, and update `state/...yaml`.
