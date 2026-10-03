# Testing the Equivalence Principle with Satellite Laser Ranging

**Project ID**: PROJ-752-testing-the-equivalence-principle-with-s

## Overview

This project implements a scientific pipeline to test the Weak Equivalence Principle (WEP) using Satellite Laser Ranging (SLR) data from multiple satellites (LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, Starlette). The pipeline estimates the Eötvös parameter ($\eta$) by analyzing differential accelerations between satellites with different compositions.

## Scientific Goal

To constrain the Eötvös parameter $\eta = \frac{|a_1 - a_2|}{g}$ to precision levels competitive with state-of-the-art benchmarks (currently $< 10^{-13}$) using ground-based SLR observations.

## Pipeline Architecture

The pipeline is organized into the following phases:

1. **Phase 1: Setup** - Project initialization and dependency management
2. **Phase 2: Research Prerequisites** - Benchmark identification and configuration gating
3. **Phase 3: Foundational** - Core infrastructure (schemas, models, config)
4. **Phase 4: User Story 1** - Data Ingestion and Pre-processing
5. **Phase 5: User Story 2** - Differential Acceleration Parameter Estimation
6. **Phase 6: User Story 3** - Statistical Validation and Robustness Analysis
7. **Phase 7: User Story 4** - Feasibility and Resource Validation

## Quick Start

### Prerequisites

- Python 3.9+
- Required system packages: `build-essential`, `libffi-dev`

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-752-testing-the-equivalence-principle-with-s

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running the Pipeline

The main entry point is `code/cli/main.py`:

```bash
python code/cli/main.py --config config.yaml
```

To run specific stages:

```bash
# Run data ingestion
python code/scripts/run_ingestion_pipeline.py

# Run validation
python code/scripts/validate_quickstart.py
```

## Directory Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Statistical analysis modules
│ ├── cli/ # Command-line interface
│ ├── data/ # Data ingestion and preprocessing
│ ├── dynamics/ # Dynamical models
│ ├── models/ # Data models and estimators
│ ├── utils/ # Utility functions
│ └── scripts/ # Pipeline scripts
├── data/ # Data artifacts
│ ├── raw/ # Raw SLR data
│ ├── processed/ # Cleaned and aligned data
│ └── results/ # Analysis results and plots
├── docs/ # Documentation
├── tests/ # Test suite
├── contracts/ # Schema definitions
├── config.yaml # Configuration file
└── requirements.txt # Dependencies
```

## Key Components

### Data Ingestion (`code/data/ingestion.py`)
- Fetches SLR normal point data from ILRS archive
- Parses raw files into `NormalPoint` objects
- Aggregates data across multiple satellites

### Preprocessing (`code/data/preprocessing.py`)
- Filters residuals > 2cm [UNRESOLVED-CLAIM: c_779ef0eb — status=not_enough_info]
- Handles sparse satellites
- Aligns time series across satellites

### Dynamics Model (`code/models/dynamics.py`)
- Implements GGM geopotential (GGM05C)
- Jacchia drag model
- Solar Radiation Pressure (SRP)
- Relativistic corrections (Schwarzschild, Lense-Thirring)

### Estimator (`code/models/estimator.py`)
- Separate least-squares fit for each satellite (Primary)
- Joint least-squares fit (Comparison)
- Extracts differential acceleration $a_c$

### Eötvös Analysis (`code/analysis/eotvos.py`)
- Computes $\eta = |a_c| / g$
- Calculates 95% confidence intervals
- Performs sensitivity sweeps across geopotential models

### Validation (`code/analysis/validation.py`)
- F-test and BIC model comparison
- Bonferroni/Holm-Bonferroni/Benjamini-Hochberg corrections
- Sensitivity analysis across geopotential models

## Output Artifacts

- `data/processed/cleaned_slr_data.csv` - Preprocessed SLR data
- `data/results/orbit_solutions.json` - Fitted orbit parameters
- `data/results/eotvos_metrics.json` - Eötvös parameter estimates
- `data/results/sensitivity_analysis.png` - Sensitivity sweep visualization
- `data/results/feasibility_gap_report.json` - Data availability report

## Configuration

The `config.yaml` file controls all pipeline parameters:

```yaml
paths:
 data_raw: data/raw
 data_processed: data/processed
 data_results: data/results

benchmark_values:
 etvos_limit: 1.0e-13 # State-of-the-art precision target
 citation: "DOI:10.xxxx/xxxxx"

hyperparams:
 residual_threshold_cm: 2.0
 min_arc_length_days: 30
 convergence_tolerance: 1e-8
```

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Key test modules:
- `tests/test_ingestion.py` - URL validation and retry logic
- `tests/test_preprocessing.py` - Quality filtering
- `tests/test_estimator.py` - Solver convergence
- `tests/test_validation.py` - F-test and BIC logic
- `tests/test_sensitivity.py` - Geopotential sensitivity

## Constraints and Limitations

- **Memory**: Pipeline exits if RSS > 6GB (GitHub Actions free-tier constraint) [UNRESOLVED-CLAIM: c_0ffae6a6 — status=not_enough_info]
- **Time**: Pipeline exits if runtime > 6 hours [UNRESOLVED-CLAIM: c_5a07d691 — status=not_enough_info]
- **Data**: Uses real ILRS archive data; no synthetic fallbacks
- **Compute**: CPU-only execution (no GPU dependencies)

## References

1. ILRS (International Laser Ranging Service) - Network is unreachable"))]
2. Murphy, T. W. (2009). "Lunar Laser Ranging: The Millimeter Challenge"
3. Williams, J. G., et al. (2004). "Lunar Laser Ranging Tests of the Equivalence Principle"

## License

This project is for scientific research purposes.

## Contact

For questions, please refer to the project documentation or open an issue.
