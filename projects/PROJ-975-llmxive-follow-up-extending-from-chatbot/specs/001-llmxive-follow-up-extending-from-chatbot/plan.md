# Implementation Plan: llmXive follow-up: extending “From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent”

**Branch**: `001-gene-regulation` | **Date**: 2026-10-25 | **Spec**: `specs/001-gene-regulation/spec.md`  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
We will build a fully deterministic synthetic environment (a substantial number of tasks, many Python “skill” functions) with three configurable semantic‑overlap levels. A factorial experiment will run the Digital Colleague agent across library sizes {smallest considered size, 20, 30, 40, 50, 60, 70, 80, 90, 100}, overlap levels (low, medium, high), and pruning on/off. All artifacts are validated against JSON/YAML contracts, and every step is designed to be CPU‑only and to finish well within the GitHub Actions free‑tier limits.

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
- **Constraints**: All embeddings computed with the CPU‑only MiniLM model; peak RAM < 2 GB; total wall‑clock < 1 h on a comparable runner. No GPU is required.

## Constitution Check

| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | PASS | Fixed seeds, pinned `requirements.txt`, end‑to‑end CI run. |
| II. Verified Accuracy | PASS | No external citations; all library versions are public. |
| III. Data Hygiene | PASS | Immutable raw files, checksums recorded in `data/checksums.json`. |
| IV. Single Source of Truth | PASS | All figures/tables derived from `analysis_report.json`. |
| V. Versioning Discipline | PASS | SHA‑256 of every artifact stored in `data/checksums.json`. |
| VI. Synthetic Environment Validity | PASS | Ground‑truth paths generated independently of retrieval logic; overlap constraints enforced mathematically. |
| VII. Pruning Intervention Fidelity | PASS | Pruning runs at regular task intervals.; baseline runs (pruning disabled) are executed for direct comparison. |

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
    ├── execution_log.schema.yaml
    ├── experiment_log.schema.yaml
    └── analysis_report.schema.yaml
```

### Source Code (repository root)

```
projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/
├── data/
│   ├── raw/
│   │   ├── tasks.json
│   │   └── skills.json
│   ├── checksums.json
│   └── results/
│       ├── metrics.csv
│       ├── analysis_report.json
│       └── runtime_report.json
├── code/
│   ├── __init__.py
│   ├── copy_contracts.py          # copies contracts & writes checksums
│   ├── generate_data.py           # creates tasks.json, skills.json, checksums.json
│   ├── write_checksums.py         # utility to recompute & verify SHA‑256
│   ├── logging_config.py          # defines LOG_COLUMNS
│   ├── agent.py                   # experiment loop, writes metrics.csv
│   ├── pruning.py                 # implements prune_fr04(library)
│   ├── analysis.py                # piecewise logistic regression, VIF, mediation
│   └── requirements.txt
├── tests/
│   ├── unit/
│   │   ├── test_generate_data.py
│   │   ├── test_write_checksums.py
│   │   ├── test_pruning.py
│   │   └── test_logging_config.py
│   ├── contract/
│   │   ├── test_contract_copy.py
│   │   ├── test_schemas.py
│   │   └── test_logging_schema.py
│   └── integration/
│       └── test_full_experiment.py
└── contracts/                         # copied to CI root for validation
    ├── task.schema.yaml
    ├── skill.schema.yaml
    ├── execution_log.schema.yaml
    ├── experiment_log.schema.yaml
    └── analysis_report.schema.yaml
```

**Structure Decision**: All contract files live under the repository root `contracts/` (project‑owned) to avoid any interaction with the platform‑owned `state/` directory. `copy_contracts.py` copies the exact schema files from the spec folder into `contracts/` and records their SHA‑256 in `data/checksums.json` (addresses T001 and T003).

## Phase Ordering (CPU‑First)

| Phase | Description | Primary Outputs | FR/SC addressed |
|-------|-------------|-----------------|-----------------|
| **0 – Environment Setup** | `pip install -r code/requirements.txt` | – | – |
| **1 – Contract Duplication & Verification** | `python code/copy_contracts.py` copies each contract file verbatim, computes SHA‑256, writes entries to `data/checksums.json`. Then `pytest tests/contract/test_contract_copy.py` asserts `src_hash == dst_hash` for every contract (loads `contract_hashes.json`). | `contracts/*`, updated `data/checksums.json` | T001, Constitution III, IV |
| **2 – Synthetic Data Generation** | `python code/generate_data.py --seed 42 --overlap high` creates `tasks.json`, `skills.json`, computes embeddings, enforces overlap thresholds, writes SHA‑256 of both files to `data/checksums.json`. Includes a memory‑guard that aborts with “Memory Limit Exceeded” if RAM > 6 GB. | `tasks.json`, `skills.json`, `checksums.json` | FR‑001, FR‑002, VI, V |
| **3 – Checksum Verification** | `python code/write_checksums.py data/raw/tasks.json data/raw/skills.json` recomputes SHA‑256 and asserts equality with entries in `data/checksums.json`. Unit test `tests/unit/test_write_checksums.py` validates this step. | Pass/fail report | T002, III |
| **4 – Schema Validation of Raw Data** | `pytest tests/contract/test_schemas.py -k "task or skill"` validates `tasks.json` & `skills.json` against `task.schema.yaml` / `skill.schema.yaml`. | Pass/fail report | III, IV |
| **5 – Agent Execution (Full Factorial)** | ```bash\npython code/agent.py \\\n --library-sizes 10 20 30 40 50 60 70 80 90 100 \\\n --overlap low medium high \\\n --pruning on off \\\n --seed 42 \\\n --randomize-tasks\n```\n*For each experimental configuration a **fresh random seed** is set and an **independent sample of tasks** (≈125 tasks) is drawn **without replacement** from a **larger master pool of [deferred] tasks**. This guarantees statistical independence across conditions (addresses methodology‑5add40b1).*\n*Pruning runs **exactly every 10 tasks** and follows FR‑004: a skill is removed **only if** `usage_count == 0` **and** `min_cosine_similarity_to_any_other_skill_in_library < 0.70` **and** the skill does **not** appear in any task’s `ground_truth_skills` (addresses plan_consistency‑0e9f06fd).*\n*Logs each task to `metrics.csv` using `LOG_COLUMNS`. Edge‑case tags (`missing_skill`, `max_overlap`, `memory_limit`) are recorded. | `metrics.csv`, `runtime_report.json` | FR‑003, FR‑006, VII |
| **6 – Runtime Profiling** | Wrapper records total wall‑clock time to `data/results/runtime_report.json` and adds the value to `data/checksums.json`. | `runtime_report.json` | SC‑005 |
| **7 – Execution‑Log Validation** | `pytest tests/contract/test_logging_schema.py` validates `metrics.csv` (experiment_log schema) **and** the JSON‑L execution logs against `execution_log.schema.yaml`. | Pass/fail report | III |
| **8 – Statistical Analysis** | `python code/analysis.py --input data/results/metrics.csv` performs: <br>• **Predictor set** (raw, not orthogonalized): `library_size` (continuous), `overlap_level` (categorical), `pruning_enabled` (binary), plus two‑way interactions (`library_size*pruning_enabled`, `overlap_level*pruning_enabled`). VIF is computed on these raw predictors (must be < 5). <br>• **Total Redundancy**: measured mean pairwise cosine similarity among the *active* library’s embeddings after pruning; varies with random skill generation, satisfying independence from `library_size`. <br>• **Piecewise Logistic Regression (PLR)**: two‑segment logistic model on binary exact‑match success using `pwlf`. Breakpoint `x₀` is the “tipping point”. <br>• **Bootstrap CI**: 1 000 resamples → 95 % CI for `x₀`. <br>• **Likelihood‑Ratio Test**: compare PLR vs. single‑segment logistic model (p‑value). <br>• **Mediation**: test indirect effect of pruning via observed `total_redundancy`, using the raw predictors (no orthogonalization). <br>• **VIF**: reported for raw predictors; analysis aborts with warning if any VIF ≥ 5. <br>• **Power analysis** (Section 4) reports the achieved power given the per‑condition sample size (~125). <br>Writes `analysis_report.json`. | `analysis_report.json` | FR‑005, FR‑007, SC‑001 – SC‑006 |
| **9 – Analysis‑Report Validation** | `pytest tests/contract/test_schemas.py -k "analysis_report"` validates `analysis_report.json` against its schema. | Pass/fail report | III |
| **10 – Quickstart Verification** | Run the commands from `quickstart.md` on a fresh runner; confirm that the final `analysis_report.json` matches the one produced in Phase 8. | Identical `analysis_report.json` | I |

All phases respect the Limited‑duration CI limit (empirical profiling < 1 h) and stay under a modest RAM usage limit. No GPU is required.

## Mapping of Functional Requirements & Success Criteria

| FR / SC | Phase(s) | Artifact |
|---------|----------|----------|
| FR‑001 | 2 | `tasks.json` |
| FR‑002 | 2 | `skills.json` |
| FR‑003 | 5 | `metrics.csv` |
| FR‑004 | 5 (pruning.py) | Updated library size during execution |
| FR‑005 | 8 | `analysis_report.json.breakpoint_estimate` |
| FR‑006 | 5 & 8 | `retrieval_precision`, `retrieval_diversity` columns |
| FR‑007 | 8 | VIF values in `analysis_report.json` |
| SC‑001 | 8 | Success‑rate column & aggregated statistic |
| SC‑002 | 8 | Retrieval Precision column |
| SC‑003 | 8 | Pruning vs. baseline comparison in report |
| SC‑004 | 8 | Breakpoint estimate |
| SC‑005 | 6 | Runtime report logged; note if > 6 h |
| SC‑006 | 8 | VIF < 5.0 enforced; flagged otherwise |

---

