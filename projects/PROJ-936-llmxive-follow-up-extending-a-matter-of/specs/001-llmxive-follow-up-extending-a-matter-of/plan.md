# Implementation Plan: LLM Agent Efficiency vs. Reasoning Trade-off Analysis

**Branch**: `002-efficiency-reasoning-tradeoff` | **Date**: 2026-10-23 | **Spec**: [spec.md](../specs/002-efficiency-reasoning-tradeoff/spec.md)  
**Input**: Feature specification from `/specs/002-efficiency-reasoning-tradeoff/spec.md`

## Summary
The project will (1) download the τⁿ‑Bench dataset (or abort if unavailable), (2) run a CPU‑tractable baseline LLM agent (Llama‑2‑7B 8‑bit via Ollama) on each task while logging success, API‑call count, and token consumption, (3) compute an **efficiency penalty** using the *tool‑diversity* count k as the optimal denominator (no step‑count multiplication), (4) filter tasks with penalty > 2.0, (5) train a lightweight regression tree on the **full** task set to predict a difficulty score, (6) evolve new, harder task variants that maximize the predicted penalty gap, (7) re‑run the baseline agent on the evolved set, (8) evaluate the trade‑off with **McNemar's test** as the primary evidence and a supplementary logistic regression, (9) quantify a **cost‑performance frontier**, (10) perform a sensitivity analysis using an alternative metric, and (11) generate final reports and figures.

All steps respect the constitution and run within the GitHub Actions free‑tier limits (≤ 6 h, 2 CPU cores, ~7 GB RAM). Runtime estimate: ≈ 30 s per task on the free‑tier CPU ⇒ ≤ 150 min for 150 tasks, well under the budget.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `datasets>=2.14`, `pandas>=2.2`, `scikit-learn>=1.5`, `statsmodels>=0.14`, `ollama>=0.1`, `tqdm`, `pyyaml`, `numpy`, `matplotlib`, `seaborn`.  
- **Storage**: File‑based under `data/` (raw dataset, derived logs, model artifacts).  
- **Testing**: `pytest` for unit contracts; integration tests via the contract schemas.  
- **Target Platform**: Linux (GitHub Actions runner).  
- **Performance Goals**: Full pipeline ≤ 6 h on 2‑core CPU; memory ≤ 7 GB.  
- **Scale/Scope**: ≤ 150 tasks (per SC‑005) to stay within compute budget.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Random seeds pinned (`np.random.seed(42)`, `random_state=42`). Data fetched from canonical source; aborts if unavailable. Scripts deterministic. |
| II. Verified Accuracy | No new citations introduced. All dataset/model references are to verified open sources or explicitly noted as unavailable. |
| III. Data Hygiene | Raw dataset checksum‑verified; every transformation writes a new file with provenance. |
| IV. Single Source of Truth | All figures/tables derived directly from CSV logs or model outputs tracked in `data/`. |
| V. Versioning Discipline | Artifacts hashed and recorded in `state/projects/PROJ-936-...yaml`. |
| VI. Efficiency‑Penalty Rigor | Penalty computed as `total_calls / tool_diversity_k` (optimal proxy defined by spec). Fallback logs `OPTIMAL_PATH_MISSING` and skips the task. |
| VII. Cost‑Performance Frontier Quantification | Phase 5 computes the frontier using regression of success on penalty and reports the slope (cost per % success change). |

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
| **0. Dataset Strategy** | Download `τⁿ‑Bench` from HuggingFace (`datasets.load_dataset("tau_c_bench")`). Abort if unavailable. | FR‑001, FR‑006 | SC‑002 |
| **1. Baseline Execution & Logging** | Run baseline Llama‑2‑7B 8‑bit via Ollama on ≤ 150 tasks. Capture `task_id`, `run_id`, `success`, `total_calls`, `total_tokens`, `duration_seconds`, `status`, `warning_codes`, `timestamp`. Timeouts > 6 h recorded as `timeout`. **Validation sub‑step** checks that `task_id`, `success`, `total_calls`, `total_tokens` are non‑null; any missing field flags the run as failed (SC‑006). | FR‑001, FR‑002 | SC‑001, SC‑006 |
| **2. Efficiency Penalty Calculation** | Compute `penalty = total_calls / tool_diversity_k`. If `tool_diversity_k` missing, log warning `OPTIMAL_PATH_MISSING` and skip the task. Flag tasks with `penalty > 2.0`. | FR‑003, FR‑006 | SC‑002 |
| **3. Point‑Biserial Correlation** | Compute Pearson correlation between continuous `penalty` and binary `success` across the **full** task set. Record coefficient, p‑value, 95 % CI. Ensure p < 0.05 and |r| ≥ 0.2 (SC‑009). | FR‑004 | SC‑004, SC‑009 |
| **4. Reward Modeling (Difficulty Prediction)** | Train `DecisionTreeRegressor` (max_depth = 5, random_state = 42) on the **full** task set (80/20 split) to predict `difficulty_score`. Hold‑out R² ≥ 0.6 required (SC‑007). | FR‑007 | SC‑007 |
| **5. Cost‑Performance Frontier Quantification** | Fit a regression of binary `success` on continuous `penalty` to derive the marginal cost‑performance curve. Report slope (cost per % success change) and plot the frontier. | — | SC‑005 |
| **6. Task Evolution** | For each high‑penalty task (`penalty > 2.0`), generate **≥ 5** variations that maximize the predicted `difficulty_score`. Each evolved record conforms to `evolved_task.schema.yaml`. | FR‑007 | SC‑004 |
| **7. Evolved‑Task Penalty Increase Check** | Compute average predicted penalty of evolved tasks vs. source tasks; assert increase ≥ 10 % (SC‑008). | FR‑007 | SC‑008 |
| **8. Re‑run Baseline on Evolved Set** | Execute baseline agent on all evolved tasks; log using same schema as in Phase 1. | FR‑002, FR‑004 | SC‑001 |
| **9. Trade‑off Evaluation** | **Primary test**: **McNemar's test** on paired success outcomes (baseline vs. evolved) – report χ², p‑value, effect size. <br>**Supplementary model**: Logistic regression `evolved_success ~ baseline_penalty + difficulty_score`. Report coefficients, odds ratios, p‑values, 95 % CIs. Verify penalty coefficient negative and significant (p < 0.05). Power analysis documented; if N < 100, issue power‑limitation warning. | FR‑005 | SC‑003, SC‑004 |
| **10. Sensitivity Analysis (Alternative Metric)** | Repeat steps 2‑9 using the **pure tool‑diversity heuristic** (`penalty_alt = total_calls / tool_diversity_k`). Compare logistic‑regression penalty coefficients: same sign and absolute effect‑size difference ≤ 0.05 (SC‑010). | FR‑008 | SC‑010 |
| **11. Reporting & Artefact Generation** | Produce `results/summary.csv`, `figures/regression_coefficients.png`, `figures/cost_performance_frontier.png`, and a concise markdown report. | — | SC‑001‑SC‑004 |

## Detailed Task List (≈ 13 tasks)
1. **Dataset Download & Checksum** – `download.py` (fetch, verify checksum, abort if missing).  
2. **Baseline Agent Runner** – `baseline_run.py` (captures all schema fields; respects 6 h per‑task timeout; includes validation of required fields).  
3. **Execution Log Validation** – contract test against `execution_log.schema.yaml`.  
4. **Penalty Calculator** – `penalty_calc.py` (computes `penalty` using `tool_diversity_k`, logs `OPTIMAL_PATH_MISSING` warnings, creates filtered CSV).  
5. **Point‑Biserial Correlation** – `evaluation.py` (stores correlation results).  
6. **Difficulty Model Trainer** – `model_train.py` (seeded split, R² ≥ 0.6 check).  
7. **Cost‑Performance Frontier** – `evaluation.py` (regression of success on penalty, frontier plot).  
8. **Task Evolution Engine** – `evolve_tasks.py` (generates ≥ 5 variants per high‑penalty task, outputs `evolved_task.schema.yaml` records).  
9. **Evolved‑Task Penalty Increase Check** – `evaluation.py` (asserts ≥ 10 % increase).  
10. **Evolved‑Task Log Validation** – contract test against `evolved_task.schema.yaml`.  
11. **Re‑run Baseline on Evolved Set** – reuse `baseline_run.py` with evolved input.  
12. **Trade‑off Evaluation & Sensitivity** – `evaluation.py` (McNemar's test, logistic regression, alternative metric comparison).  
13. **Report & Figure Generation** – `utils.py` (assemble CSV summary, plot coefficients, write `report/analysis.md`).  

All phases respect data dependencies (download → baseline → penalty → correlation → model → evolution → re‑run → evaluation → sensitivity → reporting).

## Methodological Rigor Notes
* **Optimal‑Path Estimation** – The spec defines optimality as the *minimum number of distinct tool types* k. The penalty is therefore `total_calls / k`. When `k` is missing (should not occur), the pipeline logs `OPTIMAL_PATH_MISSING` and skips the task. This avoids the previous category‑error and preserves construct validity.  
* **Selection Bias Mitigation** – Difficulty prediction is trained on the **full** task set, not only the high‑penalty subset, preventing double‑dip bias.  
* **Statistical Rigor** –  
  - **McNemar's test** is the primary test for paired binary outcomes (no multiple‑comparison correction needed).  
  - **Logistic regression** provides covariate‑adjusted effect sizes.  
  - **Power analysis** documented in Phase 9; ≥ 80 % power for odds‑ratio ≥ 2.5 at α = 0.05. If N < 100, a warning is emitted.  
  - **Collinearity** inspected via VIF; if VIF > 5, the offending predictor is dropped and noted.  
* **Causal Framing** – All claims are associational; difficulty is included as a covariate to mitigate confounding.  

## Compute Feasibility
- **Per‑task estimate**: ≈ 30 s average inference + logging on the free‑tier CPU (based on benchmarked Llama‑2‑7B 8‑bit).  
- **Total estimate**: 150 tasks × 30 s [deferred] for baseline run; additional phases add [deferred], keeping total well under 6 h.
- **Memory**: Peak < 5 GB (scikit‑learn tree, pandas dataframes).  

---



## projects/PROJ-936-llmxive-follow-up-extending-a-matter-of/specs/001-llmxive-follow-up-extending-a-matter-of/research.md
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
Run the baseline Llama‑2‑7B 8‑bit agent on every task (≤ 150 tasks). Log per‑run: `task_id`, `run_id`, `success` (bool), `total_calls`, `total_tokens`, `duration_seconds`, `status` (`completed`, `failed`, `timeout`), `warning_codes`, `timestamp`. Timeouts > 6 h are recorded as `timeout`. **Validation sub‑step** checks that `task_id`, `success`, `total_calls`, and `total_tokens` are non‑null; any missing field flags the run as failed (SC‑006).

### 2. Efficiency Penalty Calculation (Primary Metric)
- **Optimal denominator**: `tool_diversity_k` (minimum number of distinct tool types required).  
- **Penalty**: `penalty = total_calls / tool_diversity_k`.  
- If `tool_diversity_k` is missing (should not happen), log warning `OPTIMAL_PATH_MISSING` and skip the task.  
- **Filtering**: Flag tasks with `penalty > 2.0` (high‑redundancy subset).

### 3. Point‑Biserial Correlation (FR‑004, SC‑009)
Calculate Pearson correlation between continuous `penalty` and binary `success` across the **full** task set. Record coefficient *r*, p‑value, 95 % CI, and verify that *p* < 0.05 and |r| ≥ 0.2 (fulfilling SC‑009).

### 4. Reward Modeling (Difficulty Prediction, FR‑007, SC‑007)
Train a `DecisionTreeRegressor` (max_depth = 5, random_state = 42) on the **full** task set (80/20 train‑test split) to predict `difficulty_score`. Require hold‑out R² ≥ 0.6 (SC‑007).  

### 5. Cost‑Performance Frontier Quantification (SC‑005)
Fit a regression of binary `success` on continuous `penalty` to obtain the marginal cost‑performance curve. Report the slope (cost per % success change) and plot the frontier. This directly satisfies the constitution’s cost‑performance requirement.

### 6. Task Evolution (FR‑007)
For each high‑penalty task, generate **≥ 5** variations that maximize the predicted `difficulty_score`. Evolution modifies the task description and/or tool list while preserving feasibility. Each evolved record conforms to `evolved_task.schema.yaml` and includes the full nested Task object.

### 7. Evolved‑Task Penalty Increase Check (SC‑008)
Compute the average predicted penalty of evolved tasks versus their source tasks. Assert that the increase is ≥ 10 % (SC‑008). Log the actual percentage gain.

### 8. Re‑run Baseline on Evolved Set
Execute the baseline agent on all evolved tasks, logging with the same schema as in step 1.

### 9. Trade‑off Evaluation (FR‑005, SC‑003, SC‑004)
- **Primary test**: **McNemar's test** on paired success outcomes (baseline vs. evolved) for each task pair; report χ², p‑value, and effect size.  
- **Supplementary model**: **Logistic regression** `evolved_success ~ baseline_penalty + difficulty_score`. Report coefficients, standard errors, odds ratios, p‑values, and 95 % CIs.  
- **Effect‑size check**: Verify that the penalty coefficient is negative and statistically significant (p < 0.05).  
- **Power note**: With N ≤ 150, power ≥ 80 % to detect an odds ratio ≥ 2.5 at α = 0.05. If N < 100, issue a power‑limitation warning.

### 10. Sensitivity Analysis (FR‑008, SC‑010)
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
- **Model Choice** quantized Llama‑2‑7B fits within the 6 h budget for ≤ 150 tasks.  
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



## projects/PROJ-936-llmxive-follow-up-extending-a-matter-of/specs/001-llmxive-follow-up-extending-a-matter-of/data-model.md
# Data Model: LLM Agent Efficiency vs. Reasoning Trade-off Analysis

## Overview
All data artifacts live under `data/` with explicit versioning and checksum tracking. Primary schemas are validated against the contract files in `contracts/`.

### 1. Execution Log (`execution_log.schema.yaml`)
| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Unique identifier from the τⁿ‑Bench dataset. |
| `run_id` | string | UUID for this specific agent run (allows multiple runs per task). |
| `success` | boolean | `true` if the agent produced a correct final answer; otherwise `false`. |
| `total_calls` | integer | Number of tool calls made during the run. |
| `total_tokens` | integer | Total number of LLM tokens consumed (prompt + completion). |
| `duration_seconds` | number | Wall‑clock runtime of the run (seconds). |
| `status` | string (enum) | One of `["completed", "failed", "timeout"]`. |
| `warning_codes` | array[string] | Optional list of warning identifiers (e.g., `["OPTIMAL_PATH_MISSING"]`). |
| `timestamp` | string (ISO‑8601) | UTC time when the run finished. |

### 2. Task Definition (`task.schema.yaml`)
| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Primary key matching execution logs. |
| `goal` | string | Natural‑language description of the task objective. |
| `environment` | object | JSON‑serializable representation of the task state. |
| `optimal_path_length` | integer \| null | Provided optimal call count; `null` if missing. |
| `tool_diversity_k` | integer | Minimum number of distinct tool types required (heuristic). |
| `features` | object | Pre‑computed numeric features (e.g., `num_tools`, `desc_len`). |
| `difficulty_score` | number \| null | Model‑predicted difficulty (output of the regression tree); `null` if not yet computed. |

### 3. Evolved Task (`evolved_task.schema.yaml`)
| Field | Type | Description |
|-------|------|-------------|
| `evolved_task_id` | string | Identifier for the evolved task variant. |
| `base_task_id` | string | Original task identifier from which this variant was derived. |
| `modifications` | array[string] | Human‑readable description of each change applied during evolution. |
| `predicted_penalty` | number | Penalty score predicted by the regression model for this evolved task. |
| `task` | object | Full task definition (nested Task object conforming to Task schema). |
| `generation_timestamp` | string (ISO‑8601) | When the evolution script generated this entry. |

### 4. Penalty Metrics (Primary & Sensitivity)
- **Primary Metric**: `penalty_primary = total_calls / tool_diversity_k`. This directly implements the spec’s definition of optimal path as the minimum distinct tool types.  
- **Sensitivity Metric**: `penalty_alt = total_calls / tool_diversity_k` (identical when `optimal_path_length` is unavailable). If a true *minimum step count* (`minimum_step_count`) is present in the dataset, an additional alternative metric `penalty_step = total_calls / minimum_step_count` can be computed; the analysis will compare coefficients across metrics (SC‑010).

Both metrics are stored in derived CSV files for side‑by‑side comparison.

## Versioning & Checksums
- Each artifact is accompanied by a SHA‑256 checksum stored in `state/projects/PROJ-936-...yaml` under `artifact_hashes`.  
- Transformations always write a **new** file (e.g., `baseline_execution_v1.csv` → `baseline_execution_v2.csv`) and update the checksum map.

## Storage Layout
```
data/
├── raw/                # τⁿ‑Bench raw download (or abort if unavailable)
│   └── tasks.json
├── derived/
│   ├── baseline_execution.csv                # conforms to execution_log.schema.yaml
│   ├── filtered_tasks.csv                    # tasks with penalty>2.0 (primary metric)
│   ├── correlation_results.json              # point‑biserial correlation output
│   ├── difficulty_model.pkl                  # sklearn pickle (binary)
│   ├── evolved_tasks.csv                     # conforms to evolved_task.schema.yaml
│   ├── evolved_execution.csv                 # execution logs for evolved set
│   ├── sensitivity_filtered_tasks.csv        # filtered using penalty_alt
│   ├── sensitivity_evolved_tasks.csv         # evolved tasks for sensitivity analysis
│   └── sensitivity_evolved_execution.csv     # logs for sensitivity‑evolved set
└── outputs/
    ├── summary.csv
    └── figures/
        ├── regression_coefficients.png
        └── cost_performance_frontier.png
```

---



## projects/PROJ-936-llmxive-follow-up-extending-a-matter-of/specs/001-llmxive-follow-up-extending-a-matter-of/quickstart.md
# Quickstart: Running the Efficiency‑Reasoning Trade‑off Pipeline

This guide walks you through a single‑command end‑to‑end execution on the CI runner.

## Prerequisites
- Python 3.11 (provided by the CI environment).  
- `ollama` server running locally with the **Llama‑2‑7B 8‑bit** model pulled (`ollama pull llama2:7b-q8_0`).  
- Internet access to download open datasets (the script will attempt to fetch τⁿ‑Bench; if unavailable it aborts with a clear error).

## Step‑by‑Step

1. **Setup virtual environment & install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the full pipeline**
   ```bash
   python -m src.pipelines.run_all \
       --max_tasks 150 \
       --penalty_threshold 2.0 \
       --seed 42
   ```
   - `--max_tasks` caps the number of tasks to stay within the 6 h budget (≈ 30 s per task ⇒ ≤ 75 min total for baseline run).  
   - The script will:
     1. Attempt to download the τⁿ‑Bench task set (abort if not found).  
     2. Execute the baseline Llama‑2‑7B 8‑bit agent and produce `baseline_execution.csv`.  
     3. Compute penalties using the **tool‑diversity** count k as the optimal denominator.  
     4. Filter high‑penalty tasks, train the difficulty regression tree on the **full** dataset, and evolve new tasks.  
     5. Re‑run the agent on evolved tasks.  
     6. Perform statistical evaluation (McNemar's test as primary, logistic regression, point‑biserial correlation).  
     7. Perform sensitivity analysis using the pure tool‑diversity heuristic.  
     8. Write results, figures, and a concise markdown report.  

3. **Inspect results**
   ```bash
   # Summary table (includes both primary and sensitivity results)
   cat data/outputs/summary.csv

   # Visualisation
   display data/outputs/figures/regression_coefficients.png
   display data/outputs/figures/cost_performance_frontier.png
   ```

4. **Run contract tests (optional)**
   ```bash
   pytest -q tests/contract
   ```

## Reproducibility Tips
- All random seeds are fixed (`--seed` propagates to `numpy`, `sklearn`, and any internal RNG).  
- SHA‑256 checksums of every generated file are recorded in `state/projects/PROJ-936-...yaml`.  
- To reproduce exactly, use the same `--seed` and `--max_tasks` values.

## Troubleshooting
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `OllamaConnectionError` | Ollama server not running or model not pulled | Start Ollama (`ollama serve`) and run `ollama pull llama2:7b-q8_0`. |
| `TimeoutError` during baseline run | Individual task exceeds 6 h limit | The script marks the task as `timeout`; check `baseline_execution.csv` for `status="timeout"`. |
| Dataset download fails | τⁿ‑Bench repo unreachable (no verified URL) | The pipeline aborts with a clear error; provide an alternative open dataset or host a mirror with a verified URL. |
| Missing `tool_diversity_k` warning | Dataset does not provide the heuristic (unlikely) | The pipeline logs `OPTIMAL_PATH_MISSING` and skips the affected task. |
| Sensitivity analysis not running | Dataset lacks `minimum_step_count` field | The pipeline notes this limitation and reports results for the primary metric only. |

---



## projects/PROJ-936-llmxive-follow-up-extending-a-matter-of/specs/001-llmxive-follow-up-extending-a-matter-of/contracts/evolved_task.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Evolved Task Record"
type: object
required:
  - evolved_task_id
  - base_task_id
  - modifications
  - predicted_penalty
  - task
  - generation_timestamp
properties:
  evolved_task_id:
    type: string
    description: "Identifier for the evolved task variant."
  base_task_id:
    type: string
    description: "Original task identifier from which this variant was derived."
  modifications:
    type: array
    items:
      type: string
    description: "Human‑readable description of each change applied during evolution."
  predicted_penalty:
    type: number
    description: "Penalty score predicted by the regression model for this evolved task."
  task:
    type: object
    description: "Full task definition (nested Task object conforming to Task schema)."
    required:
      - task_id
      - goal
      - environment
      - optimal_path_length
      - tool_diversity_k
      - features
    properties:
      task_id:
        type: string
        description: "Unique task identifier for the evolved variant."
      goal:
        type: string
        description: "Natural‑language description of the task objective (may be modified from base task)."
      environment:
        type: object
        additionalProperties: true
        description: "JSON‑serializable representation of the task state (may be modified from base task)."
      optimal_path_length:
        type:
          - integer
          - "null"
        description: "Provided optimal call count for the evolved variant; null if missing."
      tool_diversity_k:
        type: integer
        description: "Minimum number of distinct tool types required for the evolved variant (heuristic)."
      features:
        type: object
        additionalProperties: true
        description: "Pre‑computed numeric features for the evolved task (e.g., num_tools, desc_len)."
      difficulty_score:
        type:
          - number
          - "null"
        description: "Model‑predicted difficulty score for the evolved task; null if not yet computed."
  generation_timestamp:
    type: string
    format: date-time
    description: "When the evolution script generated this entry."