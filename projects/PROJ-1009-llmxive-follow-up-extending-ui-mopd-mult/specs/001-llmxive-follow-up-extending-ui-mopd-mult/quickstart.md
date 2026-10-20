# Quickstart: Running the Structural Adapter Pipeline (Simulation Study)

This guide assumes a fresh GitHub Actions runner (or compatible local Linux environment). **Note**: this pipeline validates the analysis methodology on a simulated dataset; it does not answer the real-data research question (see plan.md "Spec Scope Mismatch").

## 1. Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins all versions
```

## 2. Generate the Simulated Dataset (10,000 records per SC-000)
```bash
python -m src.generate.synthetic_dataset \
    --num-records 10000 \
    --seed 42 \
    --output data/raw/structural_records.csv

# Compute and record checksum
python - <<'PY'
import hashlib, pathlib
path = pathlib.Path("data/raw/structural_records.csv")
sha = hashlib.sha256()
with open(path, "rb") as f:
    for chunk in iter(lambda: f.read(8192), b""):
        sha.update(chunk)
print("checksum:", sha.hexdigest())
PY
# Record the printed checksum in `state/projects/...yaml`.
```

## 3. Clean & Extract Structural Features (FR-008)
```bash
python -m src.extract.structural_extractor \
    --input data/raw/structural_records.csv \
    --output data/derived/structural_records.csv \
    --seed 42
```
Flags missing structural data, truncates navigation-graph cycles at depth 10, and marks structural-ambiguity cases.

## 4. Noise Calibration & Null Control
```bash
python -m src.model.train \
    --data data/derived/structural_records.csv \
    --noise-sweep 0.55 0.65 0.75 0.85 \
    --null-control shuffle \
    --seed 42 \
    --output-dir outputs/
```
Reports AUC/Brier per noise level and for the shuffled-label null (anti-circularity design).

## 5. Train the Adapter
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
If memory exceeds 7 GB, the script falls back to a stratified random sample and a linear regression model (`outputs/adapter_linear.pkl`).

## 6. Feature Importance (incl. control feature)
```bash
python -m src.evaluate.feature_importance \
    --model outputs/adapter_gnn.pt \
    --data data/derived/structural_records.csv \
    --output outputs/feature_importance.csv \
    --correction bonferroni
```

## 7. Sensitivity Sweeps
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

## 8. Policy Simulation, Benchmark & Variation Evaluation (FR-009)
```bash
python -m src.evaluate.benchmark \
    --model outputs/adapter_gnn.pt \
    --policy-heads data/artifacts/policy_heads/ \
    --test-split data/derived/test_set.csv \
    --baseline data/baseline/simulated_ui_mopd_metrics.csv \
    --output outputs/benchmark.csv \
    --adapter-output outputs/adapter_output.csv \
    --plots-dir outputs/

# FR-009: synthetic navigation-graph variations
python -m src.evaluate.variations \
    --model outputs/adapter_gnn.pt \
    --test-split data/derived/test_set.csv \
    --variations shuffle_widget_order,alter_resolution \
    --output outputs/variation_degradation.csv
```
The variation script reports prediction-performance degradation relative to the original test set (must be ≤ 5 %, SC-007).

## 9. Contract Validation
```bash
python - <<'PY'
import pandas as pd, yaml, jsonschema
schema = yaml.safe_load(open("contracts/structural_record.schema.yaml"))
df = pd.read_csv("data/derived/structural_records.csv")
for _, row in df.iterrows():
    jsonschema.validate(instance=row.to_dict(), schema=schema)
print("StructuralRecord rows valid.")
PY
```

## 10. Reproducibility Manifest
All steps log their git commit, seed, and artifact hashes to `state/projects/PROJ-1009-...yaml`. Commit the updated manifest to the repo.