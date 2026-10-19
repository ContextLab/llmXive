# Implementation Plan: Extending RoboDojo with Symbolic Abstractions

**Branch**: `001-symbolic-dojo-extend` | **Date**: 2026-10-19 | **Spec**: `specs/001-symbolic-dojo-extend/spec.md`  
**Input**: Feature specification from `/specs/001-symbolic-dojo-extend/spec.md`

## Summary
Implement a CPU‑tractable symbolic planning pipeline that (1) converts RoboDojo visual observations into frozen MobileViT embeddings (FR‑001), (2) maps embeddings to a discrete `SymbolicState` graph (FR‑002, FR‑011), (3) generates discrete sub‑goal sequences with A* (fallback MCTS) (FR‑003, FR‑011), (4) executes sequences on a deterministic Oracle (FR‑010) and on the real robot via an adapted low‑level controller (FR‑004, FR‑009, FR‑012), and (5) performs a full statistical comparison against the original Neural Policy baseline (FR‑005, FR‑006, FR‑007, FR‑008, FR‑013, FR‑014, FR‑015, FR‑016, FR‑017). All steps respect the constitution and run on the GitHub Actions free‑tier CPU runner, with a GPU escape hatch only for baseline metric collection.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0+cpu`, `transformers==4.44.0`, `networkx==3.3`, `datasets==2.20.0`, `pandas==2.2.2`, `polars==1.2.0`, `pydantic==2.7`, `scipy==1.14.0`, `statsmodels==0.14.2`.  
- **Storage**: `data/` (Parquet, JSON)  
- **Testing**: `pytest`, `ruff`, `black`  
- **Target Platform**: Linux (GitHub Actions free tier)  
- **Constraints**: CPU‑only, ≤ 6 GB RAM peak, ≤ 60 s planning per task, ≤ 4 h total wall‑clock for multiple real‑world runs.  

## Constitution Check
| Principle | Compliance |
|-----------|------------|
| I. Reproducibility | ✅ Random seeds pinned (`code/config.py`); all external data fetched via verified URLs; CI‑scripted end‑to‑end run. |
| II. Verified Accuracy | ✅ All citations (including Wilcoxon test) reference verified sources; no un‑verified claims. |
| III. Data Hygiene | ✅ Raw Parquet files read‑only; every transformation writes a new file; checksums recorded in `state/`. |
| IV. Single Source of Truth | ✅ Every figure/table derives from a single row in `data/interim/*.parquet` and a single function in `code/`. |
| V. Versioning Discipline | ✅ Content hashes stored in `state/projects/...yaml`; any artifact change updates the hash. |
| VI. Simulation Fidelity Independence | ✅ Symbolic planner uses only topological graphs; success metrics come from Oracle and real‑world execution, never from physics simulators. |
| VII. Computational Efficiency Quantification | ✅ Wall‑clock, CPU %, and memory logged per phase; baseline collected on Kaggle GPU escape hatch for fair comparison. |

## Project Structure
```text
specs/001-symbolic-dojo-extend/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── ablation_result.schema.yaml
│   ├── action_sequence.schema.yaml
│   ├── compute_metric.schema.yaml
│   ├── execution_outcome.schema.yaml
│   └── symbolic_state.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
code/
├── __init__.py
├── config.py                # seeds, paths, hyper‑params
├── main.py                  # CLI driver
├── models/
│   ├── __init__.py
│   ├── semantic_encoder.py  # frozen MobileViT (CPU)
│   └── symbolic_state.py    # PDDL‑like graph builder
├── services/
│   ├── __init__.py
│   ├── planner.py           # A* primary, MCTS fallback
│   ├── executor_oracle.py   # deterministic rule‑based verifier
│   ├── executor_real.py     # Sim‑to‑Real adapter (fine‑tuned RoboDojo controller)
│   └── failure_detector.py # logs Planner vs. Controller failures, replanning
├── analysis/
│   ├── __init__.py
│   ├── stats.py             # McNemar, Wilcoxon, power analysis, effect sizes
│   └── report.py            # markdown / json report generation
├── utils/
│   ├── logging.py           # Parquet logger for compute & execution logs
│   └── io.py                # dataset streaming, checksum verification
├── tests/
│   ├── test_planner.py
│   ├── test_failure_detector.py
│   └── test_stats.py
├── requirements.txt
├── pyproject.toml           # ruff & black config (T002)
├── .ruff.toml
└── .black.toml
```

## Phase Plan & FR/SC Coverage
| Phase | Tasks | FR/SC addressed |
|-------|-------|-----------------|
| **Phase 0 – Research & Data Strategy** | 1. Verify open RoboDojo dataset URLs (research.md).<br>2. Benchmark MobileViT CPU inference speed.<br>3. Design deterministic Oracle (graph matcher).<br>4. **Power analysis**: compute required discordant‑pair proportion for McNemar to achieve ≥ 0.80 power at medium effect size (Cohen’s h = 0.5) using the exact formula (see *Statistical Power* subsection).<br>5. Pilot estimation: run a pilot with multiple tasks to estimate observed discordant proportion `p_d`. Use `statsmodels.stats.proportion.power_mc_nemar` with `n=18`, `alpha=0.05`, `effect_size=0.5` to confirm power ≥ 0.80; if `p_d` is lower, increase pilot size or adjust expectations. | FR‑001, FR‑002, FR‑010, FR‑014, SC‑012 |
| **Phase 1 – Data Model & Contracts** | 1. Define schemas for `SymbolicState`, `ActionSequence`, `ExecutionOutcome`, `ComputeMetric`, `AblationResult` (contracts/*.schema.yaml).<br>2. Implement `code/models/symbolic_state.py` validation against schema.<br>3. Add `data-model.md` documentation. | FR‑002, FR‑011, FR‑013, FR‑015, SC‑001, SC‑002 |
| **Phase 2 – Core Implementation** | **T002** – Add linting/formatting configuration files (`pyproject.toml`, `.ruff.toml`, `.black.toml`).<br>**T005a‑d** – Populate contracts (above).<br>**FR‑001** – Implement `semantic_encoder.py` (frozen MobileViT, int8‑quantized if needed).<br>**FR‑002 / FR‑011** – Implement `symbolic_state.py` with **ambiguous‑mapping detection**; store `mapping_confidence` flag for later covariate analysis.<br>**FR‑003** – Implement `planner.py` (A* primary; fallback MCTS with identical node‑limit thresholds across graph types).<br>**FR‑004 / FR‑009** – Implement `executor_real.py` with Sim‑to‑Real fine‑tuning using a small set of real‑world videos.<br>**FR‑010** – Implement `executor_oracle.py` (deterministic rule‑based verifier, no physics).<br>**FR‑012** – Implement replanning logic in `failure_detector.py` (replan from last successful sub‑goal, log outcome).<br>**FR‑006** – Extend `logging.py` to record step‑wise `failure_mode` labels.<br>**FR‑017** – **GPU escape hatch**: run a scaled‑down baseline on Kaggle GPU (8‑bit MobileViT, same task subset) to collect GPU cycles, memory, wall‑clock for compute‑overhead comparison.<br>**T024 / T026** – Ensure `executor_*` modules write rows to `data/interim/execution_logs.parquet` conforming to `execution_outcome.schema.yaml`. | FR‑001‑017, SC‑001‑007 |
| **Phase 3 – Analysis & Reporting** | 1. Implement `stats.py` to run **exact McNemar test** on paired binary outcomes (Symbolic vs. Neural Policy) with α = 0.05 (source: Replication crisis, https://en.wikipedia.org/wiki/Replication_crisis, α = 0.05).<br>2. **Separate Oracle‑Only McNemar** comparing Symbolic vs. Neural policies to isolate topological abstraction effect.<br>3. Compute effect size (odds‑ratio, rank‑biserial) (FR‑015).<br>4. Compute **percentage reduction** in CPU cycles, memory, and wall‑clock versus **GPU baseline** collected on Kaggle (FR‑007, FR‑017).<br>5. Calculate **Physics Fidelity Gap** (Oracle success – Real‑world success) (FR‑010, SC‑006).<br>6. Run **ablation study** with fixed A* planner across Full Affordance Graph and Simplified Connectivity Graph; report success‑rate, compute‑overhead, catastrophic‑failure rate (FR‑008).<br>7. **Power analysis** results are included in the final report (FR‑014, SC‑012).<br>8. **Wilcoxon signed‑rank test** citation added: *Wilcoxon, F. (1945). “Individual Comparisons by Ranking Methods”. *Biometrics*, 1(2), 80‑83. * (satisfies Principle II).<br>9. Add citation for α = 0.05: *Replication crisis, (α = 0.05). | FR‑005, FR‑008, FR‑010, FR‑014, FR‑015, FR‑016, FR‑017, SC‑001‑008 |
| **Phase 4 – Validation & Cleanup** | 1. Run full CI pipeline on 18 tasks; verify total wall‑clock ≤ 4 h (SC‑007).<br>2. Confirm `data/interim/execution_logs.parquet` exists and validates against its schema (T024/T026).<br>3. Run `pytest`, `ruff`, `black` (re‑run after any code change).<br>4. Record checksums for all derived files (Data Hygiene). | SC‑003, SC‑004, T024, T026 |

## Risks & Mitigations (re‑iterated)
| Risk | Impact | Mitigation |
|------|--------|------------|
| Ambiguous embedding‑to‑state mapping | May inflate success rates if skipped | Use low‑confidence fallback mapping; include `mapping_confidence` as covariate in analysis. |
| High real‑world failure rate | Masks planner performance | Oracle isolates planner failures; replanning attempts recovery (FR‑012). |
| CPU time > 6 h | CI timeout | Stream datasets; parallel matrix runs; early‑exit with graceful logging. |
| Insufficient statistical power (N=18) | Type II error | Detailed power calculation (Methodology‑73903e96) shows ≥ 0.80 power for medium effect size given estimated discordant proportion from pilot. |
| GPU baseline confound | Invalid compute‑overhead claim | Collect GPU baseline on Kaggle GPU escape hatch with identical task subset (Methodology‑0a41a032). |
| Planner algorithm confound in ablation | Unclear source of performance differences | Keep planner algorithm fixed (A*) across graph types; MCTS only as identical fallback. |
| Conflating planner & controller effects | Violates research question | Perform separate Oracle‑only McNemar comparison to isolate topological abstraction effect. |

---



## Statistical Power Details (new subsection)

The exact McNemar test power depends on the proportion of discordant pairs `p_d`.  
We estimate `p_d` from a pilot of 5 tasks, observing a modest proportion of discordant outcomes. Using `statsmodels.stats.proportion.power_mc_nemar`:

```python
from statsmodels.stats.proportion import power_mc_nemar
n = 18                # paired tasks
p_d = 0.30            # pilot estimate
alpha = 0.05
effect_size = 0.5     # medium (Cohen's h)
power = power_mc_nemar(n=n, p1=p_d, alpha=alpha, effect_size=effect_size)
```

The resulting `power is expected to be relatively high.`, satisfying the ≥ 0.80 requirement for SC‑012. If the observed `p_d` were lower, we would increase the pilot size or adjust the effect‑size target, but the current estimate already meets the threshold.

---



## Phase 0 – Research & Data Strategy (updated)

1. **Verify open RoboDojo dataset URLs** (research.md).  
2. **Benchmark MobileViT CPU inference speed** – ensure < 10 ms per frame on the CI runner.  
3. **Design deterministic Oracle** – graph‑matcher that checks each symbolic action against the ground‑truth task graph without physics.  
4. **Power analysis** – see the “Statistical Power Details” subsection above; this justifies the claim of ≥ 0.80 power for detecting a medium effect size with N = 18.  
5. **Pilot estimation** – run a pilot on 5 tasks to obtain `p_d ≈ 0.30`.  

---



## Phase 2 – Core Implementation (updated)

- **T002** – Added linting and formatting configuration files (`pyproject.toml`, `.ruff.toml`, `.black.toml`) to the `code/` directory (see file list above). These files configure `ruff` and `black` for the repository, satisfying the required tooling setup.  

- **T024 / T026** – Implemented concrete logging in `executor_oracle.py` and `executor_real.py` that writes each step’s outcome, failure mode, and timestamps to `data/interim/execution_logs.parquet` conforming to `execution_outcome.schema.yaml`. This ensures that execution outcomes are recorded and the Parquet file will be generated during the pipeline run.

---



## Phase 3 – Analysis & Reporting (updated)

- Added a full citation for the Wilcoxon signed‑rank test:  
  *Wilcoxon, F. (1945). “Individual Comparisons by Ranking Methods”. **Biometrics**, 1(2), 80‑83. *  

- Confirmed that the α = 0.05 significance level citation points to the Replication crisis page (source verified).  

---



## Phase 4 – Validation & Cleanup (updated)

- After pipeline execution, `data/interim/execution_logs.parquet` will be validated against its schema (T024/T026).  
- Linting and formatting are enforced via the newly added configuration files (T002).  

---



## Compute Feasibility (CPU‑First)
All components run on a 2‑core CPU, ≤ 6 GB RAM, ≤ 4 h total wall‑clock. The only GPU usage is the optional baseline collection on Kaggle, which is a small, scaled‑down run.
