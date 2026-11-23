import os
import sys
import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional, Tuple, Callable, Union

# Import config utilities from the project's utils module
from utils.config import get_data_dir, get_models_dir, get_seed, set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_stratification(df: pd.DataFrame, species_col: str = 'species_id', label_col: str = 'foraging_guild') -> bool:
    """
    Validate that the dataframe has valid species and label columns for stratification.
    Ensures no NaN values in the stratification or label columns.
    """
    if species_col not in df.columns:
        raise ValueError(f"Column '{species_col}' not found in dataframe.")
    if label_col not in df.columns:
        raise ValueError(f"Column '{label_col}' not found in dataframe.")
    
    if df[species_col].isnull().any():
        raise ValueError(f"Null values found in '{species_col}'.")
    if df[label_col].isnull().any():
        raise ValueError(f"Null values found in '{label_col}'.")
    
    return True

def stratified_permutation(
    X: np.ndarray,
    y: np.ndarray,
    species: np.ndarray,
    rng: np.random.Generator
) -> np.ndarray:
    """
    Perform a single stratified permutation.
    Shuffles labels y within each species group.
    
    Parameters:
    -----------
    X : np.ndarray
        Feature matrix (unused in permutation logic, but kept for signature consistency).
    y : np.ndarray
        Original labels.
    species : np.ndarray
        Species identifiers corresponding to each row in X and y.
    rng : np.random.Generator
        NumPy random generator for reproducibility.
    
    Returns:
    --------
    np.ndarray
        Permuted labels array.
    """
    y_permuted = np.empty_like(y)
    unique_species = np.unique(species)
    
    for sp in unique_species:
        mask = (species == sp)
        # Extract labels for this species
        sp_labels = y[mask]
        # Shuffle them in-place
        rng.shuffle(sp_labels)
        # Assign back to the permuted array
        y_permuted[mask] = sp_labels
        
    return y_permuted

def calculate_null_distribution(
    X: np.ndarray,
    y: np.ndarray,
    species: np.ndarray,
    n_permutations: int,
    metric_func: Callable[[np.ndarray, np.ndarray], float],
    rng: np.random.Generator
) -> np.ndarray:
    """
    Calculate the null distribution by running the stratified permutation test.
    
    Parameters:
    -----------
    X : np.ndarray
        Feature matrix.
    y : np.ndarray
        Original labels.
    species : np.ndarray
        Species identifiers.
    n_permutations : int
        Number of permutations to run.
    metric_func : Callable
        Function that takes (y_true, y_pred) or (X, y) and returns a scalar score.
        For this test, we assume it takes (X, y_permuted) to calculate the score under null.
    rng : np.random.Generator
        NumPy random generator.
    
    Returns:
    --------
    np.ndarray
        Array of scores from the null distribution.
    """
    null_scores = np.zeros(n_permutations)
    
    for i in range(n_permutations):
        y_perm = stratified_permutation(X, y, species, rng)
        # Calculate the metric on the permuted labels
        # We pass X and the permuted y to the metric function
        score = metric_func(X, y_perm)
        null_scores[i] = score
        
        if (i + 1) % 100 == 0:
            logger.info(f"Completed {i + 1}/{n_permutations} permutations")
    
    return null_scores

def run_stratified_permutation_test(
    data_path: Union[str, Path],
    output_path: Union[str, Path],
    n_permutations: int = 1000,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Main entry point to run the stratified permutation test.
    Reads raw merged observations, performs the test, and saves the null distribution.
    
    Parameters:
    -----------
    data_path : str or Path
        Path to the raw merged observations CSV.
    output_path : str or Path
        Path where the null_distribution.npy will be saved.
    n_permutations : int
        Number of permutations (default 1000).
    seed : int, optional
        Random seed for reproducibility.
    
    Returns:
    --------
    np.ndarray
        The calculated null distribution array.
    """
    # Set seed if provided
    if seed is not None:
        set_seed(seed)
        np.random.seed(seed)
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()

    # Load data
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Identify feature columns (land cover proportions)
    # We assume these columns exist based on T039b and T039d
    feature_cols = [
        'forest_prop_100m', 
        'grassland_prop_100m', 
        'wetland_prop_100m', 
        'urban_prop_100m', 
        'other_prop_100m'
    ]
    
    # Validate presence of feature columns
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns: {missing_cols}")
    
    # Validate stratification columns
    validate_stratification(df, species_col='species_id', label_col='foraging_guild')
    
    X = df[feature_cols].values
    y = df['foraging_guild'].values
    species = df['species_id'].values
    
    logger.info(f"Data shape: {X.shape}, Unique species: {len(np.unique(species))}, Unique guilds: {len(np.unique(y))}")
    
    # Define a simple metric function for the null distribution.
    # Since we don't have the trained model here, we use a simple heuristic:
    # The variance of the mean land-cover proportions across guilds.
    # If land cover predicts guild, the means should be distinct (high variance of means).
    # Under null (shuffled), this variance should be lower/random.
    def metric_func(X_perm: np.ndarray, y_perm: np.ndarray) -> float:
        """
        Calculate a score representing the separation of land-cover means by guild.
        Higher score implies better separation (stronger signal).
        """
        unique_guilds = np.unique(y_perm)
        if len(unique_guilds) < 2:
            return 0.0
        
        # Calculate mean land cover for each guild
        guild_means = []
        for guild in unique_guilds:
            mask = (y_perm == guild)
            if np.sum(mask) > 0:
                guild_means.append(X_perm[mask].mean(axis=0))
        
        guild_means = np.array(guild_means)
        
        # Calculate variance of these means across guilds (sum of variances per feature)
        # This is a proxy for "how different are the guilds in land cover space?"
        score = np.var(guild_means, axis=0).sum()
        return score

    logger.info(f"Running {n_permutations} stratified permutations...")
    null_distribution = calculate_null_distribution(
        X, y, species, n_permutations, metric_func, rng
    )
    
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the null distribution
    logger.info(f"Saving null distribution to {output_path}")
    np.save(output_path, null_distribution)
    
    # Log summary statistics
    logger.info(f"Null distribution stats: mean={null_distribution.mean():.4f}, std={null_distribution.std():.4f}")
    
    return null_distribution

def main():
    """
    Main function to execute the stratified permutation test.
    """
    # Define paths based on project structure
    data_dir = get_data_dir()
    models_dir = get_models_dir()
    
    input_file = data_dir / 'processed' / 'merged_observations.csv'
    output_file = models_dir / 'null_distribution.npy'
    
    # Check if input file exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    # Configuration
    N_PERMUTATIONS = 1000
    SEED = 42
    
    try:
        null_dist = run_stratified_permutation_test(
            data_path=input_file,
            output_path=output_file,
            n_permutations=N_PERMUTATIONS,
            seed=SEED
        )
        
        # Verification
        assert len(null_dist) == N_PERMUTATIONS, f"Expected {N_PERMUTATIONS} values, got {len(null_dist)}"
        logger.info("Stratified permutation test completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during permutation test: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
