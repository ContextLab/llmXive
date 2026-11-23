# The Impact of Bounded Confidence on Opinion Polarization Speed

## Project Overview

This project investigates how the structural properties of social networks influence the speed and stability of opinion polarization under the Hegselmann-Krause (HK) bounded confidence model. We focus on the relationship between the confidence threshold parameter ($\epsilon$) and the convergence time ($T$), specifically looking for power-law scaling behavior near a critical threshold ($\epsilon_c$).

## Research Questions

1. How does the critical threshold $\epsilon_c$ vary across different network topologies (Erdős-Rényi, Barabási-Albert, Watts-Strogatz)?
2. Is there a power-law relationship $T \sim (\epsilon - \epsilon_c)^{-\gamma}$ near the critical point?
3. How do structural metrics (assortativity, path length, clustering) correlate with the scaling exponent $\gamma$?

## Key Findings

- **Topology Dependence**: The critical threshold $\epsilon_c$ is lower for scale-free networks (Barabási-Albert) compared to random networks, indicating that hubs facilitate consensus.
- **Scaling Law**: A robust power-law relationship exists near $\epsilon_c$, with the exponent $\gamma$ varying by topology.
- **Structural Correlation**: High assortativity correlates with a steeper divergence in convergence time (higher $\gamma$).

## Repository Structure

```
.
├── code/
│ ├── generate_networks.py # Network generation (T012-T015)
│ ├── simulate_hk.py # HK simulation engine (T019-T025)
│ ├── analyze_scaling.py # Power-law fitting and regression (T028-T032)
│ ├── sensitivity_analysis.py # Robustness checks (T033-T034)
│ ├── utils/ # Helper modules (metrics, plotting, checksums)
│ └── contracts/ # JSON schemas for data validation
├── data/
│ ├── raw/ # Generated networks and simulation traces
│ └── processed/ # Aggregated results, fitted parameters, figures
├── tests/
│ ├── unit/ # Unit tests for logic
│ ├── contract/ # Schema validation tests
│ └── integration/ # End-to-end workflow tests
├── docs/
│ ├── methodology.md # Theoretical background and experimental design
│ ├── results_summary.md # Summary of key findings
│ ├── quickstart.md # Instructions for running the pipeline
│ └── CONTRIBUTING.md # Contribution guidelines
├── state/
│ └── projects/ # Project state and checksums
└── tasks.md # Implementation task list
```

## Getting Started

See `docs/quickstart.md` for instructions on installing dependencies and running the simulation pipeline.

## Methodology

Detailed theoretical background and experimental design are described in `docs/methodology.md`. This includes:
- The Hegselmann-Krause model formulation.
- Network generation protocols.
- Scaling analysis and regression methods.
- Sensitivity analysis procedures.

## Results

A summary of the results, including plots and statistical analysis, is available in `docs/results_summary.md`.

## Reproducibility

All results are reproducible. The codebase uses fixed random seeds, and all data artifacts are checksummed. Re-run the pipeline using the steps in `docs/quickstart.md` to regenerate the results.

## Review and Alignment

This project explicitly addresses feedback from the research review board:
- **Stephen Wolfram**: Rule-space exploration is documented in `docs/methodology.md`.
- **Alan Turing**: Static vs. adaptive thresholds are distinguished in the code and documentation.
- **David Krakauer**: Biological context and historical lineage are discussed.
- **Geoffrey West**: Scaling of $\epsilon$ with network density is analyzed.

## License

This project is open-source and available under the MIT License.
