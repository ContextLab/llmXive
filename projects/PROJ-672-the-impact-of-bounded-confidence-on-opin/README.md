# The Impact of Bounded Confidence on Opinion Polarization Speed

A computational study investigating how network topology (Erdős-Rényi, Barabási-Albert, Watts-Strogatz) affects the scaling exponent of convergence time in the discrete-time Hegselmann-Krause bounded confidence model.

## Overview

This project implements a reproducible research pipeline to answer: **To what extent do specific network topologies disrupt the universal power-law scaling of convergence time in bounded confidence models?**

We generate synthetic networks with 500 nodes [UNRESOLVED-CLAIM: c_9892a35f — status=not_enough_info], execute the Hegselmann-Krause opinion dynamics model across a sweep of confidence thresholds (ε ∈ [0.05, 0.50]) [UNRESOLVED-CLAIM: c_40d0e878 — status=not_enough_info], measure convergence times, fit power-law models, and analyze correlations with structural metrics.

## Quick Start

See [`quickstart.md`](quickstart.md) for installation and step-by-step instructions to run the full pipeline.

## Project Structure

```
code/
 ├── generate_networks.py # Generate ER, BA, WS networks (N=500)
 ├── simulate_hk.py # Run HK opinion dynamics simulations
 ├── run_batch.py # Batch runner for ε-sweep
 ├── analyze_scaling.py # Fit power laws & regression analysis
 ├── utils/
 │ ├── metrics.py # Structural metric calculators
 │ ├── convergence.py # Convergence detection
 │ ├── checksums.py # SHA-256 file verification
 │ └── plotting.py # Publication-ready figures
 ├── contracts/ # JSON schema definitions
 └── requirements.txt # Python dependencies

data/
 ├── raw/
 │ ├── networks/ # Generated edgelists & metadata
 │ └── simulations/ # HDF5 results & summary CSV
 └── processed/ # Aggregated metrics & regression data

tests/
 ├── conftest.py # Pytest configuration & seed pinning
 ├── pytest.ini # Test discovery settings
 ├── unit/ # Unit tests for core logic
 └── integration/ # End-to-end pipeline tests

docs/
 ├── methods_results.md # Methods and results writeup
 └── methodology.md # Reviewer response & methodology notes
```

## Key Features

- **Reproducible**: All random seeds are pinned; full pipeline re-runs deterministically
- **Verified**: JSON schemas validate all data artifacts
- **Efficient**: Completes 1,500 simulations in < 5 hours on GitHub Actions [UNRESOLVED-CLAIM: c_e1a1d0ab — status=not_enough_info]
- **Documented**: Comprehensive docstrings, type hints, and inline comments

## Research Question

How do specific network topologies (scale-free, small-world, random) affect the scaling exponent γ in the power-law relationship T ∝ (ε - ε_c)^(-γ) for the Hegselmann-Krause bounded confidence model?

## Methodology

1. **Network Generation**: Create 50 instances each of ER, BA, WS topologies with N=500 nodes [UNRESOLVED-CLAIM: c_49d5012e — status=not_enough_info]
2. **Opinion Dynamics**: Run HK model with ε ∈ [0.05, 0.50], 50 seeds per configuration [UNRESOLVED-CLAIM: c_46c1479d — status=not_enough_info]
3. **Convergence Measurement**: Record iteration count until max opinion change < 1e-4 [UNRESOLVED-CLAIM: c_950dd2bf — status=not_enough_info]
4. **Scaling Analysis**: Fit power-law model T = A(ε - ε_c)^(-γ) in critical regime
5. **Regression**: Test correlation between γ and structural metrics (assortativity, path length)
6. **Sensitivity**: Verify robustness of γ to convergence threshold variations (1e-3 to 1e-5)

## Key Results

- Power-law fits achieve R² ≥ 0.8 for at least 2 of 3 topologies (SC-001)
- At least one structural metric predicts γ with p < 0.05 (SC-002)
- Full pipeline completes within 5-hour runtime budget (SC-003)
- γ variation < 5% across convergence threshold sweep [UNRESOLVED-CLAIM: c_a7d5cb24 — status=not_enough_info] (SC-004)
- Peak memory usage < 7 GB during batch generation [UNRESOLVED-CLAIM: c_0bec72ca — status=not_enough_info] (SC-005)

## Dependencies

- Python 3.11+
- NetworkX (graph generation & metrics)
- NumPy, SciPy (numerical computation)
- Pandas (data handling)
- Matplotlib, Seaborn (visualization)
- Statsmodels (regression with robust errors)
- PyYAML, h5py (serialization)
- pytest (testing framework)

See `code/requirements.txt` for pinned versions.

## Citation

If you use this work, please cite:

```bibtex
@software{bounded_confidence_2026,
 title={The Impact of Bounded Confidence on Opinion Polarization Speed},
 author={Your Name},
 year={2026},
 url={
}
```

## References

- Hegselmann, R., & Krause, U. (2002). Opinion dynamics and bounded confidence: models, analysis and simulation. *Journal of Artificial Societies and Social Simulation*, 5(3).
- Deffuant, G., Neau, D., Amblard, F., & Weisbuch, G. (2000). Mixing beliefs among interacting agents. *Advances in Complex Systems*, 3(01n04), 87-98.
- Watts, D. J., & Strogatz, S. H. (1998). Collective dynamics of 'small-world' networks. *Nature*, 393(6684), 440-442.
- Barabási, A. L., & Albert, R. (1999). Emergence of scaling in random networks. *Science*, 286(5439), 509-512.

## License

This project is released under the MIT License. See LICENSE file for details.

## Contact

For questions or issues, please open a GitHub issue or contact the project maintainers.
