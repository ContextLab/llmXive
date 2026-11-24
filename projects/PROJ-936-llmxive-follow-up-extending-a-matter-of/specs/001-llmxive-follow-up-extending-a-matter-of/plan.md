# Implementation Plan: LLM Agent Efficiency vs. Reasoning Trade‑off Analysis

**Branch**: `002-efficiency-reasoning-tradeoff` | **Date**: 2026-10-24 | **Spec**: [spec.md](../specs/002-efficiency-reasoning-tradeoff/spec.md)  
**Input**: Feature specification from `/specs/002-efficiency-reasoning-tradeoff/spec.md`

## Summary
The pipeline will (1) download the open‑source **τⁿ‑Bench** task suite from HuggingFace, (2) run a CPU‑tractable baseline LLM agent (Llama‑2‑7B 8‑bit via Ollama) on a capped subset of ≤ 200 tasks while logging success, API‑call count, token usage and duration, (3) compute a **primary efficiency penalty** using `optimal_path_length` only (with a separate fallback metric for sensitivity), (4) train a difficulty‑score model on the **full** dataset (excluding any penalty‑derived features), (5) filter tasks with primary penalty > 2.0 for downstream evolution, (6) evolve ≥ 5 harder variants per high‑penalty task **based solely on predicted difficulty**, (7) re‑run the baseline on evolved tasks, (8) evaluate the trade‑off using **paired** statistical tests (McNemar/Fisher, paired t‑test, logistic regression with VIF check), (9) conduct a **formal power analysis** appropriate for the paired proportion test, (10) perform a **sensitivity analysis** using the fallback penalty, (11) validate all generated artifacts against their JSON‑Schema contracts (including `artifact.schema.yaml`), and (12) generate reproducible tables, figures and a concise markdown report.

All steps respect the GitHub Actions free‑tier limits (≤ 6 h, 2 CPU cores, ~7 GB RAM) and the project constitution.

## Technical Context
- **Language**: Python 3.11  
- **Primary Dependencies**: `datasets>=2.14`, `pandas>=2.2`, `scikit-learn>=1.5`, `statsmodels>=0.14`, `ollama>=0.1`, `tqdm`, `pyyaml`, `numpy`, `matplotlib`, `seaborn`  
- **Storage**: File‑based under `data/` (raw downloads, derived CSV/JSON, model pickle, figures)  
- **Testing**: `pytest` with contract‑based validation (`tests/contract/`)  
- **Target Platform**: Linux runner on GitHub Actions (CPU‑only)  
- **Constraints**: No GPU; all methods are CPU‑tractable.  
- **Scale**: ≤ 200 tasks (to keep total wall‑clock ≤ 6 h).  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | All random seeds are pinned (`np.random.seed(42)`, `random_state=42`). Data is fetched programmatically from the canonical HuggingFace identifier `tau_c_bench`; if the download fails the pipeline aborts with a clear error. Scripts are deterministic. |
| II. Verified Accuracy | No new literature citations are introduced. All external resources are either the open‑source HuggingFace dataset (name only) or the locally‑installed Ollama model. |
| III. Data Hygiene | Raw download is checksum‑verified; every transformation writes a new file under `data/derived/` with a recorded SHA‑256 hash in `state/projects/PROJ-936-...yaml`. |
| IV. Single Source of Truth | Every figure/table is generated directly from the CSV/JSON artifacts produced by the pipeline; no manual transcription occurs. |
| V. Versioning Discipline | All generated artifacts are hashed and the hashes are stored in the project state file. |
| VI. Efficiency‑Penalty Rigor | Primary penalty is `total_calls / optimal_path_length` (when present). A documented fallback `total_calls / tool_diversity_k` is computed **only** for sensitivity analysis. |
| VII. Cost‑Performance Frontier Quantification | Phase 5 uses a **paired t‑test** on success rates before vs. after evolution, satisfying the constitution’s frontier requirement. |

## Project Structure
```text
specs/002-efficiency-reasoning-tradeoff/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── artifact.schema.yaml
│   ├── evolved_task.schema.yaml
│   └── execution_log.schema.yaml
└── tasks.md          # (generated later)

src/
├── pipelines/
│   ├── download.py
│   ├── baseline_run.py
│   ├── penalty_calc.py
│   ├── difficulty_model.py
│   ├── correlation.py
│   ├── model_train.py
│   ├── evolve_tasks.py
│   ├── evaluation.py
│   └── utils.py
└── __main__.py

tests/
├── contract/
│   ├── test_execution_log.py
│   └── test_evolved_task.py
└── integration/
    └── test_full_pipeline.py
```

## Phase Overview & FR/SC Mapping
| Phase | Description | FRs Covered | SCs Covered |
|-------|-------------|-------------|--------------|
| **0. Dataset Strategy** | Download `tau_c_bench` via `datasets.load_dataset`. Abort if unavailable. | FR‑001 | SC‑002 |
| **1. Baseline Execution & Logging** | Run Llama‑2‑7B 8‑bit on ≤ 200 tasks; produce `execution_log` CSV. Enforce 6 h timeout → `status="timeout"`. Validate required fields (`task_id`, `success`, `total_calls`, `total_tokens`). **Log completeness check**: ≥ 99 % of rows must have non‑null required fields; otherwise abort. | FR‑001, FR‑002, FR‑011 | SC‑001, SC‑006 |
| **2. Efficiency Penalty Calculation** | Compute **primary** `penalty_primary = total_calls / optimal_path_length` (only when `optimal_path_length` is present). Log warning `OPTIMAL_PATH_MISSING` and **exclude** such tasks from primary‑penalty analyses. Compute **fallback** `penalty_alt = total_calls / tool_diversity_k` for sensitivity analysis only. Flag tasks with `penalty_primary > 2.0` for downstream evolution. | FR‑003, FR‑011 | SC‑002 |
| **3. Full‑Dataset Difficulty Modeling** | Train a `DecisionTreeRegressor(max_depth=5, random_state=42)` on **all** tasks using only raw task features (excluding any penalty‑derived columns). Use 5‑fold cross‑validation to generate **out‑of‑fold** `difficulty_score` for **every** task. Hold‑out R² ≥ 0.6 is required. | FR‑010, FR‑007 | SC‑007 |
| **4. High‑Penalty Filtering** | Create `filtered_tasks.csv` containing tasks with `penalty_primary > 2.0`. | FR‑003 | SC‑002 |
| **5. Cost‑Performance Frontier (Paired t‑test)** | Perform a **paired t‑test** comparing success rates on the original high‑penalty tasks vs. their evolved counterparts (paired per source task). Plot the frontier showing the trade‑off between penalty increase and success‑rate drop. | — | SC‑005 |
| **6. Task Evolution** | For each high‑penalty task, generate ≥ 5 variants that **maximize the predicted `difficulty_score`** (the difficulty model is the only selection criterion). Output records conforming to `evolved_task` schema. | FR‑007 | SC‑008 |
| **7. Evolved‑Task Penalty Increase Check** | After re‑running the baseline on evolved tasks, compute the **observed** average `penalty_primary` of evolved tasks and assert a ≥ 10 % increase over the source tasks. | FR‑007 | SC‑008 |
| **8. Re‑run Baseline on Evolved Set** | Execute the baseline agent on all evolved tasks; log with the same schema as Phase 1. | FR‑002, FR‑004 | SC‑001 |
| **9. Trade‑off Evaluation** | **Primary test**: **McNemar paired test** for difference in success proportions between baseline (original) and evolved outcomes. If any cell count < 5, automatically switch to **Fisher’s exact test** and log a warning. <br> **Supplementary model**: Logistic regression `evolved_success ~ baseline_penalty + difficulty_score` with VIF check; if VIF > 5, drop `difficulty_score` and re‑fit, noting the change. Report coefficients, standard errors, odds ratios, p‑values, 95 % CIs; verify the penalty coefficient is negative and significant (p < 0.05). <br> **Power analysis**: Use `statsmodels.stats.power.NormalIndPower` to compute the required sample size for detecting a proportion difference Δ = 0.15 at α = 0.05 with 80 % power (paired proportion test). Emit a clear warning if the actual N is below this threshold. | FR‑005, FR‑009 | SC‑003, SC‑004, SC‑010, SC‑011 |
| **10. Sensitivity Analysis** | Repeat Phases 2‑9 using the **fallback** `penalty_alt`. Compare logistic‑regression penalty coefficients: same sign and absolute difference ≤ 0.05. Report both primary and sensitivity results. | FR‑008 | SC‑010 |
| **11. Artifact‑Schema Validation** | Validate every generated CSV/JSON/PNG against its corresponding contract in `contracts/` (including `artifact.schema.yaml`). Failure to validate aborts the pipeline, ensuring adherence to `artifact.schema.yaml`. | — | — |
| **12. Reporting** | Assemble `data/outputs/summary.csv`, `figures/regression_coefficients.png`, `figures/cost_performance_frontier.png`, and a concise `report/analysis.md`. | — | SC‑001‑SC‑004 |

## Detailed Task List (≈ 13 tasks)
1. **download.py** – fetch dataset, compute SHA‑256, abort on failure.  
2. **baseline_run.py** – iterate over tasks, invoke Ollama, capture logs, enforce 6 h timeout, write `baseline_execution.csv`, perform completeness check.  
3. **tests/contract/test_execution_log.py** – schema validation for Phase 1 output.  
4. **penalty_calc.py** – compute primary penalty (optimal only) and fallback; issue `OPTIMAL_PATH_MISSING` warnings; write `filtered_tasks.csv`.  
5. **difficulty_model.py** – train decision tree on the **full** task set, generate out‑of‑fold `difficulty_score` for all tasks, evaluate R², serialize to `difficulty_model.pkl`.  
6. **correlation.py** – point‑biserial and partial correlation; store results in `correlation_results.json`.  
7. **evaluation.py** – (a) paired t‑test for cost‑performance frontier, (b) McNemar/Fisher test, (c) logistic regression with VIF check, (d) power analysis, (e) sensitivity analyses; generate figures.  
8. **evolve_tasks.py** – generate ≥ 5 variants per high‑penalty task maximizing difficulty; output `evolved_tasks.csv`.  
9. **tests/contract/test_evolved_task.py** – schema validation for evolved records.  
10. **evaluation.py (penalty increase)** – verify ≥ 10 % observed penalty boost on evolved tasks.  
11. **baseline_run.py (re‑run)** – run agent on evolved set, produce `evolved_execution.csv`.  
12. **artifact_validation.py** – loop over generated artifacts and validate against contracts (Phase 11).  
13. **utils.py / report generation** – assemble final CSV, figures, and `analysis.md`.  

All phases respect data dependencies (download → baseline → penalty → difficulty → filtering → evolution → re‑run → evaluation → sensitivity → validation → reporting).

## Methodological Rigor Notes
- **Optimal‑Path Proxy**: Primary denominator is the true `optimal_path_length`. The fallback `tool_diversity_k` is used **only** for sensitivity analysis.
- **Selection Bias Mitigation**: Difficulty model trained on the **full** dataset; evolution driven solely by difficulty predictions.
- **Statistical Rigor**:  
  - *Paired t‑test* for cost‑performance frontier (Constitution VII).  
  - *McNemar* (or Fisher) for paired success‑rate comparison, respecting within‑task dependence.  
  - *Logistic regression* includes VIF check; predictors with VIF > 5 are omitted and noted.  
  - *Power analysis* targets the paired proportion test (effect size Δ = 0.15).  
- **Causal Framing**: Observational; claims limited to *associational* trade‑off. Difficulty included as a covariate to reduce confounding.  

## Compute Feasibility
- **Per‑task runtime** (Llama‑2‑7B 8‑bit on CPU) ≈ 30 s (benchmark).  
- **Total** for 200 tasks baseline + similar budget for evolved set → well under 6 h.  
- **Memory** peak < 5 GB (pandas + scikit‑learn).  

---


