# Quickstart: The Impact of Digital Decluttering on Cognitive Performance and Well‑being

## Prerequisites

- Python 3.11+
- pip

## Installation

```bash
cd PROJ-249-the-impact-of-digital-decluttering-on-co
pip install -r code/requirements.txt
```

## Run the pipeline (single command)

```bash
python -m code.pipeline.run_all --config code/config/study_config.yaml
```

This command:

1. Validates `code/config/study_config.yaml`.
2. Creates the required project layout
 (`code/scoring/`, `code/analysis/`, `code/compliance/`,
 `code/viz/`, `code/validation/`, `code/pipeline/`,
 `code/tests/`, `data/raw/`, `data/processed/`,
 `data/results/`, `figures/`).
3. Writes `results/pipeline.log` that ends with `STATUS: SUCCESS`.
4. Writes `data/results/pipeline_status.json`.
5. Generates a SHA‑256 manifest `data/checksums.sha256` that includes the status file.

## Configuration

All study parameters live in `code/config/study_config.yaml`:
`seed`, `n_participants`, `dropout_rate`, `effect_sizes` (per‑metric
dict for SART, Ospan, PSS‑10, PANAS‑PA, PANAS‑NA),
`practice_effect_grid` ([0.0, 0.2, 0.4]), `bootstrap_resamples`
(10 000), `start_date` (ISO date), and `pilot_n` (5).