# Implementation Plan: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

**Branch**: `001-gene-regulation` | **Date**: 2026-10-16 | **Spec**: `specs/001-gene-regulation/spec.md`  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

The feature creates a fully deterministic synthetic environment (500 multi‑step tasks, 100 Python “skill” functions) with configurable semantic overlap. An agent is executed across library sizes 10, 30, 50, 100, with and without a Skill‑Pruning heuristic. Metrics (success rate, latency, token usage, Retrieval Precision, Retrieval Diversity) are logged, and a Piecewise Linear Regression (PLR) identifies the library‑size “tipping point”. All artifacts are validated against JSON/YAML contracts, and the entire pipeline runs on the GitHub Actions free‑tier CPU box.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `sentence-transformers` (CPU‑only), `pandas`, `numpy`, `pyyaml`, `pytest`, `jsonschema`, `pwlf` (Piecewise Linear Fit)  
**Storage**: Filesystem (JSON for raw data, CSV for experiment logs, YAML for state)  
**Testing**: `pytest` (unit, contract, integration)  
**Target Platform**: Linux runner (GitHub Actions free tier: 2 CPU, 7 GB RAM)  
**Project Type**: Research CLI / Simulation Engine  
**Performance Goals**: Full factorial sweep (4 library sizes × 2 pruning flags × 3 overlap levels) completes < 6 h; peak RAM < 2 GB.  
**Constraints**: No GPU training; all embeddings computed on CPU; random seeds pinned for reproducibility.  
**Scale/Scope**: 500 tasks, 100 skills, 12 experimental configurations per overlap level.

> All quantitative claims (e.g., “< 6 h”) are based on feasibility calculations described in `research.md`.

## Constitution Check

| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| **I. Reproducibility** | PASS | Random seeds (`random`, `numpy`) are fixed in `generate_data.py`; `requirements.txt` pins exact package versions; CI runs end‑to‑end from scratch. |
| **II. Verified Accuracy** | PASS | No external citations are introduced; all references are to the synthetic generation process or to open‑source libraries that are publicly verifiable. |
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
│   ├── logging_config.py       # full logger with LOG_COLUMNS including "edge_case"
│   └── requirements.txt
├── tests/
│   ├── unit/
│   │   └── test_pruning.py
│   ├── contract/
│   │   └── test_schemas.py     # loads real JSON files and validates against contracts
│   └── integration/
│       └── test_full_run.py
├── state/
│   └── projects/
│       └── PROJ-975-llmxive-follow-up-extending-from-chatbot.yaml
└── contracts/                  # **Explicitly at repository root** (matches T001 resolution)
    ├── task.schema.yaml
    ├── skill.schema.yaml
    ├── experiment_log.schema.yaml
    ├── execution_log.schema.yaml
    └── metrics.schema.yaml
```

**Structure Decision**: The `contracts/` directory is placed at the repository root (i.e., `projects/.../contracts`) to eliminate ambiguity from the earlier specification (T001). All schema files referenced by tests and CI live here.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None | All FR/SC are covered; no principle violations detected. | N/A |

## Tasks to Resolve Prior Verifier Rejections

| Task | Resolution |
|------|------------|
| **T007 – Logging** | `logging_config.py` will implement `get_logger(name: str) -> logging.Logger` that sets up a `FileHandler` writing CSV rows with columns `run_id,task_id,library_size,pruning_enabled,success,latency_ms,tokens_used,retrieval_precision,retrieval_diversity,edge_case`. The `"edge_case"` column is required by `experiment_log.schema.yaml`. |
| **T011 – Task Schema Test** | `tests/contract/test_schemas.py` will load the actual `data/raw/tasks.json`, parse each entry, and validate against `contracts/task.schema.yaml` using `jsonschema.validate`. |
| **T012 – Skill Schema Test** | The same test suite will load `data/raw/skills.json`, validate against `contracts/skill.schema.yaml`, and additionally compute the mean pairwise cosine similarity to assert the requested overlap level (low/medium/high). |
| **T015 – Data Generation** | `generate_data.py` will (1) create deterministic `tasks.json` and `skills.json`, (2) compute SHA‑256 checksums, (3) write those checksums plus a timestamp into `state/projects/PROJ-975-...yaml`. All files are written atomically and are immutable thereafter. |

## Phase Ordering (CPU‑First)

1. **Download / Create** – No external download; `generate_data.py` creates raw JSON files.
2. **Validate** – Contract tests (`pytest tests/contract/`) ensure schema compliance.
3. **Execute** – `agent.py` runs the experiment loops, logs to `metrics.csv`.
4. **Analyze** – `analysis.py` reads `metrics.csv`, fits PLR, computes VIF, runs hypothesis tests, writes `analysis_report.json`.
5. **Report** – Quickstart steps (see `quickstart.md`) guide the researcher through the full pipeline.

---
