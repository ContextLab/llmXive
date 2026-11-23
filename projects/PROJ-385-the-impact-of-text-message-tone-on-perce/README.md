# Project Overview

This repository implements the research pipeline for **The Impact of Text Message Tone on Perceived Emotional Support**.
It generates controlled text‑message stimuli, collects real human ratings, fits a linear mixed‑effects model, performs post‑hoc tests, and conducts sensitivity analyses on cue‑intensity definitions.

## CLI Usage

The primary entry point is the unified command‑line interface:

```bash
python code/run_pipeline.py [--mode real|mock] [--generate-report]
```

* `--mode real` runs the full analysis on real participant data located at `data/raw/real_ratings.csv`.
* `--mode mock` is reserved for CI testing with synthetic data.
* `--generate-report` creates a markdown report summarising the results and methodological notes.

Additional helper scripts are available under `code/` (e.g., `01_generate_stimuli.py`, `04_fit_lmm.py`). Use `-h/--help` on any script for usage details.

## Reproducibility

- All random operations are seeded with `RANDOM_SEED = 42` defined in `code/config.py`.
- SHA‑256 checksums for every generated artifact are recorded in `data/checksums.json` and verified by `code/verify_checksums.py`.
- The manifest file `data/manifest.json` records hashes for all pipeline outputs and is validated before downstream steps.
- The pipeline is CPU‑only and runs within the resource limits of a standard GitHub Actions runner (≤ 6 h, ≤ 7 GB RAM). [UNRESOLVED-CLAIM: c_406d60ce — status=not_enough_info]

For detailed setup instructions, see `quickstart.md`.
