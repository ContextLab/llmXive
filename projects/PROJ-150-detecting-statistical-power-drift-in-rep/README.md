# Detecting Statistical Power Drift in Replicated Studies (PROJ-150)

**Project ID**: PROJ-150-detecting-statistical-power-drift-in-rep
**Status**: Implemented
**Primary Goal**: Quantify temporal decline in statistical power across replicated studies using Linear Mixed-Effects Models (LMM).

## Overview

This pipeline analyzes the "OSF Reproducibility Project" dataset to detect whether statistical power in replicated studies has drifted over time. It implements a robust statistical workflow involving:
1. **Data Ingestion**: Fetching real data from the OSF/HuggingFace repository.
2. **Preprocessing**: Cleaning, filtering, and validating grouping variables.
3. **Residualization**: Removing deterministic effects of sample size and effect size via a Pilot OLS model.
4. **LMM Analysis**: Fitting a Full Linear Mixed-Effects Model (`power_residual ~ year + (1|field) + (1|original_study_id)`) to estimate the drift slope.
5. **Robustness Checks**: Permutation tests and sensitivity analysis.
6. **Cross-Field Aggregation**: Combining evidence across disciplines using DerSimonian-Laird weighting.

## Project Structure

```text
PROJ-150-detecting-statistical-power-drift-in-rep/
├── code/ # Implementation modules
│ ├── download.py # Data fetcher (OSF/HuggingFace)
│ ├── preprocess.py # Cleaning and grouping validation
│ ├── models.py # OLS Pilot and LMM fitting logic
│ ├── robustness.py # Permutation tests & aggregation
│ ├── visualize.py # Plotting residuals and distributions
│ ├── main.py # Pipeline orchestrator
│ └──...
├── data/
│ ├── raw/ # Raw downloaded data (excluded from git)
│ └── derived/ # Cleaned data and intermediate artifacts
├── results/ # Final outputs (JSON summaries, PNG plots)
├── state/ # Project state tracking (SHA-256 hashes)
├── tests/ # Unit and integration tests
└── README.md
```

## Prerequisites

- Python 3.9+
- `pip` for dependency management
- Network access to fetch the OSF dataset (HuggingFace)

## Installation

1. Clone the repository and navigate to the project directory.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

**Required Dependencies**:
- `pandas`, `numpy`, `scipy` (Data processing)
- `statsmodels`, `scikit-learn` (Statistical modeling)
- `matplotlib`, `seaborn` (Visualization)
- `huggingface_hub` (Data fetching)
- `pyyaml` (State management)
- `pytest` (Testing)

## Usage

### Running the Full Pipeline

To execute the entire analysis from data fetch to final report:

```bash
python code/main.py
```

This will:
1. Download the dataset to `data/raw/`.
2. Clean and validate data, saving to `data/derived/`.
3. Fit the Pilot OLS and Full LMM models.
4. Run robustness checks (permutation, sensitivity).
5. Generate visualizations and JSON reports in `results/`.

### Running Specific Modules

- **Download Data**: `python code/download.py`
- **Preprocess Data**: `python code/preprocess.py`
- **Fit Models**: `python code/models.py`
- **Run Robustness**: `python code/robustness.py`
- **Generate Plots**: `python code/visualize.py`

### Running Tests

```bash
pytest tests/ -v
```

## Methodology Summary

1. **Power Calculation**: Post-hoc power is estimated for each study based on reported effect sizes and sample sizes.
2. **Residualization**: A Pilot OLS model (`power ~ effect_size + sample_size`) removes the deterministic relationship between power and its inputs. The residuals (`power_residual`) represent the unexplained variance in power.
3. **Drift Detection**: A Linear Mixed-Effects Model (LMM) is fitted:
 `power_residual ~ year + (1|field) + (1|original_study_id)`
 - **Fixed Effect**: `year` (The primary drift metric is the slope coefficient).
 - **Random Effects**: Intercepts for `field` and `original_study_id` to account for hierarchical structure.
4. **Validation**:
 - **Likelihood Ratio Test (LRT)**: Compares the Full LMM against a reduced model (without `year`).
 - **Permutation Test**: Shuffles `year` labels to generate a null distribution.
 - **Cross-Field Aggregation**: Uses DerSimonian-Laird weighting to combine slopes across fields.

## Output Artifacts

Upon successful completion, the following files are generated:

- `results/lmm_final_summary.json`: Primary drift metrics (slope, SE, CI, LRT p-value).
- `results/power_drift_scatter.png`: Visualization of residual power vs. year.
- `results/permutation_pvalue.json`: Empirical p-value from permutation test.
- `results/aggregated_drift.json`: Cross-field aggregated drift estimate.
- `data/derived/cleaned_data.csv`: Filtered dataset ready for analysis.
- `data/derived/residuals.csv`: Residualized power values.

## Data Integrity

- **Real Data Only**: This pipeline fetches the `osf/reproducibility_project` dataset directly from HuggingFace. No synthetic data is generated.
- **Fail Loudly**: If the data source is unreachable, the pipeline raises a `DataFetchError` and halts.

## License

Internal Research Project - All rights reserved.