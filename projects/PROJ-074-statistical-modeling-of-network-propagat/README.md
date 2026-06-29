# Bayesian Hierarchical Modeling of Misinformation Cascade Size

## Overview

This project implements a reproducible Bayesian hierarchical modeling pipeline
for analyzing misinformation cascade sizes. The pipeline ingests raw cascade
data, generates network and user features, fits a Bayesian hierarchical model
with random effects, and outputs posterior summaries with diagnostic metrics.

## Project Structure

```
.
├── code/ # Python pipeline modules
│ ├── pipeline/
│ │ ├── utils.py # Core utilities (logging, seeding, checksums)
│ │ ├── load_cascade.py # Data loading and validation
│ │ ├── network_features.py
│ │ ├── user_susceptibility.py
│ │ └──...
├── data/ # Input and processed data
│ ├── raw/ # Raw cascade JSON files
│ ├── processed/ # Validated and intermediate data
│ └── checksums.txt # SHA-256 checksums for data integrity
├── results/ # Model outputs
│ ├── features.csv
│ ├── model_trace.nc
│ └── posterior_summary.csv
├── tests/ # Contract and unit tests
├── contracts/ # JSON schema definitions
├── specs/ # Design documents
├── docs/ # Documentation
├── run_pipeline.sh # Main pipeline orchestration script
├── quickstart.md # Pipeline execution guide
├── model_spec.yaml # Bayesian model specification (priors, hyperparameters)
└── requirements.txt # Python dependencies
```

## Model Specification

The Bayesian hierarchical model configuration is defined in `model_spec.yaml`.
This file specifies:
- Prior distributions for fixed effects and random intercepts
- Hyperparameters for the negative binomial likelihood
- Platform random effect logic (conditional on ≥2 platforms)
- Sampling configuration (HMC/NUTS parameters)

Refer to `model_spec.yaml` for complete model details before running the pipeline.

## Quick Start

See `quickstart.md` for detailed pipeline execution instructions.

## Requirements

- Python 3.10+
- See `requirements.txt` for pinned dependency versions

## License

See LICENSE file.
