# Quickstart: The Impact of Digital Decluttering on Cognitive Performance and Well-being

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

This is the single documented entry point. It validates the study
configuration strictly (raising on any missing or malformed key),
establishes the project layout (`code/scoring/`, `code/analysis/`,
`code/validation/`, `code/viz/`, `code/pipeline/`, `code/tests/`,
`data/raw/`, `data/processed/`, `data/results/`), writes
`data/results/pipeline_status.json`, and maintains the checksum
manifest `data/checksums.sha256` covering all files under `data/`.

As later tasks land, this command is extended to run the full study
pipeline (seeded simulation, compliance processing, change scores,
bootstrap analysis, Holm-Bonferroni correction, power simulation,
sensitivity analyses, figures, and reporting) in dependency order.

## Configuration

All study parameters live in `code/config/study_config.yaml`:
`seed`, `n_participants`, `dropout_rate`, `effect_sizes` (per-metric
dict for SART, Ospan, PSS-10, PANAS-PA, PANAS-NA),
`practice_effect_grid` ([0.0, 0.2, 0.4]), `bootstrap_resamples`
(10000), `start_date` (ISO date), and `pilot_n` (5).

## Verify checksums

```bash
sha256sum -c data/checksums.sha256
```

## Tests

```bash
pytest code/tests -v
```

## Troubleshooting

- **Config errors**: the runner raises immediately with the exact
 missing/invalid key; fix `code/config/study_config.yaml`.
- **Checksum mismatch**: a file under `data/` changed after being
 recorded; re-run the pipeline or investigate the modification.