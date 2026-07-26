# Data Model: llmXive follow-up

## Overview

This document defines the data structures for the `llmXive follow-up` project. All data flows through a pipeline of ingestion, transformation, and evaluation. The model is designed to be immutable: raw data is never modified, and derived data is written to new files with checksums.

## Entities

### 1. Trajectory (Raw)
**Source**: CHERRL logs (CSV/Parquet).
**Description**: Time-series record of a policy's training run.
**Fields**:
- `seed_id`: Unique identifier for the random seed (string).
- `bias_type`: Category of bias (Lexical, Format, Tone, Self-praise) (string).
- `timestep`: Integer index of the training step.
- `J_biased`: Float, biased reward score.
- `J_unbiased`: Float, unbiased reward score.
- `J_gold`: Float, gold reward score.

### 2. Divergence Signal (Derived)
**Source**: Computed from Trajectory.
**Description**: Time-series of divergence metrics.
**Fields**:
- `seed_id`: (string)
- `bias_type`: (string)
- `timestep`: (integer)
- `G_t`: Float, $|J_{\text{biased}} - J_{\text{unbiased}}|$.
- `dG_t`: Float, $G(t) - G(t-1)$.
- `z_G_t`: Float, Rolling z-score of $G(t)$ (window=20).
- `hacked_label`: Boolean, `True` if $z(G(t)) > 3.0$ OR $\Delta G(t) > \text{threshold}$.

### 3. Ground Truth (Derived)
**Source**: Computed from Trajectory (J_gold).
**Description**: Binary labels for actual hacking events.
**Fields**:
- `seed_id`: (string)
- `bias_type`: (string)
- `timestep`: (integer)
- `is_hacked`: Boolean, `True` if $J_{\text{gold}}$ drop $\ge 0.1$ sustained for $\ge 3$ steps.
- `independence_check`: Boolean, `True` if $r(J_{\text{unbiased}}, J_{\text{gold}}) \le 0.8$.

### 4. Evaluation Metrics (Derived)
**Source**: Computed from Divergence Signal and Ground Truth.
**Description**: Aggregated performance metrics.
**Fields**:
- `bias_type`: (string)
- `precision`: Float.
- `recall`: Float.
- `f1_score`: Float.
- `wilcoxon_p_value`: Float.
- `wilcoxon_z_statistic`: Float.
- `baseline_f1`: Float.
- `sensitivity_threshold`: Float (0.05, 0.1, 0.15).
- `effect_size`: Float (rank-biserial correlation).

## Data Flow

1.  **Ingest**: `download_cherrl_logs.py` -> `data/raw/` (Parquet).
2.  **Compute**: `compute_divergence.py` -> `data/processed/divergence_signals.parquet`.
3.  **Label**: `detect_hacking.py` + `evaluate.py` -> `data/processed/ground_truth_labels.parquet`.
4.  **Evaluate**: `evaluate.py` -> `data/processed/evaluation_report.json`.
5.  **Runtime**: `benchmark_runtime.py` -> `data/processed/runtime_metrics.json`.

## Constraints

- **Immutability**: Raw files in `data/raw/` are never modified.
- **Checksums**: Every file in `data/` must have a corresponding SHA-256 hash in `state/...yaml`.
- **Independence**: If `independence_check` is `False`, the pipeline must halt.
- **Types**: All floats are 64-bit; all integers are 32-bit.