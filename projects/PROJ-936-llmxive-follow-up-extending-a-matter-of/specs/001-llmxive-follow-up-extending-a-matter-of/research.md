# Research: LLM Agent Efficiency vs. Reasoning Trade-off Analysis

**Feature**: LLM Agent Efficiency vs. Reasoning Trade-off  
**Date**: 2026-10-11

## Objective
Quantify how redundant tool‑call sequences (high **efficiency penalty**) impact success rates of a CPU‑tractable LLM agent on multi‑hop tasks, and verify the existence of a statistically significant trade‑off while controlling for intrinsic task difficulty.

## Dataset Strategy
| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| Primary task set | *τ^c‑Bench* (HuggingFace repo) | `datasets.load_dataset("tau_c_bench", streaming=False)` | The pipeline **attempts** to download the official dataset. If the repository is unreachable or the dataset lacks `optimal_path_length`, the run aborts with a clear error (no synthetic placeholder is generated). |
| Model binaries | Llama‑2‑7B 8‑bit via Ollama (local Docker image) | `ollama run llama2:7b-q8_0` | CPU‑only; fits within the 6 h budget for ≤ 200 tasks. |
| No additional external datasets required. |

## Methodology Overview
1. **Baseline Execution** – Run the baseline Llama‑2‑7B 8‑bit agent on every task, logging `task_id`, `success` (bool), `total_calls`, `total_tokens`, `duration_seconds`, and `status`. Timeouts > 6 h are recorded as `timeout`.  
2. **Efficiency Penalty** – Compute `penalty = total_calls / optimal_path_length`. When `optimal_path_length` is `null`, compute `optimal_path_length = tool_diversity_k` (minimum distinct tool types) and emit warning `OPTIMAL_PATH_MISSING`. This penalty is **independent** of the agent’s success because the denominator comes from external ground truth (or a documented heuristic).  
3. **Filtering** – Keep tasks with `penalty > 2.0` (high‑redundancy subset).  
4. **Reward Modeling (Difficulty Prediction)** – Train a `DecisionTreeRegressor` (max_depth=5, random_state=42) on intrinsic task features (e.g., `num_tools`, `desc_len`, `tool_type_distribution`) to predict a **difficulty_score** (not the penalty). Require hold‑out R² ≥ 0.6.  
5. **Task Evolution** – For each high‑penalty task, generate ≥ 5 variations by perturbing the description and tool list to **maximize predicted difficulty** while ensuring the model‑predicted penalty increases by ≥ 10 % (checked post‑generation).  
6. **Re‑run Baseline on Evolved Set** – Execute the baseline agent on evolved tasks, logging the same metrics.  
7. **Statistical Evaluation** –  
   - **Spearman rank correlation** between baseline penalty and Δ success rate (baseline → evolved). Pearson is retained as a secondary check when normality holds.  
   - **McNemar’s test** on paired binary outcomes (success vs. failure) across original vs. evolved tasks; report p‑value (significant if p < 0.05).  
   - **Power check**: If discordant pairs < 10, emit a warning and present descriptive statistics instead of a p‑value. With ≤ 200 tasks the design yields ≥ 80 % power for a medium effect (Cohen’s h≈0.5).  
   - **Sensitivity analysis**: Repeat steps 2‑7 using **minimum step count** (when available) as an alternative optimal metric, comparing results to the tool‑diversity heuristic.  
8. **Reporting** – Produce a CSV `results/summary.csv`, two figures (`correlation.png`, `mcnemar.png`), and a concise markdown summary.

## Statistical Rigor Checklist
| Requirement | Implementation |
|-------------|----------------|
| Multiple‑comparison correction | Not needed (single Spearman and single McNemar test). |
| Sample‑size / power justification | Power warning if < 10 discordant pairs; otherwise note that ≤ 200 tasks provides ≥ 80 % power for medium effects. |
| Causal inference | Observational; claims limited to *associational* trade‑off. |
| Measurement validity | Llama‑2‑7B token counts and Ollama call counters are logged directly; tool‑diversity heuristic is documented and flagged when used. |
| Predictor collinearity | Difficulty model is tree‑based; feature importance will be reported, and any highly correlated features will be noted. |

## Decision / Rationale
- **CPU‑first**: All components (dataset loading, tree training, statistical tests) run comfortably on a modest‑core CPU runner. No GPU is required.  
- **Dataset Availability**: The plan attempts to fetch the real τ^c‑Bench dataset. If unavailable, the run aborts rather than fabricating data, preserving scientific integrity.  
- **Model Choice**: Llama‑2‑7B 8‑bit quantized via Ollama fits within the free‑tier compute budget, unlike the 8 B parameter Llama‑3‑8B.  
- **Statistical Tests**: Spearman rank correlation respects the bounded, potentially skewed nature of the penalty ratio; McNemar’s test is appropriate for paired binary outcomes.  
- **Sensitivity**: Using an alternative optimal metric (minimum step count) ensures findings are not an artefact of the heuristic.

## Expected Deliverables
- `data/derived/baseline_execution.csv` – raw logs for original tasks.  
- `data/derived/filtered_tasks.csv` – tasks with penalty > 2.0.  
- `data/derived/difficulty_model.pkl` – trained regression tree for difficulty.  
- `data/derived/evolved_tasks.csv` – generated task variations.  
- `data/derived/evolved_execution.csv` – logs for evolved tasks.  
- `results/summary.csv` – final metrics (Spearman ρ, McNemar p‑value, effect sizes).  
- `figures/correlation.png`, `figures/mcnemar.png`.  
- `report/analysis.md` – concise narrative of findings.

---

