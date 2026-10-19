# Quickstart: Minimal Auto‑ICWM Pipeline

**Feature**: `001-auto-icwm-latent-dynamics`
**Goal**: Run the minimal end‑to‑end pipeline on a small subset (a limited set of clips) and produce both the full descriptor CSV and the shortcut subset CSV.

## Prerequisites
All heavy dependencies are listed in `requirements.txt`. To use a local virtual environment:

```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## Run the Minimal Pipeline
Two helper scripts are provided in `scripts/`:

1. `scripts/quickstart.sh` – sets up `PYTHONPATH` and activates the virtualenv if present.
2. `scripts/run_minimal.sh` – generates a set of reproducible clips, extracts the three descriptors, and writes **both**:
 * `data/processed/descriptors.csv` – the full descriptor table used by downstream stages.
 * `data/descriptors_subset.csv` – a convenient shortcut referenced in the documentation.

Execute with a single command (as used by CI):

```bash
bash -c "source scripts/quickstart.sh &&./scripts/run_minimal.sh"
```

After completion, verify:

```bash
ls data/processed/descriptors.csv
wc -l data/processed/descriptors.csv # should be > 1 (header + 50 rows) [UNRESOLVED-CLAIM: c_22d1bc63 — status=not_enough_info]

ls data/descriptors_subset.csv
wc -l data/descriptors_subset.csv # should match the same row count [UNRESOLVED-CLAIM: c_f084ff56 — status=not_enough_info]
```

## What the Pipeline Does
| Step | Action | Output |
|------|--------|--------|
| 1 | Generate a sufficient number of reproducible interaction clips | `data/raw/clip_*.npz` |
| 2 | Encode each clip with the CPU‑only ICWM encoder and compute variance, lag‑1 autocorrelation, and Welch spectral density. | `data/processed/descriptors.csv` |
| 3 | Copy the full descriptor CSV to the shortcut location used by legacy documentation. | `data/descriptors_subset.csv` |
| 4 | Print a summary table to stdout | stdout |

All outputs conform to `specs/001-llmxive-follow-up-extending-in-context-w/contracts/descriptor.schema.yaml`.
