# Research: LLM Agent Efficiency vs. Reasoning Trade-off Analysis

**Feature**: LLM Agent Efficiency vs. Reasoning Trade-off  
**Date**: 2026-10-23

## Objective
Quantify how redundant tool‑call sequences (high **efficiency penalty**) impact success rates of a CPU‑tractable LLM agent on multi‑hop tasks, while controlling for intrinsic task difficulty. Validate that the trade‑off holds across two definitions of “optimal path”: (a) the **tool‑diversity** count k (primary metric), and (b) the pure tool‑diversity heuristic itself as a sensitivity check.

## Dataset Strategy
| Role | Source | Access Method | Verified? | Notes |
|------|--------|---------------|-----------|-------|
| Primary task set | τⁿ‑Bench (HuggingFace repo `tau_c_bench`) | `datasets.load_dataset("tau_c_bench")` | **No verified URL** (per "# Verified datasets") – dataset name used for programmatic loading; abort if download fails. |
| Model binaries | Llama‑2‑7B 8‑bit via Ollama (`ollama run llama2:7b-q8_0`) | Local Docker image | N/A | CPU‑only quantized model fits free‑tier budget. |

If the τⁿ‑Bench repository is unreachable, the pipeline aborts with a clear error message; no synthetic stand‑in is used.

## Methodology Overview

### 1. Baseline Execution
Run the baseline Llama‑2‑7B 8‑bit agent on every task (≤ 150 tasks). Log per‑run: `task_id`, `run_id`, `success` (bool), `total_calls`, `total_tokens`, `duration_seconds`, `status` (`completed`, `failed`, `timeout`), `warning_codes`, `timestamp`. Timeouts > 6 h are recorded as `timeout`.

### 2. Efficiency Penalty Calculation (Primary Metric)
- **Optimal denominator**: `tool_diversity_k` (minimum number of distinct tool types required).  
- **Penalty**: `penalty = total_calls / tool_diversity_k`.  
- If `tool_diversity_k` is missing (should not happen), log warning `OPTIMAL_PATH_MISSING` and skip the task.  
- **Filtering**: Flag tasks with `penalty > 2.0` (high‑redundancy subset).

### 3. Point‑Biserial Correlation (FR‑004)
Calculate Pearson correlation between continuous `penalty` and binary `success` across the **full** task set. Record coefficient *r*, p‑value, 95 % CI, and verify that *p* < 0.05 (fulfilling SC‑009).

### 4. Reward Modeling (Difficulty Prediction, FR‑007)
Train a `DecisionTreeRegressor` (max_depth = 5, random_state = 42) on the **full** task set (80/20 train‑test split) to predict `difficulty_score`. Require hold‑out R² ≥ 0.6 (SC‑007).  

### 5. Cost‑Performance Frontier Quantification (SC‑005)
Fit a regression of binary `success` on continuous `penalty` to obtain the marginal cost‑performance curve. Report the slope (cost per % success change) and plot the frontier. This directly satisfies the constitution’s cost‑performance requirement.

### 6. Task Evolution (FR‑007)
For each high‑penalty task, generate **≥ 5** variations that maximize the predicted `difficulty_score`. Evolution modifies the task description and/or tool list while preserving feasibility. Each evolved record conforms to `evolved_task.schema.yaml` and includes the full nested Task object.

### 7. Evolved‑Task Penalty Increase Check (SC‑008)
Compute the average predicted penalty of evolved tasks versus their source tasks. Assert that the increase is ≥ 10 % (SC‑008). Log the actual percentage gain.

### 8. Re‑run Baseline on Evolved Set
Execute the baseline agent on all evolved tasks, logging with the same schema as in step 1.

### 9. Trade‑off Evaluation (FR‑005)
- **Primary test**: **McNemar's test** on paired success outcomes (baseline vs. evolved) for each task pair; report χ², p‑value, and effect size.  
- **Supplementary model**: **Logistic regression** `evolved_success ~ baseline_penalty + difficulty_score`. Report coefficients, standard errors, odds ratios, p‑values, and 95 % CIs.  
- **Effect‑size check**: Verify that the penalty coefficient is negative and statistically significant (p < 0.05).  
- **Power note**: With N ≤ 150, power ≥ 80 % to detect an odds ratio ≥ 2.5 at α = 0.05. If N < 100, issue a power‑limitation warning.

### 10. Sensitivity Analysis (FR‑008)
Repeat steps 2‑9 using the **pure tool‑diversity heuristic** (`penalty_alt = total_calls / tool_diversity_k`). Compare the logistic‑regression penalty coefficients between the primary and alternative metrics:
- Same sign (both negative).  
- Absolute difference in effect size ≤ 0.05 (SC‑010).  

If the dataset lacks a secondary optimal metric, the analysis reports that only the primary metric is available.

### 11. Reporting
Produce:
- `data/outputs/summary.csv` (coefficients, p‑values, effect sizes for both metrics).  
- `data/outputs/figures/regression_coefficients.png` (forest plot of coefficients).  
- `data/outputs/figures/cost_performance_frontier.png` (cost‑performance curve).  
- `report/analysis.md` (narrative of findings, robustness conclusion, power discussion).

## Statistical Rigor Checklist
| Requirement | Implementation |
|-------------|----------------|
| Multiple‑comparison correction | Not needed (single model per metric). |
| Sample‑size / power justification | Power analysis documented in step 9; limitation flagged if N < 100. |
| Causal inference | Observational; claims limited to *associational* trade‑off. Difficulty included as covariate. |
| Measurement validity | Token and call counters come directly from Ollama; tool‑diversity heuristic validated via sensitivity analysis. |
| Predictor collinearity | VIF computed for `baseline_penalty` and `difficulty_score`; if VIF > 5, the higher‑VIF predictor is dropped and limitation noted. |

## Decision / Rationale
- **CPU‑first**: All components run on the free‑tier CPU runner; no GPU is required.  
- **Dataset Availability**: Attempt to download the official τⁿ‑Bench dataset by name; abort if not fetchable (no verified URL).  
- **Model Choice**: Quantized Llama‑2‑7B fits within the 6 h budget for ≤ 150 tasks.  
- **Metric Adjustment**: Adopt `tool_diversity_k` as the optimal denominator to avoid the category‑error flagged by reviewers.  
- **Statistical Tests**: Use McNemar's test as the primary evidence for paired binary outcomes; logistic regression provides covariate‑adjusted effect size.  
- **Selection Bias**: Train difficulty model on the full dataset, not just the high‑penalty subset.  
- **Sensitivity Analysis**: Guarantees robustness against the choice of optimal‑path proxy.  

## Expected Deliverables
- `data/derived/baseline_execution.csv` – conforms to `execution_log.schema.yaml`.  
- `data/derived/filtered_tasks.csv` – tasks with `penalty > 2.0` (primary metric).  
- `data/derived/correlation_results.json` – point‑biserial correlation output.  
- `data/derived/difficulty_model.pkl` – trained regression tree.  
- `data/derived/evolved_tasks.csv` – conforms to `evolved_task.schema.yaml`.  
- `data/derived/evolved_execution.csv` – logs for evolved tasks.  
- `data/derived/sensitivity_*` files – analogous artifacts for the alternative metric.  
- `data/outputs/summary.csv` – final statistical table (both primary and sensitivity results).  
- `data/outputs/figures/regression_coefficients.png` – coefficient forest plot.  
- `data/outputs/figures/cost_performance_frontier.png` – cost‑performance curve.  
- `report/analysis.md` – concise narrative of results and robustness conclusion.

---

