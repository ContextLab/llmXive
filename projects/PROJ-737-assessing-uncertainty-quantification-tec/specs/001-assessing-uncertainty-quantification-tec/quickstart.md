# Quickstart: Assessing Uncertainty Quantification Techniques

## Running the Pipeline

The pipeline is a single entry‑point script located at `code/pipeline.py`. Two execution modes are provided:

| Mode | Description | When to use |
|------|-------------|-------------|
| **Thin verification** (`--thin`) | Uses only the first **500** samples of each dataset, skips the conformal coverage sweep, and caps training at **2000** samples. Runs in approximately a few minutes. | Quick CI sanity check. |
| **Full analysis** (default) | Processes the full allowed training set (**≤ 2000** samples per dataset) and performs the complete conformal sweep (0.90–0.99). Uses **≥ 500** test samples per dataset to achieve adequate statistical power. Expected runtime ≤ 1 h. | Official reproducible run. |

### Step‑by‑step

```bash
# 1. Create a clean environment and install pinned dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Run a thin verification (optional)
python -m code.pipeline --thin

# 3. Run the full analysis (produces final research artefacts)
python -m code.pipeline
```

### What the Pipeline Does
1. **Downloads** the three open datasets (Band Gap, Thermal Conductivity, Elastic Modulus) and records SHA‑256 checksums.
2. **Featurises** compositions with `matminer`; falls back to elemental fractions via `pymatgen` if needed.
3. **Stratifies** each dataset into train/validation/test sets (test ≥ 500 samples).
4. **Trains** four UQ models under the **2000‑sample training cap** (FR‑002) and respecting ensemble/MC‑Dropout limits.
5. **Generates** prediction intervals for every test sample.
6. **Computes** Calibration Error (ECE) and Sharpness for each method/dataset pair; writes `metrics_raw.csv`.
7. **Runs** paired Wilcoxon signed‑rank tests on per‑sample absolute errors, interval widths, and coverage indicators; writes `statistical_report.csv`.
8. **Sweeps** conformal nominal coverage from **0.90** to **0.99** (step = 0.01) and records results in `sensitivity_report.csv`.
9. **Writes** all required CSV artefacts under `results/`:
   * `per_sample_errors.csv`
   * `metrics_raw.csv`
   * `statistical_report.csv`
   * `sensitivity_report.csv`
   * `uq_methods.csv`
   * `pipeline_log.csv`

### Expected Outputs (located in `results/`)

| File | Description | Contract |
|------|-------------|----------|
| `per_sample_errors.csv` | Sample‑level predictions, bounds, absolute errors, interval width, coverage flag. | `contracts/per_sample_errors.schema.yaml` |
| `metrics_raw.csv` | Calibration Error, Sharpness, Coverage Error per method/dataset. | `contracts/metrics.schema.yaml` |
| `statistical_report.csv` | Paired Wilcoxon p‑values and significance flags for per‑sample metrics. | `contracts/stats.schema.yaml` |
| `sensitivity_report.csv` | Coverage‑sweep results for split‑conformal. | `contracts/metrics.schema.yaml` |
| `uq_methods.csv` | Registry of each UQ method, hyper‑parameters, and status (including deterministic MLP baseline). | `contracts/uq_method.schema.yaml` |
| `pipeline_log.csv` | Execution log with step‑wise runtime, RAM usage, and overall status. | `contracts/pipeline.schema.yaml` |

### Reproducibility Guarantees
* **Fixed seeds** (`np.random.seed(42)`, `torch.manual_seed(42)`, `random.seed(42)`).
* **Deterministic downloads** (same URLs, same SHA‑256 checksums).
* **Pinned dependencies** (`requirements.txt`); identical environment on every runner.

### Construct Validity Reminder
Because an open Elastic Modulus dataset is now sourced from OQMD, all three property domains (electronic, mechanical, thermal) are represented using truly open data.

--- End of Quickstart ---
