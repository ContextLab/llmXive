# Quickstart: Minimal Auto‑ICWM Pipeline

**Feature**: `001-auto-icwm-latent-dynamics`  
**Goal**: Run the minimal end‑to‑end pipeline on a small subset (50 clips) and produce a descriptors CSV.

## 1. Prerequisites
```bash
# From the repository root
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Run the minimal pipeline
The quickstart consists of two helper scripts:

1. **quickstart.sh** – prepares the environment (activates the virtual‑env if present).  
2. **run_minimal.sh** – launches the minimal pipeline which processes 50 clips.

```bash
# In one line (as used by CI):
bash -c "source quickstart.sh && ./run_minimal.sh"
```

After the command finishes, the file `data/descriptors_subset.csv` will exist.

## 3. What the pipeline does
| Step | Action | Output |
|------|--------|--------|
| 1️⃣ | Generates a set of reproducible interaction clips (placeholder) | `data/raw/clip_*.npz` |
| 2️⃣ | Extracts three statistical descriptors (variance, lagged autocorrelation, spectral density) for each clip | `data/descriptors_subset.csv` |
| 3️⃣ | Prints a short summary table to stdout |

The current minimal implementation creates placeholder clip files and a CSV with the required column headers; later tasks will replace these placeholders with real data and computations.

## 4. Verify
```bash
ls data/descriptors_subset.csv
```
The presence of the file indicates the quickstart succeeded.
