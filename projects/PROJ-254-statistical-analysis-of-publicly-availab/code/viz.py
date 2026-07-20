"""
Visualization module for generating plots and heatmaps.
"""
import os
import logging
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.graph_objects as go
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from utils import setup_logging, get_logger, set_deterministic_seed

logger = get_logger("viz")

def load_similarity_data() -> List[Dict[str, Any]]:
    """
    Load similarity data from CSV.
    
    Returns:
        List of dicts with year and similarity.
    """
    path = Path("data/derived/yearly_similarity.csv")
    if not path.exists():
        raise FileNotFoundError("yearly_similarity.csv not found")
        
    data = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'year': int(row['year']),
                'similarity': float(row['mean_off_diagonal_similarity']),
                'variance': float(row['intra_genre_variance'])
            })
    return data

def calculate_confidence_interval(similarities: List[float], confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval for similarity values.
    
    Args:
        similarities: List of similarity values.
        confidence: Confidence level.
        
    Returns:
        Tuple of (lower, upper).
    """
    import scipy.stats as stats
    n = len(similarities)
    mean = np.mean(similarities)
    std_err = stats.sem(similarities)
    h = std_err * stats.t.ppf((1 + confidence) / 2., n-1)
    return mean - h, mean + h

def generate_similarity_trend_plot(data: List[Dict[str, Any]]):
    """
    Generate line plot of similarity trends.
    
    Args:
        data: List of similarity data.
    """
    logger.info("Generating similarity trend plot...")
    
    years = [d['year'] for d in data]
    sims = [d['similarity'] for d in data]
    
    plt.figure(figsize=(12, 6))
    plt.plot(years, sims, marker='o', linestyle='-', color='b')
    plt.xlabel('Year')
    plt.ylabel('Mean Off-Diagonal Similarity')
    plt.title('Genre Similarity Trend Over Time')
    plt.grid(True)
    
    # Save
    output_path = Path("figures/similarity_trend.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    
    logger.info(f"Saved trend plot to {output_path}")

def load_yearly_embeddings() -> Dict[int, Dict[str, np.ndarray]]:
    """Load embeddings for heatmap."""
    embeddings_dir = Path("yearly_embeddings")
    yearly_data = {}
    for year_file in embeddings_dir.glob("*.npy"):
        year = int(year_file.stem)
        data = np.load(year_file, allow_pickle=True).item()
        yearly_data[year] = data
    return yearly_data

def compute_genre_similarity_matrix(yearly_data: Dict[int, Dict[str, np.ndarray]]) -> np.ndarray:
    """
    Compute average similarity matrix across years.
    
    Args:
        yearly_data: Dict of year -> genre -> vector.
        
    Returns:
        Average similarity matrix.
    """
    # Aggregate all vectors
    all_genres = set()
    for year_data in yearly_data.values():
        all_genres.update(year_data.keys())
        
    genres = sorted(list(all_genres))
    n = len(genres)
    sim_matrix = np.zeros((n, n))
    count = np.zeros((n, n))
    
    for year_data in yearly_data.values():
        for i, g1 in enumerate(genres):
            for j, g2 in enumerate(genres):
                if g1 in year_data and g2 in year_data:
                    v1 = year_data[g1]
                    v2 = year_data[g2]
                    sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                    sim_matrix[i, j] += sim
                    count[i, j] += 1
                    
    # Average
    mask = count > 0
    sim_matrix[mask] /= count[mask]
    
    return sim_matrix, genres

def generate_genre_heatmap(yearly_data: Dict[int, Dict[str, np.ndarray]]):
    """
    Generate interactive heatmap of genre similarities.
    
    Args:
        yearly_data: Dict of year -> genre -> vector.
    """
    logger.info("Generating genre similarity heatmap...")
    
    sim_matrix, genres = compute_genre_similarity_matrix(yearly_data)
    
    fig = go.Figure(data=go.Heatmap(
        z=sim_matrix,
        x=genres,
        y=genres,
        colorscale='Viridis',
        showscale=True
    ))
    
    fig.update_layout(
        title='Average Genre Similarity Heatmap',
        xaxis_title='Genre',
        yaxis_title='Genre'
    )
    
    output_path = Path("figures/genre_similarity_heatmap.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(output_path)
    
    logger.info(f"Saved heatmap to {output_path}")

def main():
    """Main entry point for visualization."""
    setup_logging()
    set_deterministic_seed(42)
    
    try:
        # Trend plot
        data = load_similarity_data()
        generate_similarity_trend_plot(data)
        
        # Heatmap
        yearly_data = load_yearly_embeddings()
        generate_genre_heatmap(yearly_data)
        
    except Exception as e:
        logger.error(f"Visualization pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()