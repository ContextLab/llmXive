# Data Model: MobileForge Logic Distillation

## 1. Overview
This document defines the data schemas for the MobileForge Logic Distillation project. All data artifacts must conform to these schemas to ensure reproducibility and contract validation.

## 2. Data Flows

1.  **Raw Extraction**: `MobileForge Logs` (GitHub/HF) → `data/raw/triples.parquet`
2.  **Filtering**: `data/raw/triples.parquet` → `data/processed/train_splits.parquet`, `data/processed/test_splits.parquet`
3.  **Training**: `data/processed/train_splits.parquet` → `models/distilled_t5/`
4.  **Evaluation**: `models/distilled_t5/` + `models/tinyllama/` + `data/eval_tasks.json` → `state/evaluation_results.json`
5.  **Power Analysis**: `utils/power_analysis.py` → `state/validated_n.json`

## 3. Schema Definitions

### 3.1 ExtractionDataset (Raw)
Source: MobileForge Logs (GitHub/HF).
- `ui_state`: String (JSON representation of UI hierarchy or screenshot caption)
- `corrective_hint`: String (Linguistic instruction)
- `action`: String (Ground truth action sequence)
- `trajectory_status`: String (e.g., "failed_then_success", "initial_success")

### 3.2 DistilledModel (Artifact)
- `architecture`: String ("T5-small")
- `weights_path`: String (Relative path to `models/distilled_t5/`)
- `config`: JSON (Model hyperparameters, epochs, learning rate)
- `checksum`: String (SHA256 of weights)

### 3.3 EvaluationResult
- `metrics`:
  - `success_rate_distilled`: Float
  - `success_rate_baseline`: Float
  - `step_efficiency_distilled`: Float
  - `step_efficiency_baseline`: Float
- `statistical_test`:
  - `test_type`: String ("McNemar")
  - `p_value`: Float
  - `significant`: Boolean
  - `contingency_table`: List of Lists (2x2)
- `power_analysis`:
  - `n_required`: Integer
  - `power_target`: Float
  - `effect_size`: Float
  - `baseline_rate`: Float
  - `p0_source`: String ("Pilot Run" or "Fallback 0.5")
- `sensitivity_report`:
  - `thresholds`: List of Integers
  - `success_rates`: List of Floats
- `ablation`:
  - `hint_success_rate`: Float
  - `retry_success_rate`: Float

## 4. Data Integrity Rules
- **Raw Data**: Immutable. Checksums stored in `data/checksums.json`.
- **Derived Data**: New files with `_v{version}` suffix if source changes.
- **PII**: No Personally Identifiable Information allowed.
- **Missing Data**: Loaders must fail loudly; no synthetic fallbacks.