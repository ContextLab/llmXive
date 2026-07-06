import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

# Add project root to path to allow imports from utils and sibling code modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.periodic_data import get_element, get_atomic_radius, get_electronegativity, get_valence_electrons, get_atomic_number
from utils.stoichiometry_parser import parse_formula, get_total_atoms

# Constants
MODEL_OUTPUT_PATH = "data/processed/model_output.json"
FEATURES_PATH = "data/processed/final_features.csv"
FIGURES_DIR = "docs/figures"
REPORT_PATH = "docs/report.md"
VIF_THRESHOLD = 5.0  # Threshold for multicollinearity concern

def load_model_output(path):
    """Load and validate model output JSON."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model output file not found: {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    required_keys = ['r2_score', 'ci_lower', 'ci_upper', 'p_value', 'f_statistic', 'f_p_value', 'feature_importances']
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key in model output: {key}")
    
    return data

def load_features(path):
    """Load engineered features dataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Features file not found: {path}")
    return pd.read_csv(path)

def calculate_vif(df, feature_columns):
    """Calculate Variance Inflation Factor for each feature."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Add intercept column
    X = df[feature_columns].copy()
    X['intercept'] = 1.0
    
    vif_data = {}
    for col in feature_columns:
        vif = variance_inflation_factor(X.values, X.columns.get_loc(col))
        vif_data[col] = vif
    
    return vif_data

def compute_correlation_matrix(df, feature_columns):
    """Compute Pearson correlation matrix for features."""
    return df[feature_columns].corr()

def get_top_descriptors(feature_importances, n=3):
    """Get top N descriptors based on feature importance."""
    sorted_importances = sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)
    return sorted_importances[:n]

def generate_scatter_plots(df, top_descriptors, output_dir):
    """Generate scatter plots of top descriptors vs Seebeck coefficient."""
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid')
    
    seebeck_col = 'seebeck_uV_K'
    
    for i, (desc_name, importance) in enumerate(top_descriptors):
        if desc_name not in df.columns:
            print(f"Warning: Descriptor '{desc_name}' not found in dataframe, skipping plot.")
            continue
        
        plt.figure(figsize=(10, 6))
        plt.scatter(df[desc_name], df[seebeck_col], alpha=0.6, edgecolors='k', linewidth=0.5)
        
        # Add trend line
        z = np.polyfit(df[desc_name].dropna(), df[seebeck_col].dropna(), 1)
        p = np.poly1d(z)
        x_vals = np.linspace(df[desc_name].min(), df[desc_name].max(), 100)
        plt.plot(x_vals, p(x_vals), "r-", linewidth=2, label=f"Trend (slope={z[0]:.4f})")
        
        plt.xlabel(desc_name.replace('_', ' ').title())
        plt.ylabel('Seebeck Coefficient ($\mu$V/K)')
        plt.title(f'{desc_name.replace("_", " ").title()} vs Seebeck Coefficient')
        plt.legend()
        
        output_path = os.path.join(output_dir, f"seebeck_vs_{desc_name}.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved plot: {output_path}")

def classify_result(r2_score, p_value):
    """Classify the result based on R2 and p-value."""
    if r2_score > 0.4:
        classification = "Success"
    elif r2_score >= 0.2:
        classification = "Inconclusive"
    else:
        classification = "Failure"
    
    significance = "Significant" if p_value < 0.05 else "Not Significant"
    
    return classification, significance

def generate_report(model_output, vif_data, correlations, top_descriptors, classification, significance, output_path):
    """Generate the markdown report."""
    r2 = model_output['r2_score']
    ci_lower = model_output['ci_lower']
    ci_upper = model_output['ci_upper']
    p_val = model_output['p_value']
    f_stat = model_output['f_statistic']
    f_p_val = model_output['f_p_value']
    
    report_lines = [
        "# Predicting the Influence of Alloying on the Seebeck Coefficient: Final Report",
        "",
        "## Executive Summary",
        f"This report summarizes the predictive modeling results for the Seebeck coefficient based on compositional descriptors.",
        "",
        "## Key Metrics",
        f"- **R² Score**: {r2:.4f}",
        f"- **95% Confidence Interval**: [{ci_lower:.4f}, {ci_upper:.4f}]",
        f"- **Permutation P-value**: {p_val:.4f}",
        f"- **F-statistic (vs Linear Baseline)**: {f_stat:.4f}",
        f"- **F-test P-value**: {f_p_val:.4f}",
        "",
        "## Classification",
        f"- **Model Performance**: {classification}",
        f"- **Statistical Significance**: {significance}",
        "",
        "## Feature Importance Analysis",
        "Top 3 descriptors ranked by importance:",
        ""
    ]
    
    for i, (desc, imp) in enumerate(top_descriptors, 1):
        report_lines.append(f"{i}. **{desc}** (Importance: {imp:.4f})")
    
    report_lines.extend([
        "",
        "## Multicollinearity Check (VIF)",
        "Variance Inflation Factors for features:",
        ""
    ])
    
    for feat, vif in vif_data.items():
        status = "⚠️ High" if vif > VIF_THRESHOLD else "✅ OK"
        report_lines.append(f"- {feat}: {vif:.2f} {status}")
    
    report_lines.extend([
        "",
        "## Correlation Matrix",
        "Pearson correlation coefficients between descriptors:",
        "",
        "```",
    ])
    
    # Format correlation matrix as text
    corr_df = pd.DataFrame(correlations)
    for col in corr_df.columns:
        row_str = f"{col}: " + ", ".join([f"{corr_df.loc[r, col]:.3f}" for r in corr_df.index])
        report_lines.append(row_str)
    
    report_lines.extend([
        "```",
        "",
        "## Figures",
        "See generated plots in `docs/figures/`:",
        ""
    ])
    
    for desc, _ in top_descriptors:
        report_lines.append(f"- ![{desc} vs Seebeck](figures/seebeck_vs_{desc}.png)")
    
    report_lines.extend([
        "",
        "## Conclusion",
        f"The model {'successfully' if classification == 'Success' else 'did not successfully'} predict the Seebeck coefficient from compositional features.",
        f"The results are {'statistically significant' if significance == 'Significant' else 'not statistically significant'} (p < 0.05).",
        "",
        f"Based on the R² score of {r2:.4f}, the model's explanatory power is classified as **{classification}**."
    ])
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"Saved report: {output_path}")

def main():
    """Main execution function for visualization and reporting."""
    print("Starting visualization and report generation...")
    
    # Load data
    try:
        model_output = load_model_output(MODEL_OUTPUT_PATH)
        print(f"Loaded model output: R² = {model_output['r2_score']:.4f}")
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    try:
        df = load_features(FEATURES_PATH)
        print(f"Loaded features dataset with {len(df)} records")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    # Identify feature columns (exclude non-feature columns)
    feature_cols = ['mean_atomic_radius', 'electronegativity_variance', 'vec', 'atomic_number_variance', 'temperature']
    # Filter to only those present in dataframe
    feature_cols = [col for col in feature_cols if col in df.columns]
    
    if len(feature_cols) < 2:
        print("ERROR: Insufficient feature columns found in dataset for VIF/Correlation analysis.")
        sys.exit(1)
    
    # Calculate VIF and Correlations
    print("Calculating VIF and correlations...")
    vif_data = calculate_vif(df, feature_cols)
    correlations = compute_correlation_matrix(df, feature_cols)
    
    # Get top descriptors
    top_descs = get_top_descriptors(model_output['feature_importances'], n=3)
    
    # Generate plots
    print("Generating scatter plots...")
    generate_scatter_plots(df, top_descs, FIGURES_DIR)
    
    # Classify result
    classification, significance = classify_result(model_output['r2_score'], model_output['p_value'])
    
    # Generate report
    print("Generating final report...")
    generate_report(model_output, vif_data, correlations, top_descs, classification, significance, REPORT_PATH)
    
    print("Visualization and reporting complete.")

if __name__ == "__main__":
    main()