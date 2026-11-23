# llmXive: Brain Network Dynamics and Musical Emotion Perception

## Project Overview
This project investigates the relationship between brain network dynamics and
individual differences in musical emotion perception using rs-fMRI data from
OpenNeuro (ds000233) and behavioral scores (BMRQ).

## Structure
- `src/`: Source code for data pipeline, analysis, and modeling
- `tests/`: Unit, integration, and contract tests
- `specs/`: Design documents and feature specifications
- `data/`: Downloaded raw data and generated artifacts (gitignored)
- `figures/`: Generated plots and visualizations (gitignored)

## Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate it: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
3. Install dependencies: `pip install -r requirements.txt`

## Usage
Refer to `tasks.md` for the implementation roadmap and execution order.
The primary entry points are located in `src/data/` and `src/analysis/`.

## License
MIT
