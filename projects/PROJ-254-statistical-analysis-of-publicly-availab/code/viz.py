"""
Visualization module for the Statistical Analysis of Publicly Available Music Streaming Data.
Generates plots and interactive visualizations for genre evolution analysis.
"""
import os
import logging
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.graph_objects as go
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

from utils import setup_logging, get_logger, set_deterministic_seed
from memory_utils import check_memory_thresholds, trigger_garbage_collection

# Configure logging
logger = get_logger(__name__)

def load_similarity_data(filepath: str = "data/derived/yearly_similarity.csv") -> List[Dict[str, float]]:
    """
    Load yearly similarity data from CSV.

    Args:
        filepath: Path to the CSV file containing similarity data.

    Returns:
        List of dictionaries with year, mean_off_diagonal_similarity, and intra_genre_variance.
    """
    data = []
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Similarity data file not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'year': int(row['year']),
                'mean_off_diagonal_similarity': float(row['mean_off_diagonal_similarity']),
                'intra_genre_variance': float(row['intra_genre_variance'])
            })

    # Sort by year
    data.sort(key=lambda x: x['year'])
    logger.info(f"Loaded {len(data)} years of similarity data from {filepath}")
    return data

def calculate_confidence_interval(data: List[float], z_score: float = 1.96) -> Tuple[float, float]:
    """
    Calculate 95% confidence interval for a list of values.

    Args:
        data: List of numerical values.
        z_score: Z-score for the desired confidence level (default 1.96 for 95%).

    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    if not data:
        return 0.0, 0.0

    mean = np.mean(data)
    std_err = np.std(data, ddof=1) / np.sqrt(len(data))
    margin = z_score * std_err
    return mean - margin, mean + margin

def generate_similarity_trend_plot(data: List[Dict[str, float]], output_path: str = "figures/similarity_trend.png") -> str:
    """
    Generate a line plot with 95% CI bands for similarity trends over time.

    Args:
        data: List of similarity data dictionaries.
        output_path: Path to save the generated plot.

    Returns:
        Path to the saved plot file.
    """
    set_deterministic_seed(42)
    years = [d['year'] for d in data]
    similarities = [d['mean_off_diagonal_similarity'] for d in data]

    # Calculate rolling mean and CI for smoother trend
    window = 3
    rolling_similarities = []
    rolling_ci_lower = []
    rolling_ci_upper = []

    for i in range(len(years)):
        start = max(0, i - window // 2)
        end = min(len(years), i + window // 2 + 1)
        window_data = similarities[start:end]
        rolling_similarities.append(np.mean(window_data))
        lower, upper = calculate_confidence_interval(window_data)
        rolling_ci_lower.append(lower)
        rolling_ci_upper.append(upper)

    plt.figure(figsize=(12, 6))
    plt.plot(years, rolling_similarities, 'b-', linewidth=2, label='Mean Similarity')
    plt.fill_between(years, rolling_ci_lower, rolling_ci_upper, color='blue', alpha=0.2, label='95% CI')

    plt.xlabel('Year', fontsize=12)
    plt.ylabel('Mean Off-Diagonal Cosine Similarity', fontsize=12)
    plt.title('Genre Evolution: Similarity Trend Over Time', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Saved similarity trend plot to {output_path}")
    return output_path

def load_yearly_embeddings(years: List[int], base_path: str = "yearly_embeddings") -> Dict[int, np.ndarray]:
    """
    Load yearly genre embeddings from .npy files.

    Args:
        years: List of years to load.
        base_path: Base directory containing embedding files.

    Returns:
        Dictionary mapping year to embedding array.
    """
    embeddings = {}
    for year in years:
        filepath = os.path.join(base_path, f"{year}.npy")
        if os.path.exists(filepath):
            embeddings[year] = np.load(filepath)
            logger.debug(f"Loaded embeddings for year {year}: shape {embeddings[year].shape}")
        else:
            logger.warning(f"Embeddings file not found for year {year}: {filepath}")
    return embeddings

def compute_genre_similarity_matrix(embeddings: Dict[int, np.ndarray], year1: int, year2: int) -> np.ndarray:
    """
    Compute pairwise cosine similarity matrix between genres of two years.

    Args:
        embeddings: Dictionary of year -> embedding matrix.
        year1: First year.
        year2: Second year.

    Returns:
        2D numpy array of cosine similarities.
    """
    if year1 not in embeddings or year2 not in embeddings:
        raise ValueError(f"Embeddings missing for years {year1} or {year2}")

    vecs1 = embeddings[year1]
    vecs2 = embeddings[year2]

    # Normalize vectors
    norm1 = np.linalg.norm(vecs1, axis=1, keepdims=True)
    norm2 = np.linalg.norm(vecs2, axis=1, keepdims=True)

    # Avoid division by zero
    norm1 = np.where(norm1 == 0, 1, norm1)
    norm2 = np.where(norm2 == 0, 1, norm2)

    normalized1 = vecs1 / norm1
    normalized2 = vecs2 / norm2

    # Compute cosine similarity
    similarity_matrix = np.dot(normalized1, normalized2.T)
    return similarity_matrix

def generate_genre_heatmap(
    data: List[Dict[str, float]],
    embeddings: Optional[Dict[int, np.ndarray]] = None,
    output_path: str = "figures/genre_similarity_heatmap.html"
) -> str:
    """
    Generate an interactive heatmap showing genre similarity trends.
    If embeddings are provided, computes actual genre-genre similarities.
    Otherwise, visualizes the mean similarity trend as a heatmap.

    Args:
        data: List of similarity data dictionaries.
        embeddings: Optional dictionary of year -> embedding matrix.
        output_path: Path to save the HTML file.

    Returns:
        Path to the saved HTML file.
    """
    if not data:
        raise ValueError("No similarity data provided for heatmap generation")

    years = [d['year'] for d in data]
    similarities = [d['mean_off_diagonal_similarity'] for d in data]

    # If embeddings are available, compute a more detailed heatmap
    if embeddings and len(embeddings) >= 2:
        logger.info("Generating detailed genre-genre similarity heatmap")
        sorted_years = sorted(embeddings.keys())
        
        # Compute a representative similarity matrix (using first two available years)
        y1, y2 = sorted_years[0], sorted_years[1]
        sim_matrix = compute_genre_similarity_matrix(embeddings, y1, y2)
        
        # Create labels (generic if genre names not available)
        n_genres = sim_matrix.shape[0]
        genre_labels = [f"Genre_{i}" for i in range(n_genres)]
        
        fig = go.Figure(data=go.Heatmap(
            z=sim_matrix,
            x=genre_labels,
            y=genre_labels,
            colorscale='RdBu',
            zmid=0,
            hoverongaps=False,
            colorbar=dict(title="Cosine Similarity")
        ))
        
        fig.update_layout(
            title=f"Genre Similarity Heatmap ({y1} vs {y2})",
            xaxis_title="Genres",
            yaxis_title="Genres",
            width=800,
            height=800
        )
    else:
        # Fallback: Visualize the trend as a heatmap (year vs value)
        logger.info("Generating trend-based heatmap (no embeddings available)")
        
        # Create a 2D array: rows=years, cols=metrics (similarity, variance)
        z_data = np.array([
            [d['mean_off_diagonal_similarity'], d['intra_genre_variance']]
            for d in data
        ])
        
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=['Similarity', 'Variance'],
            y=[str(y) for y in years],
            colorscale='Viridis',
            colorbar=dict(title="Value")
        ))
        
        fig.update_layout(
            title="Yearly Similarity and Variance Trends",
            xaxis_title="Metric",
            yaxis_title="Year",
            width=800,
            height=600
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.write_html(output_path)
    logger.info(f"Saved interactive heatmap to {output_path}")
    return output_path

def main():
    """
    Main entry point for visualization generation.
    Generates both trend plot and heatmap.
    """
    setup_logging()
    logger.info("Starting visualization generation")

    try:
        # Load similarity data
        data = load_similarity_data("data/derived/yearly_similarity.csv")
        
        if not data:
            logger.error("No similarity data found. Cannot generate visualizations.")
            return

        # Generate trend plot
        plot_path = generate_similarity_trend_plot(data, "figures/similarity_trend.png")
        logger.info(f"Trend plot generated: {plot_path}")

        # Try to load embeddings for detailed heatmap
        years = [d['year'] for d in data]
        embeddings = load_yearly_embeddings(years, "yearly_embeddings")
        
        # Generate heatmap
        heatmap_path = generate_genre_heatmap(data, embeddings, "figures/genre_similarity_heatmap.html")
        logger.info(f"Heatmap generated: {heatmap_path}")

        logger.info("All visualizations completed successfully")

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating visualizations: {e}")
        raise

if __name__ == "__main__":
    main()