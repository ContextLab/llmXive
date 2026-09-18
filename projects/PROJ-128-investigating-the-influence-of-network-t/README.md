# Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

**Project ID**: PROJ-128

## Overview

This research project investigates the relationship between structural brain network topology (derived from diffusion MRI) and dynamic functional brain activity patterns (derived from fMRI). We employ a rigorous Leave-One-Out (LOO) K-Means clustering approach to ensure statistical independence between structural and functional metric calculations.

## Research Question

Do topological properties of structural brain networks derived from diffusion MRI predict the prevalence, stability, and switching speed of recurrent activity patterns in spontaneous brain activity?

## Key Highlights

- **MVP Status**: User Story 1 (Compute Structural and Dynamic Graph Metrics) is fully implemented and tested.
- **Statistical Rigor**: LOO K-Means ensures independence; FDR correction controls for multiple comparisons.
- **Robustness**: Sensitivity analysis validates findings against parameter variations.
- **Associational Framing**: All results are explicitly framed as associational, not causal.
- **CPU-Optimized**: Designed for environments without GPU access.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline
python code/main.py

# Validate results
python code/validate_quickstart.py
```

## Project Structure

- `code/`: Source code for the pipeline
- `data/`: Raw and processed data
- `tests/`: Unit and integration tests
- `contracts/`: Data schemas
- `docs/`: Documentation

## Documentation

Detailed documentation is available in [`docs/README.md`](docs/README.md).

## Status

- [x] Phase 1: Setup
- [x] Phase 2: Foundational
- [x] Phase 3: User Story 1 (MVP)
- [x] Phase 4: User Story 2
- [x] Phase 5: User Story 3
- [x] Phase N: Polish & Documentation (T050)

## License

MIT License
