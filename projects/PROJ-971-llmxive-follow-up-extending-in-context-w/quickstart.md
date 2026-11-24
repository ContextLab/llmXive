# Quickstart: Full Auto‑ICWM Pipeline

**Feature**: `001-auto-icwm-latent-dynamics`
**Goal**: Run the complete end‑to‑end pipeline on a small subset (50 clips) and produce the core descriptor and label datasets.

## Project Layout
- `src/pipeline/`: Core pipeline implementation (data generation, feature extraction, labeling, modelling, validation).
- `data/raw/`: Generated interaction clips (`.npz` files).
- `data/processed/`: Structured statistical descriptors (`descriptors.csv`) and grid‑search labels (`labels.csv`).
- `results/`, `reports/`, `figures/`, `model/`: Outputs of downstream analysis (not needed for the minimal run).
- `specs/`: JSON‑Schema contracts for validation.
- `scripts/`: Helper scripts for environment setup (optional).

## Prerequisites
All dependencies are listed in `requirements.txt`. To use a local virtual environment:

```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## Run the Full Pipeline (single command)

```bash
python -m src.pipeline.run_all --subset 50
```

This command will:

1. **Generate 50 reproducible interaction clips** (`data/raw/clip_*.npz`).
2. **Extract latent descriptors** (variance, lag‑1 autocorrelation, Welch spectral density) for every clip and write `data/processed/descriptors.csv`.
3. **Perform a real grid‑search labeling** for each clip and write `data/processed/labels.csv`.
4. Print a concise 50‑row summary table to *stdout* (clip ID and the three descriptors).

After the command finishes, you can verify the outputs:

```bash
# Verify descriptor table
head data/processed/descriptors.csv
wc -l data/processed/descriptors.csv # should be 51 (header + 50 rows)

# Verify label table
head data/processed/labels.csv
wc -l data/processed/labels.csv # should be 51 (header + 50 rows)
```

The CI runner executes exactly this command and checks that the generated CSV files conform to the schemas in `specs/001-llmxive-follow-up-extending-in-context-w/contracts/`.
