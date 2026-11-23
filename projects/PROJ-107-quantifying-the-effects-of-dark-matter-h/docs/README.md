# llmXive: Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation

## Project Overview

This project implements a scientific research pipeline to quantify the effects of dark matter halo shapes on galaxy formation properties. It processes data from the TNG-100 simulation (and potentially Millennium-II) to compute halo shapes, statistical correlations, and orientation misalignments.

## Architecture

The project follows a modular pipeline architecture:

- **Ingestion**: `code/ingestion/` - Data loading from TNG-100 and Millennium-II APIs
- **Processing**: `code/processing/` - Inertia tensor computation, shape metrics, alignment analysis
- **Analysis**: `code/analysis/` - Statistical tests, mass-matching, regression, sensitivity analysis
- **Utils**: `code/utils/` - Configuration, I/O utilities, logging, metadata management

## Directory Structure

```
.
├── code/
│ ├── ingestion/
│ ├── processing/
│ ├── analysis/
│ ├── utils/
│ └── tests/
├── data/
│ ├── raw/
│ │ ├── tng100/
│ │ └── millennium/
│ ├── processed/
│ │ └── matched_chunks/
│ └── metadata/
├── outputs/
│ ├── figures/
│ └── reports/
├── docs/
├── state/
└── logs/
```

## Quick Start

See [quickstart.md](./quickstart.md) for installation and execution instructions.

## Key Features

- **Halo Shape Computation**: Reduced inertia tensor eigenvalue decomposition
- **Statistical Analysis**: Kruskal-Wallis, Mann-Whitney U, Kolmogorov-Smirnov tests
- **Mass Control**: Nearest-neighbor matching with streaming support
- **Orientation Analysis**: Spin-spin and major-major axis misalignment angles
- **Sensitivity Analysis**: Threshold sweep for binning robustness

## Data Sources

- **TNG-100**: Primary dataset via official API
- **Millennium-II**: Secondary dataset (conditional on availability)
- **WDM Variants**: Experimental variants (conditional on availability)

## License

Research code for scientific collaboration.
