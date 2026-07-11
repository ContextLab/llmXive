# Data Model: Co-Evolving Policy Distillation

## Overview

This document defines the data structures used for synthetic generation, agent state tracking, and result aggregation. All data is ephemeral during execution but must be serializable to JSON/CSV for reproducibility and contract testing.

## Key Entities

### 1. TaskDomain
Represents a specific reasoning domain (Logic or Grid).
*   **Type**: `dict` / `JSON`
*   **Fields**:
    *   `domain_id`: `str` (e.g., "logic_01", "grid_01")
    *   `domain_type`: `str` ("propositional_logic" | "grid_navigation")
    *   `difficulty_level`: `int` (1-10)
    *   `rule_set_id`: `str` (Unique identifier for the rule set used)
    *   `ground_truth`: `str` (The solution or valid proof string)

### 2. RuleSet
A collection of logical or behavioral rules derived from a TaskDomain.
*   **Type**: `dict` / `JSON`
*   **Fields**:
    *   `rule_set_id`: `str`
    *   `domain_type`: `str`
    *   `rules`: `list[str]` (List of rule definitions)
    *   `validity_score`: `float` (0.0 - 1.0, based on internal consistency)

### 3. AgentState
Snapshot of an agent's knowledge and performance at a specific generation.
*   **Type**: `dict` / `JSON`
*   **Fields**:
    *   `agent_id`: `str`
    *   `condition`: `str` ("sequential" | "mixed" | "coevolving")
    *   `generation`: `int`
    *   `current_rule_set`: `list[str]`
    *   `fitness_score`: `float`
    *   `rule_evaluations_count`: `int` (Cumulative counter)

### 4. ForgettingMetric
Quantitative measure of performance degradation.
*   **Type**: `dict` / `JSON`
*   **Fields**:
    *   `agent_id`: `str`
    *   `condition`: `str`
    *   `initial_accuracy_task_a`: `float` (Measured on held-out set *immediately after* Pre-training Baseline)
    *   `initial_accuracy_task_b`: `float` (Measured on held-out set *immediately after* Pre-training Baseline, if applicable)
    *   `final_accuracy_task_a`: `float` (Measured on the *same* held-out set at end of experiment)
    *   `final_accuracy_task_b`: `float` (Measured on the *same* held-out set at end of experiment)
    *   `forgetting_rate_a`: `float` (Percentage drop)
    *   `forgetting_rate_b`: `float` (Percentage drop)
    *   `avg_forgetting_rate`: `float`
    *   `generations_to_plateau`: `int` (Convergence control metric)
    *   `final_fitness_plateau`: `float` (Convergence control metric)

## Data Flow

1.  **Generation Phase**: `TaskDomain` and `RuleSet` objects are created by `generators/` and stored in memory.
2.  **Baseline Phase**: Agents train on Task A only. `Initial Accuracy` is measured on held-out set.
3.  **Training Phase**: `AgentState` objects are updated every generation. Rule evaluations are counted and logged.
4.  **Evaluation Phase**: Agents are tested on the *same* held-out data. `ForgettingMetric` objects are calculated.
5.  **Analysis Phase**: `ForgettingMetric` objects are aggregated into a DataFrame for statistical analysis (Mixed-Design ANOVA/LMM).

## Storage Strategy

*   **Raw Logs**: JSONL files (`logs/run_{id}.jsonl`) containing `AgentState` snapshots.
*   **Results**: CSV files (`results/forgetting_metrics.csv`) containing aggregated `ForgettingMetric` data.
*   **Checkpoints**: Optional JSON files for intermediate state (if run is interrupted).
