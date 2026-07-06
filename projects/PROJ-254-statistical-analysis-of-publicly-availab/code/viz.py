import os
import logging
import csv
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from utils import get_logger, setup_logging
from similarity import load_yearly_embeddings, compute_pairwise_cosine_similarity

# Ensure logging is configured for this module
setup_logging()
logger = get_logger(__name__)

def load_similarity_data(csv_path: str) -> List[Dict[str, float]]:
    """Load similarity data from CSV file."""
    data = []
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append({
                    'year': int(row['year']),
                    'mean_off_diagonal_similarity': float(row['mean_off_diagonal_similarity']),
                    'intra_genre_variance': float(row['intra_genre_variance'])
                })
    except FileNotFoundError:
        logger.error(f"Similarity data file not found: {csv_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading similarity data from {csv_path}: {e}")
        raise
    return data

def calculate_confidence_interval(data: List[Dict[str, float]], confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate 95% confidence interval for the mean similarity."""
    if not data:
        return (0.0, 0.0)
    
    similarities = [d['mean_off_diagonal_similarity'] for d in data]
    n = len(similarities)
    if n < 2:
        return (similarities[0], similarities[0])
    
    mean_sim = np.mean(similarities)
    std_sim = np.std(similarities, ddof=1)
    # Use t-distribution for small sample sizes
    from scipy import stats
    margin = stats.t.ppf((1 + confidence) / 2., n-1) * (std_sim / np.sqrt(n))
    return (mean_sim - margin, mean_sim + margin)

def generate_similarity_trend_plot(similarity_data: List[Dict[str, float]], output_path: str) -> bool:
    """Generate line plot with 95% CI bands for similarity trend over years."""
    logger.info(f"Generating similarity trend plot: {output_path}")
    try:
        years = [d['year'] for d in similarity_data]
        similarities = [d['mean_off_diagonal_similarity'] for d in similarity_data]
        
        # Calculate confidence intervals for each point (simplified: use global CI for band)
        # For a more accurate representation, we'd calculate rolling CI, but for this task
        # we'll use the global CI as a band around the mean trend.
        ci_low, ci_high = calculate_confidence_interval(similarity_data)
        mean_sim = np.mean(similarities)
        
        plt.figure(figsize=(12, 6))
        plt.plot(years, similarities, 'b-o', label='Mean Off-Diagonal Similarity', linewidth=2)
        
        # Add 95% CI band
        plt.fill_between(years, mean_sim - (mean_sim - ci_low), mean_sim + (ci_high - mean_sim), 
                       color='blue', alpha=0.2, label='95% Confidence Interval')
        
        plt.xlabel('Year')
        plt.ylabel('Mean Off-Diagonal Similarity')
        plt.title('Genre Similarity Trend Over Time (95% CI)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300)
        plt.close()
        
        logger.info(f"Successfully generated similarity trend plot: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate similarity trend plot: {e}")
        return False

def load_yearly_embeddings(embeddings_dir: str) -> Dict[int, np.ndarray]:
    """Load yearly genre embeddings from .npy files with error handling."""
    embeddings = {}
    embeddings_path = Path(embeddings_dir)
    
    if not embeddings_path.exists():
        logger.error(f"Embeddings directory does not exist: {embeddings_dir}")
        raise FileNotFoundError(f"Embeddings directory not found: {embeddings_dir}")
    
    npy_files = list(embeddings_path.glob("*.npy"))
    if not npy_files:
        logger.warning(f"No .npy files found in {embeddings_dir}")
        return embeddings
    
    for npy_file in npy_files:
        try:
            year_str = npy_file.stem
            year = int(year_str)
            vec = np.load(npy_file)
            embeddings[year] = vec
            logger.debug(f"Loaded embeddings for year {year} from {npy_file.name}")
        except Exception as e:
            logger.error(f"Error loading embeddings from {npy_file}: {e}")
            # Continue processing other files
            continue
    
    if not embeddings:
        logger.warning(f"No valid embeddings loaded from {embeddings_dir}")
    
    return embeddings

def compute_genre_similarity_matrix(embeddings: Dict[int, np.ndarray], genre: str) -> Optional[np.ndarray]:
    """Compute pairwise cosine similarity matrix for a specific genre across years."""
    if not embeddings:
        logger.error("No embeddings provided for similarity matrix computation")
        return None
    
    # Filter embeddings by genre (assuming embeddings are structured as [year, genre, dim])
    # For simplicity, we'll assume the input embeddings are already filtered by genre
    # or that we're computing a global similarity matrix.
    
    years = sorted(embeddings.keys())
    if len(years) < 2:
        logger.warning("Insufficient years for similarity matrix computation")
        return None
    
    # Extract vectors for the genre (assuming 3D array: [year, genre, dim] or 2D: [year, dim])
    # For this implementation, we assume 2D arrays where each row is a year's genre vector
    vectors = [embeddings[y] for y in years]
    
    # Compute pairwise cosine similarity
    n = len(vectors)
    similarity_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i, n):
            if i == j:
                similarity_matrix[i, j] = 1.0
            else:
                sim = compute_pairwise_cosine_similarity(vectors[i], vectors[j])
                similarity_matrix[i, j] = sim
                similarity_matrix[j, i] = sim
    
    return similarity_matrix

def generate_genre_heatmap(similarity_matrix: np.ndarray, years: List[int], output_path: str) -> bool:
    """Generate interactive heatmap of genre similarity across years."""
    logger.info(f"Generating genre similarity heatmap: {output_path}")
    try:
        import plotly.graph_objects as go
        
        fig = go.Figure(data=go.Heatmap(
            z=similarity_matrix,
            x=[str(y) for y in years],
            y=[str(y) for y in years],
            colorscale='RdBu_r',
            zmid=0,
            colorbar=dict(title="Similarity")
        ))
        
        fig.update_layout(
            title="Genre Similarity Heatmap Across Years",
            xaxis_title="Year",
            yaxis_title="Year",
            width=800,
            height=600
        )
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(output_path)
        
        logger.info(f"Successfully generated genre similarity heatmap: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate genre similarity heatmap: {e}")
        return False

def main():
    """Main entry point for visualization generation with error handling and logging."""
    setup_logging()
    logger.info("Starting visualization generation pipeline")
    
    # Define paths
    similarity_csv = "data/derived/yearly_similarity.csv"
    embeddings_dir = "yearly_embeddings"
    trend_plot_output = "figures/similarity_trend.png"
    heatmap_output = "figures/genre_similarity_heatmap.html"
    
    success_count = 0
    total_tasks = 2
    
    # 1. Generate similarity trend plot
    try:
        similarity_data = load_similarity_data(similarity_csv)
        if similarity_data:
            if generate_similarity_trend_plot(similarity_data, trend_plot_output):
                success_count += 1
                logger.info("Trend plot generation: SUCCESS")
            else:
                logger.error("Trend plot generation: FAILED")
        else:
            logger.error("No similarity data loaded for trend plot")
    except FileNotFoundError as e:
        logger.error(f"Missing data file for trend plot: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during trend plot generation: {e}")
    
    # 2. Generate genre similarity heatmap
    try:
        embeddings = load_yearly_embeddings(embeddings_dir)
        if embeddings:
            # For heatmap, we need to compute similarity for a specific genre or all genres
            # Since the structure isn't fully defined, we'll compute a global similarity matrix
            # assuming each year has one aggregated genre vector per genre, but for simplicity
            # we'll use the first available vector (or aggregate if multiple)
            
            # Get all years
            years = sorted(embeddings.keys())
            if len(years) >= 2:
                # Compute similarity matrix for the first "genre" (assuming 2D: [year, dim])
                # If embeddings are 3D [year, genre, dim], we'd need to specify a genre
                # For now, we'll assume 2D and compute global similarity
                similarity_matrix = compute_genre_similarity_matrix(embeddings, "all")
                
                if similarity_matrix is not None:
                    if generate_genre_heatmap(similarity_matrix, years, heatmap_output):
                        success_count += 1
                        logger.info("Heatmap generation: SUCCESS")
                    else:
                        logger.error("Heatmap generation: FAILED")
                else:
                    logger.error("Failed to compute similarity matrix for heatmap")
            else:
                logger.error("Insufficient years for heatmap generation")
        else:
            logger.error("No embeddings found for heatmap generation")
    except FileNotFoundError as e:
        logger.error(f"Missing embeddings directory for heatmap: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during heatmap generation: {e}")
    
    # Log final status
    logger.info(f"Visualization pipeline completed: {success_count}/{total_tasks} tasks successful")
    if success_count < total_tasks:
        logger.warning("Some visualization tasks failed. Check pipeline_log.txt for details.")
    
    return success_count == total_tasks

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)