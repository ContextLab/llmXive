"""
Visualization module for generating similarity trend plots and heatmaps.
"""
import os
import logging
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from utils import setup_logging, get_logger, set_deterministic_seed
from memory_utils import check_memory_thresholds, trigger_garbage_collection

logger = setup_logging()

DATA_DERIVED_DIR = Path(__file__).resolve().parent.parent / "data" / "derived"
FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"

def load_similarity_data() -> pd.DataFrame:
    """
    Load similarity data from CSV.

    Returns:
        pd.DataFrame: Similarity data.

    Raises:
        FileNotFoundError: If the CSV file is missing.
    """
    path = DATA_DERIVED_DIR / "yearly_similarity.csv"
    if not path.exists():
        raise FileNotFoundError(f"Similarity data file not found: {path}")
    
    return pd.read_csv(path)

def calculate_confidence_interval(values: List[float], confidence: float = 0.95) -> float:
    """
    Calculate the confidence interval for a list of values.

    Args:
        values (List[float]): List of values.
        confidence (float): Confidence level.

    Returns:
        float: Half-width of the confidence interval.
    """
    from scipy import stats
    n = len(values)
    mean = np.mean(values)
    std_err = stats.sem(values)
    h = std_err * stats.t.ppf((1 + confidence) / 2., n-1)
    return h

def generate_similarity_trend_plot(df: pd.DataFrame):
    """
    Generate a line plot of similarity trend over years.

    Args:
        df (pd.DataFrame): DataFrame with 'year' and 'mean_off_diagonal_similarity'.
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(10, 6))
    plt.plot(df['year'], df['mean_off_diagonal_similarity'], marker='o', label='Mean Similarity')
    
    # Calculate CI (placeholder)
    ci = calculate_confidence_interval(df['mean_off_diagonal_similarity'].tolist())
    plt.fill_between(df['year'], df['mean_off_diagonal_similarity'] - ci, df['mean_off_diagonal_similarity'] + ci, color='gray', alpha=0.2, label='95% CI')
    
    plt.xlabel('Year')
    plt.ylabel('Mean Off-Diagonal Similarity')
    plt.title('Genre Similarity Trend Over Time')
    plt.legend()
    plt.grid(True)
    
    output_path = FIGURES_DIR / "similarity_trend.png"
    plt.savefig(output_path)
    plt.close()
    
    logger.info(f"Saved similarity trend plot to {output_path}")

def load_yearly_embeddings() -> Dict[int, np.ndarray]:
    """
    Load yearly embeddings from the embeddings directory.

    Returns:
        Dict[int, np.ndarray]: Dictionary mapping years to embedding vectors.
    """
    embeddings_dir = Path(__file__).resolve().parent.parent / "yearly_embeddings"
    embeddings = {}
    
    if not embeddings_dir.exists():
        logger.warning(f"Embeddings directory not found: {embeddings_dir}")
        return embeddings
    
    for file in embeddings_dir.glob("*.npy"):
        year = int(file.stem)
        embeddings[year] = np.load(file)
    
    return embeddings

def compute_genre_similarity_matrix(vectors: Dict[int, np.ndarray]) -> np.ndarray:
    """
    Compute a similarity matrix between all yearly vectors.

    Args:
        vectors (Dict[int, np.ndarray]): Dictionary of year to vector.

    Returns:
        np.ndarray: Similarity matrix.
    """
    years = sorted(vectors.keys())
    n = len(years)
    matrix = np.zeros((n, n))
    
    for i, year1 in enumerate(years):
        vec1 = vectors[year1]
        for j, year2 in enumerate(years):
            vec2 = vectors[year2]
            sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            matrix[i, j] = sim
    
    return matrix

def generate_genre_heatmap(vectors: Dict[int, np.ndarray]):
    """
    Generate an interactive heatmap of genre similarities.

    Args:
        vectors (Dict[int, np.ndarray]): Dictionary of year to vector.
    """
    import plotly.express as px
    import plotly.graph_objects as go
    
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    matrix = compute_genre_similarity_matrix(vectors)
    years = sorted(vectors.keys())
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=years,
        y=years,
        colorscale='Viridis'
    ))
    
    fig.update_layout(
        title='Genre Similarity Heatmap',
        xaxis_title='Year',
        yaxis_title='Year'
    )
    
    output_path = FIGURES_DIR / "genre_similarity_heatmap.html"
    fig.write_html(output_path)
    logger.info(f"Saved heatmap to {output_path}")

def main():
    """
    Main entry point for visualization.
    """
    set_deterministic_seed(42)
    
    try:
        # Load data
        df = load_similarity_data()
        
        # Generate trend plot
        generate_similarity_trend_plot(df)
        
        # Load embeddings and generate heatmap
        vectors = load_yearly_embeddings()
        if vectors:
            generate_genre_heatmap(vectors)
        
        logger.info("Visualization pipeline complete.")
        
    except Exception as e:
        logger.error(f"Visualization pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()