# Implementation Plan: LLM Agent Efficiency vs. Reasoning Trade-off Analysis

**Branch**: `002-efficiency-reasoning-tradeoff` | **Date**: 2026-10-11 | **Spec**: [spec.md](../specs/002-efficiency-reasoning-tradeoff/spec.md)  
**Input**: Feature specification from `/specs/002-efficiency-reasoning-tradeoff/spec.md`

## Summary
The project must (1) obtain the `τ^c‑Bench` task set (or abort if unavailable), (2) run a CPU‑tractable baseline LLM agent (**Llama‑2‑7B 8‑bit** via Ollama) on each task while logging success, API‑call count, and token consumption, (3) compute an **efficiency penalty** as `agent_calls / optimal_path_length` (or, when `optimal_path_length` is missing, use the **tool‑diversity heuristic** `tool_diversity_k`), (4) filter tasks with penalty > 2.0, (5) train a lightweight regression tree to predict a **task difficulty score** (based on intrinsic features, not the penalty), (6) **evolve** new, harder task variants that maximize predicted difficulty while monitoring penalty increase, (7) re‑run the baseline agent on the evolved set, and (8) evaluate the trade‑off via **Spearman rank correlation** and **McNemar’s test**, plus a sensitivity analysis using an alternative optimal metric (minimum step count). All steps respect the constitution (reproducibility, data hygiene, efficiency‑penalty rigor, etc.) and run within the GitHub Actions free‑tier limits (≤6 h, 2 CPU cores, ~7 GB RAM).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets>=2.14`, `pandas>=2.2`, `scikit-learn>=1.5`, `statsmodels>=0.14`, `ollama>=0.1` (for local Llama‑2‑7B 8‑bit), `tqdm`, `pyyaml`, `numpy`, `matplotlib`.  
- **Storage**: File‑based under `data/` (raw dataset, derived logs, model artifacts).  
- **Testing**: `pytest` for unit contracts; integration tests via the contract schemas.  
- **Target Platform**: Linux (GitHub Actions runner).  
- **Performance Goals**: Full pipeline ≤ 6 h on 2‑core CPU; memory ≤ 7 GB.  
- **Scale/Scope**: ≤ 200 tasks (per SC‑005 in the spec) to stay within compute budget.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Random seeds pinned (`np.random.seed(42)`, `random_state=42`). Data fetched from canonical source; aborts if unavailable. Scripts deterministic. |
| II. Verified Accuracy | No new citations introduced. All dataset/model references are to verified open sources (or explicitly flagged as unavailable). |
| III. Data Hygiene | Raw dataset checksum‑verified; every transformation writes a new file with provenance. |
| IV. Single Source of Truth | All figures/tables derived directly from CSV logs or model outputs tracked in `data/`. |
| V. Versioning Discipline | Artifacts hashed and recorded in `state/projects/PROJ-936-...yaml`. |
| VI. Efficiency‑Penalty Rigor | Penalty computed as `agent_calls / optimal_path_length` (or heuristic) for every task; logged. |
| VII. Cost‑Performance Frontier Quantification | Paired t‑tests, Spearman correlation, and McNemar’s test included in final analysis. |

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
└── tasks.md   # generated later

src/
├── data/
│   ├── raw/                # τ^c‑Bench download (or abort)
│   ├── derived/            # logs, filtered sets, models
│   └── outputs/            # figures, tables
├── pipelines/
│   ├── download.py
│   ├── baseline_run.py
│   ├── penalty_calc.py
│   ├── model_train.py
│   ├── evolve_tasks.py
│   ├── evaluation.py
│   └── utils.py
└── __main__.py             # entry point

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
| **0. Dataset Strategy** | Attempt to download `τ^c‑Bench` from HuggingFace. If unavailable, abort with clear error; no synthetic placeholder is used. | FR‑001, FR‑006 | SC‑002 |
| **1. Baseline Execution & Logging** | Run baseline Llama‑2‑7B 8‑bit via Ollama on each task; capture `task_id, success, total_calls, total_tokens, duration, status`. Handle >6 h timeout as `timeout`. | FR‑001, FR‑002 | SC‑001 |
| **2. Efficiency Penalty Calculation & Filtering** | Compute `penalty = total_calls / optimal_path_length`. If `optimal_path_length` is null, use `tool_diversity_k` and log warning `OPTIMAL_PATH_MISSING`. Flag tasks with `penalty > 2.0`. | FR‑003 | SC‑002 |
| **3. Reward Modeling (Difficulty Prediction)** | Train `DecisionTreeRegressor` (max_depth=5, random_state=42) to predict a **difficulty_score** derived from intrinsic task features (e.g., `num_tools`, `desc_len`). Hold‑out R² ≥ 0.6 required. | FR‑007 | SC‑004 |
| **4. Task Evolution** | For each high‑penalty task, generate ≥ 5 variations by perturbing description/tool list to **maximize predicted difficulty** (not penalty). Keep only variants whose predicted penalty increases by ≥ 10% (checked post‑generation). | FR‑007 (generation) | SC‑004 |
| **5. Re‑run Baseline on Evolved Set** | Execute baseline agent on evolved tasks; log results using same schema. | FR‑002, FR‑004 | SC‑001 |
| **6. Trade‑off Evaluation** | - **Spearman rank correlation** between baseline penalty and Δ success rate (baseline → evolved). <br> - **McNemar’s test** on paired success outcomes. <br> - **Power check**: warn if discordant pairs < 10; otherwise note that ≤ 200 tasks gives ≥ 80 % power for medium effect (Cohen’s h≈0.5). <br> - **Sensitivity analysis**: repeat steps 2‑6 using **minimum step count** as alternative optimal metric. | FR‑004, FR‑005 | SC‑003, SC‑004 |
| **7. Reporting & Artefact Generation** | Produce `results/summary.csv`, `figures/correlation.png`, `figures/mcnemar.png`, and a concise markdown report. | — | SC‑001‑SC‑004 |

## Detailed Task List (≈ 10 tasks)
1. **Check & Prepare Dataset** – `download.py` (abort if dataset missing).  
2. **Run Baseline Agent** – `baseline_run.py` (handles timeouts, logs `timeout` status).  
3. **Validate Execution Logs** – contract test against `execution_log.schema.yaml`.  
4. **Compute Penalties & Filter** – `penalty_calc.py` (adds `OPTIMAL_PATH_MISSING` warnings).  
5. **Train Difficulty Model** – `model_train.py` (seeded split, R² check).  
6. **Generate Evolved Tasks** – `evolve_tasks.py` (optimizes difficulty, checks penalty increase).  
7. **Run Baseline on Evolved Set** – reuse `baseline_run.py` with new input.  
8. **Statistical Evaluation** – `evaluation.py` (Spearman, McNemar, paired t‑test, power warnings).  
9. **Sensitivity Analysis** – `evaluation.py` with alternative optimal metric.  
10. **Assemble Report & Figures** – `utils.py` to render markdown & plots.

All phases are ordered to respect data dependencies (download → baseline → penalty → model → evolution → re‑run → evaluation).

---

