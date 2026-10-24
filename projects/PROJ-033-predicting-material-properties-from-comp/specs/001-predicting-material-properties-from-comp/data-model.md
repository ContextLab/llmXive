# Data Model: Predicting Material Properties from Compositional Data with Graph Neural Networks

## Overview

Artifacts flow from raw ingestion to results; all are checksummed/hashed and validated against schemas in `contracts/`. Every test/script execution also leaves a verification log under `outputs/test_logs/`.

## Raw / Processed Dataset (`data/raw/`, `data/processed/materials_processed.csv`)

Validated against `contracts/materials_dataset.schema.yaml`.

| Field | Type | Description |
|---|---|---|
| `material_id` | string | Unique source identifier; duplicate IDs are dropped (first occurrence kept). |
| `formula` | string | Chemical formula, e.g. `"Fe2O3"`. |
| `band_gap` | number, ≥ 0 | Band gap (eV); **0 = metal** and is a **valid, retained** value. |
| `hardness` | number or null, ≥ 0 | Hardness (GPa); **null** when no open source provides this property. When present, provenance must be documented. |
| `crystal_system` | enum | One of `triclinic`, `monoclinic`, `orthorhombic`, `tetragonal`, `trigonal`, `hexagonal`, `cubic`. |

Rows missing any required field (except `hardness` when null) are dropped with a logged warning. Outlier removal uses a **1.5 × IQR filter per target independently**; per‑target drop counts are logged (`outlier_dropped: {band_gap: N1, hardness: N2}`). Materials containing elements absent from the periodic‑table lookup are skipped with a warning. The loader is split into three pure functions (`validate_row()`, `drop_outliers_iqr()`, `load_and_clean()`) to allow isolated unit testing.

**Metals (`band_gap == 0`) are retained** – a bug in the prior implementation is corrected and pinned by unit tests.

## Composition Graph (in‑memory; cached under `data/processed/graphs/`)

Built by `src/graphs/composition.py` as a PyG `Data` object:

- `x` – shape `[n_elements, 5]` (**element fraction**, atomic number, electronegativity, valence electrons, atomic radius).  
- `edge_index` – fully‑connected clique including self‑loops.  
- `edge_weight` – Euclidean distance in the 4‑D periodic‑property space (deterministic function of node features).  
- `y` – tensor `[2]` containing `[band_gap, hardness]` (hardness may be `null`).

## Structure‑Aware Graph (optional, for the structure‑aware baseline)

When the Matbench Expt Gap dataset is used, each material includes a `structure` object (CIF). `src/graphs/structure.py` builds a PyG `Data` object with atom nodes, 3‑D coordinates, and coordination edges. Missing structures are skipped with a warning; the pipeline continues without failure.

## Model Checkpoint (`outputs/gnn_checkpoint_<hash>.pt` and `outputs/structure_gnn_checkpoint_<hash>.pt`)

Contains the state dict plus metadata (hyperparameters, seed, fold index, dataset checksum). One checkpoint per CV fold; used by the inference script.

## Metrics JSON (`data/results_composition_only.json`)

Conforms to `contracts/model_metrics.schema.yaml`. Includes per‑target (`band_gap`, `hardness`) mean ± std for R², MAE, RMSE; a `rf_baseline` block with the same structure; and a required **`delta_vs_rf`** block (GNN − RF baseline gap). **Hardness metrics may be `null`** when the input column is null. No ΔR² against a structure‑aware model is present here; that comparison is stored in `data/comparison_summary.csv`.

## Per‑System Metrics (`data/metrics_by_system.csv`)

Columns: `crystal_system`, `target`, `r2_mean`, `r2_std`, `mae_mean`, `mae_std`, `rmse_mean`, `rmse_std`.

## Predictions (`data/predictions.json`)

Output of `src/inference/predict.py` for a new formula:

```json
{
  "formula": "Fe2O3",
  "timestamp": "2026-10-24T12:34:56Z",
  "band_gap_pred": "predicted band gap (qualitative estimate)",
  "hardness_pred": null,
  "band_gap_band_disagreement": "1.23 ± 0.45",
  "hardness_band_disagreement": null
}
```

The “band_disagreement” fields are the **fold‑disagreement band** (mean ± 1.96 × std across the 5 folds), not a calibrated prediction interval.

## Embeddings (`outputs/node_embeddings.npy`)

NumPy array `[n_elements, hidden_dim]` of the final node embeddings from the trained GNN.

## Interpretability Report (`interpretability_report.md`)

Table listing principal component, external property (thermal conductivity, sound velocity, first ionization energy), Pearson *r*, two‑tailed *p*, Bonferroni‑adjusted significance flag. If no significant relationship is found, a banner “Low Interpretability” is shown.

## Verification Logs (`outputs/test_logs/`)

One JUnit XML + tee‑ed log per promised run (e.g., `phase0_contract.xml`, `loader.log`, `full_suite.xml`). These constitute the **evidence artifacts** for verification: a run without its log is considered not executed. Script logs record exit codes; any non‑zero exit fails the associated task.

## Conditional Artifacts (pending spec kickback)

If an open CIF source is later verified, the pipeline will additionally emit:

- `results_structure_aware.json` (same schema as composition results; hardness may be null).  
- `comparison_summary.csv` (ΔR², ΔMAE, ΔRMSE per target on the shared subset).

These are **not** produced under the current scope.

## Provenance

Every derived file records input checksums; hashes are stored in `state/projects/PROJ-033-predicting-material-properties-from-comp.yaml`.  

---


