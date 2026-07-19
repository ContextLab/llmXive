import os
import logging
import csv
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings

# Import from local modules as per API surface
# Note: utils and similarity are expected to be in the same directory or PYTHONPATH
from utils import get_logger, setup_logging

def load_similarity_data(similarity_path: str) -> List[Dict[str, float]]:
    """
    Load similarity data from CSV.
    
    Args:
        similarity_path: Path to the CSV file containing similarity results.
        
    Returns:
        List of dictionaries with year and similarity metrics.
    """
    data = []
    with open(similarity_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'year': int(row['year']),
                'mean_off_diagonal_similarity': float(row['mean_off_diagonal_similarity']),
                'intra_genre_variance': float(row['intra_genre_variance'])
            })
    return data

def calculate_confidence_interval(data: List[Dict[str, float]], confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate 95% confidence interval for the mean similarity.
    
    Args:
        data: List of similarity data points.
        confidence: Confidence level (default 0.95).
        
    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    if not data:
        return (0.0, 0.0)
    
    similarities = [d['mean_off_diagonal_similarity'] for d in data]
    n = len(similarities)
    mean_sim = np.mean(similarities)
    std_sim = np.std(similarities, ddof=1) if n > 1 else 0.0
    
    # Using t-distribution for small samples, z for large
    from scipy import stats
    if n < 30:
        t_val = stats.t.ppf((1 + confidence) / 2, df=n-1)
    else:
        t_val = stats.norm.ppf((1 + confidence) / 2)
        
    margin = t_val * (std_sim / np.sqrt(n))
    return (mean_sim - margin, mean_sim + margin)

def generate_similarity_trend_plot(data: List[Dict[str, float]], output_path: str, logger: logging.Logger):
    """
    Generate a line plot of similarity trends over years with 95% CI bands.
    
    Args:
        data: List of similarity data points.
        output_path: Path to save the plot.
        logger: Logger instance for status updates.
    """
    if not data:
        logger.warning("No data provided for similarity trend plot.")
        return

    years = [d['year'] for d in data]
    similarities = [d['mean_off_diagonal_similarity'] for d in data]
    
    plt.figure(figsize=(12, 6))
    plt.plot(years, similarities, marker='o', linestyle='-', color='b', label='Mean Similarity')
    
    # Calculate and plot confidence intervals (simplified for visualization)
    # In a full implementation, we might calculate per-year CIs if we had multiple samples per year
    # Here we assume the data represents yearly aggregates and plot a moving average CI or global CI
    # For this task, we'll plot a simple global CI band around the trend
    mean_sim = np.mean(similarities)
    std_sim = np.std(similarities, ddof=1)
    margin = 1.96 * std_sim / np.sqrt(len(similarities))
    
    plt.fill_between(years, mean_sim - margin, mean_sim + margin, color='b', alpha=0.2, label='95% CI')
    
    plt.xlabel('Year')
    plt.ylabel('Mean Off-Diagonal Similarity')
    plt.title('Genre Similarity Trend Over Time')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    try:
        plt.savefig(output_path)
        logger.info(f"Successfully generated similarity trend plot: {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate similarity trend plot {output_path}: {str(e)}")
        raise
    finally:
        plt.close()

def load_yearly_embeddings(embeddings_dir: str, year: int, logger: logging.Logger) -> Optional[np.ndarray]:
    """
    Load a yearly embedding file with error handling for missing files.
    
    Args:
        embeddings_dir: Directory containing yearly embedding files.
        year: The year to load embeddings for.
        logger: Logger instance for status updates.
        
    Returns:
        NumPy array of embeddings or None if file is missing or invalid.
    """
    embedding_path = Path(embeddings_dir) / f"{year}.npy"
    
    if not embedding_path.exists():
        logger.error(f"Missing embedding file for year {year}: {embedding_path}")
        return None
        
    try:
        embeddings = np.load(embedding_path)
        logger.debug(f"Loaded embeddings for year {year} with shape {embeddings.shape}")
        return embeddings
    except Exception as e:
        logger.error(f"Failed to load embeddings for year {year} from {embedding_path}: {str(e)}")
        return None

def compute_genre_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """
    Compute pairwise cosine similarity matrix for genre embeddings.
    
    Args:
        embeddings: NumPy array of shape (n_genres, embedding_dim).
        
    Returns:
        NumPy array of shape (n_genres, n_genres) with similarity values.
    """
    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / (norms + 1e-8)
    
    # Compute cosine similarity
    similarity_matrix = np.dot(normalized, normalized.T)
    return similarity_matrix

def generate_genre_heatmap(embeddings_dir: str, years: List[int], output_path: str, logger: logging.Logger):
    """
    Generate an interactive heatmap of genre similarities across years.
    
    Args:
        embeddings_dir: Directory containing yearly embedding files.
        years: List of years to include in the heatmap.
        output_path: Path to save the HTML heatmap.
        logger: Logger instance for status updates.
    """
    import plotly.graph_objects as go
    import plotly.io as pio
    
    if not years:
        logger.warning("No years provided for genre heatmap generation.")
        return

    # Load embeddings for all requested years
    all_embeddings = {}
    missing_years = []
    
    for year in years:
        emb = load_yearly_embeddings(embeddings_dir, year, logger)
        if emb is not None:
            all_embeddings[year] = emb
        else:
            missing_years.append(year)
    
    if missing_years:
        logger.warning(f"Missing embedding files for years: {missing_years}")
    
    if not all_embeddings:
        logger.error("No valid embeddings found to generate heatmap.")
        return

    # For simplicity, we'll create a heatmap of mean similarities across years
    # In a more complex version, we could show a 3D heatmap or multiple heatmaps
    similarity_means = []
    valid_years = sorted(all_embeddings.keys())
    
    for year in valid_years:
        emb = all_embeddings[year]
        sim_matrix = compute_genre_similarity_matrix(emb)
        # Extract mean off-diagonal similarity
        n = sim_matrix.shape[0]
        off_diag = sim_matrix[~np.eye(n, dtype=bool)]
        similarity_means.append(np.mean(off_diag))
    
    # Create a simple line plot as a heatmap alternative if we don't have genre-level breakdown
    # For a true genre heatmap, we would need to track which row corresponds to which genre
    # Since the embedding structure isn't specified to have genre labels, we'll create a summary heatmap
    # showing the trend of mean similarity over years
    
    fig = go.Figure(data=go.Heatmap(
        z=[similarity_means],
        x=valid_years,
        colorscale='RdYlBu_r',
        colorbar=dict(title="Mean Similarity")
    ))
    
    fig.update_layout(
        title="Genre Similarity Trend Heatmap",
        xaxis_title="Year",
        yaxis_title="Metric",
        height=400,
        width=800
    )
    
    try:
        pio.write_html(fig, file=output_path, include_plotlyjs='cdn', auto_open=False)
        logger.info(f"Successfully generated genre similarity heatmap: {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate genre similarity heatmap {output_path}: {str(e)}")
        raise

def main():
    """
    Main entry point for visualization generation with error handling and logging.
    """
    # Setup logging
    log_path = "pipeline_log.txt"
    setup_logging(log_file=log_path)
    logger = get_logger(__name__)
    
    logger.info("Starting visualization generation process.")
    
    # Configuration
    similarity_csv = "data/derived/yearly_similarity.csv"
    embeddings_dir = "yearly_embeddings"
    trend_plot_output = "figures/similarity_trend.png"
    heatmap_output = "figures/genre_similarity_heatmap.html"
    
    # Check if similarity data exists
    if not os.path.exists(similarity_csv):
        logger.error(f"Similarity data file not found: {similarity_csv}")
        logger.info("Visualization generation aborted due to missing input data.")
        return
    
    # Load similarity data
    try:
        data = load_similarity_data(similarity_csv)
        logger.info(f"Loaded {len(data)} records from similarity data.")
    except Exception as e:
        logger.error(f"Failed to load similarity data from {similarity_csv}: {str(e)}")
        return
    
    # Generate trend plot
    logger.info("Generating similarity trend plot...")
    try:
        # Ensure output directory exists
        Path(trend_plot_output).parent.mkdir(parents=True, exist_ok=True)
        generate_similarity_trend_plot(data, trend_plot_output, logger)
    except Exception as e:
        logger.error(f"Error generating similarity trend plot: {str(e)}")
    
    # Generate heatmap
    # Determine years from data
    years = sorted(list(set(d['year'] for d in data)))
    if not years:
        logger.warning("No years found in similarity data for heatmap generation.")
    else:
        logger.info(f"Generating genre similarity heatmap for years: {years}")
        try:
            Path(heatmap_output).parent.mkdir(parents=True, exist_ok=True)
            generate_genre_heatmap(embeddings_dir, years, heatmap_output, logger)
        except Exception as e:
            logger.error(f"Error generating genre similarity heatmap: {str(e)}")
    
    logger.info("Visualization generation process completed.")

if __name__ == "__main__":
    main()