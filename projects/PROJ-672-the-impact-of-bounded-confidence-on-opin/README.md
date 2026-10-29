# The Impact of Bounded Confidence on Opinion Polarization Speed

This research project investigates the interaction between network topology and the convergence dynamics of opinion polarization in bounded confidence models. Specifically, it examines whether the universal power-law scaling of convergence time is disrupted by specific structural features of scale-free (Barabási-Albert) and small-world (Watts-Strogatz) networks compared to random (Erdős-Rényi) graphs.

## Research Question
To what extent do specific network topologies (e.g., scale-free vs. small-world) disrupt the universal power-law scaling of convergence time in bounded confidence models, and what structural features of the network determine the divergence of the scaling exponent $\gamma$?

## Project Structure
- `code/`: Implementation of the research pipeline.
 - `generate_networks.py`: Synthetic network ensemble generation.
 - `simulate_hk.py`: Hegselmann-Krause (HK) model simulation.
 - `analyze_scaling.py`: Power-law fitting and regression analysis.
 - `utils/`: Shared utilities for metrics, convergence, and checksums.
- `data/`:
 - `raw/`: Original networks and simulation results.
 - `processed/`: Aggregated metrics and analysis results.
- `figures/`: Publication-ready plots.
- `tests/`: Unit and integration tests for verification.
- `specs/`: Feature specifications and research plan.

## Methodology
The pipeline follows a three-stage process:
1. **Network Generation**: Reproducible ensembles of ER, BA, and WS networks are generated with $N=500$ nodes.
2. **Opinion Dynamics**: Discrete-time HK simulations are run across a sweep of confidence thresholds $\epsilon \in [0.05, 0.50]$.
3. **Scaling Analysis**: Critical thresholds $\epsilon_c$ are detected, and power-law exponents $\gamma$ are extracted to correlate with structural metrics like assortativity and average path length.
