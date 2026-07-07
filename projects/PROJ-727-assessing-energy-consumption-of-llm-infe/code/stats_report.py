"""
T025: Write stats_report.csv containing ANOVA table, Tukey results,
regression coefficients, and sensitivity findings.

This script aggregates results from the statistical analysis pipeline
into a single CSV report file as required by FR-005 and FR-012.
"""
import os
import csv
import pandas as pd
from code.analysis import load_data, run_anova, run_tukey, run_regression
from code.sensitivity_analysis import run_sensitivity_analysis
from code.config import DATA_PROCESSED_DIR

def format_statistic(value):
    """Format float values, handling None/NaN gracefully."""
    if value is None:
        return ""
    if isinstance(value, float):
        if pd.isna(value):
            return ""
        return f"{value:.6f}"
    return str(value)

def write_stats_report():
    """
    Generate stats_report.csv with all statistical findings.
    
    Output: data/processed/stats_report.csv
    Columns: metric, model_or_group, value, note
    """
    input_file = os.path.join(DATA_PROCESSED_DIR, "energy_results_aggregated.csv")
    output_file = os.path.join(DATA_PROCESSED_DIR, "stats_report.csv")
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(
            f"Input file not found: {input_file}. "
            "Run the analysis pipeline first."
        )
    
    # Load data
    df = load_data(input_file)
    
    # Run analyses
    anova_result = run_anova(df)
    tukey_result = run_tukey(df)
    regression_result = run_regression(df)
    sensitivity_result = run_sensitivity_analysis(df)
    
    # Prepare rows for the report
    rows = []
    
    # ANOVA Results
    if anova_result:
        rows.append({
            "metric": "ANOVA_F_value",
            "model_or_group": "model_id",
            "value": format_statistic(anova_result.get("F", "")),
            "note": "Repeated-measures ANOVA F-statistic"
        })
        rows.append({
            "metric": "ANOVA_p_value",
            "model_or_group": "model_id",
            "value": format_statistic(anova_result.get("p", "")),
            "note": "Repeated-measures ANOVA p-value"
        })
        if "df_model" in anova_result:
            rows.append({
                "metric": "ANOVA_df_model",
                "model_or_group": "model_id",
                "value": format_statistic(anova_result.get("df_model", "")),
                "note": "ANOVA model degrees of freedom"
            })
        if "df_resid" in anova_result:
            rows.append({
                "metric": "ANOVA_df_resid",
                "model_or_group": "model_id",
                "value": format_statistic(anova_result.get("df_resid", "")),
                "note": "ANOVA residual degrees of freedom"
            })
    
    # Tukey HSD Results
    if tukey_result:
        for i, (comparison, res) in enumerate(tukey_result.items()):
            group1, group2 = comparison
            rows.append({
                "metric": "Tukey_diff",
                "model_or_group": f"{group1} vs {group2}",
                "value": format_statistic(res.get("meandiff", "")),
                "note": "Mean difference in energy per token"
            })
            rows.append({
                "metric": "Tukey_p_adj",
                "model_or_group": f"{group1} vs {group2}",
                "value": format_statistic(res.get("p-adj", "")),
                "note": "Tukey adjusted p-value"
            })
            rows.append({
                "metric": "Tukey_conf_low",
                "model_or_group": f"{group1} vs {group2}",
                "value": format_statistic(res.get("p-adj", "")),
                "note": f"Lower bound of {res.get('p-adj', '95%')} CI"
            })
            rows.append({
                "metric": "Tukey_conf_high",
                "model_or_group": f"{group1} vs {group2}",
                "value": format_statistic(res.get("p-adj", "")),
                "note": f"Upper bound of {res.get('p-adj', '95%')} CI"
            })
    
    # Regression Results
    if regression_result:
        rows.append({
            "metric": "Regression_slope",
            "model_or_group": "parameter_count",
            "value": format_statistic(regression_result.get("slope", "")),
            "note": "Slope of energy/token vs parameter count"
        })
        rows.append({
            "metric": "Regression_intercept",
            "model_or_group": "parameter_count",
            "value": format_statistic(regression_result.get("intercept", "")),
            "note": "Intercept of linear regression"
        })
        rows.append({
            "metric": "Regression_r_squared",
            "model_or_group": "parameter_count",
            "value": format_statistic(regression_result.get("r_squared", "")),
            "note": "R-squared of linear fit"
        })
        if "p_value" in regression_result:
            rows.append({
                "metric": "Regression_p_value",
                "model_or_group": "parameter_count",
                "value": format_statistic(regression_result.get("p_value", "")),
                "note": "P-value for slope coefficient"
            })
    
    # Sensitivity Analysis Results
    if sensitivity_result:
        rows.append({
            "metric": "Sensitivity_original_p",
            "model_or_group": "ANOVA",
            "value": format_statistic(sensitivity_result.get("original_p", "")),
            "note": "Original ANOVA p-value"
        })
        rows.append({
            "metric": "Sensitivity_perturbed_p",
            "model_or_group": "ANOVA",
            "value": format_statistic(sensitivity_result.get("perturbed_p", "")),
            "note": "Perturbed ANOVA p-value (±10% energy)"
        })
        rows.append({
            "metric": "Sensitivity_delta_p",
            "model_or_group": "ANOVA",
            "value": format_statistic(sensitivity_result.get("delta_p", "")),
            "note": "Difference in p-values"
        })
        rows.append({
            "metric": "Sensitivity_robust",
            "model_or_group": "ANOVA",
            "value": sensitivity_result.get("robust", ""),
            "note": "True/False: Is result robust to perturbation?"
        })
    
    # Write to CSV
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    with open(output_file, 'w', newline='') as f:
        fieldnames = ["metric", "model_or_group", "value", "note"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Stats report written to: {output_file}")
    return output_file

def main():
    """Entry point for T025."""
    write_stats_report()

if __name__ == "__main__":
    main()
