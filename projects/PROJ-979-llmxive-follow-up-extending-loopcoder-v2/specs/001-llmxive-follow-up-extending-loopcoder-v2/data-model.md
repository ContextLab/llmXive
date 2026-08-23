# Data Model: llmXive follow-up

## Overview

This document defines the schema for all data artifacts produced and consumed by the project. All data is stored in `data/` with strict checksumming.

## Entity Definitions

### 1. InputProblem
Represents a code generation or reasoning problem from HumanEval/MBPP, containing the prompt and the reference solution.
- **Source**: HumanEval / MBPP raw parquet.
- **Fields**:
  - `problem_id`: Unique identifier for the problem.
  - `prompt`: String (the input prompt).
  - `canonical_solution`: String (reference solution, for verification).
  - `test_suite`: String (code to execute tests).
  - `difficulty_stratum`: String (pre-defined based on baseline pass@1 rates from literature).

### 2. EntropyProxy
Scalar uncertainty metric derived from $N=10$ samples.
- **Source**: `code/src/entropy.py`.
- **Fields**:
  - `problem_id`: FK to InputProblem.
  - `entropy_value`: Float (Shannon entropy).
  - `num_clusters`: Integer (number of semantic clusters).
  - `exclusion_flag`: Boolean (true if entropy undefined/excluded).

### 3. ConvergenceTrajectory
Step-by-step convergence data.
- **Source**: `code/src/inference.py`.
- **Fields**:
  - `problem_id`: FK to InputProblem.
  - `loop_count`: Integer ($k \in \{1, 2, 3\}$).
  - `passed`: Boolean (did the output pass tests?).
  - `is_censored`: Boolean (true if $k_{max}$ reached).
  - `convergence_step`: Integer (first $k$ where `passed` is true, else null).

### 4. RouterPrediction
Output of the logistic regression model.
- **Source**: `code/src/analysis.py`.
- **Fields**:
  - `problem_id`: FK to InputProblem.
  - `predicted_k`: Integer (predicted optimal loop count).
  - `probability_k1`: Float (probability of converging at $k=1$).
  - `flops_savings`: Float (relative to static $k=2$).

### 5. StatisticalResults
Aggregated analysis results.
- **Source**: `code/src/analysis.py` / `robustness.py`.
- **Fields**:
  - `metric_name`: String (e.g., 'spearman_rho', 'p_value', 'holm_adjusted_p').
  - `value`: Float.
  - `stratum`: String (if applicable).
  - `confidence_interval`: List(Float, Float).

## File Paths & Checksums

| File | Path | Format | Checksum Method |
| :--- | :--- | :--- | :--- |
| Raw HumanEval | `data/raw/humaneval.parquet` | Parquet | SHA-256 |
| Raw MBPP | `data/raw/mbpp.parquet` | Parquet | SHA-256 |
| Entropy Data | `data/processed/entropy_proxies.csv` | CSV | SHA-256 |
| Convergence Data | `data/processed/convergence_results_core.csv` | CSV | SHA-256 |
| Router Model | `data/processed/router_model.pkl` | Pickle | SHA-256 |
| Final Results | `data/processed/correlation_results_final.json` | JSON | SHA-256 |

## Data Flow

1. **Ingestion**: `data_loader.py` fetches raw parquet, validates checksums, writes to `data/raw/`.
2. **Entropy**: `entropy.py` reads raw, generates `entropy_proxies.csv`.
3. **Inference**: `inference.py` reads raw + entropy, runs loops, writes `convergence_results_core.csv`.
4. **Analysis**: `analysis.py` reads both, produces `correlation_results_final.json` and `router_model.pkl`.
5. **Robustness**: `robustness.py` reads results, produces `adjusted_pvalues.json`.
