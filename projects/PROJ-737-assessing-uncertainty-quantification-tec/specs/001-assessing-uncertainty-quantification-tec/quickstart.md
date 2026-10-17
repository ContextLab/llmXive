# Quickstart: Assessing Uncertainty Quantification Techniques

## Command

```bash
python -m code.main --thin
```

## What this runs

- **Four UQ methods** are evaluated:
  1. **Gaussian Process Regression (GPR)**
  2. **Monte‑Carlo Dropout (MC‑Dropout)**
  3. **Deep Ensemble**
  4. **Split‑Conformal prediction**

- **Training sample cap** – each method is trained on at most **2000 samples** per dataset (the pipeline enforces this cap automatically).

- **Deterministic sampling rule** – the pipeline selects the first *N* rows of each raw dataset using a fixed random seed (`seed=42`). This guarantees reproducible “first‑N rows” subsampling across runs.

- **Statistical comparison** – after predictions are generated, a **paired Wilcoxon signed‑rank test** is performed on the per‑sample error vectors of each method pair. This test respects the paired nature of the predictions (same test set) and provides a rigorous significance assessment.

- **Proxy property note** – the **Formation Energy** dataset is used as a proxy for **Elastic Modulus** (the original Elastic Modulus dataset is not publicly available). All conclusions about mechanical stiffness are qualified accordingly.

## Expected outputs

Running the command creates the following artefacts (all under the project root):

- `data/raw/` – downloaded CSVs (checked‑summed).
- `data/processed/` – featurized train/val/test splits.
- `data/results/per_sample_errors.csv` – per‑sample predictions adhering to the schema defined in `specs/001-assessing-uncertainty-quantification-tec/contracts/per_sample_errors.schema.yaml`.
- `data/results/pipeline_run.json` – execution log conforming to the pipeline schema.
- Additional CSV/PNG artefacts produced by later tasks (metrics, statistical reports, figures, etc.).

The thin run operates on a **100‑sample** subset of each dataset (overridden by `--thin`) but still respects the 2000‑sample cap and the deterministic sampling rule.

## Re‑run

To execute the full pipeline (all datasets, full caps) use the command from the main quickstart guide:

```bash
python code/main.py \
    --max-samples 2000 \
    --mc-dropout-passes 50 \
    --ensemble-size 3 \
    --coverage-sweep-start 0.80 \
    --coverage-sweep-stop 0.99 \
    --coverage-sweep-step 0.01 \
    --seed 42
```
