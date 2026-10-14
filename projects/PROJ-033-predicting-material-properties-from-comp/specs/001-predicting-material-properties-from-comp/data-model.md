# Data Model: Predicting Material Properties from Compositional Data with Graph Neural Networks

## Overview

Artifacts flow from raw ingestion to results; all are checksummed/hashed and validated against schemas in `contracts/`.

## Raw/Processed Dataset (`data/raw/`, `data/processed/materials_processed.csv`)

Validated against `contracts/materials_dataset.schema.yaml`.

| Field | Type | Description |
|---|---|---|
| `material_id` | string | Unique source identifier; duplicates by ID are dropped (polymorphs with the same formula but different IDs are retained and counted). |
| `formula` | string | Chemical formula, e.g. `"Fe2O3"`. |
| `band_gap` | float, ≥ 0 | Band gap (eV); 0 = metal (retained). |
| `hardness` | float, ≥ 0 | Hardness (GPa). |
| `crystal_system` | enum | One of 7 crystal systems. |

Rows missing any required field are dropped with a logged warning; rows outside 1.5×IQR of either target are dropped with a logged count (spec Assumptions); materials with unknown elements are skipped with a warning. The cleaned data is written to a **new** derived file (`materials_processed.csv`); the raw file is never modified.

## Composition Graph (in-memory; cache under `data/processed/graphs/`)

Built by `src/graphs/composition.py` as PyG `Data` objects held in-memory during training, optionally cached under `data/processed/graphs/`: `x` shape `[n_elements, 5]` (**element fraction**, atomic number, electronegativity, valence electrons, atomic radius; standardized — note the element-fraction feature is a planned deviation from FR-002's 4-feature list, flagged for spec kickback); fully-connected `edge_index` with self-loops; `edge_weight` = Euclidean distance in the 4-D periodic-property space (a deterministic function of the node features — carries no independent information); `y` = [band_gap, hardness].

## Model Checkpoint (`outputs/gnn_checkpoint_<hash>.pt`)

State dict + metadata (hyperparameters, seed, fold index, dataset checksum). One checkpoint per CV fold (used by the inference entry point).

## Metrics JSON (`data/results_composition_only.json`)

Per `contracts/model_metrics.schema.yaml`: per target (`band_gap`, `hardness`), `r2_mean/std`, `mae_mean/std`, `rmse_mean/std`; `rf_baseline` block with the same per-target structure; and a required **`delta_vs_rf`** block (GNN − RF per target per metric) — this block is the **single source of truth** for the RF-baseline gap and is explicitly labeled a baseline gap, NOT a structure information-loss ΔR². Per-fold detail included.

## Per-System Metrics (`data/metrics_by_system.csv`)

Columns: `crystal_system`, `target`, `r2_mean`, `r2_std`, `mae_mean`, `mae_std`, `rmse_mean`, `rmse_std`.

## Predictions (`data/predictions.json`)

Output of `src/inference/predict.py` for a new formula: `formula`, `timestamp` (ISO 8601), `band_gap_pred`, `hardness_pred`, and the **fold-disagreement band** (mean ± 1.96 × std across the 5 fold checkpoints) for each target — labeled a fold-disagreement band, not a calibrated [deferred] prediction interval (spec FR-007 deviation, flagged for kickback).

## Embeddings (`outputs/node_embeddings.npy`)

Array `[n_elements, hidden_dim]` from the final trained model.

## Interpretability Report (`interpretability_report.md`)

Table: principal component, external property (**thermal conductivity, sound velocity, first ionization energy only** — properties not used as input features and not training targets; atomic mass and bulk modulus are excluded as quasi-circular), Pearson r, two-tailed p, Bonferroni-adjusted significance flag; "Low Interpretability" banner when no correlation is significant.

## Conditional artifacts (pending spec kickback)

If a verified open CIF source is restored, the pipeline additionally emits `results_structure_aware.json` and `comparison_summary.csv` (ΔR²/ΔMAE/ΔRMSE per target on the shared subset) per US-2. These are **not** produced under the current scope.

## Provenance

Every derived file records its input checksums; hashes recorded in `state/projects/PROJ-033-predicting-material-properties-from-comp.yaml`.