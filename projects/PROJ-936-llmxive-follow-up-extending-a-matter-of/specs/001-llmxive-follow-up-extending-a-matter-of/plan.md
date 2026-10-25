# Implementation Plan: LLM Agent Efficiency vs. Reasoning Trade‑off Analysis

**Branch**: `002-efficiency-reasoning-tradeoff` | **Date**: 2026-10-24 | **Spec**: [spec.md](../specs/002-efficiency-reasoning-tradeoff/spec.md)  
**Input**: Feature specification from `/specs/002-efficiency-reasoning-tradeoff/spec.md`

## Summary
The pipeline will (1) download the open‑source **τⁿ‑Bench** task suite from HuggingFace, (2) run a CPU‑tractable baseline LLM agent (Llama‑2‑7B 8‑bit via Ollama) on a capped subset of ≤ 200 tasks while logging success, API‑call count, token usage and duration, (3) compute an **efficiency penalty** using the true `optimal_path_length` when available and a documented fallback to the **tool‑diversity** heuristic `k` otherwise, (4) filter tasks with penalty > 2.0, (5) train a lightweight decision‑tree regressor **only on the filtered high‑penalty set** to predict a difficulty score, (6) evolve ≥ 5 harder variants per high‑penalty task using out‑of‑fold difficulty predictions, (7) re‑run the baseline on the evolved set and **measure the observed average penalty increase** (≥ 10 % required), (8) evaluate the trade‑off with a **chi‑squared test for independent proportions** (primary) and a **logistic regression** using out‑of‑fold difficulty scores (supplementary), (9) conduct a **formal power analysis** for the chi‑squared test and emit a warning if under‑powered, (10) perform a **sensitivity analysis** using the pure tool‑diversity denominator, and (11) generate reproducible tables, figures and a concise markdown report.

All steps respect the project constitution and run within the GitHub Actions free‑tier limits (≤ 6 h, 2 CPU cores, ~7 GB RAM).

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
| II. Verified Accuracy | No new literature citations are introduced. All external resources are either the open‑source HuggingFace dataset (name only, no URL) or the locally‑installed Ollama model. |
| III. Data Hygiene | Raw download is checksum‑verified; every transformation writes a new file under `data/derived/` with a recorded SHA‑256 hash in `state/projects/PROJ-936-...yaml`. |
| IV. Single Source of Truth | Every figure/table is generated directly from the CSV/JSON artifacts produced by the pipeline; no manual transcription occurs. |
| V. Versioning Discipline | All generated artifacts are hashed and the hashes are stored in the project state file. |
| VI. Efficiency‑Penalty Rigor | Penalty is computed as `total_calls / optimal_path_length` when that field exists; otherwise the fallback `total_calls / tool_diversity_k` is used, with a logged warning `OPTIMAL_PATH_MISSING`. |
| VII. Cost‑Performance Frontier Quantification | Phase 8 fits a regression of binary success on continuous penalty and outputs a frontier plot, satisfying the constitution’s cost‑performance requirement. |

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
| **0. Dataset Strategy** | Attempt to download `tau_c_bench` via `datasets.load_dataset`. Abort if unavailable. | FR‑001, FR‑006 | SC‑002 |
| **1. Baseline Execution & Logging** | Run Llama‑2‑7B 8‑bit on ≤ 200 tasks; produce `execution_log` records (CSV). Enforce timeout > 6 h → `status="timeout"`. Validate required fields (`task_id`, `success`, `total_calls`, `total_tokens`). | FR‑001, FR‑002 | SC‑001, SC‑006 |
| **2. Efficiency Penalty Calculation** | Compute `penalty = total_calls / optimal_path_length` when present; otherwise `penalty = total_calls / tool_diversity_k`. Log warning `OPTIMAL_PATH_MISSING` when falling back. Flag tasks with `penalty > 2.0`. | FR‑003, FR‑006 | SC‑002 |
| **3. Correlation & Partial Correlation** | Compute (a) Pearson point‑biserial correlation between `penalty` and binary `success` over the **full** task set, and (b) **partial correlation** controlling for out‑of‑fold `difficulty_score`. Store coefficients, p‑values, 95 % CI. Require *p* < 0.05 and |r| ≥ 0.2. | FR‑004 | SC‑004, SC‑009 |
| **4. Difficulty (Reward) Modeling** | Train `DecisionTreeRegressor(max_depth=5, random_state=42)` **only on the filtered high‑penalty tasks** (penalty > 2.0). Use 5‑fold cross‑validation to generate **out‑of‑fold** `difficulty_score` for **all** tasks (including those not used for training). Require hold‑out R² ≥ 0.6. **Exclude `tool_diversity_k` from the feature set** to avoid circularity. | FR‑007 | SC‑007 |
| **5. Cost‑Performance Frontier** | Fit a linear regression `success ~ penalty`; report slope (cost per % success change) and plot the frontier. | — | SC‑005 |
| **6. Task Evolution** | For each high‑penalty task, generate ≥ 5 variants that maximize the out‑of‑fold `difficulty_score`. Output records conforming to `evolved_task` schema. `tool_diversity_k` is **not** used as a model feature. | FR‑007 | SC‑008 |
| **7. Evolved‑Task Penalty Increase Check** | After re‑running the baseline on evolved tasks, compute the **observed** average penalty of evolved tasks and assert ≥ 10 % increase over the source tasks. This provides independent evidence of difficulty amplification. | FR‑007 | SC‑008 |
| **8. Re‑run Baseline on Evolved Set** | Execute the baseline agent on all evolved tasks; log with the same schema as in step 1. | FR‑002, FR‑004 | SC‑001 |
| **9. Trade‑off Evaluation** | **Primary test**: **Chi‑squared test** for difference in success proportions between baseline (original tasks) and baseline (evolved tasks). Report χ², p‑value, and effect size. <br> **Supplementary model**: Logistic regression `evolved_success ~ baseline_penalty + difficulty_score` using **out‑of‑fold** difficulty scores. Report coefficients, standard errors, odds ratios, p‑values, 95 % CIs; verify the penalty coefficient is negative and significant (p < 0.05). <br> **Power analysis**: Using `statsmodels.stats.power.GofChisquarePower`, compute the minimum required sample size for an expected odds‑ratio ≈ 2.5 at α = 0.05. Emit a clear warning if the actual N is below this threshold. | FR‑005 | SC‑003, SC‑004, SC‑010 |
| **10. Sensitivity Analysis** | Repeat steps 2‑9 using the **pure tool‑diversity** denominator (`penalty_alt = total_calls / tool_diversity_k`). Compare logistic‑regression penalty coefficients: same sign and absolute difference ≤ 0.05. | FR‑008 | SC‑010 |
| **11. Reporting & Artefact Generation** | Assemble `data/outputs/summary.csv`, `figures/regression_coefficients.png`, `figures/cost_performance_frontier.png`, and a concise `report/analysis.md`. | — | SC‑001‑SC‑004 |

## Detailed Task List (≈ 13 tasks)
1. **download.py** – fetch dataset, compute SHA‑256, abort on failure.  
2. **baseline_run.py** – iterate over tasks, invoke Ollama, capture logs, enforce 6 h timeout, write `baseline_execution.csv`.  
3. **tests/contract/test_execution_log.py** – schema validation for Phase 1 output.  
4. **penalty_calc.py** – compute primary penalty with fallback, issue `OPTIMAL_PATH_MISSING` warnings, write `filtered_tasks.csv`.  
5. **correlation.py** – point‑biserial and partial correlation; store results in `correlation_results.json`.  
6. **model_train.py** – train decision tree on filtered tasks, generate out‑of‑fold `difficulty_score` for all tasks, evaluate R², serialize to `difficulty_model.pkl`.  
7. **evaluation.py** – cost‑performance regression and frontier plot.  
8. **evolve_tasks.py** – generate ≥ 5 variants per high‑penalty task, output `evolved_tasks.csv`.  
9. **tests/contract/test_evolved_task.py** – schema validation for evolved records.  
10. **evaluation.py (penalty increase)** – verify ≥ 10 % observed penalty boost on evolved tasks.  
11. **baseline_run.py (re‑run)** – run agent on evolved set, produce `evolved_execution.csv`.  
12. **evaluation.py (trade‑off)** – chi‑squared test, logistic regression with out‑of‑fold scores, power analysis, warnings if under‑powered.  
13. **utils.py / report generation** – assemble final CSV, figures, and `analysis.md`.  

All phases respect data dependencies (download → baseline → penalty → correlation → model → evolution → re‑run → evaluation → sensitivity → reporting).

## Methodological Rigor Notes
- **Optimal‑Path Proxy**: The primary denominator is the true `optimal_path_length` when present; otherwise the *tool‑diversity* count *k* is used as a documented fallback. Sensitivity analysis reports results for both.  
- **Selection Bias**: Difficulty model is trained **only** on the high‑penalty subset, matching FR‑007, and predictions for all tasks are obtained via out‑of‑fold cross‑validation to avoid leakage.  
- **Statistical Rigor**:  
  - *Chi‑squared test* is appropriate for independent binary outcomes (no multiple‑comparison correction needed).  
  - *Logistic regression* supplies covariate‑adjusted effect sizes; predictors are out‑of‑fold `difficulty_score` and `baseline_penalty`.  
  - *Power analysis* computes required N for the expected odds‑ratio; a warning is emitted if the actual N is insufficient.  
  - VIF is computed for `baseline_penalty` and `difficulty_score`; predictors with VIF > 5 are dropped and noted.  
- **Causal Framing**: All claims are explicitly associational; difficulty is included as a covariate to mitigate confounding.  

## Compute Feasibility
- **Per‑task runtime** (Llama‑2‑7B 8‑bit on CPU) ≈ 30 s (benchmark).  
- **Total** for 200 tasks [deferred] for baseline + similar budget for evolved set → well under 6 h.  
- **Memory** peak < 5 GB (pandas + scikit‑learn).  

---



