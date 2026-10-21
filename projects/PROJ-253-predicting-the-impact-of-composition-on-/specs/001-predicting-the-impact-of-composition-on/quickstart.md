# Quickstart: Predicting Perovskite Band Gaps from Composition

This guide shows how to run the full analysis on a fresh GitHub Actions runner (or locally).

## 1. Clone the repository & install dependencies
```bash
git clone https://github.com/your-org/perovskite-bandgap.git
cd perovskite-bandgap
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions
```

## 2. Set optional environment variables
| Variable | Purpose | Example |
|----------|---------|---------|
| `MP_API_KEY` | Materials Project API key (if you prefer the API over the Zenodo mirror). | `export MP_API_KEY=your_key_here` |
| `PYTHONHASHSEED` | Guarantees deterministic hashing for reproducibility. | `export PYTHONHASHSEED=0` |

If `MP_API_KEY` is **not** set, the pipeline falls back to the open parquet datasets listed in `research.md`.

## 3. Run the end‑to‑end pipeline
```bash
python -m src.pipeline.run_all
```
`run_all` orchestrates the nine phases described in `plan.md`. Progress is logged to `logs/pipeline.log`.

## 4. Inspect results
- Processed features: `data/processed/perovskite_features.csv`
- Trained models: `models/rf_best.pkl`, `models/gb_best.pkl`
- Evaluation summary: `results/summary.json`
- Figures (SHAP summary, performance plots): `figures/`
- Audit log (warnings about missing elements, metallic entries): `logs/pipeline.log`

## 5. Re‑run a single stage (optional)
```bash
# Example: only run the feature‑engineering step
python -m src.pipeline.featurize \
    --input data/raw/dft.parquet \
    --output data/processed/perovskite_features.csv
```
All scripts accept `--seed 42` to enforce the same randomness.

## 6. Verify contracts
```bash
pytest tests/contract/test_processed_dataset.py
```
The test checks that `data/processed/perovskite_features.csv` conforms to `contracts/processed_dataset.schema.yaml`.

---
