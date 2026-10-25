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
Timeouts > 6 h are logged as `timeout`. Missing required fields cause the run to be flagged as failed (SC‑006).

### 2. Efficiency Penalty (Primary Metric)
- **Optimal denominator**: `optimal_path_length` when present.  
- **Fallback**: `tool_diversity_k` (minimum number of distinct tool types required) if `optimal_path_length` is missing.  
- **Penalty**: `penalty = total_calls / optimal_path_length` (primary) or `penalty = total_calls / tool_diversity_k` (fallback).  
- If `optimal_path_length` is absent, emit warning `OPTIMAL_PATH_MISSING` and use the fallback.  
- Flag tasks with `penalty > 2.0` for downstream evolution.

*Construct‑validity note*: The fallback is a heuristic; it may over‑estimate penalties. A dedicated **sensitivity analysis** (Phase 10) evaluates robustness to this choice.

### 3. Correlation & Partial Correlation (FR‑004)
Compute (a) Pearson point‑biserial correlation between continuous `penalty` and binary `success` across the **full** task set, and (b) a **partial correlation** controlling for out‑of‑fold `difficulty_score` (derived from the difficulty model). Store coefficient *r*, p‑value, 95 % CI; require *p* < 0.05 and |r| ≥ 0.2 (SC‑009). The partial correlation mitigates confounding between efficiency and difficulty.

### 4. Reward Modeling – Difficulty Prediction (FR‑007)
Train a `DecisionTreeRegressor(max_depth=5, random_state=42)` **on the filtered high‑penalty tasks only** (penalty > 2.0). Use 5‑fold cross‑validation to generate **out‑of‑fold** `difficulty_score` predictions for **all** tasks (including those not used for training). Hold‑out R² ≥ 0.6 is required (SC‑007). **Importantly, `tool_diversity_k` is excluded from the feature set** to avoid circularity with the penalty metric.

### 5. Cost‑Performance Frontier (SC‑005)
Fit a linear regression `success ~ penalty`; obtain the marginal cost‑performance slope (cost per % success change) and plot the frontier.

### 6. Task Evolution (FR‑007)
For each high‑penalty task, generate **≥ 5** variants that maximize the out‑of‑fold `difficulty_score`. Each variant is stored as an `evolved_task` record conforming to `evolved_task.schema.yaml`. The evolution algorithm does **not** use `tool_diversity_k` as a model feature.

### 7. Evolved‑Task Penalty Increase Check (SC‑008)
After re‑running the baseline on evolved tasks, compute the **observed** average penalty of evolved tasks and assert a ≥ 10 % increase over the source tasks. This provides independent evidence of difficulty amplification, distinct from any model‑predicted penalty.

### 8. Re‑run Baseline on Evolved Set
Execute the baseline agent on all evolved tasks; log with the same schema as in step 1.

### 9. Trade‑off Evaluation (FR‑005)
- **Primary test**: **Chi‑squared test** for difference in success proportions between baseline (original tasks) and baseline (evolved tasks). Report χ², p‑value, and effect size.  
- **Supplementary model**: Logistic regression `evolved_success ~ baseline_penalty + difficulty_score` using **out‑of‑fold** difficulty scores. Report coefficients, standard errors, odds ratios, p‑values, 95 % CIs; verify the penalty coefficient is negative and significant (p < 0.05).  
- **Power analysis**: Using `statsmodels.stats.power.GofChisquarePower`, compute the minimum required sample size for an expected odds‑ratio ≈ 2.5 at α = 0.05. If the actual N is below this threshold, emit a clear warning about limited power.

### 10. Sensitivity Analysis (FR‑008)
Repeat steps 2‑9 using the **pure tool‑diversity** denominator (`penalty_alt = total_calls / tool_diversity_k`). Compare logistic‑regression penalty coefficients:
- Same sign (both negative).  
- Absolute difference in effect size ≤ 0.05 (SC‑010).  

If the dataset lacks an alternative optimal metric, the analysis reports results only for the primary metric.

### 11. Reporting
Produce:
- `data/outputs/summary.csv` (coefficients, p‑values, effect sizes for primary and sensitivity analyses).  
- `data/outputs/figures/regression_coefficients.png` (forest plot).  
- `data/outputs/figures/cost_performance_frontier.png`.  
- `report/analysis.md` (narrative of findings, robustness checks, power discussion).

## Statistical Rigor Checklist
| Requirement | Implementation |
|-------------|----------------|
| Multiple‑comparison correction | Not needed (single model per metric). |
| Sample‑size / power justification | Formal power analysis in Phase 9; warning if N < required. |
| Causal inference | Observational; claims limited to *associational* trade‑off. Difficulty included as a covariate. |
| Measurement validity | Token and call counters read directly from Ollama; tool‑diversity fallback validated via sensitivity analysis. |
| Predictor collinearity | VIF computed for `baseline_penalty` and `difficulty_score`; predictors with VIF > 5 are dropped and noted. |

## Decision / Rationale
- **CPU‑first**: All components run on the free‑tier CPU runner; no GPU is required.  
- **Dataset Availability**: Attempt to download τⁿ‑Bench by name; abort if unavailable (no fabricated mirror).  
- **Model Choice**: Quantized Llama‑2‑7B fits within the 6 h budget for ≤ 200 tasks.  
- **Metric Adjustment**: Primary penalty uses `optimal_path_length` when available, with a documented fallback to `tool_diversity_k`.  
- **Statistical Tests**: Chi‑squared test provides a valid comparison for independent groups; logistic regression supplies effect‑size estimates with out‑of‑fold scores to avoid circularity.  
- **Selection Bias Mitigation**: Difficulty model trained on the filtered high‑penalty set; predictions for all tasks are out‑of‑fold.  
- **Sensitivity Analysis**: Guarantees robustness to the choice of optimal‑path proxy.  

## Expected Deliverables
- `data/derived/baseline_execution.csv` – conforms to `execution_log` schema.  
- `data/derived/filtered_tasks.csv` – tasks with `penalty > 2.0`.  
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



