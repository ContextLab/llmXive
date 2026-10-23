# Implementation Plan: llmXive follow-up: extending "Self-Improving Language Models with Bidirectional Evolutionary Search"

**Branch**: `001-symbolic-bes` | **Date**: 2026-10-23 | **Spec**: `specs/001-symbolic-bes/spec.md`  
**Input**: Feature specification from `specs/001-symbolic-bes/spec.md`

## Summary
The project builds a deterministic verification pipeline for logic/arithmetic puzzles, replaces the neural backward step of the Bidirectional Evolutionary Search (BES) framework with a rule‑based symbolic planner, and evaluates the symbolic‑guided BES against a neural‑verifier baseline. Success is measured by success‑rate difference (paired McNemar’s test) and computational‑overhead difference (t‑test on CPU‑seconds), with additional scalability analysis. All components run on a CPU‑only GitHub Actions runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `datasets==2.18.0` – programmatic data handling (streaming if needed)  
  - `transformers==4.41.2` – small CPU‑only LLM (e.g., `gpt2`)  
  - `torch==2.2.2+cpu` – CPU‑only PyTorch backend  
  - `scikit-learn==1.5.0` – statistical tests  
  - `scipy==1.13.1` – t‑test & regression  
  - `pyyaml==6.0.1` – schema validation  
  - `pytest==8.2.2` – test runner  
- **Storage**: Local filesystem under `data/` (raw puzzles, verifier scripts, processed logs).  
- **Testing**: `pytest` for unit & integration suites.  
- **Target Platform**: GitHub Actions free‑tier (a limited number of CPU cores, ~7 GB RAM, no GPU).  
- **Performance Goals**:  
  - Verifier execution ≤ 100 ms per solution (FR‑001).  
  - Full experiment ≤ 6 h on CI runner.  
- **Constraints**: CPU‑only; no CUDA, no low‑bit quantization.  
- **Scale/Scope**: Synthetic puzzle dataset ranging N = 10 → 500, population size 30‑60, generations 10‑30 (tuned to fit runtime).

## Constitution Check
| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | PASS | `requirements.txt` pinned; seeds recorded in metadata; deterministic verifier scripts. |
| II. Verified Accuracy | PASS | All citations will be validated; alpha value `[ref-alpha]` is sourced from Wikipedia. |
| III. Data Hygiene | PASS | Checksums for every file in `data/`; raw data immutable. |
| IV. Single Source of Truth | PASS | All figures & statistics derived from `data/processed/` logs; no hand‑typed numbers. |
| V. Versioning Discipline | PASS | Content hashes stored in project state; any change updates timestamp. |
| VI. Deterministic Verification Integrity | PASS | Verification performed exclusively by external Python scripts (`code/dataset/verifier.py`). |
| VII. Computational Efficiency Benchmarking | PASS | CPU‑seconds measured directly for **both** symbolic‑guided and neural‑verifier runs; no GPU‑hour estimation used. |

## Project Structure
```text
specs/001-symbolic-bes/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
projects/PROJ-884-llmxive-follow-up-extending-self-improvi/
├── data/
│   ├── raw/               # generated puzzle definitions & verifier scripts
│   └── processed/         # logs, BES runs, analysis results
├── code/
│   ├── __init__.py
│   ├── utils/
│   │   └── seed.py
│   ├── dataset/
│   │   ├── __init__.py
│   │   ├── generator.py          # puzzle generation (FR‑001)
│   │   └── verifier.py           # deterministic verification (FR‑001)
│   ├── symbolic/
│   │   ├── __init__.py
│   │   ├── parser.py             # parse formal constraints
│   │   └── planner.py            # sub‑goal decomposition (FR‑002, FR‑006)
│   ├── bes/
│   │   ├── __init__.py
│   │   ├── population.py         # manage candidate solutions
│   │   ├── forward_step.py       # CPU LLM recombination (FR‑003)
│   │   └── backward_step.py      # symbolic planner integration (FR‑002)
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── metrics.py            # success‑rate & cost aggregation (FR‑004)
│   │   └── stats.py              # McNemar’s test, t‑test, TOST, power checks (FR‑005)
│   └── main.py                   # experiment entry point
├── tests/
│   ├── unit/
│   │   ├── test_generator.py          # imports DataGenerationError (T001 fixed)
│   │   ├── test_verifier.py
│   │   └── test_symbolic_planner.py   # catches ParseFailure & ContradictionDetected (T002 fixed)
│   └── integration/
│       └── test_bes_loop.py
├── requirements.txt
└── README.md
```

## Mapping of Functional & Success Criteria to Plan Tasks
| Requirement | Covered By |
|-------------|------------|
| **FR‑001** | `code/dataset/generator.py` + `code/dataset/verifier.py` (Phase 1 tasks 1.1‑1.2) |
| **FR‑002** | `code/symbolic/planner.py` (Phase 1 task 1.3) |
| **FR‑003** | `code/bes/forward_step.py` (Phase 1 task 1.4) |
| **FR‑004** | `code/analysis/metrics.py` (Phase 1 task 1.5) |
| **FR‑005** | `code/analysis/stats.py` (Phase 1 task 1.5) |
| **FR‑006** | Planner returns `ParseFailure` / `ContradictionDetected`; logger records exclusion (Phase 1 task 1.3) |
| **SC‑001** | Success‑rate comparison via **paired McNemar’s test** (Phase 2 task 2.4) |
| **SC‑002** | Computational‑overhead comparison via **independent t‑test** on CPU‑seconds (Phase 2 task 2.4) |
| **SC‑003** | Planner‑generated sub‑goals validated before LLM call (Phase 1 task 1.3 & 1.4) |
| **SC‑004** | McNemar’s test p‑value output (Phase 2 task 2.4) |
| **SC‑005** | Log‑log regression on `complexity_metric` vs. runtime (Phase 2 task 2.4) |

## Implementation Phases & Tasks
### Phase 0 – Research & Design
- **0.1** Finalize synthetic puzzle generation strategy (type, scaling, reproducibility).  
- **0.2** Define statistical analysis plan (McNemar’s test, TOST, t‑test, power analysis) – **alpha = 0.0497** `[ref-alpha]`.  
- **0.3** Select CPU‑only LLM (e.g., `gpt2`) and verify it fits within CI memory/time budget.  
- **0.4** Draft contracts (`dataset.schema.yaml`, `output.schema.yaml`) and validate against mock data.  

### Phase 1 – Data & Core Logic
| Task | Description | FR/SC |
|------|-------------|-------|
| **1.1** | Implement `code/dataset/generator.py` to create puzzles of varying N, write JSONL + verifier scripts. | FR‑001 |
| **1.2** | Implement `code/dataset/verifier.py` – deterministic, returns `(bool, error_code)` within 100 ms. | FR‑001 |
| **1.3** | Implement `code/symbolic/planner.py` with proper exception classes `ParseFailure` and `ContradictionDetected`; ensure exclusion logging (FR‑002, FR‑006). | FR‑002, FR‑006 |
| **1.4** | Implement `code/bes/forward_step.py` using a small CPU LLM to recombine trajectories guided by planner sub‑goals. | FR‑003 |
| **1.5** | Implement `code/analysis/metrics.py` and `stats.py` for success‑rate, cost aggregation, McNemar’s test, TOST, t‑test, and power checks (FR‑004, FR‑005). | FR‑004, FR‑005 |
| **1.6** | **Fix Test Suite Issue T001** – add `from code.dataset.errors import DataGenerationError` to `tests/unit/test_generator.py`. | — |
| **1.7** | **Fix Test Suite Issue T002** – modify `tests/unit/test_symbolic_planner.py` to catch `ParseFailure` and `ContradictionDetected` (real exception classes). | — |
| **1.8** | Validate generated puzzle files against `contracts/dataset.schema.yaml`. | — |
| **1.9** | Validate BES run output against `contracts/output.schema.yaml`. | — |

### Phase 2 – Execution & Analysis
| Task | Description | SC |
|------|-------------|----|
| **2.1** | Run pilot experiment (N = 10‑30, pop = 30, gens = 10) to profile runtime & memory. | — |
| **2.2** | Run full symbolic‑guided BES on the full synthetic dataset (N = 10‑500). | SC‑001, SC‑002 |
| **2.3** | Run baseline neural‑verifier BES (same puzzles, same seeds). | SC‑001, SC‑002 |
| **2.4** | Execute statistical analysis: **paired McNemar’s test** for success‑rate, **independent t‑test** on CPU‑seconds, TOST equivalence, and log‑log regression for scalability. | SC‑001‑SC‑005 |
| **2.5** | Generate summary tables & figures (CSV, PNG) adhering to Single Source of Truth. | — |
| **2.6** | Archive all artifacts, checksums, and `MANIFEST.md` for reproducibility. | I, III, V |

### Deliverables
- `plan.md` (this document)  
- `research.md` (detailed dataset & analysis plan)  
- `data-model.md` (entity schemas)  
- `quickstart.md` (installation & run instructions)  
- `contracts/dataset.schema.yaml` & `contracts/output.schema.yaml` (validation schemas)  

---

