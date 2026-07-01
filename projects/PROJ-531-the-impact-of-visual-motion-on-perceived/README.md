# The Impact of Visual Motion on Perceived Agency in Virtual Interactions

## ⚠️ Project Scope & Ethics Declaration

**This project is strictly a synthetic data stress-test. No human participants are involved. No claims of human perception validation are made. Real data path is disabled due to unavailability.**

This declaration is referenced in all downstream tasks and analysis outputs to ensure strict adherence to ethical guidelines and project scope.

## Overview

This research pipeline investigates the relationship between visual motion characteristics (latency, smoothness, lead time) and perceived agency in virtual avatar interactions. Due to the unavailability of real human participant data, this project utilizes a validated synthetic data generator to stress-test the analysis pipeline.

## Key Features

- Synthetic data generation with known ground-truth motion-agency relationships
- Robust preprocessing pipeline with VIF diagnostics
- Multiple statistical modeling approaches (OLS, Ridge, Random Forest)
- Sensitivity analysis for threshold robustness
- Automated visualization and interpretation

## Project Structure

```
.
├── code/ # Implementation modules
│ ├── data/ # Data acquisition and generation
│ ├── modeling/ # Statistical models and analysis
│ ├── preprocessing/ # Data cleaning and feature engineering
│ ├── visualization/ # Plot generation
│ └── utils/ # Configuration and logging
├── data/
│ ├── raw/ # Raw downloaded/generated data
│ └── processed/ # Cleaned, analysis-ready data
├── docs/ # Documentation
│ └── scope.md # Detailed scope and ethics declaration
├── specs/ # Feature specifications and contracts
├── tests/ # Test suite
└── requirements.txt # Python dependencies
```

## Quick Start

1. **Setup Environment**
 ```bash
 pip install -r requirements.txt
 ```

2. **Generate Synthetic Data**
 ```bash
 python code/data/generate_synthetic_data.py
 ```

3. **Preprocess Data**
 ```bash
 python code/preprocessing/output_cleaned_data.py
 ```

4. **Run Analysis**
 ```bash
 python code/modeling/model_fitting.py
 ```

5. **Generate Visualizations**
 ```bash
 python code/visualization/plots.py
 ```

## Ethics & Limitations

- **Synthetic Data Only**: All data used in this project is synthetically generated. No real human participants were involved.
- **No Human Validation**: Results are not claims of human perception validation.
- **Stress-Test Purpose**: The primary goal is to validate the analysis pipeline, not to draw conclusions about human behavior.
- **Real Data Disabled**: The real data acquisition path is disabled due to unavailability.

For detailed scope information, see [docs/scope.md](docs/scope.md).

## References

- Feature Requirements: `specs/001-visual-motion-agency/`
- Data Schema: `specs/001-visual-motion-agency/contracts/dataset.schema.yaml`
- Analysis Output Schema: `specs/001-visual-motion-agency/contracts/analysis_output.schema.yaml`

## License

This project is for research purposes only.
