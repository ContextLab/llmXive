# Quickstart: Minimal Auto-ICWM Pipeline

**Feature**: `001-auto-icwm-latent-dynamics`
**Goal**: Run the minimal end-to-end pipeline on a small subset (50 clips) and produce the descriptors CSV `data/descriptors_subset.csv`.

## 1. Prerequisites

All heavy dependencies (numpy, pandas, scipy, scikit-learn, gymnasium) are
available in the project Python environment. If you prefer a local
virtual-env:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Run the minimal pipeline

The quickstart consists of two project-local helper scripts:

1. **`quickstart.sh`** – prepares the environment (activates `.venv` if
   present, sets `PYTHONPATH` to the project root).
2. **`run_minimal.sh`** – runs the real minimal pipeline on 50 clips:
   generates 50 reproducible interaction clips
   (`src/pipeline/generate_clips.py` → `data/raw/clip_*.npz`), runs the
   CPU-only ICWM encoder and computes the three statistical descriptors
   (variance, lag-1 autocorrelation, Welch spectral density) per clip
   (`src/pipeline/extract_descriptors.py`), then prints a summary table
   (`src/pipeline/run_end_to_end.py`).

```bash
# Single command (as used by CI):
bash -c "source quickstart.sh && ./run_minimal.sh"
```

After the command finishes, `data/descriptors_subset.csv` exists with one
row per clip (columns: `clip_id`, `variance`, `autocorr_lag1`,
`spectral_density`) and no null/NaN entries.

## 3. What the pipeline does

| Step | Action | Output |
|------|--------|--------|
| 1 | Generates 50 reproducible interaction clips (state/action/observation tuples) | `data/raw/clip_*.npz` |
| 2 | Encodes each clip with the ICWM encoder and computes variance, lag-1 autocorrelation, and Welch spectral density | `data/descriptors_subset.csv` |
| 3 | Prints a summary table of the descriptors to stdout | stdout |

## 4. Verify

```bash
ls data/descriptors_subset.csv
wc -l data/descriptors_subset.csv   # 51 lines (header + 50 clips)
```

The presence of the file with 50 data rows indicates the quickstart succeeded.