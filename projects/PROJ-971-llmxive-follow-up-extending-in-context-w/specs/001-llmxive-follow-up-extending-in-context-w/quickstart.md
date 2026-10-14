# Quickstart: Running the Auto‑ICWM Latent‑Dynamics Pipeline

**Feature**: `001-auto-icwm-latent-dynamics`  
**Prerequisites**: GitHub Actions runner (Linux, 2 CPU cores, ≈ 7 GB RAM) or a local machine with the same specs.

## 1. Setup Environment
```bash
# From the repository root
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins versions as listed in plan.md
```

## 2. Run the Full Pipeline
A single entry‑point executes all phases in the correct order.

```bash
python -m src.pipeline.run_all \
    --seed 42 \
    --num_train_clips 500 \
    --num_test_clips 200 \
    --output_dir data/
```

### What the script does
| Step | Action | Output (under `data/`) |
|------|--------|------------------------|
| 1️⃣ | `generate_clips.py` – creates raw simulation episodes | `raw/*.npz` |
| 2️⃣ | `extract_descriptors.py` – computes variance, autocorr, spectral density | `processed/descriptors.csv` |
| 3️⃣ | `grid_search_labels.py` – exhaustive τ/k search on training clips | `processed/labels.csv` |
| 4️⃣ | `train_regressor.py` – fits MLP (or linear) model | `model/regressor.pt` |
| 5️⃣ | `validate_autocwm.py` – zero‑shot evaluation on test clips | `results/validation_results.csv` |
| 6️⃣ | `resource_monitor.py` – logs runtime & RAM usage | `logs/resource_usage.json` |

## 3. Inspect Results
```bash
# Descriptors
head data/processed/descriptors.csv

# Labels
head data/processed/labels.csv

# Validation summary (includes p‑values, correlation, controlled analysis)
cat results/validation_results.csv
```

Key columns in `validation_results.csv`:
- `auto_success_rate`
- `baseline_success_rate`
- `p_value_mcnemar`
- `p_value_wilcoxon`
- `variance_complexity_corr`

## 4. Run Tests (contract validation)
```bash
pytest -q tests/contract
```
All tests must pass before committing.

## 5. Resource Check (optional)
```bash
python -c "import json; print(json.dumps(json.load(open('logs/resource_usage.json')), indent=2))"
```
Ensure `total_runtime_seconds` ≤ 21600 (6 h) and `max_ram_gb` ≤ 7.

---



