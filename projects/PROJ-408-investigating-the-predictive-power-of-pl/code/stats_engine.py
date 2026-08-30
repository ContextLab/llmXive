import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from config import get_config
from logging_config import get_logger, log_pipeline_step

logger = get_logger(__name__)

def load_distance_matrix(file_path: Union[str, Path]) -> Tuple[np.ndarray, List[str]]:
    """
    Load a distance matrix from a CSV file.
    
    Args:
        file_path: Path to the CSV file containing the distance matrix.
        
    Returns:
        Tuple of (numpy array of distances, list of species labels).
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Distance matrix file not found: {file_path}")
    
    df = pd.read_csv(file_path, index_col=0)
    labels = df.index.tolist()
    matrix = df.values.astype(float)
    
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"Distance matrix must be square. Got shape {matrix.shape}")
        
    return matrix, labels

def calculate_jaccard_dissimilarity_matrix(
    metabolite_matrix: np.ndarray,
    labels: List[str]
) -> np.ndarray:
    """
    Calculate Jaccard dissimilarity matrix from binary metabolite presence/absence vectors.
    
    Args:
        metabolite_matrix: 2D numpy array where rows are species and columns are metabolites.
                         Values should be binary (0 or 1).
        labels: List of species labels corresponding to the rows.
        
    Returns:
        2D numpy array of Jaccard dissimilarities.
    """
    from scipy.spatial.distance import pdist, squareform
    
    if metabolite_matrix.shape[0] != len(labels):
        raise ValueError(f"Number of rows ({metabolite_matrix.shape[0]}) must match number of labels ({len(labels)})")
    
    # Calculate pairwise Jaccard distances
    distances = pdist(metabolite_matrix, metric='jaccard')
    dissimilarity_matrix = squareform(distances)
    
    logger.info(f"Calculated Jaccard dissimilarity matrix for {len(labels)} species")
    return dissimilarity_matrix

def run_mantel_test(
    matrix1: np.ndarray,
    matrix2: np.ndarray,
    n_permutations: int = 9999,
    seed: Optional[int] = None
) -> Dict[str, float]:
    """
    Perform a Mantel test between two distance matrices.
    
    Args:
        matrix1: First distance matrix (e.g., phylogenetic distances).
        matrix2: Second distance matrix (e.g., metabolite dissimilarities).
        n_permutations: Number of permutations for significance testing.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing 'r' (correlation coefficient), 'p_value', and 'null_distribution'.
    """
    if matrix1.shape != matrix2.shape:
        raise ValueError(f"Matrices must have the same shape. Got {matrix1.shape} and {matrix2.shape}")
    
    if seed is not None:
        np.random.seed(seed)
    
    # Flatten upper triangles (excluding diagonal)
    n = matrix1.shape[0]
    idx = np.triu_indices(n, k=1)
    v1 = matrix1[idx]
    v2 = matrix2[idx]
    
    # Calculate observed correlation
    r_observed = np.corrcoef(v1, v2)[0, 1]
    
    # Permutation test
    null_distributions = []
    for _ in range(n_permutations):
        np.random.shuffle(v2)
        r_perm = np.corrcoef(v1, v2)[0, 1]
        null_distributions.append(r_perm)
    
    null_distribution = np.array(null_distributions)
    
    # Calculate p-value (two-tailed)
    # Count how many permuted correlations are as extreme or more extreme than observed
    extreme_count = np.sum(np.abs(null_distribution) >= np.abs(r_observed))
    p_value = (extreme_count + 1) / (n_permutations + 1)
    
    result = {
        'r': float(r_observed),
        'p_value': float(p_value),
        'null_distribution': null_distribution.tolist(),
        'n_permutations': n_permutations
    }
    
    logger.info(f"Mantel test completed: r={r_observed:.4f}, p={p_value:.4f}")
    return result

def calculate_climate_distance_matrix(
    climate_data: pd.DataFrame,
    labels: List[str]
) -> np.ndarray:
    """
    Calculate climate distance matrix using Euclidean distance on normalized continuous climate vectors.
    
    This function takes USDA PLANTS climate zone data (converted to continuous vectors)
    and computes pairwise Euclidean distances between species based on their climate profiles.
    
    Args:
        climate_data: DataFrame where rows are species and columns are continuous climate variables.
                    Expected columns include normalized values for temperature, precipitation, etc.
        labels: List of species labels corresponding to the rows in climate_data.
        
    Returns:
        2D numpy array of Euclidean distances between species based on climate profiles.
        
    Raises:
        ValueError: If the number of rows in climate_data doesn't match the number of labels.
                    If climate_data contains no numeric columns.
    """
    if len(climate_data) != len(labels):
        raise ValueError(f"Number of rows in climate_data ({len(climate_data)}) must match number of labels ({len(labels)})")
    
    # Ensure we have numeric data
    numeric_data = climate_data.select_dtypes(include=[np.number])
    
    if numeric_data.empty:
        raise ValueError("Climate data contains no numeric columns for distance calculation")
    
    # Normalize the data (z-score normalization)
    # This is crucial for Euclidean distance to be meaningful across different scales
    normalized_data = (numeric_data - numeric_data.mean()) / numeric_data.std()
    
    # Fill any NaN values (from division by zero if std=0) with 0
    normalized_data = normalized_data.fillna(0)
    
    # Calculate pairwise Euclidean distances
    from scipy.spatial.distance import pdist, squareform
    
    distances = pdist(normalized_data.values, metric='euclidean')
    distance_matrix = squareform(distances)
    
    logger.info(f"Calculated climate distance matrix for {len(labels)} species using Euclidean distance on normalized climate vectors")
    
    return distance_matrix

def run_partial_mantel_test(
    matrix1: np.ndarray,
    matrix2: np.ndarray,
    control_matrix: np.ndarray,
    n_permutations: int = 9999,
    seed: Optional[int] = None
) -> Dict[str, float]:
    """
    Perform a Partial Mantel test, controlling for a third matrix.
    
    This tests the correlation between matrix1 and matrix2 while controlling for the effect of control_matrix.
    
    Args:
        matrix1: First distance matrix (e.g., phylogenetic distances).
        matrix2: Second distance matrix (e.g., metabolite dissimilarities).
        control_matrix: Control matrix (e.g., climate distances) to partial out.
        n_permutations: Number of permutations for significance testing.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing 'partial_r', 'p_value', 'standard_r', and 'null_distribution'.
    """
    if matrix1.shape != matrix2.shape or matrix1.shape != control_matrix.shape:
        raise ValueError(f"All matrices must have the same shape. Got {matrix1.shape}, {matrix2.shape}, and {control_matrix.shape}")
    
    if seed is not None:
        np.random.seed(seed)
    
    n = matrix1.shape[0]
    idx = np.triu_indices(n, k=1)
    v1 = matrix1[idx]
    v2 = matrix2[idx]
    vc = control_matrix[idx]
    
    # Calculate standard Mantel r
    standard_r = np.corrcoef(v1, v2)[0, 1]
    
    # Calculate partial correlation
    # Partial correlation r12.3 = (r12 - r13*r23) / sqrt((1-r13^2)*(1-r23^2))
    r13 = np.corrcoef(v1, vc)[0, 1]
    r23 = np.corrcoef(v2, vc)[0, 1]
    
    numerator = standard_r - (r13 * r23)
    denominator = np.sqrt((1 - r13**2) * (1 - r23**2))
    
    if denominator == 0:
        partial_r = 0.0
    else:
        partial_r = numerator / denominator
    
    # Permutation test for partial Mantel
    # We permute the residuals of matrix2 after regressing on control_matrix
    # This is the standard approach for partial Mantel tests
    
    # Regress v2 on vc to get residuals
    # Using simple linear regression: v2 = a + b*vc + error
    slope, intercept = np.polyfit(vc, v2, 1)
    predicted_v2 = slope * vc + intercept
    residuals_v2 = v2 - predicted_v2
    
    # Regress v1 on vc to get residuals (optional, but more rigorous)
    slope1, intercept1 = np.polyfit(vc, v1, 1)
    predicted_v1 = slope1 * vc + intercept1
    residuals_v1 = v1 - predicted_v1
    
    null_distributions = []
    for _ in range(n_permutations):
        np.random.shuffle(residuals_v2)
        # Calculate correlation between residuals
        r_perm = np.corrcoef(residuals_v1, residuals_v2)[0, 1]
        if np.isnan(r_perm):
            r_perm = 0.0
        null_distributions.append(r_perm)
    
    null_distribution = np.array(null_distributions)
    
    # Calculate p-value (two-tailed)
    extreme_count = np.sum(np.abs(null_distribution) >= np.abs(partial_r))
    p_value = (extreme_count + 1) / (n_permutations + 1)
    
    result = {
        'partial_r': float(partial_r),
        'p_value': float(p_value),
        'standard_r': float(standard_r),
        'null_distribution': null_distribution.tolist(),
        'n_permutations': n_permutations
    }
    
    logger.info(f"Partial Mantel test completed: partial_r={partial_r:.4f}, standard_r={standard_r:.4f}, p={p_value:.4f}")
    return result

def save_mantel_results(
    results: Dict[str, any],
    output_path: Union[str, Path]
) -> None:
    """
    Save Mantel test results to a JSON file.
    
    Args:
        results: Dictionary containing Mantel test results.
        output_path: Path to the output JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Mantel results saved to {output_path}")

def load_climate_data_from_usda(
    species_list: List[str],
    climate_data_file: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """
    Load climate data for a list of species from USDA PLANTS database.
    
    This function expects climate data to be pre-fetched and stored in a CSV file
    with species names as index and continuous climate variables as columns.
    
    Args:
        species_list: List of species names to retrieve climate data for.
        climate_data_file: Optional path to a pre-existing climate data CSV file.
                          If not provided, attempts to load from default location.
                          
    Returns:
        DataFrame with climate data for the requested species.
        
    Raises:
        ValueError: If no real climate data source is available or if data fetch fails.
    """
    config = get_config()
    
    if climate_data_file is None:
        climate_data_file = config.get('climate_data_file', 'data/processed/climate_data.csv')
    
    climate_path = Path(climate_data_file)
    
    if not climate_path.exists():
        raise FileNotFoundError(
            f"Climate data file not found at {climate_path}. "
            "Please ensure USDA PLANTS climate data has been fetched via T024."
        )
    
    df = pd.read_csv(climate_path, index_col=0)
    
    # Filter for requested species
    available_species = [s for s in species_list if s in df.index]
    missing_species = [s for s in species_list if s not in df.index]
    
    if len(missing_species) > 0:
        logger.warning(f"Climate data missing for {len(missing_species)} species: {missing_species[:5]}...")
    
    result_df = df.loc[available_species]
    
    if result_df.empty:
        raise ValueError(
            f"No climate data available for any of the requested species: {species_list[:5]}..."
        )
    
    logger.info(f"Loaded climate data for {len(result_df)} species")
    return result_df