# Quickstart: Assessing Uncertainty Quantification Techniques

## Running the Full Pipeline

The pipeline can be executed in two modes:

| Mode | Description | When to use |
|------|-------------|-------------|
| **Thin verification** (`--thin`) | Uses the first 500 samples of each dataset; skips the conformal coverage sweep. | Quick CI sanity check (≈ 2 min). |
| **Full analysis** (default) | Processes the full allowed training set (capped at **2000 samples per dataset**) and runs the complete conformal sweep. | Official reproducible run (≤ 1 h). |

```bash
# Install pinned dependencies
pip install -r requirements.txt

# Thin run (verifies that everything works)
python -m code.main --thin

# Full run (produces the final research artifacts)
python -m code.main
```

### What the Pipeline Does
1. **Downloads** the three open datasets (Band Gap, Thermal Conductivity, Formation Energy).  
2. **Featurizes** compositions using `matminer`; falls back to elemental fractions if needed.  
3. **Splits** each dataset into stratified train/val/test sets (test ≥ 200 samples).  
4. **Trains** four UQ models under a **2000‑sample training cap** (FR‑002).  
5. **Generates** prediction intervals, computes **Calibration Error (ECE)** and **Sharpness** per sample.  
6. **Runs** paired Wilcoxon signed‑rank tests with Bonferroni correction; reports effect sizes.  
7. **Sweeps** nominal coverage 0.80–0.99 for the split‑conformal method (SC‑004).  
8. **Writes** all results to CSV files that conform to the schemas in `contracts/`.  

### Expected Outputs
All files are placed under `results/`:

| File | Description | Contract |
|------|-------------|----------|
| `per_sample_errors.csv` | Sample‑level predictions, bounds, and absolute errors. | `contracts/per_sample_errors.schema.yaml` |
| `metrics_*.csv` | Calibration error, sharpness, and coverage error per method/dataset. | `contracts/evaluation_metric.schema.yaml` (implicit) |
| `statistical_report.csv` | Paired Wilcoxon p‑values, significance flags, effect sizes. | `contracts/stats.schema.yaml` |
| `sensitivity_conformal.csv` | Coverage‑sweep results for split‑conformal. | `contracts/evaluation_metric.schema.yaml` |
| `uq_methods.csv` | Registry of each UQ method, hyperparameters, status. | `contracts/uq_method.schema.yaml` (implicit) |
| `pipeline_log.csv` | Execution log with step‑wise status, runtimes, memory usage. | `contracts/pipeline.schema.yaml` |
| `cost_metrics.csv` | Runtime and peak RAM for each method (supports VI). | `contracts/cost_metric.schema.yaml` (implicit) |

### Reproducibility Guarantees
- Random seeds are fixed (`np.random.seed(42)`, `torch.manual_seed(42)`).  
- All data downloads are deterministic (same URL, same checksum).  
- The same `requirements.txt` is used on every runner.

### Construct Validity Reminder
Formation Energy is used as a proxy for Elastic Modulus due to data availability constraints. All statements about mechanical stiffness are qualified accordingly (see `research.md`).

---
