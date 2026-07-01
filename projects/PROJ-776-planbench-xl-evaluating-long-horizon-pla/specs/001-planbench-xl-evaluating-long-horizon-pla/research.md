# Research: PlanBench-XL Reproduction & Validation

## 1. Overview
This research phase validates the feasibility of reproducing the PlanBench-XL benchmark (arXiv:2606.22388) within the constraints of a free-tier CI environment. It confirms dataset availability, model accessibility, and the computational tractability of the proposed approach.

**Critical Note on Statistical Power**: This study uses a sample size of n=5 tasks per condition. This is **insufficient for statistical significance** (power analysis not applicable). The goal is **functional validation** (does the code run? do the conditions work?) and **mechanism verification** (does blocking cause a drop?), NOT precise metric replication or hypothesis testing. The "statistically significant performance drop" requirement in User Story 2 of the source spec is scientifically impossible with n=5 and is flagged as a **Spec Contradiction**.

## 2. Verified Datasets

| Dataset Name | Source/URL | Verification Status | Notes |
|:--- |:--- |:--- |:--- |
| **PlanBench-XL (Vendored)** | `external/PlanBench-XL` (Git Submodule) | **Verified** (Local) | Contains `tasks.json`, `database.json`, `scripts/run_retail_batch.py`. |
| **Paper Data** | ` | **Verified** (ArXiv) | Source of the benchmark logic and reported metrics. |

*Note: No external public dataset URL is required as the benchmark data is vendored via the git submodule as per the spec's assumption of "Data Integrity".*

## 3. Dataset Strategy

The project relies entirely on the **vendored PlanBench-XL submodule**.
- **Fit for Purpose**: The vendored data contains the `tasks.json` (queries) and `database.json` (tool definitions) required by `run_retail_batch.py`.
- **Variable Check**: The tasks require tool retrieval and execution logic. The dataset provides the necessary `tool_descriptions` and `task_goals`.
- **Subset Strategy**: To meet the 6-hour CI limit, the plan restricts execution to **5 tasks** per configuration (Default, Blocker, Noise). This is a sampling strategy, not a full re-run of the comprehensive task benchmark. The same 5 tasks are used across all conditions to control for task difficulty variance.

## 4. Model Strategy

The spec references `gpt-5.4`, `gpt-5.4-mini`, `llama3.3-70b`, and `qwen3-14b`.
- **Selected Models**:
 1. `gpt-5.4-mini`: Primary target for baseline (assumed available via OpenAI API).
- **Excluded Models**:
 - `llama3.3-70b` (Local/CUDA): **Excluded** due to GPU requirement and RAM constraints (>40GB).
 - `qwen3-14b` (Local): **Excluded** due to RAM constraints and lack of CPU-optimized inference in the default script.
- **Rationale**: The spec (SC-004) explicitly requires rejecting GPU models. The plan focuses on API-accessible models that fit the CPU-only runner environment. If `gpt-5.4-mini` is unavailable, the script will log a **HARD FAILURE** for that model (FR-006) and skip it, rather than silently passing.

## 5. Statistical & Methodological Rigor

- **Sample Size**: The 5-task subset is insufficient for statistical significance. The goal is **functional validation** (does the code run? do the conditions work?) rather than precise metric replication.
- **Comparisons**:
 - **Blocker vs. Default**: We expect `Accuracy_Blocker < Accuracy_Default`. With n=5, this is a **heuristic verification of mechanism**, not a hypothesis test.
 - **Noise vs. Default**: Similar heuristic check.
- **Stochastic Mitigation**:
 - **Temperature**: All runs MUST use `temperature=0.0` to minimize non-determinism.
 - **Seeds**: If time permits, 3 runs with different seeds will be performed, but the primary validation relies on the single run with fixed temperature.
- **Limitations**:
 - **Power**: Extremely low. Results are indicative of code correctness, not agent performance.
 - **Non-determinism**: LLM outputs vary. The plan focuses on the *direction* of the effect (performance drop) rather than exact numbers.
 - **API Variability**: Rate limits or API changes may cause transient failures.
 - **Spec Contradiction**: User Story 2 requires "statistically significant performance drop". This is impossible with n=5. The final report will explicitly flag this contradiction and report raw rates with wide confidence intervals instead.

## 6. Compute Feasibility Analysis

- **Runtime**: 5 tasks × 3 conditions × 1 model = 15 tasks.
 - Estimated time per task: Several minutes (API latency + tool execution).
 - Total estimated time: [deferred] (well under 6h limit).
- **Memory**:
 - Python script + JSON logs: < 500MB.
 - No model weights loaded locally (API usage).
 - **Verdict**: Fits comfortably within 7GB RAM.
- **Disk**:
 - Logs: ~10KB per task × 15 tasks = 150KB.
 - **Verdict**: Well under 500MB limit.
- **GPU**: None required.

## 7. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **API Key Missing** | Run fails for specific models. | FR-006: Script logs a **HARD FAILURE** for the model and continues. If all models fail, job exits with error. |
| **API Rate Limits** | Run exceeds 6h limit. | Limit to 5 tasks; implement exponential backoff in script. |
| **Submodule Corruption** | Data missing. | Startup check (Edge Case) exits with error code 1. |
| **Tool Timeout** | Infinite loop. | FR-004: Hard timeout per tool call. |
| **State Persistence** | Learning effects between conditions. | **State Reset Protocol**: Terminate process and delete `results/{run_id}/` between conditions. |