# Quickstart: llmXive Follow-up – Semantic Collapse Threshold

This guide shows how to run the full end‑to‑end pipeline on a fresh GitHub Actions runner (or locally).

## 1. Setup
```bash
# Assume repository is already checked out
git checkout 001-semantic-collapse-threshold
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions
```

## 2. Verify Checksums (Data Hygiene)
```bash
python -m src.utils.logging verify_checksums
# Reads artifact_hashes.yaml and compares SHA‑256 values
```

## 3. Run the Full Pipeline
```bash
# Hydra config `conf/config.yaml` contains all defaults.
# Phase 0 (gate) runs first; aborts if the gate fails.
python -m src.pipeline.run all \
    +seed=42 \
    +sample_size=50000 \
    +distortion_grid.snr_levels="[-12,-9,-6,-3,0,3,6,9,12]" \
    +distortion_grid.rt_levels="[0.2,0.4,0.6,0.8,1.0,1.2]" \
    +use_paid_cluster=true \
    +gpu_shards=4   # split into four parallel GPU nodes
```

The command executes the following sub‑commands in order:
1. `download` – fetches Voices‑in‑the‑Wild‑2M, verifies checksums.  
2. `distort` – generates distorted audio (GPU off‑load to paid cluster, 4 shards).  
3. `asr` – runs the five small ASR models.  
4. `sss` – computes Semantic Similarity Scores (fallback to phoneme edit distance if needed).  
5. `collapse` – identifies deterministic collapse points and universal intensity.  
6. `create_manual_validation` – randomly selects a representative set of stress curves and launches the expert annotation UI (simulated here; in practice this step outputs `data/derived/manual_collapse.parquet`).  
7. `evaluate_collapse_precision` – computes precision/recall of deterministic collapse identification against the manual set (requires ≥ 0.90 for both).  
8. `train_regressor` – fits the hierarchical regression model (predicting **annotated collapse intensity**).  
9. `evaluate` – runs permutation baseline, interaction significance, sensitivity analysis, partial‑correlation, universality checks, and schema validation.

## 4. Inspect Results
```bash
# Stress‑curve preview (first 5 rows)
python - <<'PY'
import pandas as pd
print(pd.read_parquet('data/derived/stress_curves.parquet').head())
PY

# Collapse points summary
python - <<'PY'
import pandas as pd
print(pd.read_parquet('data/derived/collapse_points.parquet').describe())
PY

# Manual validation set (precision/recall)
python - <<'PY'
import pandas as pd
df = pd.read_parquet('data/derived/manual_collapse.parquet')
print(df[['clip_id','expert_label','collapse_intensity']].head())
PY

# Critical interaction vectors
python - <<'PY'
import pandas as pd
print(pd.read_parquet('data/derived/critical_vector.parquet'))
PY
```

## 5. Run Tests
```bash
pytest -v
# Includes contract validation tests in tests/unit/test_contracts.py
```

## 6. Generate Figures (optional)
```bash
python -m src.pipeline.visualize \
    --stress-curves data/derived/stress_curves.parquet \
    --collapse-points data/derived/collapse_points.parquet \
    --critical-vectors data/derived/critical_vector.parquet \
    --output-dir figures/
```

All artifacts are reproducible; re‑run with a different seed or sample size to perform sensitivity analyses (FR‑006).  

---

