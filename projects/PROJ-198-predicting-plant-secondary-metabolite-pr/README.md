# llmXive: Predicting Plant Secondary Metabolite Profiles from Genomic Data

## Overview

This project implements an automated pipeline for predicting plant secondary metabolite
profiles using genomic data, cluster analysis, and phylogenetic modeling.

## Features

- **Data Alignment**: Automated download of genomic assemblies and metabolite tables
- **Feature Extraction**: AntiSMASH processing and BGC-metabolite mapping
- **Predictive Modeling**: PGLS, Random Forest, and Elastic Net with phylogenetic correction
- **Sensitivity Analysis**: Threshold robustness testing

## Quick Start

```bash
# Install dependencies
pip install -r code/requirements.txt

# Run data pipeline
python code/cli/main.py run-data-pipeline

# Run modeling pipeline
python code/cli/main.py run-modeling-pipeline

# Generate final report
python code/cli/main.py generate-report
```

## Project Structure

```
code/
├── cli/ # Command-line interface
├── data/ # Data download and preprocessing
├── modeling/ # Machine learning and phylogenetic models
├── utils/ # Utility functions
├── models/ # Pydantic schemas
└── scripts/ # Helper scripts

data/
├── raw/ # Raw downloaded data
├── interim/ # Intermediate processing results
└── processed/ # Final aligned datasets and reports

tests/
├── unit/ # Unit tests
└── integration/ # Integration tests
```

## Performance Optimization (T037)

The pipeline automatically applies PCA dimensionality reduction before PGLS
modeling when the number of features exceeds the number of samples, preventing
overfitting in high-dimensional regimes.

## License

MIT License
