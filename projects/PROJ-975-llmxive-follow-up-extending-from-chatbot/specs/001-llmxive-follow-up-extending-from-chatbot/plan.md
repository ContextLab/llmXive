# Implementation Plan: llmXive follow-up: extending “From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent”

**Branch**: `001-gene-regulation` | **Date**: 2026-10-23 | **Spec**: `specs/001-gene-regulation/spec.md`  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
Create a fully deterministic synthetic environment (a substantial set of multi‑step tasks + 100 Python “skill” functions) with three configurable semantic‑overlap levels (low, medium, high). Run the Digital Colleague agent across a factorial set of library sizes (10‑100) **and** across all three overlap levels, with and without a **Skill‑Pruning** heuristic, logging a strict CSV schema. Fit a **piecewise logistic regression** (single breakpoint) on the binary exact‑match success outcome, compute VIF on orthogonalized predictors, and evaluate the pruning effect via a direct comparison and mediation analysis. All steps write only to **project‑owned** directories (`data/`, `code/`, `contracts/`) and are fully verified against JSON/YAML contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `pandas==2.2.2`  
  - `numpy==2.0.0`  
  - `scikit-learn==1.5.0`  
  - `sentence-transformers==2.2.2` (CPU‑only, model `all-MiniLM-L6-v2`)  
  - `pwlf==2.2.1`  
  - `statsmodels==0.14.2`  
  - `pyyaml==6.0.2`  
  - `jsonschema==4.22.0`  
  - `pytest==8.2.2`  
- **Storage**: Filesystem (JSON for raw data, CSV for experiment logs, YAML/JSON for analysis reports).  
- **Testing**: `pytest` (unit, contract, integration).  
- **Target Platform**: GitHub Actions free‑tier (2 CPU, ≈7 GB RAM, ≤6 h).  
- **Constraints**: All embeddings computed with the CPU‑only MiniLM model; peak RAM < 2 GB; total wall‑clock < 1 h; **no GPU** required.

## Constitution Check

| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Fixed seeds (`random.seed(42)`, `np.random.seed(42)`); `requirements.txt` pins exact versions; CI runs end‑to‑end from a clean checkout. |
| II. Verified Accuracy | PASS | No external citations are introduced; all library versions are publicly verifiable. |
| III. Data Hygiene | PASS | Raw files (`tasks.json`, `skills.json`) are immutable after generation; checksums stored in **project‑owned** `data/checksums.json`. |
| IV. Single Source of Truth | PASS | All figures/tables are generated from `data/results/analysis_report.json`. |
| V. Versioning Discipline | PASS | Every artifact’s SHA‑256 recorded in `data/checksums.json`. |
| VI. Synthetic Environment Validity | PASS | Ground‑truth solution paths are generated independently of any retrieval logic; overlap constraints are enforced mathematically. |
| VII. Pruning Intervention Fidelity | PASS | Pruning runs exactly at regular task intervals; baseline runs (pruning disabled) are executed for direct comparison. |

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
    └── analysis_report.schema.yaml
```

### Source Code (repository root)

```
projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/
├── data/
│   ├── raw/
│   │   ├── tasks.json
│   │   └── skills.json
│   ├── checksums.json               # project‑owned checksum file
│   ├── results/
│   │   ├── metrics.csv
│   │   ├── analysis_report.json
│   │   └── runtime_report.json      # total wall‑clock time
│   └── runtime_report.json          # duplicate for easy access
├── code/
│   ├── __init__.py
│   ├── generate_data.py              # creates tasks.json, skills.json, checksums.json
│   ├── copy_contracts.py              # copies spec contracts verbatim & records SHA‑256
│   ├── agent.py                       # experiment loop, writes metrics.csv
│   ├── pruning.py                     # implements `prune_redundant(library)` (FR‑004)
│   ├── analysis.py                    # piecewise logistic regression, VIF, mediation
│   ├── logging_config.py              # defines LOG_COLUMNS matching required CSV header
│   └── requirements.txt
├── tests/
│   ├── unit/
│   │   ├── test_pruning.py
│   │   └── test_generate_data.py
│   ├── contract/
│   │   └── test_schemas.py
│   └── integration/
│       └── test_full_run.py
└── contracts/                         # root‑level contracts for CI validation
    ├── task.schema.yaml
    ├── skill.schema.yaml
    ├── experiment_log.schema.yaml
    ├── execution_log.schema.yaml
    └── analysis_report.schema.yaml
```

**Structure Decision**: All contract files live under the repository root `contracts/` (project‑owned) to avoid any interaction with the platform‑owned `state/` directory. The `copy_contracts.py` script copies the exact schema files from `specs/.../contracts/` into `contracts/` and records their SHA‑256 in `data/checksums.json` for verification (addresses **T001**).

## Phase Ordering (CPU‑First)

| Phase | Description | Primary Outputs | FR/SC addressed |
|-------|-------------|-----------------|-----------------|
| **0 – Environment Setup** | `pip install -r code/requirements.txt` | – | – |
| **1 – Contract Duplication & Verification** | `python code/copy_contracts.py` copies each contract file verbatim from the spec folder, computes SHA‑256, writes entries to `data/checksums.json`, then runs `pytest tests/contract/` to validate schemas. | `contracts/*`, updated `data/checksums.json` | T001, Constitution III, IV |
| **2 – Synthetic Data Generation** | `python code/generate_data.py --seed 42 --overlap high` creates `tasks.json`, `skills.json`, computes embeddings, enforces overlap thresholds, writes SHA‑256 of both files to `data/checksums.json`. If RAM > 6 GB, aborts with clear `Memory Limit Exceeded` (SC‑005). | `tasks.json`, `skills.json`, `checksums.json` | FR‑001, FR‑002, VI, V |
| **3 – Schema Validation of Raw Data** | `pytest tests/contract/` validates `tasks.json` & `skills.json` against `task.schema.yaml` / `skill.schema.yaml`. | Pass/fail report | III, IV |
| **4 – Agent Execution** | `python code/agent.py \`<br>`  `--library-sizes 10 20 30 40 50 60 70 80 90 100 \`<br>`  `--overlap low medium high \`<br>`  `--pruning {on,off} \`<br>`  `--seed 42 \`<br>`  `--randomize-tasks`<br>Runs the full factorial experiment. For each configuration tasks are **randomly shuffled** and a **fresh sample without replacement** of 500 tasks is drawn, guaranteeing independence across runs. Logs each task to `metrics.csv` using `LOG_COLUMNS` defined in `logging_config.py`. Edge‑case tags (`missing_skill`, `max_overlap`, `memory_limit`) are recorded. | `metrics.csv` | FR‑003, FR‑006, VII |
| **5 – Runtime Profiling** | After the agent loop finishes, a tiny wrapper records the total wall‑clock time (seconds) to `data/results/runtime_report.json` and adds the value to `data/checksums.json`. | `runtime_report.json` | SC‑005 |
| **6 – Execution‑Log Validation** | `pytest tests/contract/` validates `metrics.csv` (experiment_log schema) **and** the JSON‑L execution logs against `execution_log.schema.yaml`. | Pass/fail report | III |
| **7 – Statistical Analysis** | `python code/analysis.py --input data/results/metrics.csv` performs: <br>• **Pre‑orthogonalization** of `library_size` and `total_redundancy` (center + QR) before fitting. <br>• **Piecewise logistic regression** (single breakpoint) on binary exact‑match success vs. predictors. <br>• **Bootstrap CI** (1 000 resamples) for breakpoint. <br>• **VIF** computed on orthogonalized predictors (must be < 5). <br>• **Mediation analysis** for pruning effect (direct effect + indirect via redundancy change). <br>• **Permutation test** for breakpoint significance. <br>Writes `analysis_report.json`. | `analysis_report.json` | FR‑005, FR‑007, SC‑001 – SC‑006 |
| **8 – Output Contract Validation** | `pytest tests/contract/` also validates `analysis_report.json` against its schema. | Pass/fail report | III |
| **9 – Quickstart Verification** | Run the Quickstart commands from `quickstart.md` on a fresh runner to ensure end‑to‑end reproducibility. | Identical `analysis_report.json` | I |

All phases respect the 6‑hour CI limit (empirical profiling < 1 h) and stay under 2 GB RAM. No GPU is required.

## Mapping of Functional Requirements & Success Criteria

| FR / SC | Phase(s) | Artifact |
|---------|----------|----------|
| FR‑001 | 2 | `tasks.json` |
| FR‑002 | 2 | `skills.json` |
| FR‑003 | 4 | `metrics.csv` |
| FR‑004 | 4 (pruning.py) | Updated library size during execution |
| FR‑005 | 7 | `analysis_report.json.breakpoint_estimate` |
| FR‑006 | 4 & 7 | `retrieval_precision`, `retrieval_diversity` columns |
| FR‑007 | 7 | VIF values in `analysis_report.json` |
| SC‑001 | 7 | Success rate column & aggregated statistic |
| SC‑002 | 7 | Retrieval Precision column |
| SC‑003 | 7 | Pruning vs. baseline comparison in report |
| SC‑004 | 7 | Breakpoint estimate |
| SC‑005 | 5 | Runtime report logged; note if >6 h |
| SC‑006 | 7 | VIF < 5.0 enforced; flagged otherwise |

---

