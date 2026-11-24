# Quickstart: Running the Structural Adapter Pipeline (Simulation‑Ready)

> **IMPORTANT** – The pipeline as described below requires **either** (a) an open Uni‑GUI‑style dataset **or** (b) permission to use the synthetic dataset generator. If the specification has not been amended to allow simulation, stop after step 1 and await the spec update.

## 1. Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins all versions
```

## 2. Generate a Synthetic Dataset (Approved Simulation Scope)
*Only run if the spec has been amended to permit simulation.*
```bash
python -m src.generate.synthetic_dataset \
    --num-records <large‑scale dataset> \
    --seed 42 \
    --output data/raw/structural_records.csv
```
The generator creates a realistic latent‑variable label (`task_success`) that is **not** a deterministic function of the three topology features (see Anti‑circularity Design). It also adds a `latent_factor` column (used only for generation) and a `control_feature` column for sanity‑checking importance methods. The script prints the SHA‑256 checksum (record it in `state/projects/...yaml`).

## 3. Extract & Clean Structural Features (FR‑001 & FR‑008)
```bash
python -m src.extract.structural_extractor \
    --input data/raw/structural_records.csv \
    --output data/derived/structural_records.csv \
    --max-graph-depth 10 \
    --seed 42
```
- Flags records with missing fields.  
- Truncates navigation‑graph cycles at depth 10.  
- Emits `structural_ambiguity` flags.

## 4. Train the Lightweight Adapter (FR‑002)
```bash
python -m src.model.train \
    --data data/derived/structural_records.csv \
    --model gnn \
    --epochs 30 \
    --batch-size 128 \
    --seed 42 \
    --fallback-sample-size 4000 \
    --output outputs/adapter_gnn.pt
```
If memory usage exceeds 7 GB, the script automatically falls back to the stratified 4 000‑record sample and trains a linear regression model (`outputs/adapter_linear.pkl`). **The training routine enforces** AUC‑ROC ≥ 0.80 and Brier ≤ 0.20; if either metric is not met, the script exits with a non‑zero status and logs the failure.

## 5. Feature Importance (FR‑003, FR‑007)
```bash
python -m src.evaluate.feature_importance \
    --model outputs/adapter_gnn.pt \
    --data data/derived/structural_records.csv \
    --output outputs/feature_importance.csv \
    --correction bonferroni
```
The CSV contains SHAP values, permutation importance, and Bonferroni‑adjusted p‑values for the three topology features, the `control_feature`, and (if present) the `latent_factor` (which should be non‑predictive).

## 6. Sensitivity Sweeps (FR‑006)
```bash
python -m src.evaluate.sensitivity \
    --model outputs/adapter_gnn.pt \
    --data data/derived/structural_records.csv \
    --parameter widget_depth --values 3 4 5 \
    --output outputs/sensitivity_depth.png

python -m src.evaluate.sensitivity \
    --model outputs/adapter_gnn.pt \
    --data data/derived/structural_records.csv \
    --parameter branching_factor --values 1.0 1.5 2.0 \
    --output outputs/sensitivity_branching.png

python -m src.evaluate.sensitivity \
    --model outputs/adapter_gnn.pt \
    --data data/derived/structural_records.csv \
    --parameter graph_connectivity --values 0.3 0.5 0.7 \
    --output outputs/sensitivity_connectivity.png
```
Each figure reports the variance of overall success rate across the sweep (must be ≤ 0.02, SC‑006).

## 7. Platform‑Masking Control (Isolate Structural Effect)
```bash
python -m src.model.train \
    --data data/derived/structural_records.csv \
    --model gnn \
    --epochs 30 \
    --batch-size 128 \
    --seed 42 \
    --mask-platform \
    --output outputs/adapter_gnn_platform_masked.pt
```
`--mask-platform` randomises `platform_id` at each epoch, preventing the model from exploiting platform cues. Run the same evaluation pipeline (steps 5‑6) on this masked model to compare feature importance and performance.

## 8. Policy‑Head Simulation & Benchmark (FR‑004, FR‑005)
*Run only after the spec authorizes simulated policy heads.*
```bash
python -m src.evaluate.benchmark \
    --model outputs/adapter_gnn.pt \
    --policy-heads data/artifacts/policy_heads/ \
    --test-split data/derived/test_set.csv \
    --baseline data/baseline/simulated_ui_mopd_metrics.csv \
    --output outputs/benchmark.csv \
    --adapter-output outputs/adapter_output.csv \
    --plots-dir outputs/
```
The script logs per‑step inference latency, peak memory, and task‑success rates; it also runs McNemar’s test (SC‑005) and checks that latency ≤ 1/5th of baseline (SC‑002) and success‑rate tolerance ≤ 5 % (SC‑003).

## 9. Synthetic‑Variation Evaluation (FR‑009)
```bash
python -m src.evaluate.variations \
    --model outputs/adapter_gnn.pt \
    --test-split data/derived/test_set.csv \
    --variations shuffle_widget_order alter_resolution \
    --output outputs/variation_degradation.csv
```
The CSV reports degradation percentages; they must be ≤ 5 % (SC‑007).

## 10. Contract Validation
```bash
python - <<'PY'
import pandas as pd, yaml, jsonschema, sys

def validate(csv_path, schema_path):
    schema = yaml.safe_load(open(schema_path))
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        jsonschema.validate(instance=row.to_dict(), schema=schema)

for name, schema_file in [
    ("StructuralRecord", "contracts/structural_record.schema.yaml"),
    ("PolicyHead", "contracts/policy_head.schema.yaml"),
    ("AdapterModelOutput", "contracts/adapter_output.schema.yaml")
]:
    try:
        validate(f"outputs/{name.lower()}.csv", schema_file)
        print(f"{name} rows valid.")
    except Exception as e:
        print(f"{name} validation error:", e)
        sys.exit(1)
PY
```

## 11. Reproducibility Manifest
All scripts log their git commit hash, random seed, and SHA‑256 checksums of generated files to `state/projects/PROJ-1009-...yaml`. Commit the updated manifest to the repository.
