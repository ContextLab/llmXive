# Evaluating the Impact of Data Scaling on Robustness of Statistical Tests

This repository contains the implementation of a simulation engine to evaluate how different data scaling methods (standardization, min‑max, robust scaling) affect the robustness of common statistical tests (t‑test, ANOVA, chi‑squared). The project is organized as a typical Python research package with clear separation between simulation, preprocessing, analysis, and visualization components.

## Project Structure

```
.
├── code/ # Source code
│ ├── __init__.py
│ ├── main.py # CLI entry point
│ ├── simulation/
│ │ ├── __init__.py
│ │ ├── config.py
│ │ ├── generator.py
│ │ └── schema.py # Seed‑config handling (added)
│ ├── preprocessing/
│ │ ├── __init__.py
│ │ └── scaling.py
│ ├── analysis/
│ │ ├── __init__.py
│ │ └── tests.py
│ └── tests/
│ └── __init__.py # Added for test discovery
├── data/
│ └── config/
│ └── seed_config.json # Created at runtime by the simulation
├── results/
├── figures/
├── specs/
├── quickstart.md
├── code/requirements.txt
├── code/pyproject.toml
├── code/ruff.toml
└── code/.pre-commit-config.yaml
```

## Getting Started

See `quickstart.md` for detailed instructions on installing dependencies, running simulations, ingesting real‑world data, and generating analyses.
