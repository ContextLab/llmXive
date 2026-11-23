import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import logging
import json

from utils.config import get_processed_data_dir, get_state_dir

logger = logging.getLogger(__name__)

def load_processed_data() -> pd.DataFrame:
    path = get_processed_data_dir() / "features.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Data not found: {path}")
    return pd.read_parquet(path)

def load_model_results() -> Dict[str, Any]:
    path = get_state_dir() / "model_results.json"
    if not path.exists():
        raise FileNotFoundError(f"Model results not found: {path}")
    with open(path) as f:
        return json.load(f)

def create_scatter_plot(df: pd.DataFrame, output_path: Path):
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x="csa_index", y="food_security_index")
    plt.title("CSA Index vs Food Security")
    plt.savefig(output_path)
    plt.close()

def generate_scatter_plot_report(df: pd.DataFrame) -> Dict[str, Any]:
    return {"correlation": df["csa_index"].corr(df["food_security_index"])}

def create_coefficient_plot(results: Dict[str, Any], output_path: Path):
    params = results.get("params", {})
    pvalues = results.get("pvalues", {})
    names = list(params.keys())
    values = list(params.values())
    pvals = [pvalues.get(n, 1.0) for n in names]
    
    plt.figure(figsize=(10, 6))
    plt.barh(names, values)
    plt.title("Model Coefficients")
    plt.savefig(output_path)
    plt.close()

def create_distribution_plot(df: pd.DataFrame, output_path: Path):
    plt.figure(figsize=(10, 6))
    sns.histplot(df["csa_index"], kde=True)
    plt.title("CSA Index Distribution")
    plt.savefig(output_path)
    plt.close()

def main():
    """
    Main entry point for visualization.
    """
    logger.info("Starting visualization pipeline...")
    
    processed_dir = get_processed_data_dir()
    figures_dir = processed_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # Load Data
    df = load_processed_data()
    results = load_model_results()
    
    # 1. Scatter Plot
    create_scatter_plot(df, figures_dir / "scatter_csa_vs_food_security.png")
    
    # 2. Coefficient Plot
    create_coefficient_plot(results, figures_dir / "coefficient_plot.png")
    
    # 3. Distribution Plot
    create_distribution_plot(df, figures_dir / "distribution_plot.png")
    
    logger.info(f"Plots saved to {figures_dir}")

if __name__ == "__main__":
    main()
