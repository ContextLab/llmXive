# The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

**Project ID**: PROJ-540

## Overview

This project investigates the relationship between frequent exposure to negative news on social media ("doomscrolling") and levels of anticipatory anxiety. Using public survey data, we employ statistical modeling (multiple linear regression) to estimate associations while controlling for baseline anxiety, age, and gender.

## Key Objectives

- **Primary**: Quantify the association between `news_exposure_freq` and `anxiety_score`.
- **Secondary**: Verify construct validity to ensure `baseline_anxiety` and `anxiety_score` are distinct measures.
- **Robustness**: Perform sensitivity analysis on high-engagement subsets of social media users.
- **Visualization**: Generate scatter plots with regression lines and 95% confidence intervals.

## Project Structure

```text
.
├── code/ # Core implementation logic
│ ├── config.py # Configuration, seeds, and environment handling
│ ├── ingest.py # Data download and schema validation
│ ├── clean.py # Data cleaning and power checks
│ ├── model.py # Regression and correlation analysis
│ ├── validity.py # Construct validity checks
│ ├── robustness.py # Sensitivity analysis logic
│ ├── viz.py # Visualization generation
│ ├── report_generator.py # Final report generation
│ └── exceptions.py # Custom exception definitions
├── data/
│ ├── raw/ # Downloaded raw dataset
│ └── processed/ # Cleaned analysis-ready data
├── outputs/
│ ├── analysis.log # Runtime logs
│ ├── regression_results.json
│ ├── correlation_results.json
│ ├── robustness_results.json
│ ├── plot.png # Visualization output
│ └── final_report.md # Generated findings
├── tests/ # Unit and integration tests
│ ├── test_ingest.py
│ ├── test_clean.py
│ ├── test_model.py
│ ├── test_validity.py
│ ├── test_robustness.py
│ └── test_viz.py
├── requirements.txt # Python dependencies
├── README.md # This file
└── docs/ # Additional documentation
```

## Setup and Installation

1. **Prerequisites**: Python 3.11+
2. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
3. **Configure Environment**:
 Ensure `config.yaml` (or environment variables) contains the dataset URL and a random seed for reproducibility.
 ```bash
 export DOOMSCROLL_SEED=42
 ```

## Execution Pipeline

Run the full analysis pipeline:

```bash
# 1. Ingest and Clean Data
python code/ingest.py
python code/clean.py

# 2. Statistical Modeling
python code/model.py

# 3. Robustness Checks
python code/robustness.py

# 4. Visualization
python code/viz.py

# 5. Generate Final Report
python code/report_generator.py
```

## Data Sources

This project utilizes public survey data (e.g., GSS, Pew Research) as configured in `config.py`. The data is downloaded automatically upon running the ingestion script.

## Methodology

- **Variables**:
 - Predictor: `news_exposure_freq` (Frequency of negative news exposure)
 - Outcome: `anxiety_score` (Anticipatory anxiety measure)
 - Controls: `baseline_anxiety`, `age`, `gender`
- **Model**: Multiple Linear Regression (OLS)
- **Validation**: Construct validity checks to prevent mathematical coupling; assumption checks (linearity, homoscedasticity, normality, VIF).
- **Robustness**: Conditional analysis on the top 25% of social media engagement.

## Reproducibility

All random seeds are explicitly set and logged at runtime (see `code/config.py`). The pipeline is deterministic given the same input data and configuration.

## License

This project is for research purposes. Data usage complies with the source provider's terms of service.
