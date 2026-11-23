# PROJ-526: Quantifying the Impact of Dataset Size on ML Accuracy

**Automated Science Pipeline Implementation**

This repository contains the implementation for quantifying how dataset size impacts machine learning accuracy for material properties. It follows a rigorous scientific pipeline including data acquisition, descriptor generation, learning curve analysis, and statistical validation.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the full pipeline
python code/download_data.py
python code/generate_descriptors.py
python code/consolidate_data.py
python code/validate_properties.py
python code/train_learning_curves.py
python code/fit_scaling_laws.py
python code/analyze_physics.py
python code/visualize_results.py
python code/generate_final_summary.py
```

## Documentation

For detailed documentation, see [`docs/PROJECT_README.md`](docs/PROJECT_README.md).

## Key Results

- **Scaling Exponents**: Extracted from power-law fits for each property.
- **Statistical Significance**: Determined via Permutation Test (N<5 protocol).
- **Data Availability**: 2-3 properties analyzed (amended from target of 15).

## Project Status

- **Phase 1 (Setup)**: Complete
- **Phase 2 (Foundational)**: Complete (Amendments T035, T036 ratified)
- **Phase 3 (US1 - Data)**: Complete
- **Phase 4 (US2 - Learning Curves)**: Complete
- **Phase 5 (US3 - Analysis)**: Complete
- **Phase N (Polish)**: Complete

## Notes on Amendments

Due to data availability constraints (N=2-3 properties), the project operates under formal amendments:
- **T035**: Reduced subsets/seeds (5x1 instead of 10x3).
- **T036**: Statistical protocol updated to Permutation Test for small N.
