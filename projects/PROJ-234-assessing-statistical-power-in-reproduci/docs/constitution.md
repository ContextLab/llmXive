# Project Constitution

This document defines the core principles, scope, and operational guidelines for the **Assessing Statistical Power in Reproducible Research with Public Datasets** project.

## Core Principles

1. **Reproducibility First**: All analyses must be transparent, repeatable, and based on verifiable data sources.
2. **Statistical Rigor**: Observed power and Minimum Detectable Effect Size (MDES) are calculated using established statistical methods.
3. **Open Science**: Preference is given to open-access publications and public datasets (e.g., OpenML).
4. **Fail Loudly**: Scripts must not silently fall back to synthetic data; real data sources must be used or the process must fail explicitly.

## Project Scope

This project aims to:
- Retrieve and filter top public datasets from OpenML.
- Extract statistical parameters (sample size, effect sizes) from associated publications.
- Compute observed statistical power and MDES.
- Generate an audit report highlighting the fraction of studies with low power (< 0.8).

## Documentation Links

- **[Research](../research.md)**: Detailed research questions, hypotheses, and methodological background.
- **[Plan](../plan.md)**: Project execution plan, user stories, and milestone definitions.
- **[Quickstart](../quickstart.md)**: Instructions for setting up the environment and running the pipeline.

## Governance

- **Data Integrity**: All data artifacts must be derived from real sources.
- **Code Quality**: All Python code must pass linting (black, flake8) and unit tests.
- **Reporting**: Final reports must include disclaimers regarding the limitations of observed power.