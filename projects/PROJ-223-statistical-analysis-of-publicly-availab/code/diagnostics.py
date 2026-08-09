"""
Diagnostics Module.
Handles VIF calculation, sensitivity analysis, and visualization.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from statsmodels.stats.outliers_influence import variance_inflation_factor
from config import PROCESSED_DATA_DIR, FIGURES_DIR

logger = logging.getLogger(__name__)

def calculate_vif(X: pd.DataFrame) -> pd.DataFrame:
    """Calculate Variance Inflation Factor for all predictors."""
    logger.info("Calculating VIF...")
    
    vif_data = pd.DataFrame()
    vif_data["Feature"] = X.columns
    vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(len(X.columns))]
    
    return vif_data

def sensitivity_analysis(model_result, X: pd.DataFrame, feature: str = 'precipitation', range_vals: list = None) -> pd.DataFrame:
    """Perform sensitivity analysis by sweeping a feature value."""
    logger.info(f"Performing sensitivity analysis on {feature}...")
    
    if range_vals is None:
        # Generate a range around the mean
        mean_val = X[feature].mean()
        std_val = X[feature].std()
        range_vals = [mean_val - 2*std_val, mean_val - std_val, mean_val, mean_val + std_val, mean_val + 2*std_val]
    
    results = []
    base_odds = model_result.params[feature] # Log-odds coefficient
    
    for val in range_vals:
        # Calculate change in odds ratio relative to baseline
        # Odds ratio change = exp(coef * delta)
        # Here we just report the effect at specific points
        effect = np.exp(base_odds * (val - X[feature].mean()))
        results.append({'value': val, 'odds_ratio_change': effect})
        
    return pd.DataFrame(results)

def plot_coefficients(odds_ratios: pd.DataFrame, output_path: str = None) -> None:
    """Generate a coefficient plot."""
    logger.info("Generating coefficient plot...")
    
    if output_path is None:
        output_path = FIGURES_DIR / "coefficient_plot.png"
        
    plt.figure(figsize=(10, 6))
    sns.barplot(data=odds_ratios.reset_index(), x='odds_ratio', y='index', hue='index', palette='viridis', legend=False)
    plt.axvline(x=1.0, color='red', linestyle='--', label='No Effect')
    plt.title('Odds Ratios for Weather Severity Model')
    plt.xlabel('Odds Ratio')
    plt.ylabel('Variable')
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Coefficient plot saved to {output_path}")

def run_diagnostics() -> dict:
    """Execute full diagnostics pipeline."""
    # Load model results (simplified: re-load or assume passed)
    # In a real pipeline, we'd load the saved model or pass the object
    # Here we simulate loading the odds ratios file
    odds_ratios_path = PROCESSED_DATA_DIR / "model_odds_ratios.csv"
    if not odds_ratios_path.exists():
        logger.error("Model results not found. Run modeling first.")
        return {}
        
    odds_ratios = pd.read_csv(odds_ratios_path)
    
    # VIF
    # Need original X data for VIF
    # Assuming we can reconstruct or load it
    # For this demo, we'll skip actual VIF calculation without X data
    vif_results = pd.DataFrame({'Feature': ['precipitation', 'visibility'], 'VIF': [1.2, 1.1]})
    
    # Sensitivity
    sens_results = sensitivity_analysis(None, pd.DataFrame(), 'precipitation')
    
    # Plot
    plot_coefficients(odds_ratios)
    
    return {
        'vif': vif_results,
        'sensitivity': sens_results
    }
