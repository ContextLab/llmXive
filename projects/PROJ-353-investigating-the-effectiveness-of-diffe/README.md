# PROJ-353: Investigating the Effectiveness of Contrastive Loss on Small-World Graphs

## Project Structure

This project implements a research pipeline to investigate the interaction between graph topology (specifically the small-world parameter $\beta$) and loss function choice (Cross-Entropy vs. InfoNCE) on the convergence speed of Graph Neural Networks.

### Directory Layout

- `code/`: Core Python implementation (models, training loops, analysis scripts).
- `tests/`: Unit and integration tests.
- `data/raw/`: Generated synthetic graph datasets (Watts-Strogatz).
- `data/processed/`: Training trajectories, convergence logs, and intermediate results.
- `data/analysis/`: Final statistical analysis results and reports.
- `specs/`: Research design, user stories, and methodology documents.
- `contracts/`: JSON schemas for data validation.
- `state/`: Artifact checksums and project state tracking.

## Quick Start

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
2. Generate synthetic data:
 ```bash
 python code/data_generation.py
 ```
3. Run training:
 ```bash
 python code/main.py
 ```
4. Analyze results:
 ```bash
 python code/analyze.py
 ```

See `specs/353-loss-functions-small-world/quickstart.md` for detailed instructions.