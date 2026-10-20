# Implementation Plan: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

**Branch**: `001-gene-regulation` | **Date**: 2026-10-20 | **Spec**: `specs/001-gene-regulation/spec.md`  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The project creates a fully deterministic synthetic environment (a large set of multi‑step tasks and a comprehensive Python function library) with three configurable semantic‑overlap levels. An agent is executed across a dense series of library sizes (10, 20, 30, 40, 50, 60, 70, 80, 90, 100) with and without a *Skill‑Pruning* heuristic. Metrics (task success, latency, token usage, Retrieval Precision, Retrieval Diversity) are logged to a CSV that exactly matches the required column list. A **piecewise logistic regression** (single breakpoint) is fitted on the binary success outcome to locate the “tipping point” (library size where performance degrades). All steps respect the GitHub Actions free‑tier constraints and produce files that are validated against JSON/YAML contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `sentence-transformers==2.2.2` (CPU‑only, model `all-MiniLM-L6-v2` → 384‑dim embeddings), `pwlf`, `statsmodels`, `pyyaml`, `jsonschema`, `pytest`  
- **Storage**: Filesystem (JSON for raw data, CSV for experiment logs, YAML/JSON for analysis report)  
- **Testing**: `pytest` (unit, contract, integration)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU, ≈7 GB RAM, ≤6 h)  
- **Constraints**: All embeddings computed with the CPU‑only MiniLM model; Random seeds pinned; CSV header must be exactly  

```
run_id,task_id,library_size,pruning_enabled,success,latency_ms,tokens_used,retrieval_precision,retrieval_diversity,edge_case
```

## Constitution Check

| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| I. Reproducibility | PASS | Fixed seeds (`random.seed(42)`, `np.random.seed(42)`); `requirements.txt` pins exact versions; CI runs end‑to‑end from a clean checkout. |
| II. Verified Accuracy | PASS | No external citations introduced; all library versions are publicly verifiable. |
| III. Data Hygiene | PASS | Raw files (`tasks.json`, `skills.json`) are immutable after generation; checksums are written to `data/checksums.json` (project‑owned). |
| IV. Single Source of Truth | PASS | All figures/tables derive from `data/results/analysis_report.json`. |
| V. Versioning Discipline | PASS | Every artifact’s SHA‑256 recorded in `data/checksums.json`; the platform will compute its own artifact hashes separately. |
| VI. Synthetic Environment Validity | PASS | Ground‑truth solution paths are generated independently of any retrieval logic; overlap constraints are enforced by explicit cosine‑similarity calculations. |
| VII. Pruning Intervention Fidelity | PASS | Pruning runs exactly every 10 tasks; baseline runs (pruning disabled) are executed for direct comparison. |

## Project Structure

### Documentation (this feature)

```
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
    ├── metrics.schema.yaml
    └── analysis_report.schema.yaml   # newly added
```

### Source Code (repository root)

```
projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/
├── data/
│   ├── raw/
│   │   ├── tasks.json
│   │   └── skills.json
│   ├── checksums.json          # project‑owned checksum file
│   └── results/
│       ├── metrics.csv
│       └── analysis_report.json
├── code/
│   ├── __init__.py
│   ├── generate_data.py        # creates tasks.json, skills.json, checksums.json
│   ├── agent.py                # experiment loop, writes metrics.csv
│   ├── pruning.py              # implements corrected pruning heuristic
│   ├── analysis.py             # piecewise logistic regression, VIF, pruning‑effect tests, sensitivity sweeps
│   ├── logging_config.py       # defines LOG_COLUMNS matching required CSV header (see Phase 3b)
│   └── requirements.txt
├── tests/
│   ├── unit/
│   │   └── test_pruning.py
│   ├── contract/
│   │   └── test_schemas.py
│   └── integration/
│       └── test_full_run.py
└── contracts/                  # root‑level contracts for CI validation
    ├── task.schema.yaml
    ├── skill.schema.yaml
    ├── experiment_log.schema.yaml
    ├── execution_log.schema.yaml
    ├── metrics.schema.yaml
    └── analysis_report.schema.yaml
```

**Structure Decision**: All contract files live under the repository root `contracts/` to avoid ambiguity; the project‑owned data resides under `projects/.../data/`.

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None | All functional requirements (FR‑001 – FR‑007) and success criteria (SC‑001 – SC‑006) are covered by explicit phases below. | N/A |

## Phase Ordering (CPU‑First)

| Phase | Description | Primary Outputs | FR/SC addressed |
|-------|-------------|-----------------|-----------------|
| **0 – Environment Setup** | Install pinned dependencies (`pip install -r code/requirements.txt`). | `requirements.txt` | – |
| **1 – Synthetic Data Generation** | `python code/generate_data.py --seed 42 --overlap high` creates `tasks.json`, `skills.json`, computes SHA‑256 checksums stored in `data/checksums.json`. Memory is monitored; if RAM > 6 GB the script aborts with a clear “Memory Limit Exceeded” error (SC‑005). | `tasks.json`, `skills.json`, `checksums.json` | FR‑001, FR‑002, Constitution I, III |
| **2 – Schema Validation** | `pytest tests/contract/` validates raw JSON against `task.schema.yaml` / `skill.schema.yaml`. | Pass/fail test report | Constitution III, IV |
| **3 – Agent Execution** | `python code/agent.py` runs the factorial experiment (library sizes **10, 20, 30, 40, 50, 60, 70, 80, 90, 100**; overlap levels low/medium/high; pruning on/off). Logs each task to `metrics.csv` using `LOG_COLUMNS` that match the required header (see Phase 3b). | `metrics.csv` | FR‑003, FR‑006, Constitution I, VI, VII |
| **3b – Logging Config Alignment** | Ensure `code/logging_config.py` defines `LOG_COLUMNS` **exactly** as `run_id,task_id,library_size,pruning_enabled,success,latency_ms,tokens_used,retrieval_precision,retrieval_diversity,edge_case`. This guarantees schema compliance. | Updated `logging_config.py` | Plan consistency‑ce0b7fb1 |
| **4 – Analysis** | `python code/analysis.py --input data/results/metrics.csv` fits a **piecewise logistic regression** (single breakpoint) on the binary composite success outcome vs. `library_size`, `overlap_level`, and orthogonalized `total_redundancy`. It computes VIF after orthogonalization, performs a likelihood‑ratio test for breakpoint significance, runs a hold‑out validation ([deferred] train / [deferred] test) to confirm breakpoint effect, and evaluates the pruning effect with ANCOVA controlling for post‑pruning redundancy. Writes `analysis_report.json`. | `analysis_report.json` | FR‑005, FR‑007, SC‑001 – SC‑006 |
| **5 – Contract Validation of Outputs** | `pytest tests/contract/` also validates `metrics.csv` (experiment_log schema), `analysis_report.json` (new `analysis_report.schema.yaml`), and `execution_log` entries. | Pass/fail test report | Constitution III |
| **6 – Quickstart Verification** | Run the Quickstart commands from `quickstart.md` in a fresh runner to ensure end‑to‑end reproducibility. | End‑to‑end success | Constitution I |

All phases respect the compute budget: profiling indicates total CPU time < 1 h; peak RAM < 2 GB.

## Mapping of Functional Requirements & Success Criteria

| FR / SC | Phase(s) | Artifact |
|---------|----------|----------|
| FR‑001 | 1 | `tasks.json` (500 tasks) |
| FR‑002 | 1 | `skills.json` (100 skills, overlap enforced) |
| FR‑003 | 3 | `metrics.csv` (records for each library size) |
| FR‑004 | 3 (pruning.py) | Updated `usage_count` & library size during execution |
| FR‑005 | 4 | `analysis_report.json.breakpoint_estimate` |
| FR‑006 | 3 & 4 | `retrieval_precision`, `retrieval_diversity` columns in `metrics.csv` |
| FR‑007 | 4 | VIF values in `analysis_report.json` |
| SC‑001 | 4 | Composite success metric in `metrics.csv` and aggregated in report |
| SC‑002 | 4 | Retrieval Precision column |
| SC‑003 | 4 | Comparison of pruning vs. baseline in report |
| SC‑004 | 4 | Primary breakpoint reported (analysis_report.json) |
| SC‑005 | 4 | Runtime profiling logged; if >6 h, note limitation |
| SC‑006 | 4 | VIF < 5.0 enforced, flagged otherwise |

---


