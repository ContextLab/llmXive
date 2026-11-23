# Mode Labeling Guide

## Overview
This project operates in two distinct modes: **CI Mode** and **Research Mode**.
It is critical to distinguish between these modes to prevent the conflation of
simulation results with scientific findings.

## CI Mode (Continuous Integration)
- **Purpose**: Automated pipeline validation, regression testing, and integration checks.
- **Data Source**: Synthetic scores decoupled from mask metrics (randomized).
- **Correlation Expectation**: Low correlation ($r < 0.1$) between synthetic metrics and scores is expected and valid.
- **Gate Behavior**: The proxy validation gate (T035) logs `EXPECTED_LOW_CORRELATION` and allows execution to continue.
- **Claim Validity**: Results generated in this mode **DO NOT** support human-grounded scientific claims.
- **Labeling**: All outputs must be explicitly labeled `CI_MODE` or `SIMULATION_ONLY`.

## Research Mode
- **Purpose**: Scientific inquiry, model training, and publication-quality analysis.
- **Data Source**: Real human-annotated data (e.g., `data/annotations/human_scores.csv`).
- **Correlation Expectation**: High correlation ($r \ge 0.7$) between synthetic metrics and human scores is required.
- **Gate Behavior**: The proxy validation gate (T035) enforces $r \ge 0.7$. If failed, it raises `SystemExit(1)` to block downstream training.
- **Claim Validity**: Only results from this mode support "Human-Grounded" claims.
- **Labeling**: All outputs must be labeled `RESEARCH_MODE`.

## Implementation Details
- **Configuration**: Mode is set via `config.py` (e.g., `set_mode('CI')` or `set_mode('RESEARCH')`).
- **Logging**: The active mode is logged to `data/results/validation_log.txt` at the start of every run.
- **Artifact Manifest**: The `data/results/quickstart_manifest.json` includes a `mode` field indicating the source of the data.

## Verification Checklist
Before publishing results:
1. Verify `config.mode` matches the intended operational mode.
2. Check `data/results/validation_log.txt` for the mode declaration.
3. Ensure `data/results/evaluation_report.json` contains the `mode_label` field.
4. Confirm that no synthetic data was used to generate claims in Research Mode.
