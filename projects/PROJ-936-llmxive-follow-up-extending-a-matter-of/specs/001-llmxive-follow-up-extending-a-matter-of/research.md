# Research: LLM Agent Efficiency vs. Reasoning Trade‑off Analysis

**Feature**: LLM Agent Efficiency vs. Reasoning Trade‑off  
**Date**: 2026-10-24

## Objective
Quantify the relationship between **efficiency penalty** (redundant tool‑call sequences) and **task success rate** for a CPU‑tractable LLM agent, while controlling for intrinsic task difficulty. Validate that the observed trade‑off is robust to the choice of optimal‑path proxy.

## Dataset Strategy
| Role | Source | Access Method | Verified? | Notes |
|------|--------|---------------|-----------|-------|
| Primary task set | τⁿ‑Bench (HuggingFace repo `tau_c_bench`) | `datasets.load_dataset("tau_c_bench")` | **No verified URL** – dataset name used for programmatic loading; pipeline aborts if download fails. |
| Model binaries | Llama‑2‑7B 8‑bit via Ollama (`ollama run llama2:7b-q8_0`) | Local Docker image | N/A | Quantized model fits the free‑tier CPU budget. |

If the τⁿ‑Bench repository cannot be fetched, the pipeline stops with a clear error; no synthetic data are generated.

## Methodology Overview

### 1. Baseline Execution
Run the quantized Llama‑2‑7B agent on ≤ 200 tasks. For each run record:
`task_id`, `run_id`, `success` (bool), `total_calls`, `total_tokens`, `duration_seconds`, `status` (`completed`, `failed`, `timeout`), `warning_codes`, `timestamp`.  
Timeouts > 6 h are logged as `timeout`; the run is marked as failure.  

**Log completeness check**: after execution, verify that ≥ 99 % of rows have non‑null `task_id`, `success`, `total_calls`, and `total_tokens`; abort with a clear error if the threshold is not met.

### 2. Efficiency Penalty (Primary Metric)
- **Primary denominator**: `optimal_path_length` (when present).  
- **Fallback denominator**: `tool_diversity_k` (minimum number of distinct tool types required).  
- **Primary penalty**: `penalty_primary = total_calls / optimal_path_length`.  
- **Fallback penalty** (used only for sensitivity analysis): `penalty_alt = total_calls / tool_diversity_k`.  

If `optimal_path_length` is missing, the pipeline logs warning `OPTIMAL_PATH_MISSING` and **excludes** the task from primary‑penalty analyses (but includes it in the sensitivity branch).  
Flag tasks with `penalty_primary > 2.0` for downstream evolution.

### 3. Correlation & Partial Correlation (FR‑004)
Compute (a) Pearson point‑biserial correlation between continuous `penalty_primary` and binary `success` across the **full** task set, and (b) a **partial correlation** controlling for the out‑of‑fold `difficulty_score` (derived from the difficulty model). Store coefficient *r*, p‑value, 95 % CI; require *p* < 0.05 and |r| ≥ 0.2 (SC‑009). The partial correlation mitigates confounding between efficiency and difficulty.

### 4. Full‑Dataset Difficulty Modeling (FR‑010)
Train a `DecisionTreeRegressor(max_depth=5, random_state=42)` on **all** tasks using only raw task features (excluding any penalty‑derived columns, including `tool_diversity_k`). Use 5‑fold cross‑validation to generate **out‑of‑fold** `difficulty_score` predictions for **every** task. Hold‑out R² ≥ 0.6 is required (SC‑007). The resulting difficulty scores are independent of the efficiency‑penalty metric.

### 5. Cost‑Performance Frontier (SC‑005)
Perform a **paired t‑test** comparing success rates on the original high‑penalty tasks versus their evolved variants (paired per source task). Plot the frontier showing the trade‑off between penalty increase and success‑rate drop.

### 6. Task Evolution (FR‑007)
For each high‑penalty task, generate **≥ 5** variants that **maximize the predicted `difficulty_score`** (the difficulty model is the only selection criterion). Each variant is stored as an `evolved_task` record conforming to `evolved_task.schema.yaml`, including `optimal_path_length`, `features`, etc. The evolution algorithm does **not** use `penalty_primary` as a selection driver, avoiding circularity.

### 7. Evolved‑Task Penalty Increase Check (SC‑008)
After re‑running the baseline on evolved tasks, compute the **observed** average `penalty_primary` of evolved tasks and assert a ≥ 10 % increase over the source tasks. This provides independent evidence that the evolution succeeded in making tasks harder.

### 8. Re‑run Baseline on Evolved Set
Execute the baseline agent on all evolved tasks; log with the same schema as in step 1.

### 9. Trade‑off Evaluation (FR‑005, FR‑009)
- **Primary test**: **McNemar paired test** for difference in success proportions between baseline (original tasks) and baseline (evolved tasks). If any cell count < 5, automatically switch to **Fisher’s exact test** and log a warning. Report statistic, p‑value, and effect size.  
- **Supplementary model**: Logistic regression `evolved_success ~ baseline_penalty + difficulty_score` using the out‑of‑fold difficulty scores. Compute VIF for predictors; if VIF > 5, drop `difficulty_score` and re‑fit, noting the change. Report coefficients, standard errors, odds ratios, p‑values, 95 % CIs; verify the penalty coefficient is negative and significant (p < 0.05).  
- **Power analysis**: Use `statsmodels.stats.power.NormalIndPower` to compute the required sample size for detecting a proportion difference of Δ = 0.15 at α = 0.05 with 80 % power (paired proportion test). Emit a clear warning if the actual N is below this threshold (fulfills FR‑009 and SC‑011).

### 10. Sensitivity Analysis (FR‑008)
Repeat steps 2‑9 using the **fallback** `penalty_alt`. Compare logistic‑regression penalty coefficients: same sign (both negative) and absolute difference ≤ 0.05. Report both primary and sensitivity results.

### 11. Artifact‑Schema Validation (Phase 11)
Validate every generated CSV/JSON/PNG against its corresponding JSON‑Schema contract in `contracts/` (including `artifact.schema.yaml`). Failure to validate aborts the pipeline, ensuring adherence to `artifact.schema.yaml`.

### 12. Reporting
Produce:
- `data/outputs/summary.csv` (coefficients, p‑values, effect sizes for primary and sensitivity analyses).  
- `data/outputs/figures/regression_coefficients.png` (forest plot).  
- `data/outputs/figures/cost_performance_frontier.png`.  
- `report/analysis.md` (narrative of findings, robustness checks, power discussion).

## Statistical Rigor Checklist
| Requirement | Implementation |
|-------------|----------------|
| Multiple‑comparison correction | Not needed (single model per metric). |
| Sample‑size / power justification | Formal power analysis in Phase 9; warning if N < required (paired proportion test). |
| Causal inference | Observational; claims limited to *associational* trade‑off. Difficulty included as a covariate. |
| Measurement validity | Token and call counters read directly from Ollama; tool‑diversity fallback validated via sensitivity analysis. |
| Predictor collinearity | VIF computed for `baseline_penalty` and `difficulty_score`; predictors with VIF > 5 are omitted and noted. |

## Decision / Rationale
- **CPU‑first**: All components run on the free‑tier CPU runner; no GPU is required.  
- **Dataset Availability**: Attempt to download τⁿ‑Bench by name; abort if unavailable (no fabricated mirror).  
- **Model Choice**: Quantized Llama‑2‑7B fits within the 6 h budget for ≤ 200 tasks.  
- **Metric Adjustment**: Primary penalty uses `optimal_path_length` only; fallback used solely for sensitivity.  
- **Statistical Tests**: Paired t‑test for frontier, McNemar/Fisher for success‑rate comparison, logistic regression with VIF check, and power analysis appropriate for paired proportion test.  
- **Selection Bias Mitigation**: Difficulty model trained on the **full** dataset; evolution driven solely by difficulty predictions.  
- **Independence Assurance**: Paired tests respect the within‑task relationship between baseline and evolved outcomes.  

## Expected Deliverables
- `data/derived/baseline_execution.csv` – conforms to `execution_log` schema.  
- `data/derived/filtered_tasks.csv` – tasks with `penalty_primary > 2.0`.  
- `data/derived/correlation_results.json`.  
- `data/derived/difficulty_model.pkl`.  
- `data/derived/evolved_tasks.csv` – conforms to `evolved_task` schema.  
- `data/derived/evolved_execution.csv`.  
- `data/derived/sensitivity_*` files (alternative‑metric artifacts).  
- `data/outputs/summary.csv`.  
- `data/outputs/figures/regression_coefficients.png`.  
- `data/outputs/figures/cost_performance_frontier.png`.  
- `report/analysis.md`.  

---


