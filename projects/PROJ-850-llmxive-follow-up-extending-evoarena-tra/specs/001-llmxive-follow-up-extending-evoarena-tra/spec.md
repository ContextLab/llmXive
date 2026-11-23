# Project Specification: EvoMem-Conflict Filtering for Robust LLM Agents

## Overview
This project implements a conflict-detection heuristic to filter memory patches in LLM agents, reducing context noise and improving execution accuracy on dynamic benchmarks.

## Functional Requirements

### FR-001: Agent Interface
Define a standard interface for agents to retrieve memory patches and execute tasks.

### FR-002: Fallback Retrieval
If conflict detection fails or returns no results, the agent MUST retrieve the latest state plus the 2 most recent non-conflict patches to prevent context starvation.

### FR-005: Statistical Analysis
Perform statistical significance testing on agent performance metrics.
- **Binary Data (Accuracy)**: Use **McNemar's test** (Ratified correction for binary outcomes).
- **Continuous Data (Latency/Tokens)**: Use **Wilcoxon signed-rank test**.
- **Auto-Select**: System must automatically detect data type and select the appropriate test.

### FR-006: Memory Noise Reduction
Track and report the percentage of non-conflict patches filtered out by the heuristic.

### FR-007: Safe Mode Retrieval
On timeout or failure of the conflict detector, default to safe retrieval mode: latest state + 2 most recent non-conflict patches.

### FR-008: Sensitivity Analysis
Execute sensitivity analysis on thresholds [0.5, 0.7, 0.9] and model sizes to ensure robustness.

### FR-009: Power Analysis Methodology
Calculate sample size using **Cohen's h** for binary data comparisons.
- **Parameters**: MDES = 0.2, Power = 0.8, α = 0.05.
- **Ratification**: Methodology changed from "Cohen's d" to "Cohen's h" to align with binary outcome data (Task T003b).
- **Deliverable**: `research.md` updated with calculated sample size.

## Success Criteria

### SC-001: Heuristic Performance
Conflict detector achieves ≥80% precision and recall on synthetic validation pairs.

### SC-002: CPU Tractability
All models used must run on CPU with ≤0.5B parameters and inference time ≤500ms per pair.

### SC-003: Reproducibility
All experiments must be reproducible with deterministic seeds (seed=42).

### SC-004: Statistical Validity
Statistical tests must be correctly applied based on data type (Binary -> McNemar, Continuous -> Wilcoxon).

### SC-005: Execution Constraints
Full experiment must complete within the time limit defined in `config.json` on CPU hardware.

### SC-006: Methodological Consistency
Power analysis must use **Cohen's h** for binary data.
- **Ratified**: "Cohen's d" replaced by "Cohen's h" in FR-009 and SC-006 to ensure methodological correctness for binary data.
- **Note**: This change was ratified in Task T003b.

## Data Model

### Memory Patch
- `patch_id`: string
- `content`: string
- `timestamp`: datetime
- `is_conflict`: boolean (null if not yet evaluated)

### Task Execution Log
- `task_id`: string
- `agent_variant`: string
- `context_tokens`: integer
- `inference_time`: float
- `success_status`: boolean
- `hallucination_flag`: boolean

## User Stories

### US1: Conflict-Detection Heuristic Implementation
Implement a CPU-tractable conflict detector using DistilBERT to flag semantic contradictions in memory patches.

### US2: Dual-Agent Execution Pipeline
Instantiate and run `EvoMem-All` and `EvoMem-Conflict` agents on the task dataset, logging execution metrics.

### US3: Statistical Comparison and Reporting
Analyze execution logs to calculate accuracy, hallucination rates, and statistical significance.

## Constraints

- **Hardware**: All experiments must run on CPU (no GPU dependencies).
- **Data**: Must use real data from `Terminal-Bench-Evo` or verified synthetic fallback.
- **Models**: Max 0.5B parameters, default precision.
- **Dependencies**: `transformers`, `scikit-learn`, `pandas`, `pytest`, `datasets`, `tqdm`, `statsmodels`, `python-Levenshtein`.