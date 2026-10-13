# Quickstart: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

## Prerequisites
- **Python** 3.11 or newer  
- **MRtrix3** (system binary; `mrconvert`, `tckgen`, `tck2connectome` must be in `$PATH`). On the GitHub Actions runner MRtrix3 is pre‑installed; on a local machine install via the official package manager.  
- **Git** (to clone the repository)  

## Installation

```bash
# 1️⃣ Clone the repository
git clone <repo-url>
cd projects/PROJ-472-investigating-the-impact-of-network-stru

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3️⃣ Install Python dependencies
pip install -r requirements.txt
```

## Configuration
Edit `src/config.yaml` if you wish to change:
- **Dataset URL** (default points to the verified OpenNeuro ds004230 dataset)  
- Avalanche thresholds (`thresholds: [0.75, 0.80]`)  
- Random seed (`seed: 42`)  

## Running the Full Pipeline

```bash
python -m src.cli.run_pipeline
```

The command performs, in order:

1. **Data download & checksum verification** (`download.py`).  
2. **dMRI preprocessing** (`preprocess_dMRI.py`) → adjacency matrices (with fallback to pre‑computed matrix if tractography fails).  
3. **EEG preprocessing** (`preprocess_EEG.py`) → cleaned epochs (band‑pass 1–40 Hz, down‑sample 250 Hz, ICA).  
4. **Metric computation** (`network_metrics.py`, `avalanche_metrics.py`).  
5. **Statistical validation** (`stats.py`) – Spearman correlation, permutation testing, VIF diagnostics, and threshold sensitivity sweep.  
6. **Report generation** (`report.md`) in `data/results/`.

### Expected Outputs
- `data/processed/` – `.npy` connectivity matrices & cleaned EEG.  
- `data/results/metrics.csv` – participant‑level structural & avalanche metrics.  
- `data/results/correlations.csv` – Spearman + permutation results for each metric pair and threshold.  
- `data/results/collinearity_status.json` – VIF diagnostics and high‑collinearity flags.  
- `data/results/report.md` – final narrative (includes data‑availability disclaimer).

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `mrtrix3` command not found | MRtrix3 not installed or not on `$PATH` | Install MRtrix3 or add its `bin/` directory to `$PATH`. |
| Out‑of‑memory error during dMRI conversion | Too many subjects loaded simultaneously | Reduce `max_subjects` in `config.yaml` or run on a machine with more RAM. |
| `powerlaw` fails to converge for a participant | Poor avalanche distribution (e.g., too few events) | Participant will be excluded automatically; check `data/results/metrics.csv` for missing exponents. |
| No matched dMRI + EEG found | By design – the open dataset provides both modalities; ensure you are using the designated dataset. | Verify that `src/config.yaml` points to the correct OpenNeuro URL. |

## Notes on Compute
- The pipeline is **CPU‑first**; no CUDA calls are present.  
- If MRtrix3 tractography fails, the script falls back to the pre‑computed connectivity matrix bundled with ds004230 (logged in `data/logs/fallback.log`).  
- All random processes (permutation shuffling, any stochastic steps) use the seed from `src/utils/seed.py`.

---



