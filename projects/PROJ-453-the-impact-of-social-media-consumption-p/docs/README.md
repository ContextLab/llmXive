# The Impact of Social Media Consumption Patterns on Cognitive Flexibility

## Project Overview
This research project investigates the relationship between social media consumption patterns (specifically platform switching) and cognitive flexibility using large-scale public survey datasets.

## Research Question
Does frequent switching between social media platforms correlate with reduced cognitive flexibility scores, independent of total screen time?

## Data Sources
- **HILDA (Household, Income and Labour Dynamics in Australia)**: Wave 20
- **ESS (European Social Survey)**: Round 10
- **AddHealth**: National Longitudinal Study of Adolescent to Adult Health

## Pipeline Structure
The analysis follows a strict four-phase pipeline:
1. **Feasibility Check**: Verify variable presence in datasets
2. **Ingestion & Engineering**: Download, clean, and derive variables
3. **Modeling**: Fit OLS models with diagnostics and sensitivity analysis
4. **Visualization**: Generate publication-ready figures

## Key Outputs
- `data/processed/participants_cleaned.csv`: Final analysis dataset
- `results/models/regression_summary.json`: Model coefficients and diagnostics
- `results/figures/regression_plot.png`: Primary visualization
- `results/final_report.json`: Comprehensive analysis report

## License
Open source research code.
