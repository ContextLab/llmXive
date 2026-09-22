# The Impact of Perceived Social Support on Resilience to Online Harassment

This project implements a rigorous statistical analysis of the relationship between perceived social support and resilience to online harassment, using data from the Cyberbullying Survey 2021.

## Methodological Approach

This analysis strictly follows the **Revised Approach (Single-Dataset Analysis)** as mandated by the project plan.
- **Data Source**: Cyberbullying Survey 2021 (UCI ID: 123).
- **Exclusion**: The GSS 2022 dataset is explicitly excluded due to methodological invalidity in matching synthetic cohorts.
- **Goal**: Estimate the buffering effect of social support on harassment severity without confounding by dataset source.

## Prerequisites

- Python 3.9+
- Required packages (install via `pip install -r requirements.txt`):
 - `ucimlrepo` (for data fetching)
 - `pandas`, `numpy`, `scikit-learn`, `statsmodels`
 - `pyyaml`, `logging`
- A stable internet connection to fetch the real dataset.

## Data Sources

- **Primary Dataset**: Cyberbullying Survey 2021
 - Source: UCI Machine Learning Repository
 - Fetch Method: `ucimlrepo.fetch_dataset(dataset_id=123)`
 - Verification: The pipeline includes a strict "Fail Loudly" check. If the real data cannot be fetched, the pipeline aborts to prevent synthetic data fabrication.

## How to Run the Pipeline

1. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Verify Data Source (Optional but Recommended)**:
 ```bash
 python code/data/verify_source.py
 ```

3. **Run the Full Pipeline**:
 ```bash
 python code/main_pipeline.py
 ```
 This will execute:
 - Data Ingestion (T012)
 - Preprocessing & Imputation (T013)
 - Cohort Construction & Validation (T014-T016)
 - Interaction Modeling & Bootstrapping (T020-T024)
 - Sensitivity Analysis (T027-T029)
 - Reporting & Validation (T025, T060, T063, T064)

4. **Validate Outputs**:
 ```bash
 python code/quickstart_validator.py
 ```

## Expected Outputs

All outputs are generated in the `data/results/` directory:

- `analysis_cohort.csv`: The cleaned, validated dataset ready for analysis.
- `validation_report.json`: Checks for variance and VIF.
- `platform_status.json`: Verification of the `platform` column (T070b).
- `regression_results.csv`: Coefficients, SEs, p-values, and bootstrap CIs.
- `sensitivity_analysis.csv`: Results from continuous severity and platform stratification models.
- `regression_summary.md`: Human-readable interpretation of the findings.
- `data_lineage_report.md`: Trace of data transformations.
- `reproducibility_audit.json`: Hash verification of stochastic components.
- `performance_report.json`: Runtime metrics.
- `lint_report.txt` & `test_report.txt`: Code quality and test results.

## Project Structure

```
.
├── code/
│ ├── data/ # Ingestion, preprocessing, cohort building
│ ├── analysis/ # Models, bootstrapping, sensitivity, results
│ ├── config/ # YAML configurations (scales, seeds, bootstrap)
│ ├── main_pipeline.py
│ └──...
├── data/
│ ├── raw/ # Downloaded raw data
│ └── results/ # Generated outputs
├── tests/ # Unit and contract tests
├── requirements.txt
└── README.md
```

## License

This project is for research purposes.
