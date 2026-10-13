# The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## Project Overview

This repository contains a reproducible research pipeline that investigates how musical training during adolescence influences resting‑state functional connectivity, with a focus on auditory, motor, and executive control networks.

The codebase is organized into clearly separated modules for data handling, preprocessing, analysis, and visualization. Synthetic data are used for verification, while real neuroimaging data (e.g., ABCD or HCP‑Adolescents) can be processed in analysis mode.

## Directory Structure

```
/ # Project root
├─ code/ # Python source code
│ ├─ __init__.py
│ ├─ main.py # CLI entry‑point
│ ├─ data/ # Data loading, synthetic generator, mock NIfTI utilities
│ ├─ analysis/ # Atlas handling, connectivity, statistics, correlation, NBS, etc.
│ └─ utils/ # Logging, memory monitoring, helper utilities
├─ data/ # Data storage (raw, processed, results, atlases)
│ ├─ raw/ # Real or mock NIfTI files, raw behavioural CSVs
│ ├─ processed/ # Cleaned tables, connectivity matrices, intermediate results
│ └─ results/ # Final CSVs, figures, summary tables
├─ tests/ # Unit and integration test suite
│ ├─ unit/
│ └─ integration/
├─ specs/ # Specification documents for the feature branch
├─ figures/ # Generated figures (PNG, SVG)
├─ results/ # Additional result artefacts (e.g., summary CSVs)
├─ requirements.txt # Python dependencies
├─ README.md # This file
└─ quickstart.md # Quick‑start guide
```

The three top‑level folders (`code/`, `data/`, `tests/`) are required for the pipeline to function and are explicitly referenced in the test suite.

## Getting Started

See the accompanying **quick‑start guide** (`quickstart.md`) for installation instructions, required Python version, and example commands to run the pipeline in both verification (synthetic) and analysis (real) modes.

## License

This project is released under the MIT License. See the `LICENSE` file for details.