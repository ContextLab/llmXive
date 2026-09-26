"""
Beta Diversity Analysis Module.

Implements PERMANOVA (Permutational Multivariate Analysis of Variance)
to test for associations between beta diversity distances and continuous
cognitive flexibility scores.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
import skbio
from skbio.stats.distance import permanova

from code.src.utils.config import (
    get_project_root,
    get_results_dir,
    get_processed_data_dir,
    set_global_seed,
    SEED
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_filtered_cohort() -> pd.DataFrame:
    """
    Load the filtered cohort data from the processed directory.

    Returns:
        pd.DataFrame: The filtered cohort with microbiome and cognitive data.

    Raises:
        FileNotFoundError: If the filtered cohort file does not exist.
    """
    processed_dir = get_processed_data_dir()
    cohort_path = processed_dir / "filtered_cohort.csv"

    if not cohort_path.exists():
        raise FileNotFoundError(
            f"Filtered cohort not found at {cohort_path}. "
            "Please run the ingestion and filtering pipeline first."
        )

    logger.info(f"Loading filtered cohort from {cohort_path}")
    return pd.read_csv(cohort_path)


def load_distance_matrix(cohort: pd.DataFrame) -> Tuple[pd.DataFrame, skbio.DistanceMatrix]:
    """
    Calculate Bray-Curtis dissimilarity matrix from OTU table.

    Args:
        cohort (pd.DataFrame): The filtered cohort containing OTU counts.

    Returns:
        Tuple[pd.DataFrame, skbio.DistanceMatrix]:
            - The OTU table (participants x taxa) as DataFrame.
            - The calculated Bray-Curtis distance matrix.
    """
    # Identify OTU columns (assuming they start with 'otu_' or contain specific pattern)
    # Based on synthetic_gen, OTU columns are typically named 'otu_1', 'otu_2', etc.
    otu_columns = [col for col in cohort.columns if col.startswith('otu_')]

    if not otu_columns:
        raise ValueError(
            "No OTU columns found in the cohort. "
            "Expected columns starting with 'otu_'."
        )

    logger.info(f"Found {len(otu_columns)} OTU columns for beta diversity calculation.")

    otu_table = cohort.set_index('participant_id')[otu_columns]

    # Convert to skbio OrdinationTable / DistanceMatrix compatible format
    # skbio expects a 2D array-like where rows are samples
    distance_matrix = skbio.stats.distance.braycurtis(otu_table.values)

    # Create a proper skbio DistanceMatrix object
    dm = skbio.DistanceMatrix(distance_matrix, ids=otu_table.index)

    return otu_table, dm


def run_permanova(
    distance_matrix: skbio.DistanceMatrix,
    cohort: pd.DataFrame,
    variable: str = 'cognitive_score',
    permutations: int = 999
) -> Dict[str, Any]:
    """
    Perform PERMANOVA analysis to test association between distance matrix
    and a continuous variable (cognitive score).

    Args:
        distance_matrix (skbio.DistanceMatrix): The beta diversity distance matrix.
        cohort (pd.DataFrame): The cohort dataframe containing the variable.
        variable (str): Name of the continuous variable to test against.
        permutations (int): Number of permutations for the test.

    Returns:
        Dict[str, Any]: Dictionary containing PERMANOVA results.
    """
    if variable not in cohort.columns:
        raise ValueError(f"Variable '{variable}' not found in cohort.")

    # Ensure the distance matrix IDs match the cohort index
    # PERMANOVA expects the grouping/continuous variable to align with the distance matrix rows
    # We need to pass the dataframe with the variable aligned to the distance matrix IDs
    df_for_permanova = cohort.set_index('participant_id')[[variable]]

    # Filter to only include samples present in both
    common_ids = list(set(distance_matrix.ids) & set(df_for_permanova.index))
    
    if len(common_ids) == 0:
        raise ValueError("No common participant IDs between distance matrix and cohort.")
    
    logger.info(f"Running PERMANOVA with {len(common_ids)} samples.")

    # Subset the dataframe to match the distance matrix order
    df_aligned = df_for_permanova.loc[common_ids]

    # Run PERMANOVA
    # Note: skbio.stats.distance.permanova expects the dataframe to have the variable
    result = permanova(
        distance_matrix,
        df_aligned,
        column=variable,
        permutations=permutations
    )

    logger.info(f"PERMANOVA completed. F-statistic: {result['test_statistic']:.4f}, p-value: {result['p_value']:.4f}")

    return {
        "method": "PERMANOVA",
        "distance_metric": "bray_curtis",
        "variable": variable,
        "n_permutations": permutations,
        "n_samples": len(common_ids),
        "f_statistic": result["test_statistic"],
        "r_squared": result["pseudo_f"] if "pseudo_f" in result else result.get("r_squared", None), # skbio returns pseudo_f in some versions, or r_squared
        "p_value": result["p_value"],
        "p_value_method": result.get("p_value_method", "permutation")
    }


def main():
    """
    Main entry point for Beta Diversity Analysis.
    Executes PERMANOVA and saves results to data/results/beta_diversity_results.json
    """
    logger.info("Starting Beta Diversity Analysis (PERMANOVA)...")
    
    # Set global seed for reproducibility
    set_global_seed(SEED)

    try:
        # 1. Load Data
        cohort = load_filtered_cohort()
        
        # 2. Calculate Distance Matrix
        otu_table, distance_matrix = load_distance_matrix(cohort)
        
        # 3. Run PERMANOVA
        results = run_permanova(
            distance_matrix, 
            cohort, 
            variable='cognitive_score',
            permutations=999
        )

        # 4. Save Results
        results_dir = get_results_dir()
        output_path = results_dir / "beta_diversity_results.json"
        
        import json
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        print(f"PERMANOVA Analysis Complete. Results saved to: {output_path}")
        print(json.dumps(results, indent=2))

    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during PERMANOVA: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
