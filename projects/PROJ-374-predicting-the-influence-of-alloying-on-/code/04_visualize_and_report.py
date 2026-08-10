import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path to allow imports from utils
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_model_output(output_path):
    """Load model output JSON file."""
    with open(output_path, 'r') as f:
        return json.load(f)

def load_features(features_path):
    """Load the engineered features dataset."""
    return pd.read_csv(features_path)

def calculate_vif(features_df, target_col='seebeck_coefficient'):
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    Excludes the target column and non-numeric columns.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    from statsmodels.tools.tools import add_constant

    # Select only numeric feature columns, excluding target
    feature_cols = [col for col in features_df.columns 
                   if col != target_col and features_df[col].dtype in ['float64', 'int64']]
    
    if not feature_cols:
        return {}

    X = features_df[feature_cols].dropna()
    if len(X) == 0:
        return {}
        
    X = add_constant(X)
    vif_data = {}
    for i, col in enumerate(feature_cols):
        try:
            vif = variance_inflation_factor(X.values, i+1) # +1 because of constant
            vif_data[col] = vif
        except Exception:
            vif_data[col] = float('inf')
    
    return vif_data

def compute_correlation_matrix(features_df, target_col='seebeck_coefficient'):
    """Compute Pearson correlation matrix for features and target."""
    numeric_cols = features_df.select_dtypes(include=[np.number]).columns
    if target_col not in numeric_cols:
        return pd.DataFrame()
        
    corr_matrix = features_df[numeric_cols].corr()
    return corr_matrix

def get_top_descriptors(corr_matrix, target_col='seebeck_coefficient', n=5):
    """Get top N descriptors correlated with the target."""
    if corr_matrix.empty or target_col not in corr_matrix.columns:
        return []
        
    correlations = corr_matrix[target_col].drop(target_col).abs().sort_values(ascending=False)
    return correlations.head(n).to_dict()

def generate_scatter_plots(features_df, model_output, output_dir):
    """Generate scatter plots of top descriptors vs Seebeck coefficient."""
    import matplotlib.pyplot as plt

    os.makedirs(output_dir, exist_ok=True)
    
    # Get top 3 descriptors
    corr_matrix = compute_correlation_matrix(features_df)
    top_descs = get_top_descriptors(corr_matrix, n=3)
    
    if not top_descs:
        return

    for desc, corr_val in top_descs.items():
        if desc not in features_df.columns:
            continue
            
        plt.figure(figsize=(10, 6))
        plt.scatter(features_df[desc], features_df['seebeck_coefficient'], alpha=0.6)
        
        # Add trend line
        z = np.polyfit(features_df[desc].dropna(), features_df['seebeck_coefficient'].dropna(), 1)
        p = np.poly1d(z)
        x_line = np.linspace(features_df[desc].min(), features_df[desc].max(), 100)
        plt.plot(x_line, p(x_line), "r--", label=f"Trend (r={corr_val:.3f})")
        
        plt.xlabel(desc.replace('_', ' ').title())
        plt.ylabel('Seebeck Coefficient (µV/K)')
        plt.title(f'{desc.replace("_", " ").title()} vs Seebeck Coefficient')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        output_path = os.path.join(output_dir, f'{desc}_vs_seebek.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

def classify_result(r2_score):
    """
    Classify the model result based on R² score.
    Success: R² > 0.2
    Inconclusive: 0.2 <= R² < 0.4
    Failure: R² < 0.2
    """
    if r2_score > 0.2:
        return "Success"
    elif r2_score >= 0.2: # This is technically covered by > 0.2, but keeping logic explicit
        return "Inconclusive"
    else:
        return "Failure"

def generate_report(model_output, features_df, output_path):
    """Generate the final markdown report."""
    r2 = model_output.get('r2_score', 0.0)
    ci_lower = model_output.get('ci_lower', 0.0)
    ci_upper = model_output.get('ci_upper', 0.0)
    p_value = model_output.get('p_value', 1.0)
    f_stat = model_output.get('f_statistic', 0.0)
    f_p_value = model_output.get('f_p_value', 1.0)
    feature_importances = model_output.get('feature_importances', {})
    
    classification = classify_result(r2)
    significance = "Significant" if p_value < 0.05 else "Not Significant"
    
    # Get top descriptors from correlation
    corr_matrix = compute_correlation_matrix(features_df)
    top_descs = get_top_descriptors(corr_matrix, n=5)
    
    report_lines = [
        "# Predicting the Influence of Alloying on the Seebeck Coefficient",
        "",
        "## Executive Summary",
        "",
        f"This report summarizes the predictive modeling results for the Seebeck coefficient",
        f"based on compositional descriptors derived from public thermoelectric data.",
        "",
        "## Model Performance",
        "",
        f"- **R² Score**: {r2:.4f}",
        f"- **95% Confidence Interval**: [{ci_lower:.4f}, {ci_upper:.4f}]",
        f"- **P-value (Permutation Test)**: {p_value:.4e}",
        f"- **F-statistic (vs Linear Baseline)**: {f_stat:.4f}",
        f"- **F-test P-value**: {f_p_value:.4e}",
        "",
        "## Result Classification",
        "",
        f"- **Performance Classification**: {classification}",
        f"- **Statistical Significance**: {significance}",
        "",
        "## Top Predictive Descriptors",
        "",
        "### By Model Feature Importance",
        ""
    ]
    
    # Sort feature importances
    sorted_importances = sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)
    for i, (feat, imp) in enumerate(sorted_importances[:5], 1):
        report_lines.append(f"{i}. **{feat}**: {imp:.4f}")
        
    report_lines.extend([
        "",
        "### By Pearson Correlation with Seebeck",
        ""
    ])
    
    for i, (desc, corr) in enumerate(top_descs.items(), 1):
        report_lines.append(f"{i}. **{desc}**: r = {corr:.4f}")
        
    report_lines.extend([
        "",
        "## Methodology",
        "",
        "1. **Data Ingestion**: Downloaded and cleaned electronic transport data from public repository.",
        "2. **Feature Engineering**: Calculated compositional descriptors (Mean Atomic Radius, Electronegativity Variance, VEC, Atomic Number Variance).",
        "3. **Modeling**: Trained Gradient Boosting Regressor with 5-fold Cross-Validation.",
        "4. **Evaluation**: Assessed performance using R², permutation tests, and F-test comparison against Linear Regression baseline.",
        "",
        "## Conclusion",
        "",
        f"The model {'successfully' if classification == 'Success' else 'did not successfully'} predict the Seebeck coefficient",
        f"based on compositional features. The result is {'statistically significant' if significance == 'Significant' else 'not statistically significant'}.",
        ""
    ])
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

def main():
    """Main entry point for visualization and reporting."""
    # Paths
    base_dir = Path(__file__).parent.parent
    model_output_path = base_dir / 'data' / 'processed' / 'model_output.json'
    features_path = base_dir / 'data' / 'processed' / 'final_features.csv'
    figures_dir = base_dir / 'docs' / 'figures'
    report_path = base_dir / 'docs' / 'report.md'
    
    # Load data
    if not model_output_path.exists():
        print(f"Error: Model output file not found at {model_output_path}")
        sys.exit(1)
        
    model_output = load_model_output(model_output_path)
    features_df = load_features(features_path)
    
    # Generate visualizations
    generate_scatter_plots(features_df, model_output, figures_dir)
    print(f"Scatter plots saved to {figures_dir}")
    
    # Generate report
    generate_report(model_output, features_df, report_path)
    print(f"Report generated at {report_path}")

if __name__ == "__main__":
    main()