# Data Lineage Report

## Source
- **Dataset**: Cyberbullying Survey 2021
- **Source ID**: 123
- **Provider**: UCI Machine Learning Repository
- **Fetch Method**: `ucimlrepo.fetch_dataset(dataset_id=123)`

## Transformations
1. **Ingestion**: Raw data loaded from UCI.
2. **Imputation**: MICE applied to predictors (age, gender, education, income, social_support, harassment_severity).
3. **Derivation**: `harassment_exposure` derived from `harassment_severity` (>0).
4. **Scoring**: CES-D, GAD-7, PCL-5 scores calculated per `config/scales.yaml`.
5. **Filtering**: Rows with missing outcomes removed.
6. **Validation**: Variance and VIF checks passed.

## Output
- `data/results/analysis_cohort.csv`
- `data/results/regression_results.csv`
- `data/results/sensitivity_analysis.csv`

## Verification
No synthetic data generation functions were called during this run.
