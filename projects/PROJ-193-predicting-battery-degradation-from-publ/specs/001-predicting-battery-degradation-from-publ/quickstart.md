# Quickstart: Battery Degradation Prediction Pipeline

**Status**: All code is runnable; **result generation is blocked** until a verified open NASA Ames Battery Dataset download URL is reachable (see `plan.md` / `research.md`). No synthetic data are used anywhere (FR‑ref).

## Prerequisites

```bash
git clone <repo-url> && cd <repo>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Step 1 – Data Ingestion (requires verified data source)

```bash
python -m src.data.ingest \
    --source https://data.nasa.gov/dataset/battery-cycling-data \
    --output data/raw/ \
    --log-level INFO
```

- Retries up to 3 × 60 s on failure.  
- Checksums each CSV; logs completeness ratio (SC‑005).  
- Fails with a clear error if the endpoint is unavailable (FR‑012).

## Step 2 – Preprocessing

```bash
python -m src.data.preprocess \
    --input data/raw/ \
    --output data/processed/processed_v1.npz \
    --seed 42
```

- Resamples each cycle to **100 uniform time‑steps**.  
- Normalizes **per cell** using statistics from **cycles 1‑50** only (FR‑010).  
- Builds tensors of shape `(N_cells, 50, 100, 3)`.  
- Computes `target_fade` using **cycle 150** (or first > 100) per the revised definition.  
- Creates train/val split and held‑out protocol test split (FR‑011).

## Step 3 – Model Training (plain Bi‑LSTM + attention)

```bash
python -m src.model.train \
    --data data/processed/processed_v1.npz \
    --output models/bilstm_v1.pt \
    --max-runtime 1800   # 30 min wall‑clock limit
```

- CPU‑only (`device="cpu"`).  
- Adam optimizer, early stopping on validation loss.  
- 2‑layer Bi‑LSTM, 64 units per layer, **attention head** (FR‑003, FR‑008).  
- Lightweight hyper‑parameter sweep; defaults used if sweep exceeds 30 min.

## Step 4 – Baseline (incremental‑capacity)

```bash
python -m src.model.baseline \
    --data data/processed/processed_v1.npz \
    --output models/baseline_v1.pkl
```

- Features derived **only from cycles 1‑50** (FR‑010).  

## Step 5 – Evaluation & Uncertainty

```bash
python -m src.model.evaluate \
    --model models/bilstm_v1.pt \
    --data data/processed/processed_v1.npz \
    --output results/predictions.json
```

- Reports R², RMSE on full test set and unseen‑protocol subset (SC‑004).  
- Monte‑Carlo dropout (10 passes) + **split‑conformal calibration** → [deferred] prediction‑interval coverage (SC‑006).  
- Power analysis for ΔR² = 0.05 (FR‑014).  

## Step 6 – Interpretability

```bash
# SHAP summary plot
python -m src.interpret.shap_analysis \
    --model models/bilstm_v1.pt \
    --data data/processed/processed_v1.npz \
    --output figures/shap_summary.png

# Permutation importance table
python -m src.interpret.permutation_importance \
    --model models/bilstm_v1.pt \
    --data data/processed/processed_v1.npz \
    --output results/permutation_importance.csv

# Integrated Gradients attribution
python -m src.interpret.integrated_gradients \
    --model models/bilstm_v1.pt \
    --data data/processed/processed_v1.npz \
    --output results/ig_attribution.npy

# Attention‑weight attribution
python -m src.interpret.attention_attribution \
    --model models/bilstm_v1.pt \
    --data data/processed/processed_v1.npz \
    --output results/attention_weights.npy

# Aggregate raw attributions & derive early‑cycle signatures
python -m src.interpret.feature_aggregation \
    --shap results/shap_summary.npy \
    --perm results/permutation_importance.csv \
    --ig results/ig_attribution.npy \
    --attention results/attention_weights.npy \
    --output results/aggregated_feature_importance.json

# Map signatures to literature (SC‑010)
python -m src.interpret.literature_mapping \
    --aggregated results/aggregated_feature_importance.json \
    --output results/literature_match_report.txt
```

- `feature_aggregation.py` collapses raw time‑step/channel scores to per‑cycle/channel importance and computes derived signatures (voltage variance, current slope, temperature fluctuation).  
- `literature_mapping.py` checks that at least three of the top‑ranked signatures match known early‑cycle degradation markers (SC‑010).

## Step 7 – Contract Validation (runs on fixtures)

```bash
pytest -q tests/contract/
```

- Validates `processed_dataset.schema.yaml` and `model_output.schema.yaml` against generated artefacts.

## Notes
- All steps are deterministic (seed = 42).  
- Runtime, memory, and disk usage are logged for SC‑002.  
- Until the NASA Ames dataset source is confirmed reachable, Steps 1 – 6 will exit with a descriptive error rather than fabricating data.

---



