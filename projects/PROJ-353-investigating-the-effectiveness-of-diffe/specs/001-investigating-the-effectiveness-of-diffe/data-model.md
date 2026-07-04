# Data Model: Investigating Loss Functions on Small-World Graphs

## Overview

This document defines the data structures used to store generated graphs, training trajectories, and analysis results. All data is persisted as JSON/JSONL files in `data/` and validated against the schemas in `contracts/`.

## Entities

### 1. SyntheticGraph

Represents a single Watts-Strogatz graph instance.

-   **id**: `str` (UUID)
-   **rewiring_probability**: `float` ($\beta \in [0.0, 1.0]$)
-   **node_count**: `int` (Fixed at 100)
-   **edge_list**: `list[list[int]]` (Adjacency list)
-   **clustering_coefficient**: `float` (Computed global coefficient)
-   **node_labels**: `list[int]` (Community labels derived from initial ring)
-   **seed**: `int` (Random seed used for generation)

### 2. TrainingRun

Represents one training experiment (one graph, one loss function).

-   **run_id**: `str`
-   **graph_id**: `str` (FK to SyntheticGraph)
-   **loss_type**: `str` ("ce" or "infonce")
- **steps_to_convergence**: `int` (Epochs to reach [deferred] accuracy, or 1000 if censored)
-   **censored**: `bool` (True if max epochs reached without convergence)
-   **final_accuracy**: `float` (Accuracy at end of training)
-   **trajectory**: `list[dict]` (Per-epoch logs: `{"epoch": int, "loss": float, "accuracy": float}`)
-   **hyperparameters**: `dict` (Learning rate, batch size, temperature $\tau$, etc.)

### 3. AnalysisResult

Aggregated statistical outputs.

-   **tobit_ce**: `dict` (`{"coef": float, "p_value": float}`)
-   **tobit_infonce**: `dict` (`{"coef": float, "p_value": float}`)
-   **tobit_interaction_f**: `float`
-   **tobit_interaction_p**: `float`
-   **tobit_interaction_corrected_p**: `float`
-   **cox_hazard_ratio**: `float`
-   **cox_p_value**: `float`
-   **significant**: `bool` (Based on corrected p-value < 0.05)
-   **power_analysis**: `dict` (Post-hoc power calculation)

## File Formats

-   `data/raw/graphs.jsonl`: One line per `SyntheticGraph`.
-   `data/logs/training_runs.jsonl`: One line per `TrainingRun`.
-   `data/analysis/results.json`: Single JSON object for `AnalysisResult`.

## Schema Validation

All files are validated against the JSON schemas in `contracts/` before being used for analysis. This ensures that fields like `rewiring_probability` and `seed` are present in `SyntheticGraph` (satisfying Constitution Principle VII) and that `censored` flags are correctly set in `TrainingRun`.
