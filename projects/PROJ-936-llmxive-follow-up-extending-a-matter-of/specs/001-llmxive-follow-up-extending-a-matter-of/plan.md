# Implementation Plan: LLM Agent Efficiency vs. Reasoning Trade-off Analysis

**Branch**: `002-efficiency-reasoning-tradeoff` | **Date**: 2026-10-12 | **Spec**: [spec.md](../specs/002-efficiency-reasoning-tradeoff/spec.md)  
**Input**: Feature specification from `/specs/002-efficiency-reasoning-tradeoff/spec.md`

## Summary
The project must (1) obtain the `τ^c‑Bench` task set (or abort if unavailable), (2) run a CPU‑tractable baseline LLM agent (**Llama‑2‑7B 8‑bit** via Ollama) on each task while logging success, API‑call count, and token consumption, (3) compute an **efficiency penalty** as `agent_calls / optimal_path_length` (or, when `optimal_path_length` is missing, use the **tool‑diversity heuristic** `tool_diversity_k`), (4) filter tasks with penalty > 2.0, (5) train a lightweight regression tree to predict a **task difficulty score** (based on intrinsic features), (6) **evolve** new, harder task variants that maximize predicted difficulty, (7) re‑run the baseline agent on the evolved set, and (8) evaluate the trade‑off using a **Logistic Regression model** (controlling for difficulty) with a **sensitivity analysis** comparing results across both optimal metrics (tool_diversity_k vs. minimum step count). All steps respect the constitution and run within the GitHub Actions free‑tier limits (≤6 h, 2 CPU cores, ~7 GB RAM).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets>=2.14`, `pandas>=2.2`, `scikit-learn>=1.5`, `statsmodels>=0.14`, `ollama>=0.1`, `tqdm`, `pyyaml`, `numpy`, `matplotlib`.  
- **Storage**: File‑based under `data/` (raw dataset, derived logs, model artifacts).  
- **Testing**: `pytest` for unit contracts; integration tests via the contract schemas.  
- **Target Platform**: Linux (GitHub Actions runner).  
- **Performance Goals**: Full pipeline ≤ 6 h on 2‑core CPU; memory ≤ 7 GB.  
- **Scale/Scope**: ≤ 200 tasks (per SC‑005 in the spec) to stay within compute budget.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Random seeds pinned (`np.random.seed(42)`, `random_state=42`). Data fetched from canonical source; aborts if unavailable. Scripts deterministic. |
| II. Verified Accuracy | No new citations introduced. All dataset/model references are to verified open sources. |
| III. Data Hygiene | Raw dataset checksum‑verified; every transformation writes a new file with provenance. |
| IV. Single Source of Truth | All figures/tables derived directly from CSV logs or model outputs tracked in `data/`. |
| V. Versioning Discipline | Artifacts hashed and recorded in `state/projects/PROJ-936-...yaml`. |
| VI. Efficiency‑Penalty Rigor | Penalty computed as `agent_calls / optimal_path_length` (or heuristic) for every task; logged. Sensitivity analysis validates trade-off across both metrics. |
| VII. Cost‑Performance Frontier Quantification | Logistic regression used to quantify the relationship between baseline penalty, difficulty, and evolved success. |

## Project Structure
```text
specs/002-efficiency-reasoning-tradeoff/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── execution_log.schema.yaml
│   └── evolved_task.schema.yaml
└── tasks.md

src/
├── data/
│   ├── raw/
│   ├── derived/
│   └── outputs/
├── pipelines/
│   ├── download.py
│   ├── baseline_run.py
│   ├── penalty_calc.py
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
| **0. Dataset Strategy** | Attempt to download `τ^c‑Bench` from HuggingFace. If unavailable, abort. | FR‑001, FR‑006 | SC‑002 |
| **1. Baseline Execution & Logging** | Run baseline Llama‑2‑7B 8‑bit via Ollama; capture `task_id, run_id, success, total_calls, total_tokens, duration, status, warning_codes, timestamp`. Handle >6 h timeout as `timeout`. | FR‑001, FR‑002 | SC‑001 |
| **2. Efficiency Penalty Calculation & Filtering** | Compute `penalty = total_calls / optimal_path_length`. If `optimal_path_length` is null, use `tool_diversity_k` and log warning `OPTIMAL_PATH_MISSING`. Flag tasks with `penalty > 2.0`. | FR‑003 | SC‑002 |
| **3. Reward Modeling (Difficulty Prediction)** | Train `DecisionTreeRegressor` to predict a **difficulty_score** from intrinsic task features. Hold‑out R² ≥ 0.6 required. | FR‑007 | SC‑004 |
| **4. Task Evolution** | For each high‑penalty task, generate ≥ 5 variations to **maximize predicted difficulty**. Each evolved record conforms to `evolved_task.schema.yaml` and includes a full nested Task object (goal, environment, optimal_path_length, tool_diversity_k, features). | FR‑007 | SC‑004 |
| **5. Re‑run Baseline on Evolved Set** | Execute baseline agent on evolved tasks; log results using same schema. | FR‑002, FR‑004 | SC‑001 |
| **6. Trade‑off Evaluation** | - **Logistic Regression (Primary)**: Model `evolved_success` using `baseline_penalty` and `difficulty_score` as predictors. <br> - **Power check**: Note that N=200 provides ≥80% power to detect an Odds Ratio ≥ 2.5 for the penalty predictor. <br> - **Sensitivity analysis**: Repeat steps 2‑6 using **minimum step count** as alternative optimal metric. Compare trade-off coefficients across both metrics. | FR‑004, FR‑005, FR‑008 | SC‑003, SC‑004 |
| **7. Reporting & Artefact Generation** | Produce `results/summary.csv`, `figures/regression_coefficients.png`, and a concise markdown report. | — | SC‑001‑SC‑004 |

## Detailed Task List (≈ 12 tasks)
1. **Check & Prepare Dataset** – `download.py` (abort if dataset missing).  
2. **Run Baseline Agent** – `baseline_run.py` (captures all schema fields: `run_id`, `timestamp`, etc.).  
3. **Validate Execution Logs** – contract test against `execution_log.schema.yaml`.  
4. **Compute Penalties & Filter** – `penalty_calc.py` (adds `OPTIMAL_PATH_MISSING` warnings; logs tool_diversity_k as heuristic proxy).  
4b. **Generate Task Sub-objects for Evolved Variants** – `evolve_tasks.py` step 1 produces full Task records (with `optimal_path_length`, `tool_diversity_k`, `features`) for each evolved variant, conforming to the Task schema.
5. **Train Difficulty Model** – `model_train.py` (seeded split, R² check).  
6. **Generate Evolved Tasks** – `evolve_tasks.py` (maximizes difficulty; generates full Task sub-objects nested within evolved_task records).  
7. **Validate Evolved Tasks** – contract test against `evolved_task.schema.yaml` (verifies nested Task object structure and all required fields).  
8. **Run Baseline on Evolved Set** – reuse `baseline_run.py` with new input.  
9. **Statistical Evaluation (Primary)** – `evaluation.py` (Logistic Regression with difficulty covariate, power check).  
10. **Sensitivity Analysis (Alternative Metric)** – `evaluation.py` with alternative optimal metric (minimum step count where available); compare trade-off coefficients across both metrics.  
11. **Validate Sensitivity Results** – Ensure both metrics produce consistent directional findings.  
12. **Assemble Report & Figures** – `utils.py` to render markdown & plots.

All phases are ordered to respect data dependencies (download → baseline → penalty → model → evolution → validation → re‑run → evaluation → sensitivity analysis).

## Methodological Rigor Notes

### Optimal Path Definition & Heuristic Proxy
The spec mandates that when `optimal_path_length` is missing, the system MUST use the **tool diversity heuristic** (`tool_diversity_k` = minimum distinct tool types required). This is a **constructed proxy metric** that measures reasoning breadth (tool diversity) rather than step count. The plan acknowledges that this heuristic may **deflate the denominator** relative to a true minimal step count, potentially **inflating the penalty ratio**. To address this category-error concern:

1. **Primary Analysis**: Uses tool_diversity_k-based penalty (as spec mandates).  
2. **Sensitivity Analysis**: Repeats the trade-off evaluation using **minimum step count** (where available in the dataset) as an alternative optimal metric.  
3. **Robustness Check**: Compares Logistic Regression coefficients, p-values, and effect sizes across both metrics to validate that the core trade-off hypothesis (efficiency penalty predicts evolved-task failure) holds **regardless of the optimal definition**.  

This two-metric approach prevents the penalty from appearing inflated solely due to metric construction; instead, it validates that the trade-off is a genuine phenomenon, not a measurement artifact.

### Power & Sample Size
With N≤200 tasks, the study is powered (≥80%) to detect a medium effect size (Odds Ratio ≥ 2.5) for the baseline penalty predictor in the Logistic Regression model at α=0.05. If the final sample size is smaller, power limitations will be explicitly reported.

### Causal vs. Associational Claims
All claims are framed as **associational** (observational design). The Logistic Regression model includes difficulty as a covariate to reduce confounding, but the study does not claim causal effects of efficiency on success.

All phases are ordered to respect data dependencies (download → baseline → penalty → model → evolution → validation → re‑run → evaluation → sensitivity analysis).