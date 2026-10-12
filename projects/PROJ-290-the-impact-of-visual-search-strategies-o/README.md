# The Impact of Visual Search Strategies on Attentional Capture by Emotional Faces

**Project ID:** PROJ-290-the-impact-of-visual-search-strategies-o

## Overview

This repository implements a reproducible research pipeline that investigates whether individuals employ **global (holistic)** or **local (feature‑based)** visual search strategies when detecting emotional faces. Using publicly available eye‑tracking datasets, the pipeline:

1. **Downloads** and validates raw eye‑tracking data from HuggingFace Datasets.
2. **Extracts** fixation metrics (eye vs. mouth region duration, saccade amplitude, dispersion).
3. **Computes** a continuous fixation ratio (eye / mouth duration) as the primary predictor.
4. **Performs** exploratory participant classification via k‑means clustering (with robustness checks).
5. **Fits** linear mixed‑effects models (LMM) linking fixation patterns to detection time.
6. **Runs** permutation tests, multiple‑comparison corrections, and power analyses.
7. **Generates** publication‑ready tables, figures, and a final markdown report.

The pipeline follows the specifications in `specs/001-the-impact-of-visual-search-strategies-o/spec.md` and the implementation plan in `plan.md`. All steps are automated, version‑controlled, and produce verifiable artifacts stored under `data/`, `results/`, and `state/`.

## Repository Structure

```
projects/PROJ-290-the-impact-of-visual-search-strategies-o/
├── code/
│ ├── __init__.py
│ ├── config.py
│ ├── data/
│ │ ├── download.py
│ │ └── validate.py
│ ├── features/
│ │ ├── extraction.py
│ │ └── classification.py
│ ├── analysis/
│ │ ├── lmm.py
│ │ ├── power.py
│ │ ├── posthoc_power.py
│ │ ├── results_table.py
│ │ └── sensitivity_analysis.py
│ └── utils/
│ ├── logging.py
│ ├── seed.py
│ └── hash_artifacts.py
├── data/
│ ├── raw/
│ └── processed/
├── results/
│ ├── figures/
│ ├── reports/
│ └── sensitivity_report.yaml
├── state/
├── tests/
├── requirements.txt
├── pyproject.toml
└── README.md ← this file
```

## Getting Started

1. **Clone the repository** and navigate to the project root.
2. **Create a virtual environment** and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate
 pip install -r requirements.txt
 ```
3. **Run the pipeline** following the steps in `quickstart.md`.

## License

This project is released under the MIT License. See the `LICENSE` file for details.