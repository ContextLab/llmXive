# The Impact of Bounded Confidence on Opinion Polarization Speed

This repository contains a reproducible computational study of how network topology influences the scaling of convergence time in bounded‑confidence opinion dynamics. The pipeline generates synthetic networks, runs Hegselmann‑Krause simulations across a sweep of confidence thresholds, analyses scaling laws, and produces publication‑ready figures.

## Repository layout

```
.
├── code/ # Core Python scripts and utilities
├── data/
│ ├── raw/ # Generated networks and simulation outputs
│ └── processed/ # Derived metrics, fits, and regression results
├── docs/ # Methods, results, and reviewer response markdown
├── outputs/
│ └── figures/ # Publication‑ready PNG figures
├── tests/ # pytest test suite
├── quickstart.md # Quick start guide (see below)
└── README.md # This file
```

## Getting started

See `quickstart.md` for a step‑by‑step guide to install dependencies, generate a single network instance, and run the full pipeline.

## Contributing

Contributions are welcome via pull requests. Please ensure that all new code is covered by unit tests and that the documentation in `docs/` is kept up‑to‑date.

## License

This project is released under the MIT License.
