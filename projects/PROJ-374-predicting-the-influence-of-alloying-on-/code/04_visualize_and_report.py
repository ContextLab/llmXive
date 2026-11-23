import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports if running as script
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from utils.periodic_data import get_element
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor

def load_model_output(filepath):
    """Load model output JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def load_features(filepath):
    """Load engineered features CSV."""
    return pd.read_csv(filepath)

def calculate_vif(df, feature_cols):
    """Calculate Variance Inflation Factor for given features."""
    X = df[feature_cols].dropna()
    if len(X) == 0:
        return {col: np.nan for col in feature_cols}
    
    vif_data = {}
    for i, col in enumerate(feature_cols):
        if col in X.columns:
            try:
                vif = variance_inflation_factor(X.values, i)
                vif_data[col] = vif
            except Exception:
                vif_data[col] = np.nan
        else:
            vif_data[col] = np.nan
    return vif_data

def compute_correlation_matrix(df, feature_cols, target_col):
    """Compute Pearson correlation matrix."""
    relevant_cols = feature_cols + [target_col]
    available_cols = [c for c in relevant_cols if c in df.columns]
    if len(available_cols) < 2:
        return {}
    
    corr_matrix = df[available_cols].corr()
    return corr_matrix.to_dict()

def get_top_descriptors(correlation_dict, target_col, n=5):
    """Get top N descriptors by absolute correlation with target."""
    correlations = []
    for col, val in correlation_dict.items():
        if col != target_col and target_col in val:
            corr_val = val[target_col]
            correlations.append((col, corr_val))
    
    correlations.sort(key=lambda x: abs(x[1]), reverse=True)
    return correlations[:n]

def generate_scatter_plots(df, top_descs, target_col, output_dir):
    """Generate scatter plots for top descriptors."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for i, (col, corr_val) in enumerate(top_descs):
        if col not in df.columns or target_col not in df.columns:
            continue
        
        plt.figure(figsize=(8, 6))
        plt.scatter(df[col], df[target_col], alpha=0.6, s=20)
        
        # Add trend line
        m, b = np.polyfit(df[col].dropna(), df[target_col].dropna(), 1)
        x_vals = np.linspace(df[col].min(), df[col].max(), 100)
        plt.plot(x_vals, m*x_vals + b, 'r-', linewidth=2, label=f'Trend (r={corr_val:.3f})')
        
        plt.xlabel(col)
        plt.ylabel(target_col)
        plt.title(f'{col} vs {target_col}')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        filename = f"descriptor_{i+1}_vs_{target_col}.png"
        plt.savefig(output_path / filename, dpi=150, bbox_inches='tight')
        plt.close()

def classify_result(r2_score):
    """Classify result based on R² score."""
    if r2_score > 0.4:
        return "Success"
    elif r2_score >= 0.2:
        return "Inconclusive"
    else:
        return "Failure"

def generate_report(model_output, features_df, output_path):
    """Generate the final report markdown."""
    r2 = model_output.get('r2_score', 0.0)
    ci_lower = model_output.get('ci_lower', 0.0)
    ci_upper = model_output.get('ci_upper', 0.0)
    p_value = model_output.get('p_value', 1.0)
    f_stat = model_output.get('f_statistic', 0.0)
    f_p_value = model_output.get('f_p_value', 1.0)
    feature_importances = model_output.get('feature_importances', [])
    
    classification = classify_result(r2)
    significance = "Significant" if p_value < 0.05 else "Not Significant"
    
    # Calculate correlations for top descriptors
    feature_cols = [item['feature'] for item in feature_importances]
    corr_matrix = compute_correlation_matrix(features_df, feature_cols, 'Seebeck_uV_mK')
    top_descs = get_top_descriptors(corr_matrix, 'Seebeck_uV_mK', n=5)
    
    report_lines = [
        "# Predicting the Influence of Alloying on the Seebeck Coefficient",
        "",
        "## Summary of Results",
        "",
        f"**Model Performance:**",
        f"- R² Score: {r2:.4f}",
        f"- 95% Confidence Interval: [{ci_lower:.4f}, {ci_upper:.4f}]",
        f"- P-value (Permutation Test): {p_value:.4e}",
        f"- Significance: {significance}",
        "",
        f"**Model Comparison (F-Test):**",
        f"- F-statistic: {f_stat:.4f}",
        f"- F-test P-value: {f_p_value:.4e}",
        "",
        f"**Classification:** {classification}",
        "",
        "## Top Descriptors",
        "",
        "The following descriptors showed the strongest correlation with the Seebeck coefficient:",
        ""
    ]
    
    for i, (col, corr_val) in enumerate(top_descs, 1):
        report_lines.append(f"{i}. **{col}**: r = {corr_val:.4f}")
    
    report_lines.extend([
        "",
        "## Feature Importances",
        "",
        "Ranked feature importances from the trained Gradient Boosting model:",
        ""
    ])
    
    for i, item in enumerate(feature_importances, 1):
        report_lines.append(f"{i}. **{item['feature']}**: {item['importance']:.4f}")
    
    report_lines.extend([
        "",
        "## Methodology",
        "",
        "- **Dataset**: Public thermoelectric database (DOI: 10.1038/sdata.2017.85)",
        "- **Families**: Bi-Te, Pb-Te, Skutterudites",
        "- **Model**: Gradient Boosting Regressor (n_estimators=100, max_depth=3)",
        "- **Validation**: Cross-validation with 5 folds",
        "- **Significance Testing**: Permutation test (1000 iterations)",
        "",
        "## Conclusion",
        "",
        f"The model {'successfully' if classification == 'Success' else 'shows inconclusive results' if classification == 'Inconclusive' else 'failed to'} predict the Seebeck coefficient based on compositional descriptors.",
        f"The results are {'statistically significant' if significance == 'Significant' else 'not statistically significant'} (p < 0.05).",
        ""
    ])
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

def main():
    """Main entry point for visualization and reporting."""
    project_root = Path(__file__).parent.parent
    model_output_path = project_root / 'data' / 'processed' / 'model_output.json'
    features_path = project_root / 'data' / 'processed' / 'final_features.csv'
    report_path = project_root / 'docs' / 'report.md'
    figures_path = project_root / 'docs' / 'figures'
    
    # Load data
    if not model_output_path.exists():
        print(f"Error: Model output file not found at {model_output_path}", file=sys.stderr)
        sys.exit(1)
    
    model_output = load_model_output(model_output_path)
    
    if not features_path.exists():
        print(f"Error: Features file not found at {features_path}", file=sys.stderr)
        sys.exit(1)
    
    features_df = load_features(features_path)
    
    # Generate report
    generate_report(model_output, features_df, report_path)
    print(f"Report generated at {report_path}")
    
    # Generate plots
    feature_cols = [item['feature'] for item in model_output.get('feature_importances', [])]
    top_descs = get_top_descriptors(
        compute_correlation_matrix(features_df, feature_cols, 'Seebeck_uV_mK'),
        'Seebeck_uV_mK',
        n=3
    )
    generate_scatter_plots(features_df, top_descs, 'Seebeck_uV_mK', figures_path)
    print(f"Plots generated in {figures_path}")

if __name__ == '__main__':
    main()
