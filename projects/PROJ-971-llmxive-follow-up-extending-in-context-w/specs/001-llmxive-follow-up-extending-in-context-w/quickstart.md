# Quickstart: Minimal Auto‑ICWM Pipeline

**Feature**: `001-auto-icwm-latent-dynamics`  
**Goal**: Run the minimal end‑to‑end pipeline on a small subset (a limited set of clips) and produce `data/descriptors_subset.csv`.

## Prerequisites
All heavy dependencies are listed in `requirements.txt`. To use a local virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the Minimal Pipeline
Two helper scripts are provided in `scripts/`:

1. `scripts/quickstart.sh` – sets up `PYTHONPATH` and activates the virtualenv if present.  
2. `scripts/run_minimal.sh` – generates a set of reproducible clips, extracts the three descriptors, and writes `data/descriptors_subset.csv`.

Execute with a single command (as used by CI):

```bash
bash -c "source scripts/quickstart.sh && ./scripts/run_minimal.sh"
```

After completion, verify:

```bash
ls data/descriptors_subset.csv
wc -l data/descriptors_subset.csv   # should be > 1 (header + 50 rows)
```

## What the Pipeline Does
| Step | Action | Output |
|------|--------|--------|
| 1 | Generate a sufficient number of reproducible interaction clips | `data/raw/clip_*.npz` |
| 2 | Encode each clip with the CPU‑only ICWM encoder and compute variance, lag autocorrelation, and Welch spectral density. | `data/descriptors_subset.csv` |
| 3 | Print a summary table to stdout | stdout |

All outputs conform to `contracts/descriptor.schema.yaml`.

---

