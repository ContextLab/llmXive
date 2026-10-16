# Implementation Plan: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

**Branch**: `001-gene-regulation` | **Date**: 2026-10-16 | **Spec**: `specs/001-gene-regulation/spec.md`  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

The feature builds a deterministic synthetic environment (500 multi‑step tasks, 100 Python “skill” functions) with configurable semantic overlap (low/medium/high). An agent is executed across library sizes 10, 30, 50, 100, with and without a Skill‑Pruning heuristic. Metrics (task success, latency, token usage, Retrieval Precision, Retrieval Diversity) are logged, and a Piecewise Linear Regression (PLR) identifies the library‑size “tipping point”. All artifacts are validated against JSON/YAML contracts, and the entire pipeline runs on the GitHub Actions free‑tier CPU box.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `sentence-transformers` (CPU‑only), `pandas`, `numpy`, `pyyaml`, `pytest`, `jsonschema`, `pwlf`, `statsmodels`  
**Storage**: Filesystem (JSON for raw data, CSV for experiment logs, YAML for state)  
**Testing**: `pytest` (unit, contract, integration)  
**Target Platform**: Linux runner (GitHub Actions free tier: 2 CPU, 7 GB RAM)  
**Project Type**: Research CLI / Simulation Engine  
**Performance Goals**: Full factorial sweep (4 library sizes × 2 pruning flags × 3 overlap levels) completes < 6 h; peak RAM < 2 GB.  
**Constraints**: No GPU training; all embeddings computed on CPU; random seeds pinned for reproducibility.  
**Scale/Scope**: 500 tasks, 100 skills, 12 primary experimental configurations per overlap level.

> All quantitative claims (e.g., “< 6 h”) are based on feasibility calculations described in `research.md`.

## Constitution Check

| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| **I. Reproducibility** | PASS | Random seeds (`random`, `numpy`) are fixed in `generate_data.py`; `requirements.txt` pins exact package versions; CI runs end‑to‑end from scratch. |
| **II. Verified Accuracy** | PASS | No external citations are introduced; all references are to open‑source libraries that are publicly verifiable. |
| **III. Data Hygiene** | PASS | `generate_data.py` writes SHA‑256 checksums for `tasks.json`, `skills.json`, and `metrics.csv` into `state/projects/PROJ-975-...yaml`. Files are immutable after creation. |
| **IV. Single Source of Truth** | PASS | Every figure/table in the eventual paper will be derived from `data/results/analysis_report.json` (the sole source). |
| **V. Versioning Discipline** | PASS | All artifacts (code, data, state) are content‑hashed; the hash map lives in the same state YAML. |
| **VI. Synthetic Environment Validity** | PASS | Ground‑truth solution paths are generated independently of any retrieval logic; semantic overlap is enforced by explicit cosine‑similarity constraints (FR‑002). |
| **VII. Pruning Intervention Fidelity** | PASS | Pruning is triggered exactly every 10 tasks; baseline runs (pruning disabled) are executed in parallel for direct comparison (SC‑003). |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── task.schema.yaml
    ├── skill.schema.yaml
    ├── experiment_log.schema.yaml
    ├── execution_log.schema.yaml
    └── metrics.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/
├── data/
│   ├── raw/
│   │   ├── tasks.json
│   │   └── skills.json
│   └── results/
│       ├── metrics.csv
│       └── analysis_report.json
├── code/
│   ├── __init__.py
│   ├── generate_data.py        # creates tasks.json, skills.json, checksums, state yaml
│   ├── agent.py                # execution loop, logging via logging_config
│   ├── pruning.py              # Skill‑Pruning heuristic (FR‑004)
│   ├── analysis.py             # PLR, VIF, hypothesis tests, sensitivity sweeps
│   ├── logging_config.py       # implements get_logger() with LOG_COLUMNS including "edge_case"
│   └── requirements.txt
├── tests/
│   ├── unit/
│   │   └── test_pruning.py
│   ├── contract/
│   │   └── test_schemas.py     # validates real JSON/CSV files against contracts
│   └── integration/
│       └── test_full_run.py
├── state/
│   └── projects/
│       └── PROJ-975-llmxive-follow-up-extending-from-chatbot.yaml
└── contracts/                  # **Create directory: contracts/ at repository root**
    ├── task.schema.yaml
    ├── skill.schema.yaml
    ├── experiment_log.schema.yaml
    ├── execution_log.schema.yaml
    └── metrics.schema.yaml
```

**Structure Decision**: The `contracts/` directory is placed **at the repository root** (i.e., `contracts/`) to eliminate any ambiguity about relative paths. All schema files referenced by tests and CI live here, satisfying the verifier’s concern about “contracts (root level)”.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None | All FR/SC are covered; no principle violations detected. | N/A |

## Phase Ordering (CPU‑First)

1. **Generate Synthetic Data** – `generate_data.py` creates `tasks.json` & `skills.json`.  
2. **Validate Schemas** – `pytest tests/contract/` checks every file against its contract.  
3. **Execute Agent** – `agent.py` runs the factorial experiment, appends rows to `metrics.csv`.  
4. **Analyze Results** – `analysis.py` reads `metrics.csv`, fits PLR, computes VIF, runs hypothesis tests, writes `analysis_report.json`.  
5. **Report** – Quickstart steps (see `quickstart.md`) guide the researcher through the full pipeline.

---
