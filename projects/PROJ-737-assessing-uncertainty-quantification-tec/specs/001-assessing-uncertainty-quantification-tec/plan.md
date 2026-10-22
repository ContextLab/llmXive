# Implementation Plan: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

## Overview
This plan operationalizes the functional and non‑functional requirements (FR‑001…FR‑005, NFR‑001…NFR‑003) and the success criteria (SC‑001…SC‑005). Each requirement is mapped to a concrete pipeline phase, and all phases are ordered to respect data dependencies and compute constraints.

## 1. Data Acquisition & Verification
| Phase | Action | FR/SC addressed |
|-------|--------|-----------------|
| 1.1   | Download the three open datasets (Band Gap, Thermal Conductivity, Formation Energy) using HuggingFace `datasets.load_dataset`. | FR‑001, SC‑005 |
| 1.2   | Verify SHA‑256 checksum of each downloaded CSV (or dataset shard) and record in `data/` metadata. | FR‑001, Constitution III |
| 1.3   | If a download fails (rate limit or network error), log the failure and continue with remaining datasets (partial_success). | NFR‑002, SC‑001 |

### Construct Validity Note
Formation Energy is used as a proxy for Elastic Modulus because no open mechanical‑property dataset meeting the RAM constraints is available. This proxy captures thermodynamic stability rather than stiffness; therefore any claim about “mechanical‑property” uncertainty is qualified as exploratory and limited to the proxy’s interpretive scope. No strong causal inference about Elastic Modulus is made.

## 2. Featurization
| Phase | Action | FR/SC addressed |
|-------|--------|-----------------|
| 2.1   | Convert `composition` strings to feature vectors using `matminer`’s `CompositionFeaturizer`. | FR‑003 |
| 2.2   | If `matminer` import fails, fall back to elemental fraction vectors generated with `pymatgen` utilities. | FR‑003, NFR‑002 |
| 2.3   | Enforce a hard cap of **2000 training samples per dataset** (randomly sampled if the raw set exceeds this). | FR‑002, NFR‑001 |
| 2.4   | Perform a stratified split by property range into train/val/test, guaranteeing **≥ 200 test samples** per dataset. | FR‑003, SC‑005 |

## 3. Model Training (Baseline)
| Phase | Action | FR/SC addressed |
|-------|--------|-----------------|
| 3.1   | Train a small XGBoost regressor (max_depth=4, n_estimators=100) for each dataset – serves as baseline for the split‑conformal method. | FR‑002 |
| 3.2   | Train a small MLP (≤ 2 M parameters) with dropout = 0.2 for MC‑Dropout and Deep Ensemble baselines. | FR‑002 |
| 3.3   | For GPR, fit `sklearn.gaussian_process.GaussianProcessRegressor` on the capped training set (max 2000 samples). | FR‑002 |
| 3.4   | Record training time and peak RAM; abort if RAM > 2 GB (log as partial_success). | NFR‑001, NFR‑002 |

## 4. Uncertainty‑Quantification Methods
| Method | Baseline Model | Key Settings (CPU‑only) | FR/SC addressed |
|--------|----------------|--------------------------|-----------------|
| GPR | GPR model | RBF kernel, α=1e‑6 | FR‑002 |
| MC Dropout | MLP | 50 stochastic forward passes (≤ 200 allowed) | FR‑002 |
| Deep Ensemble | 3 independently seeded MLPs (same architecture) | Ensemble size = 3, sequential training | FR‑002 |
| Split‑Conformal | XGBoost | Calibration hold‑out ([deferred] of training), nominal coverage swept 0.80–0.99 (step = 0.01) | FR‑002, SC‑004 |

All methods run on CPU‑only wheels; no GPU or 8‑bit quantization is used.

## 5. Metric Computation
### Calibration Error (CE)
- Compute **Expected Calibration Error (ECE)** as an **aggregate** statistic: predictions are binned (10 equal‑frequency bins); for each bin, absolute difference between nominal coverage and empirical coverage is weighted by bin size and summed. This corrects the earlier per‑sample phrasing.

### Sharpness
- Mean prediction‑interval width `mean(U‑L)` across the test set.

Both metrics are calculated per‑method/dataset pair and stored in `metrics_*.csv` (see contracts/metrics.schema.yaml).

## 6. Statistical Testing
| Phase | Action | FR/SC addressed |
|-------|--------|-----------------|
| 6.1   | For each dataset, construct paired vectors of per‑sample **Calibration Error** and **Sharpness** across the four methods. | FR‑004 |
| 6.2   | Apply **Paired Wilcoxon signed‑rank test** for each method pair (6 pairs) on each metric (2 metrics) → 12 tests per dataset, 36 total. | FR‑004, SC‑003 |
| 6.3   **Multiple‑Comparison Correction**: Use Bonferroni correction across 36 tests (α_adj ≈ 0.0014). | SC‑003 |
| 6.4   **Power Analysis**: Assuming a medium effect size (Cohen’s d ≈ 0.5), paired Wilcoxon with n = 200, α_adj = 0.0014 yields power ≈ 0.30. The study is therefore exploratory; any non‑significant result is reported as such. | SC‑003, methodology‑aa9c58a9 |
| 6.5   Record p‑values and significance flags in `statistical_report.csv`. | SC‑003 |

## 7. Sensitivity Analysis (Split‑Conformal)
Sweep nominal coverage from 0.80 to 0.99 in 0.01 increments, record resulting empirical coverage and CE for each step. Results saved as `sensitivity_conformal.csv`.

## 8. Output Generation & Logging
| Output | Path | Contract |
|--------|------|----------|
| per_sample_errors.csv | `results/per_sample_errors.csv` | contracts/per_sample_errors.schema.yaml |
| metrics_*.csv | `results/metrics_*.csv` | contracts/metrics.schema.yaml |
| statistical_report.csv | `results/statistical_report.csv` | contracts/stats.schema.yaml |
| sensitivity_conformal.csv | `results/sensitivity_conformal.csv` | contracts/metrics.schema.yaml |
| uq_methods.csv | `results/uq_methods.csv` | contracts/uq_method.schema.yaml |
| pipeline_log.csv | `results/pipeline_log.csv` | contracts/pipeline.schema.yaml |

All files are written atomically; partial results are retained if a method fails.

## 9. Resource Monitoring
- Use `psutil` to record peak RAM and wall‑clock time per step; enforce the 2 GB cap.
- Log any step that exceeds the budget as `partial_success` with a warning.

## 10. Reproducibility Guarantees
- Fixed seeds: `np.random.seed(42)`, `torch.manual_seed(42)`, `random.seed(42)`.
- Deterministic data loading (same split seeds).
- All dependencies pinned in `requirements.txt`.
- Entire pipeline executable via `python -m code.main` (full) or `python -m code.main --thin` (quick sanity check).

## 11. Constitution Check
- **I. Reproducibility** – All random seeds fixed; data URLs immutable.
- **III. Data Hygiene** – Checksums recorded, no in‑place mutation.
- **VI. Computational‑Budget Discipline** – RAM ≤ 2 GB, wall‑time ≤ 1 h (estimated).
- **VII. Statistical‑Rigor Standard** – Paired Wilcoxon, Bonferroni correction, power analysis disclosed.

--- End of Plan ---