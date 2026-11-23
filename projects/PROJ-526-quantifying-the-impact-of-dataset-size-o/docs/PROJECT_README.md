# Project: Quantifying the Impact of Dataset Size on ML Accuracy for Material Properties

**Project ID**: PROJ-526
**Status**: Implementation Complete (Phases 1-5)
**Last Updated**: 2024-01-XX

## Overview

This project investigates how the size of training datasets affects the predictive accuracy of machine learning models for material properties. We analyze scaling laws (power-law relationships) across multiple material properties using composition-only descriptors (Magpie vectors).

## Key Findings Summary

- **Properties Analyzed**: 2-3 properties (Electronic and Mechanical classes) due to data availability constraints.
- **Methodology**:
 - Data retrieved from HuggingFace (Materials Project/AFLOW).
 - Magpie descriptors computed for composition-only features.
 - Learning curves generated using 5 subset sizes: [1000, 5000, 10000, 20000, 40000].
 - Power-law fitting applied with $R^2$ threshold of 0.9.
 - **Statistical Validation**: Permutation Test used for N<5 (amended from Kruskal-Wallis).
- **Amendments**: Formal amendments T035 and T036 ratified to adjust sample sizes (N=2-3) and statistical protocols.

## Project Structure

```
.
├── code/
│ ├── download_data.py # Fetches raw data from HuggingFace
│ ├── generate_descriptors.py # Computes Magpie vectors
│ ├── consolidate_data.py # Merges data into master parquet
│ ├── train_learning_curves.py # Trains models on varying subset sizes
│ ├── fit_scaling_laws.py # Fits power-law models
│ ├── analyze_physics.py # Computes physics metrics & permutation tests
│ ├── visualize_results.py # Generates plots
│ ├── generate_final_summary.py # Aggregates all results
│ ├── config.py # Configuration management
│ ├── models.py # Data models
│ └── utils/
│ ├── integrity.py # Checksum utilities
│ ├── seed.py # RNG seeding
│ └── logging_config.py # Logging setup
├── data/
│ ├── raw/ # Downloaded raw datasets
│ └── processed/
│ ├── materials_master.parquet
│ ├── scaling_results.csv
│ └── final_analysis.csv
├── tests/
│ ├── contract/ # Schema validation tests
│ ├── unit/ # Unit tests for logic
│ └── integration/ # Integration tests
├── state/
│ ├── amendments.md # Formal project amendments
│ └── properties_status.json # Property validation status
├── docs/
│ └── PROJECT_README.md # This file
├── requirements.txt # Python dependencies
└── README.md # Root entry point
```

## Prerequisites

- Python 3.10+
- Access to HuggingFace Hub (token required for some datasets)
- Sufficient disk space (~14GB recommended)

## Installation

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Set up environment variables (if required by `config.py`):
 ```bash
 export HF_TOKEN="your_huggingface_token"
 ```

## Execution Workflow

Run the pipeline in the following order:

1. **Data Acquisition & Descriptors**:
 ```bash
 python code/download_data.py
 python code/generate_descriptors.py
 python code/consolidate_data.py
 python code/validate_properties.py # Validates N >= 15 (or amended N)
 ```
2. **Learning Curves & Scaling**:
 ```bash
 python code/train_learning_curves.py
 python code/fit_scaling_laws.py
 ```
3. **Physics Analysis & Visualization**:
 ```bash
 python code/analyze_physics.py
 python code/visualize_results.py
 python code/generate_final_summary.py
 ```

## Output Artifacts

- `data/processed/materials_master.parquet`: Consolidated dataset with Magpie features.
- `data/processed/scaling_results.csv`: Scaling exponents and fit quality per property.
- `data/processed/final_analysis.csv`: Final summary including permutation test results.
- `figures/`: Generated plots (learning curves, heatmaps).

## Amendments & Constraints

- **T035**: Deviation from Constitution Principle VII (reduced subsets/seeds) due to data constraints.
- **T036**: Success Criterion SC-001 baseline modified to N=2-3; Permutation Test mandated for N<5.
- **FR-001**: Pipeline halts if distinct property count < 15 (unless amended).

## Contributing

Please refer to the `CONTRIBUTING.md` (if available) for guidelines.

## License

[Insert License Here]
