# Quickstart: llmXive follow-up: extending "Translation as a Bridging Action"

## Prerequisites
- Python 3.10+  
- GitHub Actions‑compatible runner (multiple CPU cores, 7 GB RAM) or a local Linux/macOS machine with similar resources.  
- Sufficient disk space (on the order of gigabytes) for raw and processed data.

## 1. Clone & Set Up Environment
```bash
git clone 
cd PROJ-855-llmxive-follow-up-extending-translation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Verify Configuration
The file `code/config.yaml` contains all thresholds and random seeds. You may edit it, but the default values satisfy the specification.

```bash
cat code/config.yaml
```

## 3. Generate Synthetic Dataset
```bash
python code/generate_data.py --config code/config.yaml
```
- **Outputs**: `data/raw/synthetic_episodes.parquet`, `data/checksums.json`  
- **Checks**: script validates schema (`contracts/dataset.schema.yaml`) and logs any crashes, automatically replacing failed episodes.

## 4. Create Geometry‑Disjoint Train/Test Splits
```bash
python code/split_data.py --input data/raw/synthetic_episodes.parquet \
    --train data/processed/train.parquet \
    --test data/processed/test.parquet
```
- Guarantees no `geometry_id` overlap between splits (SC‑code).

## 5. Train Models (CPU‑only)
```bash
# Main translation‑only Transformer
python code/train_model.py --train data/processed/train.parquet \
    --output data/processed/trained_model.pt

# Geometry‑Only baseline (MLP)
python code/train_baseline.py --train data/processed/train.parquet \
    --output data/processed/geometry_baseline.pt

# Random‑Translation control
python code/train_control.py --train data/processed/train.parquet \
    --output data/processed/random_baseline.pt
```
Each script prints the total parameter count and writes `model_summary.txt`. All training runs on CPU; `torch.cuda.is_available()` must be `False`.

## 6. Evaluate & Perform Statistical Tests
```bash
python code/evaluate.py \
    --model data/processed/trained_model.pt \
    --baseline data/processed/geometry_baseline.pt \
    --control data/processed/random_baseline.pt \
    --test data/processed/test.parquet \
    --output data/processed/metrics_report.json
```
- Generates accuracies, AUC‑ROC, confusion matrix, McNemar p‑values (SC‑003, SC‑004, SC‑006).  
- **Enforces** that the translation‑only model improves accuracy by **≥ 2 %** over both baselines; the script aborts with an error if this condition is not met.

## 7. Sensitivity Analysis (Optional)
```bash
python code/sensitivity.py \
    --model data/processed/trained_model.pt \
    --test data/processed/test.parquet \
    --output data/sweep/variance_report.json
```
Reports variance of accuracy across the prescribed Gaussian‑noise levels (σ ∈ {0.0, 0.001, 0.002, 0.003, 0.004} m).

## 8. Full Reproducibility Check
To confirm the pipeline is fully reproducible, delete all generated artifacts and rerun:

```bash
rm -rf data/raw/* data/processed/*
python code/generate_data.py --config code/config.yaml
python code/split_data.py --input data/raw/synthetic_episodes.parquet \
    --train data/processed/train.parquet \
    --test data/processed/test.parquet
python code/train_model.py --train data/processed/train.parquet \
    --output data/processed/trained_model.pt
python code/evaluate.py \
    --model data/processed/trained_model.pt \
    --baseline data/processed/geometry_baseline.pt \
    --control data/processed/random_baseline.pt \
    --test data/processed/test.parquet \
    --output data/processed/metrics_report.json
```

The newly produced `metrics_report.json` should match the previous one within statistical variance, satisfying Constitution I.

---

