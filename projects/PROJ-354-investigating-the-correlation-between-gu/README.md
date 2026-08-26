# Gut Microbiome-Cognitive Correlation Study

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This project investigates the correlation between gut microbiome composition (16S rRNA sequencing data) and cognitive assessment scores using UK Biobank data. The analysis employs rigorous statistical methods including Isometric Log-Ratio (ILR) transformation for compositional data, Lasso/Ridge regularized linear models, and comprehensive sensitivity analyses.

## Key Features

- **Streaming Data Processing**: Handles >14GB datasets within 7GB RAM constraints [UNRESOLVED-CLAIM: c_de95c116 — status=not_enough_info]
- **Compositional Data Analysis**: Bayesian-multiplicative zero-replacement and ILR transformation
- **Regularized Regression**: Lasso and Ridge models with confounder control
- **Multiple Testing Correction**: Benjamini-Hochberg procedure
- **Sensitivity Analysis**: Over-control bias, threshold sweeps, model comparison
- **Validation Gates**: Power analysis and citation validation before proceeding

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure UK Biobank token
export UK_BIOBANK_TOKEN="your_token_here"

# Run the pipeline
python code/download.py
python code/preprocess.py
python code/analysis.py
python code/visualize.py

# Run tests
pytest tests/
```

For detailed instructions, see [quickstart.md](quickstart.md).

## Project Structure

```
.
├── code/ # Core implementation
├── data/ # Data storage
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Processed data
├── results/ # Analysis results
│ ├── associations/ # Statistical results
│ ├── plots/ # Visualizations
│ ├── sensitivity/ # Sensitivity analysis
│ ├── power/ # Power analysis
│ └── validation/ # Validation reports
├── tests/ # Test suite
├── docs/ # Documentation
├── requirements.txt # Dependencies
└── quickstart.md # Quick start guide
```

## Methodology

1. **Data Download**: Streaming fetch from UK Biobank with checksumming
2. **Preprocessing**:
 - Cohort filtering (antibiotic exclusion, missing data)
 - Bayesian-multiplicative zero-replacement (alpha=1e-6)
 - Genus-level aggregation
 - ILR transformation
3. **Statistical Analysis**:
 - Regularized linear models (Lasso/Ridge)
 - Confounder adjustment (age, sex, BMI, diet, activity, medication)
 - Benjamini-Hochberg correction
 - Age-interaction analysis
4. **Sensitivity Analysis**:
 - Over-control bias assessment
 - Threshold sweep analysis
 - Model selection comparison

## Validation Gates

- **Power Gate**: Ensures study is adequately powered (power >= 0.8)
- **Citation Gate**: Validates cognitive instrument citations
- **Data Integrity**: Checksumming and PII masking throughout

## Documentation

- [Quick Start Guide](quickstart.md) - Getting started
- [API Reference](docs/API.md) - Module documentation
- [Project Documentation](docs/README.md) - Detailed methodology

## Requirements

See [requirements.txt](requirements.txt) for full dependency list.

## License

MIT License - see LICENSE file for details.

## Contributing

See CONTRIBUTING.md for development guidelines.