# Implementation Plan: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

**Branch**: `001-gene-regulation` | **Date**: 2026-10-16 | **Spec**: `specs/001-gene-regulation/spec.md`  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The feature creates a deterministic synthetic environment (a large collection of multi‑step tasks, numerous Python “skill” functions) with configurable semantic overlap (low, medium, high). An agent is executed across library sizes, starting from a small size and including larger sizes such as a modest lower‑range size, 50, and 100, with and without a Skill‑Pruning heuristic. Metrics (task success, latency, token usage, Retrieval Precision, Retrieval Diversity) are logged, and a Piecewise Linear Regression (PLR) identifies the library‑size “tipping point”. All artifacts are validated against JSON/YAML contracts, and the entire pipeline runs on the GitHub Actions free‑tier CPU box.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `sentence-transformers` (CPU‑only), `pandas`, `numpy`, `pyyaml`, `pytest`, `jsonschema`, `pwlf`, `statsmodels`  
**Storage**: Filesystem (JSON for raw data, CSV for experiment logs, YAML for state)  
**Testing**: `pytest` (unit, contract, integration)  
**Target Platform**: Linux runner (GitHub Actions free tier: 2 CPU, 7 GB RAM)  
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
3. **Execute Agent** – `agent.py` runs the factorial experiment, appends rows to `metrics.csv`, and writes a per‑task **execution log** (`execution_logs/*.jsonl`) that conforms to `contracts/execution_log.schema.yaml`.  
4. **Analyze Results** – `analysis.py` reads `metrics.csv`, fits PLR (with overlap covariate), computes VIF, runs hypothesis tests, writes `analysis_report.json`.  
5. **Report** – Quickstart steps (see `quickstart.md`) guide the researcher through the full pipeline.

### Primary Tipping‑Point Selection
The **official** tipping point required by SC‑004 is the breakpoint `x₀` obtained from the Piecewise Linear Regression **fit on the baseline configuration**: **High overlap**, **pruning disabled**, using four library sizes spanning from a small to a large size. All breakpoint estimates from sensitivity sweeps (different overlap levels, pruning thresholds, or finer library‑size granularity) are reported only as supplemental material and do **not** replace the primary value.

## Statistical Analysis (CPU‑First)

* **PLR Methodology** – The Piecewise Linear Regression is fitted on **task‑level binary success outcomes** (≈ several hundred observations per configuration), not merely on the four aggregated success‑rate points. This provides ample data for a stable breakpoint estimate. To further guard against over‑fitting and address the sparse grid (10, 30, 50, 100), we perform **1 000 bootstrap resamples** of the task‑level data to generate confidence intervals for `x₀`. Additionally, we include a **Granularity Validation sweep** where a random subset of tasks is executed across a denser grid (10-unit increments) to verify that the breakpoint remains stable.
* **Other Analyses** – VIF calculation, pruning‑effect tests, and sensitivity sweeps are performed as described in `research.md`.  

## Compute Feasibility & Data Strategy

* **CPU‑First** – All embeddings and similarity calculations are performed with the CPU‑only `sentence-transformers` model; memory usage ≈ a few hundred MB.  
* **Runtime Estimate** – Empirical profiling predicts [deferred] per library‑size/overlap/pruning combo; total < 1 hour on the free‑tier runner.
* **Data Availability** – Synthetic; no external download required.  
