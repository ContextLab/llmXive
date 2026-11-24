# Quickstart: Predicting Glass Transition Temperature from Compositional Descriptors with Explainable Boosting Machines

This guide shows how to run the full analysis on the free GitHub Actions runner (CPU-only). The steps assume you have cloned the repository and are in the project root.

## 1. Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins rdkit, interpret, scikit-learn, datasets, pandas, etc.
```

## 2. Verify Data Integrity
```bash
python -m code.ingest --check
# Computes SHA-256 checksums and prints a summary.
# If any checksum mismatches, the script aborts.
```

## 3. Run the Pipeline (single command)

```bash
python -m code.run_all \
    --seed 42 \
    --max-memory-gb 6 \
    --timeout-hours 5
```

`run_all` orchestrates the following sub-commands (see `code/run_all.py` for the DAG):

| Sub-command | Purpose |
|-------------|---------|
| `code.ingest` | Download open SMILES and physical-properties datasets, verify checksums. |
| `code.descriptors` | Compute compositional descriptors, median-impute, standard-scale, write `feature_matrix.csv`. |
| `code.physical_properties` | Compute FFV & chain stiffness, write `data/physical_properties.csv`. |
| `code.train_ebm` *(conditional)* | If `feature_matrix.csv` contains an `experimental_tg` column, train EBM with 5-fold CV, save model and metadata. |
| `code.interpret` *(conditional)* | Generate PDP & interaction plots (only if a model was trained). |
| `code.validate` *(conditional)* | Correlate top feature importances with **FFV and Chain Stiffness** from `data/physical_properties.csv` (when a model was trained) and run (deferred) sensitivity analysis. |

If the `experimental_tg` column is missing, the pipeline **skips the model-related stages with a clear log message** (graceful skip, not a fatal error) and completes the descriptor and physical-property stages; this behavior is aligned with plan.md and research.md.

## 4. Inspect Results
- **Feature matrix**: `data/processed/feature_matrix.csv`  
- **Physical properties**: `data/physical_properties.csv`  
- **Model** (if trained): `outputs/models/ebm_model.pkl`  
- **Figures** (if generated): `outputs/figures/` (e.g., `pdp_molecular_weight.png`)  
- **Validation report** (if generated): `outputs/reports/validation_report.md`

## 5. Run Contract Tests
```bash
pytest -m contract
```
The test suite validates that `feature_matrix.csv` and `ebm_model.pkl` conform to the schemas in `contracts/`.

## 6. Adding a Real $T_g$ Target (when available)
1. Place a CSV with columns `polymer_id` and `experimental_tg` into `data/raw/`.  
2. Re-run `python -m code.run_all` – the conditional steps will now execute, producing a trained model and the full suite of interpretability and validation outputs.