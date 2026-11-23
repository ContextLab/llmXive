# Implementation Plan: llmXive follow-up: extending "Self-Improving Language Models with Bidirectional Evolutionary Search"

**Branch**: `001-symbolic-bes` | **Date**: 2026-10-25 | **Spec**: `specs/001-symbolic-bes/spec.md`  
**Input**: Feature specification from `specs/001-symbolic-bes/spec.md`

## Summary
The project builds a deterministic verification pipeline for a synthetic set of logic/arithmetic puzzles, replaces the neural backward step of the Bidirectional Evolutionary Search (BES) framework with a rule‑based symbolic planner, and evaluates the symbolic‑guided BES against a neural‑verifier baseline. Success is measured by:

1. **Primary success‑rate comparison** – paired **McNemar’s test** (binary outcomes on matched instances) at α = 0.0497 (source: Two‑proportion Z‑test, https://en.wikipedia.org/wiki/Two-proportion_Z-test).  
2. **Supplementary two‑proportion Z‑test** – reported for completeness but not used for primary inference.  
3. **Computational cost comparison** – paired **t‑test** on CPU‑seconds (one‑tailed, testing `μ_symbolic < μ_neural`) at α = 0.0497.  
4. **Equivalence testing** – TOST with Δ = 0.05 for success‑rate equivalence.  
5. **Scalability regression** – log‑log linear regression of complexity vs. mean runtime (R² ≥ 0.85).  

All components run on a CPU‑only GitHub Actions free‑tier runner; GPU‑hours are recorded as not applicable to satisfy Principle VII.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `datasets==2.18.0` – data handling (streaming if needed)  
  - `transformers==4.41.2` – small CPU‑only LLM (`gpt2`)  
  - `torch==2.2.2+cpu` – CPU backend for the LLM  
  - `scikit-learn==1.5.0` – statistical utilities  
  - `scipy==1.13.1` – t‑test & regression  
  - `statsmodels==0.14.2` – McNemar’s test, TOST, power analysis  
  - `pyyaml==6.0.1` – schema validation  
  - `pytest==8.2.2` – test runner  
- **Storage**: Local filesystem under `data/` (raw puzzles, verifier scripts, processed logs).  
- **Testing**: `pytest` for unit & integration suites.  
- **Target Platform**: GitHub Actions free‑tier (a modest number of CPU cores, several GB of RAM, no GPU).  
- **Performance Goals**:  
  - Verifier execution ≤ 100 ms per solution (FR‑001).  
  - Full experiment ≤ 6 h on CI runner.  
- **Constraints**: CPU‑only; no CUDA or low‑bit quantization.  
- **Scale/Scope**: Synthetic puzzle set ranging N = 10 → 500, population size 30‑60, generations 10‑30 (tuned to fit runtime).

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | PASS | `requirements.txt` pinned; seeds recorded; deterministic verifier scripts. |
| II. Verified Accuracy | PASS | All citations will be validated; α = 0.0497 sourced from Wikipedia (see Research). |
| III. Data Hygiene | PASS | SHA‑256 checksums recorded for every file; raw data immutable. |
| IV. Single Source of Truth | PASS | All figures & statistics derive from `data/processed/` logs; no hand‑typed numbers. |
| V. Versioning Discipline | PASS | Content hashes stored in project state; any change updates timestamp. |
| VI. Deterministic Verification Integrity | PASS | Verification performed exclusively by external Python scripts (`code/dataset/verifier.py`). |
| VII. Computational Efficiency Benchmarking | PASS | CPU‑seconds measured directly; GPU‑hours recorded as `0` (placeholder) to satisfy constitutional requirement. |

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
│   │   ├── generator.py          # puzzle generation (FR‑001) – now outputs single JSON object with a "puzzles" list
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
│   │   └── stats.py              # McNemar, TOST, paired t‑test, power checks (FR‑005)
│   └── main.py                   # experiment entry point (fixed to exit 0 on success)
├── tests/
│   ├── unit/
│   │   ├── test_generator.py          # expects JSON with "puzzles"
│   │   ├── test_verifier.py
│   │   └── test_symbolic_planner.py   # catches ParseFailure & ContradictionDetected
│   └── integration/
│       └── test_bes_loop.py
├── requirements.txt
└── README.md
```

## Mapping of Functional & Success Criteria to Plan Tasks
| Requirement | Covered By |
|-------------|------------|
| **FR‑001** | `code/dataset/generator.py` (produces JSON with `"puzzles"` list) + `code/dataset/verifier.py` |
| **FR‑002** | `code/symbolic/planner.py` (throws `ParseFailure` / `ContradictionDetected`) |
| **FR‑003** | `code/bes/forward_step.py` (CPU LLM recombination) |
| **FR‑004** | `code/analysis/metrics.py` |
| **FR‑005** | `code/analysis/stats.py` (McNemar, TOST, paired t‑test, power) |
| **FR‑006** | Planner exception handling & exclusion logging (task 1.3) |
| **SC‑001** | Success‑rate comparison via **paired McNemar’s test** (task 2.4) |
| **SC‑002** | CPU‑seconds comparison via **paired t‑test** (task 2.4) |
| **SC‑003** | Planner‑generated sub‑goals validated before LLM call (tasks 1.3 & 1.4) |
| **SC‑004** | McNemar p‑value output (task 2.4) |
| **SC‑005** | Log‑log regression on complexity vs. runtime (task 2.4) |
| **SC‑006** | Separate **planner feasibility rate** reported via `feasibility_rate` (optional field in output schema). |

## Implementation Phases & Tasks

### Phase 0 – Research & Design
| Task | Description |
|------|-------------|
| **0.1** | Finalize synthetic puzzle generation strategy (types, scaling, reproducibility). |
| **0.2** | Define statistical analysis plan (paired McNemar, paired t‑test, TOST, power analysis) – α = 0.0497 (cited). |
| **0.3** | Select CPU‑only LLM (`gpt2`) and verify memory/time budget on CI. |
| **0.4** | Draft JSON‑Schema contracts (`dataset.schema.yaml`, `output.schema.yaml`) and validate against mock data. |

### Phase 1 – Data & Core Logic
| Task | Description | FR/SC |
|------|-------------|-------|
| **1.1** | Implement `code/dataset/generator.py` to create puzzles and write a **single JSON object** `{ "puzzles": [ … ] }` (matches `tests/unit/test_generator.py`). | FR‑001 |
| **1.2** | Implement `code/dataset/verifier.py` – deterministic, returns `(bool, error_code)` within 100 ms. | FR‑001 |
| **1.3** | Implement `code/symbolic/planner.py` with exception classes `ParseFailure` and `ContradictionDetected`; log exclusions per FR‑006 and compute feasibility rate. | FR‑002, FR‑006 |
| **1.4** | Implement `code/bes/forward_step.py` using the small CPU LLM to recombine trajectories guided by planner sub‑goals. | FR‑003 |
| **1.5** | Implement `code/analysis/metrics.py` and `stats.py` for aggregation, paired McNemar, paired t‑test, TOST, and power checks. | FR‑004, FR‑005 |
| **1.6** | **Fix Test Suite Issue T001** – generator now outputs a single JSON object with a `"puzzles"` list (already done). | — |
| **1.7** | **Fix Test Suite Issue T002** – ensure `tests/unit/test_symbolic_planner.py` catches the real exception classes (`ParseFailure`, `ContradictionDetected`). | — |
| **1.8** | Validate generated puzzle files against `contracts/dataset.schema.yaml`. | — |
| **1.9** | Validate BES run output against `contracts/output.schema.yaml` (now includes optional `feasibility_rate`). | — |
| **1.10** | **Fix Task T003** – ensure `code/main.py` (the CLI entry point) executes end‑to‑end without error (exit 0) by wiring together generator → BES loop → analysis. | — |

### Phase 2 – Execution & Analysis
| Task | Description | SC |
|------|-------------|----|
| **2.1** | Run pilot experiment (N = 10‑30, pop = 30, gens = 10) to profile runtime & memory. |
| **2.2** | Run full symbolic‑guided BES on the full synthetic dataset (N = 10‑500). |
| **2.3** | Run baseline neural‑verifier BES (same puzzles, same seeds). |
| **2.4** | Execute statistical analysis: **paired McNemar’s test**, **TOST equivalence**, **paired t‑test**, and log‑log regression for scalability. |
| **2.5** | Generate summary tables & figures (CSV, PNG) adhering to Single Source of Truth. |
| **2.6** | Archive all artifacts, checksums, and `MANIFEST.md` for reproducibility. |

### Deliverables
- `plan.md` (this document)  
- `research.md` (detailed dataset & analysis plan)  
- `data-model.md` (entity schemas)  
- `quickstart.md` (installation & run instructions)  
- `contracts/dataset.schema.yaml` & `contracts/output.schema.yaml` (validation schemas)  

---

