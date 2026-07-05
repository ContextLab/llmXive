import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import json
import logging

# Configure logging for the module
logger = logging.getLogger(__name__)

# Ensure styles are consistent
sns.set_theme(style="whitegrid")

def load_processed_data(data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the processed merged dataset from disk.
    
    Args:
        data_path: Path to the parquet file. Defaults to data/processed/merged_sample.parquet
        
    Returns:
        DataFrame containing the processed data.
    """
    if data_path is None:
        # Default path based on project structure
        data_path = Path("data/processed/merged_sample.parquet")
    
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data file not found at {data_path}. "
                                "Run the data pipeline (T019) first.")
    
    logger.info(f"Loading processed data from {data_path}")
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
    return df

def create_scatter_plot(
    df: pd.DataFrame,
    x_col: str = "csa_index",
    y_col: str = "food_security_score",
    output_path: Optional[Path] = None,
    title: str = "CSA Index vs Food Security Score",
    hue_col: Optional[str] = None
) -> Path:
    """
    Create a scatter plot showing the relationship between CSA Index and Food Security.
    
    Args:
        df: Input DataFrame
        x_col: Column name for X-axis
        y_col: Column name for Y-axis
        output_path: Path to save the plot. Defaults to figures/scatter_csa_food_security.png
        title: Plot title
        hue_col: Optional column to color points by (e.g., country)
        
    Returns:
        Path to the saved plot file.
    """
    if output_path is None:
        output_path = Path("figures/scatter_csa_food_security.png")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(10, 8))
    
    if hue_col and hue_col in df.columns:
        sns.scatterplot(data=df, x=x_col, y=y_col, hue=hue_col, alpha=0.6, edgecolor=None)
        plt.legend(title=hue_col)
    else:
        sns.scatterplot(data=df, x=x_col, y=y_col, alpha=0.6, edgecolor=None)
    
    plt.title(title, fontsize=14)
    plt.xlabel(x_col.replace('_', ' ').title())
    plt.ylabel(y_col.replace('_', ' ').title())
    
    # Add trend line
    if len(df) > 1:
        z = np.polyfit(df[x_col].dropna(), df[y_col].dropna(), 1)
        p = np.poly1d(z)
        x_line = np.linspace(df[x_col].min(), df[x_col].max(), 100)
        plt.plot(x_line, p(x_line), "r--", linewidth=2, label=f'Trend (R²={np.corrcoef(df[x_col].dropna(), df[y_col].dropna())[0,1]**2:.2f})')
        plt.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Scatter plot saved to {output_path}")
    return output_path

def generate_scatter_plot_report(
    df: pd.DataFrame,
    x_col: str = "csa_index",
    y_col: str = "food_security_score"
) -> Dict[str, Any]:
    """
    Generate a statistical report for the scatter plot relationship.
    
    Args:
        df: Input DataFrame
        x_col: Column name for X-axis
        y_col: Column name for Y-axis
        
    Returns:
        Dictionary containing correlation, slope, intercept, and sample size.
    """
    valid_df = df[[x_col, y_col]].dropna()
    
    if len(valid_df) < 2:
        return {
            "correlation": None,
            "slope": None,
            "intercept": None,
            "n": len(df),
            "valid_n": len(valid_df),
            "message": "Insufficient data for correlation calculation"
        }
    
    corr = valid_df[x_col].corr(valid_df[y_col])
    slope, intercept = np.polyfit(valid_df[x_col], valid_df[y_col], 1)
    
    return {
        "correlation": float(corr),
        "slope": float(slope),
        "intercept": float(intercept),
        "n": len(df),
        "valid_n": len(valid_df),
        "message": "Calculation successful"
    }

def create_coefficient_plot(
    coefficients: pd.DataFrame,
    output_path: Optional[Path] = None,
    title: str = "Model Coefficients with Confidence Intervals"
) -> Path:
    """
    Create a coefficient plot showing standardized coefficients and confidence intervals.
    
    Args:
        coefficients: DataFrame with columns ['variable', 'coef', 'std_err', 'pval']
        output_path: Path to save the plot. Defaults to figures/coefficients.png
        title: Plot title
        
    Returns:
        Path to the saved plot file.
    """
    if output_path is None:
        output_path = Path("figures/coefficients.png")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Sort by coefficient value
    df_sorted = coefficients.sort_values(by='coef')
    
    plt.figure(figsize=(10, 8))
    
    # Calculate confidence intervals (95%)
    df_sorted['ci_lower'] = df_sorted['coef'] - 1.96 * df_sorted['std_err']
    df_sorted['ci_upper'] = df_sorted['coef'] + 1.96 * df_sorted['std_err']
    
    # Plot
    y_pos = np.arange(len(df_sorted))
    plt.errorbar(
        df_sorted['coef'], 
        y_pos, 
        xerr=[df_sorted['coef'] - df_sorted['ci_lower'], df_sorted['ci_upper'] - df_sorted['coef']],
        fmt='o', 
        capsize=5, 
        linewidth=1, 
        color='black',
        markersize=8
    )
    
    plt.yticks(y_pos, df_sorted['variable'])
    plt.axvline(x=0, color='red', linestyle='--', alpha=0.7)
    plt.title(title, fontsize=14)
    plt.xlabel('Standardized Coefficient')
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Coefficient plot saved to {output_path}")
    return output_path

def create_distribution_plot(
    df: pd.DataFrame,
    col: str,
    output_path: Optional[Path] = None,
    title: Optional[str] = None,
    bins: int = 30,
    kde: bool = True,
    stat: str = 'count'
) -> Path:
    """
    Create a distribution plot (histogram with optional KDE) for a specific column.
    
    This function visualizes the distribution of a single variable, helping to identify
    skewness, outliers, and the general shape of the data. It is commonly used for
    exploratory data analysis of key variables like CSA Index, food security scores,
    or income levels.
    
    Args:
        df: Input DataFrame
        col: Column name to plot
        output_path: Path to save the plot. Defaults to figures/distribution_{col}.png
        title: Plot title. Defaults to "{col} Distribution"
        bins: Number of histogram bins. Defaults to 30
        kde: Whether to plot Kernel Density Estimate. Defaults to True
        stat: Statistic to plot on y-axis ('count', 'frequency', 'density', 'probability'). Defaults to 'count'
        
    Returns:
        Path to the saved plot file.
        
    Raises:
        ValueError: If the column is not numeric or does not exist in the DataFrame.
        FileNotFoundError: If the input DataFrame is empty.
    """
    if col not in df.columns:
        raise ValueError(f"Column '{col}' not found in DataFrame. Available columns: {list(df.columns)}")
    
    if not pd.api.types.is_numeric_dtype(df[col]):
        raise ValueError(f"Column '{col}' must be numeric for distribution plotting.")
    
    # Remove NaN values for plotting
    plot_data = df[col].dropna()
    
    if len(plot_data) == 0:
        raise ValueError(f"No valid data to plot for column '{col}' after removing NaN values.")
    
    if output_path is None:
        output_path = Path(f"figures/distribution_{col.replace(' ', '_').replace('-', '_')}.png")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if title is None:
        title = f"Distribution of {col.replace('_', ' ').title()}"
    
    plt.figure(figsize=(10, 6))
    
    # Create the histogram with KDE
    sns.histplot(
        data=plot_data, 
        kde=kde, 
        bins=bins, 
        stat=stat,
        color='skyblue', 
        edgecolor='black', 
        alpha=0.7
    )
    
    # Add statistics to the plot
    mean_val = plot_data.mean()
    median_val = plot_data.median()
    std_val = plot_data.std()
    
    # Add vertical lines for mean and median
    plt.axvline(mean_val, color='red', linestyle='dashed', linewidth=2, label=f'Mean: {mean_val:.2f}')
    plt.axvline(median_val, color='green', linestyle='dashed', linewidth=2, label=f'Median: {median_val:.2f}')
    
    # Add text box with statistics
    stats_text = f"Mean: {mean_val:.2f}\nMedian: {median_val:.2f}\nStd Dev: {std_val:.2f}\nN: {len(plot_data)}"
    plt.text(0.05, 0.95, stats_text, transform=plt.gca().transAxes, 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
             verticalalignment='top', fontsize=10)
    
    plt.title(title, fontsize=14)
    plt.xlabel(col.replace('_', ' ').title())
    plt.ylabel(stat.title())
    plt.legend()
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Distribution plot saved to {output_path}")
    return output_path

def main():
    """
    Main entry point to generate all visualization plots for User Story 3.
    
    This function orchestrates the generation of:
    1. Scatter plots (CSA vs Food Security)
    2. Coefficient plots (Model results)
    3. Distribution plots (Key variable distributions)
    
    It expects the processed data to be available at data/processed/merged_sample.parquet
    and model results to be available (simulated here for standalone execution if needed).
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Load data
        logger.info("Starting visualization pipeline...")
        df = load_processed_data()
        
        # 1. Scatter Plot
        logger.info("Generating scatter plot...")
        scatter_path = create_scatter_plot(df, x_col="csa_index", y_col="food_security_score")
        logger.info(f"Scatter plot created: {scatter_path}")
        
        # Generate scatter report
        scatter_report = generate_scatter_plot_report(df, "csa_index", "food_security_score")
        report_path = Path("figures/scatter_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(scatter_report, f, indent=2)
        logger.info(f"Scatter report saved: {report_path}")
        
        # 2. Distribution Plots for key variables
        key_variables = [
            "csa_index", 
            "food_security_score", 
            "household_income", 
            "farm_size_hectares"
        ]
        
        for var in key_variables:
            if var in df.columns:
                logger.info(f"Generating distribution plot for {var}...")
                dist_path = create_distribution_plot(df, col=var)
                logger.info(f"Distribution plot created: {dist_path}")
            else:
                logger.warning(f"Variable {var} not found in dataset, skipping distribution plot.")
        
        # 3. Coefficient Plot (Simulated data if model output not strictly loaded in this context,
        # but in full pipeline this would come from model.py output)
        # For robustness, we check if a coefficients file exists or create a placeholder if in test mode
        # In a real run, this would be loaded from model output
        coef_path = Path("data/processed/model_coefficients.csv")
        if coef_path.exists():
            logger.info("Loading model coefficients for coefficient plot...")
            coeffs = pd.read_csv(coef_path)
            coef_plot_path = create_coefficient_plot(coeffs)
            logger.info(f"Coefficient plot created: {coef_plot_path}")
        else:
            logger.info("Model coefficients file not found. Skipping coefficient plot generation.")
            logger.info("Ensure T023 (Model) has been run to generate model_coefficients.csv")
        
        logger.info("Visualization pipeline completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in visualization pipeline: {e}")
        raise

if __name__ == "__main__":
    main()