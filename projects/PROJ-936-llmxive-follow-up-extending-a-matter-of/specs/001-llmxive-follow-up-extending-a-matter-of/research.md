# Research: LLM Agent Efficiency vs. Reasoning Trade-off Analysis

**Feature**: LLM Agent Efficiency vs. Reasoning Trade-off  
**Date**: 2026-10-12

## Objective
Quantify how redundant tool‑call sequences (high **efficiency penalty**) impact success rates of a CPU‑tractable LLM agent on multi‑hop tasks, and verify the existence of a statistically significant trade‑off while controlling for intrinsic task difficulty. Validate that the trade‑off hypothesis holds across multiple definitions of "optimal path length" to ensure robustness against metric construction artifacts.

## Dataset Strategy
| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| Primary task set | *τ^c‑Bench* (HuggingFace repo) | `datasets.load_dataset("tau_c_bench", streaming=False)` | The pipeline **attempts** to download the official dataset. If the repository is unreachable or the dataset lacks `optimal_path_length`, the run aborts with a clear error. |
| Model binaries | A quantized Llama model via Ollama (local Docker image) | `ollama run llama2:7b-q8_0` | CPU‑only; fits within the 6 h budget for ≤ 200 tasks. |

## Methodology Overview

### 1. Baseline Execution
Run the baseline Llama‑2‑7B 8‑bit agent on every task, logging `task_id`, `success` (bool), `total_calls`, `total_tokens`, `duration_seconds`, and `status`. Timeouts > 6 h are recorded as `timeout`.

### 2. Efficiency Penalty Calculation (Primary Metric: Tool Diversity Heuristic)
Compute `penalty = total_calls / optimal_path_length`. When `optimal_path_length` is `null`, compute `optimal_path_length = tool_diversity_k` (minimum distinct tool types) and emit warning `OPTIMAL_PATH_MISSING`. 

**Critical Note on Metric Construction**: The tool‑diversity heuristic measures the minimum number of **distinct tool types** required to solve a task, not the minimum number of **steps**. This is a **constructed proxy metric** for reasoning breadth. When `tool_diversity_k` is used as the denominator in the penalty ratio, it may **deflate the denominator relative to a true minimal step count**, potentially **inflating the penalty**. This is acknowledged as a **heuristic fallback** mandated by the spec, not as a measure of absolute efficiency. To validate that the trade‑off is a genuine phenomenon and not merely a measurement artifact, a sensitivity analysis using an alternative optimal metric is required (see Step 8 below).

### 3. Filtering
Keep tasks with `penalty > 2.0` (high‑redundancy subset).

### 4. Reward Modeling (Difficulty Prediction)
Train a `DecisionTreeRegressor` (max_depth=5, random_state=42) on intrinsic task features to predict a **difficulty_score**. Require hold‑out R² ≥ 0.6.

### 5. Task Evolution
For each high‑penalty task, generate ≥ 5 variations by perturbing the description and tool list to **maximize predicted difficulty**. Evolution is driven by difficulty, not by a target penalty increase, to avoid circularity in the trade-off analysis. Each evolved task record includes a full nested Task object with all required fields (`task_id`, `goal`, `environment`, `optimal_path_length`, `tool_diversity_k`, `features`).

### 6. Re-run Baseline on Evolved Set
Execute the baseline agent on evolved tasks, logging the same metrics.

### 7. Statistical Evaluation (Primary: Tool Diversity Heuristic)
- **Logistic Regression**: Model the probability of success on evolved tasks (`evolved_success`) using `baseline_penalty` and `difficulty_score` as independent variables. This controls for the confound where higher difficulty drives both penalty and failure.  
- **Power Analysis**: With N=200 tasks, the study is powered (≥80%) to detect a medium effect size (Odds Ratio ≥ 2.5) for the baseline penalty predictor at α=0.05.  
- **Interpretation**: Report the coefficient, standard error, and p-value for the baseline penalty term. A significant negative coefficient indicates that higher efficiency penalties predict lower success rates on evolved tasks.

### 8. Sensitivity Analysis (Alternative Metric: Minimum Step Count)
Repeat steps 2–7 using **minimum step count** (when available in the dataset) as an alternative optimal metric:

- **Recompute penalty** as `agent_calls / minimum_step_count`.  
- **Refilter** tasks with penalty > 2.0 (may result in a different subset).  
- **Retrain difficulty model** on the new filtered set.  
- **Re-evolve tasks** and re-run baseline on the new evolved set.  
- **Refit Logistic Regression** with the new penalty metric and difficulty score.  
- **Compare coefficients**: Report the baseline penalty coefficient (and p-value) from both metrics side-by-side.  
- **Robustness conclusion**: If both metrics yield a significant negative coefficient for the baseline penalty term (i.e., higher penalty predicts lower success), conclude that the trade-off is robust to the definition of "optimal path length" and is not merely a measurement artifact.

If the dataset does not provide `minimum_step_count`, the sensitivity analysis will note this limitation and report results for the tool-diversity heuristic only.

## Statistical Rigor Checklist
| Requirement | Implementation |
|-------------|----------------|
| Multiple‑comparison correction | Not needed (single Logistic Regression model per metric). |
| Sample‑size / power justification | Power analysis justifies N=200 for medium effect size (OR ≥ 2.5). If final N is smaller, power limitation is explicitly reported. |
| Causal inference | Observational; claims limited to *associational* trade‑off. Difficulty is included as a covariate to reduce confounding. |
| Measurement validity | Llama‑2‑7B token counts and Ollama call counters are logged directly. Tool‑diversity heuristic is documented as a spec‑mandated fallback and validated via sensitivity analysis. |
| Predictor collinearity | Difficulty and penalty will be checked for collinearity (VIF); if high (VIF > 5), the model will report the most stable predictor and note the collinearity limitation. |

## Decision / Rationale
- **CPU‑first**: All components run on a modest‑core CPU runner. No GPU is required.  
- **Dataset Availability**: The plan attempts to fetch the real τ^c‑Bench dataset. If unavailable, the run aborts.  
- **Model Choice**: Llama‑2‑7B 8‑bit quantized via Ollama fits within the free‑tier compute budget.  
- **Statistical Tests**: Logistic Regression is used instead of Spearman correlation or McNemar's test to allow for covariate control (difficulty) and to correctly handle binary outcomes for non-identical task instances.  
- **Evolution Strategy**: Evolving for difficulty only (not penalty) ensures that the relationship between baseline penalty and evolved failure is not a tautology.  
- **Sensitivity Analysis**: Two-metric approach (tool diversity vs. minimum step count) prevents the penalty from appearing inflated solely due to metric construction; instead, it validates that the trade-off is a genuine phenomenon.

## Expected Deliverables
- `data/derived/baseline_execution.csv` – raw logs for original tasks.  
- `data/derived/filtered_tasks.csv` – tasks with penalty > 2.0 (primary metric: tool diversity).  
- `data/derived/difficulty_model.pkl` – trained regression tree for difficulty.  
- `data/derived/evolved_tasks.csv` – generated task variations with nested Task objects.  
- `data/derived/evolved_execution.csv` – logs for evolved tasks.  
- `data/derived/sensitivity_filtered_tasks.csv` – tasks with penalty > 2.0 (alternative metric: minimum step count).  
- `data/derived/sensitivity_evolved_tasks.csv` – evolved tasks for sensitivity analysis.  
- `data/derived/sensitivity_evolved_execution.csv` – logs for sensitivity-evolved tasks.  
- `results/summary.csv` – final metrics (Logistic Regression coefficients, p-values, effect sizes for both metrics).  
- `figures/regression_coefficients.png` – visualization of coefficients and confidence intervals for both metrics.  
- `report/analysis.md` – concise narrative of findings, including robustness conclusion.
