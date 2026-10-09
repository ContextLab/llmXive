# Quickstart: Quantifying Neural Representation Drift During Skill Learning

## Prerequisites
- Python 3.11+
- GitHub Actions free‑tier runner or equivalent local environment (2 CPU, ≤7 GB RAM)

## Installation

```bash
# 1. Clone the repository
git clone <REPO_URL>
cd projects/PROJ-171-quantifying-neural-representation-drift-/code

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

## Data Setup
The pipeline automatically generates a synthetic dataset that contains spike counts, trial success rates, and known drift parameters. This ensures the data exactly fits the requirements of FR-001 and FR-009 without relying on external gated or modality-mismatched datasets.

```bash
# Verify synthetic data generation (optional)
python -m src.validation.synthetic --generate --validate
```

- **Source**: Synthetic generator (`src.validation.synthetic`).
- **Modality**: Spike-sorted electrophysiology + Behavioral logs.

## Running the Full Analysis (MVP)

```bash
python -m src.main --config config/default.yaml
```

What the command does:
1. **Ingest** – generates synthetic data, validates required columns.  
2. **Preprocess** – filters units (≥80 % stability), excludes performance‑modulated neurons, interpolates missing behavioral logs.  
3. **Drift** – computes RDMs, fits **both** the linear drift model (`b_lin`) for FR-005 and the exponential drift model (`b_exp`) for Constitution VII.  
4. **Correlation** – Pearson correlation, 10 k permutation test, LMM (`learning_speed ~ b_exp + (1|subject)`).  
5. **Validation** – threshold sweep (0.70‑0.90), metric comparison, split‑half reliability.  
6. **Outputs** – CSV/JSON results in `data/results/`, figures in `docs/paper/`.

### Configuration Flags
- `config.primary_model` (default `"exponential"`): determines which drift metric is used as the primary predictor for the correlation analysis. Set to `"linear"` to prioritize the FR-005 metric.  
- `config.stability_thresholds` (list): thresholds to sweep; default `[0.70,0.75,0.80,0.85,0.90]`.

## Synthetic Ground‑Truth Validation (SC‑001)

```bash
python -m src.validation.synthetic --generate --validate
```

- Generates a synthetic dataset with a known drift rate `b_gt`.
- Runs the full pipeline.
- Prints whether recovered `b` is within 5 % of `b_gt`.

## Sensitivity Analysis (FR‑008)

```bash
python -m src.validation.sensitivity --thresholds 0.70 0.75 0.80 0.85 0.90
```

- Sweeps the unit‑stability threshold.
- Saves a plot `fig_sensitivity_thresholds.png` in `docs/paper/`.

## Troubleshooting

- **Missing variable error**: `RuntimeError: Missing variable 'spike_counts'`. This occurs if the synthetic generator is disabled and no valid dataset is provided.  
- **MemoryError**: Reduce the number of subjects via `--subject-list` if necessary.  
- **Convergence warning**: If `DriftResult.convergence_status` is `"failed_fallback"`, one of the fits did not converge. Review the RDM plot for flat distances.  

All steps are fully reproducible; re‑run the same command on a fresh runner to obtain identical results.