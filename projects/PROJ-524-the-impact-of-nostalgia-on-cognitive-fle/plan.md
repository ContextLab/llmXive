# Project Plan: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

## Overview
This project investigates the relationship between nostalgia induction and cognitive flexibility in aging adults (65+), using the Wisconsin Card Sorting Test (WCST) as a primary metric.

## Objectives
1. Ingest and validate WCST data from aging adult populations.
2. Analyze differences in cognitive flexibility metrics between nostalgia and control conditions.
3. Perform sensitivity analysis to ensure robustness of findings.

## Data Sources
- **Primary**: Publicly available WCST datasets (OpenML/HuggingFace).
- **Fallback**: Methodological Simulation (see Simulation Methodology section).

## Simulation Methodology (Verified Accuracy Gate)
If real data is unavailable, the pipeline falls back to a strictly defined simulation:
- **Seed**: Fixed random seed (default 42) for reproducibility.
- **Distributions**: Normal distributions for cognitive metrics, with means derived from literature (Nostalgia: PE=12.5, CC=4.8; Control: PE=18.2, CC=3.9).
- **Constraints**: Age >= 65, non-null metrics.
- **Transparency**: All simulation parameters are logged in `data/raw/metadata.json` under the `simulation_methodology` key.
- **Labeling**: All outputs generated from simulation are explicitly flagged as `simulation_mode: true`.

## Reproducibility Gates
1. **Data Source Verification**: The system must check for `data/verified_source.json`. If present, it must match the loaded package. If missing, simulation is allowed but must be logged.
2. **Simulation Transparency**: The `simulation_methodology` field in `data/raw/metadata.json` must contain exact seed, distribution parameters, and sample size.
3. **Assumption Checks**: Statistical assumptions (normality, homogeneity) must be logged in `data/results/assumption_checks.json`.
4. **Robustness Summary**: A comparison of primary vs. robustness analyses must be generated in `data/results/robustness_summary.md`.

## Execution Pipeline
1. **Ingestion**: Fetch real data or generate simulation.
2. **Preprocessing**: Filter by age (>=65), score validity, and MMSE (if available).
3. **Analysis**: Welch's t-test, Bonferroni correction, effect sizes.
4. **Sensitivity**: Threshold sweeps and robustness checks.
5. **Reporting**: Final report generation with all verification gates passed.

## Dependencies
- Python 3.9+
- pandas, scipy, statsmodels, numpy, pyyaml, datasets, pytest

## Success Criteria
- Pipeline runs end-to-end without errors.
- All required artifacts (JSON, CSV, MD) are generated.
- Simulation fallback is transparent and reproducible.
- Statistical assumptions are validated and logged.
