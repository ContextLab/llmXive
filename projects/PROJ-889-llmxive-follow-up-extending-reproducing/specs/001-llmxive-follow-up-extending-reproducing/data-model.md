# Data Model: llmXive follow-up: extending "Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based R"

## Overview

This document defines the data structures used throughout the pipeline. All data is stored as CSV files in `data/processed` to ensure interoperability and ease of inspection. Data is validated against YAML schemas defined in `contracts/` using the `jsonschema` library at runtime.

## Entities

### 1. Trajectory (Raw/Ingested)
**Source**: CHERRL log files.
**Description**: Time-series record of a policy's training run.

| Column | Type | Description |
|--------|------|-------------|
| `timestep` | int | Training step index. |
| `seed_id` | str | Random seed identifier (e.g., "seed_01"). |
| `bias_type` | str | Rubric type: "Lexical", "Format", "Tone", "Self-praise". |
| `J_biased` | float | Biased reward score. |
| `J_unbiased` | float | Unbiased reward score. |
| `J_gold` | float | Independent gold reward score. |

### 2. Divergence Signal (Processed)
**Source**: Derived from `Trajectory` via `code/ingestion.py`.
**Description**: Computed features for anomaly detection, including detector labels and sensitivity analysis metadata.

| Column | Type | Description |
|--------|------|-------------|
| `timestep` | int | Training step index. |
| `seed_id` | str | Random seed identifier. |
| `bias_type` | str | Rubric type. |
| `J_biased` | float | Biased reward score (from raw). |
| `J_unbiased` | float | Unbiased reward score (from raw). |
| `J_gold` | float | Gold reward score (from raw). |
| `G_t` | float | Divergence gap: $\|J_{\text{biased}} - J_{\text{unbiased}}\|$. |
| `dG_t` | float | Rate of change: $G(t) - G(t-1)$. |
| `z_score` | float | Rolling z-score of $G(t)$ (window size TBD by sensitivity analysis). |
| `hacked_label` | int | Binary label: 1 if $z\_score > \tau$ or $dG(t)$ threshold exceeded, else 0. |
| `normality_test_p_value` | float | P-value from Kolmogorov-Smirnov test (per rubric type). |
| `detection_method` | str | "z-score" (normal) or "iqr" (non-normal fallback). |
| `window_size` | int | Actual window size used (from sensitivity analysis). |
| `z_threshold` | float | Actual z-score threshold used (from sensitivity analysis). |

**Output File**: `data/processed/trajectories_divergence.csv`  
**Validation**: Validated against `contracts/trajectory_schema.schema.yaml` using `jsonschema`.

### 3. Ground Truth Labels (Processed)
**Source**: Derived from `Trajectory` via `code/ground_truth.py`.
**Description**: Binary labels based on $J_{\text{gold}}$ drops, with independence check results.

| Column | Type | Description |
|--------|------|-------------|
| `timestep` | int | Training step index. |
| `seed_id` | str | Random seed identifier. |
| `bias_type` | str | Rubric type. |
| `gt_hacked` | int | 1 if $J_{\text{gold}}$ drop $\ge 0.1$ sustained for 3+ steps, else 0. |
| `correlation_J_unbiased_J_gold` | float | Pearson $r$ between $J_{\text{unbiased}}$ and $J_{\text{gold}}$ (reported once per seed). |
| `correlation_J_biased_J_gold` | float | Pearson $r$ between $J_{\text{biased}}$ and $J_{\text{gold}}$ (reported once per seed). |
| `independence_check_passed` | int | 1 if both correlations $< 0.8$, else 0. |

**Output File**: `data/processed/trajectories_gt.csv`  
**Note**: This is a separate intermediate artifact from `trajectories_divergence.csv`. The two are merged during the evaluation step (Phase 4).

### 4. Evaluation Results (Aggregated)
**Source**: Merged `trajectories_divergence.csv` + `trajectories_gt.csv`, processed via `code/evaluation.py`.
**Description**: Summary metrics per bias type and overall.

| Column | Type | Description |
|--------|------|-------------|
| `bias_type` | str | Rubric type. |
| `precision` | float | Precision score (TP / (TP + FP)). |
| `recall` | float | Recall score (TP / (TP + FN)). |
| `f1_score` | float | F1-score (harmonic mean of precision and recall). |
| `t_statistic` | float | T-statistic from paired Wilcoxon test (primary) or t-test (secondary). |
| `p_value` | float | P-value from statistical test. |
| `p_value_corrected` | float | FDR-corrected p-value (Benjamini-Hochberg). |
| `effect_size` | float | Cohen's d or rank-biserial correlation (depending on test). |
| `test_method` | str | "Wilcoxon" or "t-test". |
| `threshold_type` | str | "universal" or "rubric-specific". |
| `baseline_method` | str | "random-guess" or "mean-divergence" (baseline being compared to). |

**Output File**: `data/processed/metrics.csv`  
**Validation**: Validated against `contracts/metrics_schema.schema.yaml` using `jsonschema`.

## Data Flow

1.  **Raw** (`data/raw/*.csv`) → **Ingestion** (`code/ingestion.py`) → **Divergence Signal** (`data/processed/trajectories_divergence.csv`).
   - Computes $G(t)$, $dG(t)$, z-scores, and detector labels.
   - Performs sensitivity analysis (grid search) and selects hyperparameters.
   - Validates output against schema.

2.  **Raw** (`data/raw/*.csv`) → **Ground Truth** (`code/ground_truth.py`) → **Ground Truth Labels** (`data/processed/trajectories_gt.csv`).
   - Derives ground-truth labels from $J_{\text{gold}}$ drops.
   - Computes extended independence check (both $J_{\text{unbiased}}$ and $J_{\text{biased}}$ vs $J_{\text{gold}}$).
   - Halts if independence check fails (correlation > 0.8).
   - Validates output against schema.

3.  **Divergence Signal** + **Ground Truth Labels** → **Evaluation** (`code/evaluation.py`) → **Evaluation Results** (`data/processed/metrics.csv`).
   - Merges the two intermediate artifacts.
   - Computes Precision, Recall, F1-score per bias type.
   - Runs Wilcoxon signed-rank test and t-test (sensitivity check).
   - Applies Benjamini-Hochberg correction for multiple comparisons.
   - Evaluates generalization (SC-003): if $\sigma(F1) > 0.15$, triggers rubric-specific tuning via `code/tune_rubric_specific.py`.
   - Validates output against schema.

4. **Optional**: **Rubric-Specific Tuning** (if SC-003 fails) → `code/tune_rubric_specific.py` → **Updated Metrics** (`data/processed/metrics_rubric_specific.csv`).
   - Performs separate grid search per rubric type.
   - Reports metrics with `threshold_type = "rubric-specific"`.

## Schema Validation

All processed CSV files are validated at runtime using `jsonschema`. Schemas are defined in YAML format in `contracts/`:
- `contracts/trajectory_schema.schema.yaml`: Validates `trajectories_divergence.csv`.
- `contracts/metrics_schema.schema.yaml`: Validates `metrics.csv`.

If validation fails, the pipeline halts with a clear error message indicating which rows/columns violate the schema.
