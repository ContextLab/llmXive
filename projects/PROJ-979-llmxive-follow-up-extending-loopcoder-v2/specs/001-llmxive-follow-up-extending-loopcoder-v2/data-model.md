# Data Model: llmXive follow-up: extending "LoopCoder-v2: Only Loop Once for Efficient Test-Time Computation Scali"

## Overview

This document defines the data structures used to store raw inputs, computed metrics, and analysis results. All data is stored in CSV/Parquet formats for efficient I/O and version control.

## Entities

### 1. InputProblem
Represents a single code generation problem from the dataset.
- `problem_id`: Unique identifier (e.g., "humaneval_0").
- `source`: Dataset name (e.g., "HumanEval", "MBPP").
- `prompt`: The natural language prompt.
- `canonical_solution`: The reference code solution.
- `difficulty`: (Optional) Difficulty label if available in the dataset.

### 2. EntropyProxy
Stores the semantic entropy calculation for a specific problem.
- `problem_id`: FK to `InputProblem`.
- `entropy_value`: Scalar float (Shannon entropy).
- `num_clusters`: Number of semantic clusters found.
- `num_samples`: Total samples generated (should be 10).
- `exclusion_reason`: String if sample was excluded (e.g., "zero_entropy", "underpowered").
- `execution_failed_count`: Integer count of samples that failed execution (for debugging).

### 3. ConvergenceTrajectory
Stores the iterative refinement results.
- `problem_id`: FK to `InputProblem`.
- `loop_count`: Integer ($k \in \{1, 2, 3\}$).
- `is_correct`: Boolean (True if output matches canonical solution).
- `converged_at`: Integer (The first $k$ where `is_correct` is True, or `null` if never).
- `output_hash`: SHA256 hash of the generated output (for reproducibility).

### 4. RouterResult
Stores the output of the dynamic routing simulation.
- `problem_id`: FK to `InputProblem`.
- `predicted_k`: Integer predicted by the logistic regression model.
- `actual_k`: Integer (ground truth convergence step, mapped to 4 if non-convergence).
- `flops_saved`: Integer (FLOPs saved by predicting `predicted_k` vs static baseline).
- `accuracy_delta`: Float (Change in accuracy vs baseline).
- `is_underpowered`: Boolean (True if the stratum size was < 50).

## File Layout

```text
data/
├── raw/
│   ├── humaneval.parquet       # Raw HumanEval dataset
│   └── mbpp.parquet            # Raw MBPP dataset
├── processed/
│   ├── entropy_results.csv     # Aggregated entropy per problem
│   ├── convergence_results.csv # Aggregated convergence per problem
│   └── router_simulation.csv   # Router predictions and metrics
└── checksums.txt               # SHA256 checksums for all files
```

## Data Flow

1. **Ingestion**: Raw datasets are downloaded and stored in `data/raw/`.
2. **Entropy Calculation**: `code/src/entropy.py` reads `raw/`, generates samples, and writes `entropy_results.csv`. **Strictly separates** from convergence tracking.
3. **Convergence Tracking**: `code/src/inference.py` reads `raw/`, runs iterative loops, and writes `convergence_results.csv`.
4. **Analysis**: `code/src/analysis.py` joins `entropy_results.csv` and `convergence_results.csv` to compute correlations and train the router, writing `router_simulation.csv`.