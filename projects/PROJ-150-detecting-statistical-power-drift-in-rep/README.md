# Detecting Statistical Power Drift in Replicated Studies

## Project Overview

This project implements a statistical pipeline to detect and quantify temporal drift in statistical power across replicated studies. Using the OSF Reproducibility Project dataset, we employ Linear Mixed-Effects Models (LMM) to analyze whether statistical power has changed over time, controlling for effect size and sample size.

## Methodology

The core analysis uses a Linear Mixed-Effects Model (LMM) with:
- **Fixed Effects**: `year`, `effect_size`, `sample_size`
- **Random Effects**: Random intercepts for `field` and `original_study_id`

The model tests the hypothesis that there is a significant temporal trend ($\beta_{year}$) in statistical power. A Likelihood-Ratio Test (LRT) compares the full model against a reduced model (excluding `year`) to determine significance.

For detailed methodology, see [docs/METHODOLOGY_LMM.md](docs/METHODOLOGY_LMM.md).

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Running the Full Pipeline

Execute the main pipeline script to download data, preprocess, fit models, and generate reports:

```bash
python code/main.py
```

### Individual Components

- **Data Download**: `python code/download.py`
- **Preprocessing**: `python code/preprocess.py`
- **Trend Analysis**: `python code/compute_trends.py`
- **Visualization**: `python code/visualize.py`
- **Robustness Checks**: `python code/robustness.py`

## Project Structure

```
.
├── code/ # Source code modules
│ ├── main.py # Pipeline orchestrator
│ ├── download.py # Data fetching
│ ├── preprocess.py # Data cleaning and validation
│ ├── compute_trends.py # LMM fitting and LRT
│ ├── visualize.py # Plotting residuals and trends
│ └── robustness.py # Permutation tests and sensitivity analysis
├── data/
│ ├── raw/ # Original downloaded data
│ └── derived/ # Processed data and intermediate results
├── results/ # Final outputs (summaries, plots)
├── docs/
│ └── METHODOLOGY_LMM.md # Detailed statistical methodology
├── tests/ # Test suites
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Key Outputs

- `results/lmm_final_summary.json`: Primary statistical results (slope, p-value, CI).
- `results/power_drift_scatter.png`: Visualization of residual power vs. year.
- `results/permutation_pvalue.json`: Empirical p-value from permutation test.
- `data/derived/residuals.csv`: Residual data for programmatic verification.

## Requirements

- Python 3.8+
- pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pyyaml, pytest, huggingface_hub

## License

This project is open source. See LICENSE for details.
