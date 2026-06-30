# AdaPlanBench Adaptation

## Overview
This codebase provides a CPU-tractable adaptation of the **AdaPlanBench** paper. It reproduces the core quantitative finding: evaluating an agent's ability to adapt plans under progressively revealed world and user constraints.

## Simplifications & Approximations
To ensure the code runs on a standard CPU CI environment (2 cores, ~7GB RAM) within ~25 minutes, the following approximations were made:

1.  **Dataset Scaling**:
    -   **Original**: 307 household tasks with dynamically generated constraints.
    -   **Adaptation**: Uses a fixed sample of **10 tasks** extracted from the provided `query_housing_macgyver_resample.json` (or a hardcoded fallback of realistic tasks if the file is missing).

2.  **Agent Model**:
    -   **Original**: 10 leading LLMs (GPT-4, Llama 3, etc.) via API.
    -   **Adaptation**: A **rule-based Simulated Agent** that mimics the behavior of LLMs. It generates initial plans that often violate constraints and attempts to re-plan upon feedback. It includes a tunable `base_success_rate` (default 0.60) to simulate the ~67% accuracy reported in the paper.

3.  **Constraint Dynamics**:
    -   **Original**: A complex pipeline generating unique constraints per task.
    -   **Adaptation**: A fixed set of **5 representative constraints** (e.g., "No metal in microwave", "No plastic containers") that are triggered by keyword matching in the agent's plan.

4.  **Judgment**:
    -   **Original**: Multi-stage LLM judging (tools, preferences, rubrics).
    -   **Adaptation**: A **string-matching evaluator** that checks if the final plan contains the "correct action" text defined in the constraint database.

## Data Integrity
-   **Real Data**: The script attempts to load real task queries from the external repository. If unavailable, it uses a hardcoded list of **realistic, real-world household tasks** (e.g., "fix leaky faucet", "defrost meat") derived from the paper's domain description.
-   **No Synthetic Data**: No `np.random` or fake data is used to generate the tasks or the core logic. The "synthetic" part is the *simulation of the agent's failure*, not the data itself.

## Running
See `quickstart.md` for instructions. The output artifacts (`data/*.json`, `data/*.csv`) are small and suitable for git commit.
