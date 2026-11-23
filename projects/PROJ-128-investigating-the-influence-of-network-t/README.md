# llmXive: Network Topology and Brain Activity Patterns

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This project investigates the **associational relationship** between topological properties of structural brain networks (derived from diffusion MRI) and dynamic functional states (derived from fMRI).

**Important**: This study is **associational** in nature. We do not claim causal relationships.

## Quick Links

- [Quickstart Guide](docs/quickstart.md) - Get started in 5 minutes
- [Documentation](docs/) - Full documentation
- [API Reference](docs/api.md) - Developer API (if applicable)
- [Contributing](#contributing) - How to contribute

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd llmXive-network-topology

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run the Full Pipeline

```bash
# Setup directories
python code/setup_directory_structure.py

# Run main pipeline
python code/main.py

# Generate final report
python code/reports/generate_report.py

# Validate report
python code/reports/validate_report.py
```

### Run Tests

```bash
pytest tests/
```

## Key Features

- **Structural Graph Metrics**: Global efficiency, clustering, modularity
- **Dynamic Functional States**: Sliding-window analysis, LOO K-Means
- **Structure-Function Correlation**: Pearson/Spearman with FDR correction
- **Robustness Analysis**: Window length, density, and tractography sensitivity
- **Associational Language Compliance**: Automated checking for causal language

## Data

This project uses real HCP data from OpenNeuro. No synthetic data is used.

## Methodological Notes

- **Leave-One-Out (LOO)**: Ensures statistical independence in centroid generation
- **Associational Framing**: All findings described as correlations, not causation
- **Tractography Sensitivity**: Addresses false-positive concerns (Yeh et al., 2018)

## Project Structure

```
.
├── code/ # Source code
├── data/ # Data storage
├── contracts/ # Schema definitions
├── tests/ # Test suite
├── docs/ # Documentation
├── requirements.txt # Dependencies
└── README.md # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes
4. Run tests
5. Submit a pull request

See [docs/quickstart.md](docs/quickstart.md) for detailed development setup.

## License

MIT License - see LICENSE file for details

## Acknowledgments

- HCP Consortium for open data
- Reviewer `john-von-neumann-simulated` for tractography sensitivity feedback
- llmXive automated science pipeline

## Contact

For questions, open an issue or contact the maintainers.
