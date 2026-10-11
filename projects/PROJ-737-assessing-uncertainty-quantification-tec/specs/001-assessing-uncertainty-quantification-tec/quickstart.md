# Quickstart: Assessing Uncertainty Quantification Techniques

## Prerequisites

- Python 3.11+  
- Git  
- Internet access (for dataset download)  
- ≤ 2 GB RAM (GitHub Actions runner or local machine)

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-737-assessing-uncertainty-quantification-tec
git checkout 001-assessing-uq-techniques

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

```bash
python code/main.py \
    --max-samples 5000 \
    --mc-dropout-passes 50 \
    --ensemble-size 3 \
    --coverage-sweep-start 0.80 \
    --coverage-sweep-stop 0.99 \
    --coverage-sweep-step 0.01
```

### Optional Flags

| Flag | Description |
|------|-------------|
| `--dataset <id>` | Run only on a specific dataset (`band_gap`, `thermal_conductivity`, `formation_energy`). |
| `--method <id>` | Run only a single UQ method (`gpr`, `mc_dropout`, `deep_ensemble`, `conformal`). |
| `--max-samples N` | Upper bound on samples per dataset to respect RAM limits. |
| `--seed <int>` | Override the default random seed. |

## Expected Outputs

- `data/raw/` – downloaded CSVs (checksummed).  
- `data/processed/` – featurized train/val/test splits (automatically created).  
- `results/metrics_*.csv` – Calibration Error, Sharpness, Coverage per method.  
- `results/statistical_report.csv` – Paired Wilcoxon p‑values & significance flags (conforms to `contracts/stats.schema.yaml`).  
- `results/sensitivity_conformal.csv` – Coverage sweep results.  
- `logs/execution.log` – Timestamped step‑by‑step log (including memory usage).  

## Troubleshooting

- **MemoryError**: Reduce `--max-samples` (e.g., to 2000).  
- **Dataset download failure**: Verify internet connectivity; the script logs the exact URL that failed.  
- **GPR convergence issues**: The pipeline will automatically down‑sample to ≤ 2000 points and retry.

---

