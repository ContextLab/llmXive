import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
import skbio
from skbio.stats.distance import permanova, DistanceMatrix
from skbio.diversity import beta_diversity
from code.src.utils.config import get_processed_data_dir, get_results_dir, get_logs_dir, set_global_seed

# Configure logging
logger = logging.getLogger(__name__)

def load_filtered_cohort() -> pd.DataFrame:
    """
    Load the filtered cohort data from the processed directory.
    Expects 'data/processed/filtered_cohort.csv' based on T011 output.
    """
    processed_dir = get_processed_data_dir()
    cohort_path = processed_dir / "filtered_cohort.csv"
    
    if not cohort_path.exists():
        raise FileNotFoundError(
            f"Filtered cohort not found at {cohort_path}. "
            "Please ensure T011 (filtering) has been executed successfully."
        )
    
    df = pd.read_csv(cohort_path)
    logger.info(f"Loaded {len(df)} rows from {cohort_path}")
    return df

def load_distance_matrix(cohort_df: pd.DataFrame, metric: str = "braycurtis") -> DistanceMatrix:
    """
    Calculate the beta diversity distance matrix from the OTU table portion of the cohort.
    
    The cohort is expected to contain columns for participant metadata and 
    OTU counts (columns starting with 'otu_' or similar, based on T008/T010 schema).
    For this implementation, we assume OTU columns are those not in the metadata schema.
    
    Metadata schema columns (from T003):
    participant_id, age, sex, bmi, cognitive_flexibility_score, 
    shannon_diversity, simpson_diversity, chao1, dietary_fiber, antibiotic_use
    """
    metadata_cols = [
        'participant_id', 'age', 'sex', 'bmi', 'cognitive_flexibility_score',
        'shannon_diversity', 'simpson_diversity', 'chao1', 'dietary_fiber', 'antibiotic_use'
    ]
    
    # Identify OTU columns (everything not in metadata_cols)
    otu_cols = [col for col in cohort_df.columns if col not in metadata_cols]
    
    if not otu_cols:
        raise ValueError(
            "No OTU columns found in the dataset. "
            "Expected columns starting with 'otu_' or similar based on schema."
        )
    
    otu_table = cohort_df[otu_cols].astype(float)
    
    # Ensure no negative values (OTU counts should be non-negative)
    if (otu_table < 0).any().any():
        logger.warning("Negative values found in OTU table. Clipping to zero.")
        otu_table = otu_table.clip(lower=0)
    
    # Calculate distance matrix
    logger.info(f"Calculating {metric} distance matrix for {len(otu_cols)} OTUs...")
    try:
        # skbio.beta_diversity expects a 2D array or DataFrame
        distance_matrix = beta_diversity(
            metric=metric,
            data=otu_table,
            ids=cohort_df['participant_id'].astype(str),
            validate=True
        )
        logger.info(f"Distance matrix calculated: shape {distance_matrix.shape}")
        return distance_matrix
    except Exception as e:
        logger.error(f"Error calculating distance matrix: {e}")
        raise

def run_permanova(
    distance_matrix: DistanceMatrix, 
    cohort_df: pd.DataFrame, 
    grouping_var: str = 'cognitive_quartile'
) -> Dict[str, Any]:
    """
    Run PERMANOVA analysis using skbio.stats.distance.permanova.
    
    Handles heavily skewed cognitive distributions by using cognitive quartiles
    as the grouping variable, as specified in the task requirements.
    
    Returns a dictionary with PERMANOVA results.
    """
    # Prepare metadata for PERMANOVA
    # Ensure the grouping variable exists
    if grouping_var not in cohort_df.columns:
        logger.warning(f"Grouping variable '{grouping_var}' not found. Creating cognitive quartiles.")
        cognitive_scores = cohort_df['cognitive_flexibility_score']
        
        # Check for skewness
        skewness = cognitive_scores.skew()
        logger.info(f"Cognitive flexibility score skewness: {skewness:.3f}")
        
        if abs(skewness) > 1.0:
            logger.info("High skewness detected. Using quartile-based grouping for PERMANOVA.")
            # Create quartiles
            cohort_df = cohort_df.copy()
            cohort_df['cognitive_quartile'] = pd.qcut(
                cognitive_scores, 
                q=4, 
                labels=['Q1', 'Q2', 'Q3', 'Q4'],
                duplicates='drop'
            )
            grouping_var = 'cognitive_quartile'
        else:
            # If not highly skewed, we could use continuous, but PERMANOVA requires categorical
            # Fall back to quartiles anyway for consistency
            cohort_df = cohort_df.copy()
            cohort_df['cognitive_quartile'] = pd.qcut(
                cognitive_scores, 
                q=4, 
                labels=['Q1', 'Q2', 'Q3', 'Q4'],
                duplicates='drop'
            )
            grouping_var = 'cognitive_quartile'
    
    # Extract metadata for the grouping variable
    metadata = cohort_df[[grouping_var]].astype(str)
    
    # Run PERMANOVA
    logger.info(f"Running PERMANOVA with grouping variable: {grouping_var}")
    try:
        permanova_result = permanova(
            distance_matrix=distance_matrix,
            metadata=metadata,
            column=grouping_var,
            permutations=999
        )
        
        results = {
            'test_type': 'PERMANOVA',
            'metric': 'Bray-Curtis', # Default, could be parameterized
            'grouping_variable': grouping_var,
            'f_statistic': float(permanova_result['test statistic']),
            'p_value': float(permanova_result['p-value']),
            'r_squared': float(permanova_result['R2']),
            'n_permutations': 999,
            'sample_size': len(cohort_df),
            'skewness_check': float(cohort_df['cognitive_flexibility_score'].skew())
        }
        
        logger.info(f"PERMANOVA completed: R2={results['r_squared']:.4f}, p={results['p_value']:.4f}")
        return results
        
    except Exception as e:
        logger.error(f"PERMANOVA failed: {e}")
        raise

def main():
    """
    Main entry point for beta diversity analysis.
    
    Workflow:
    1. Load filtered cohort
    2. Calculate beta diversity distance matrix
    3. Run PERMANOVA with cognitive quartiles
    4. Save results to data/results/beta_diversity_results.json
    """
    set_global_seed(42)
    logs_dir = get_logs_dir()
    results_dir = get_results_dir()
    
    # Setup file logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / 'beta_diversity.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    try:
        # Step 1: Load data
        logger.info("Step 1: Loading filtered cohort...")
        cohort_df = load_filtered_cohort()
        
        # Step 2: Calculate distance matrix
        logger.info("Step 2: Calculating beta diversity distance matrix...")
        distance_matrix = load_distance_matrix(cohort_df, metric='braycurtis')
        
        # Step 3: Run PERMANOVA
        logger.info("Step 3: Running PERMANOVA...")
        results = run_permanova(distance_matrix, cohort_df, grouping_var='cognitive_flexibility_score')
        
        # Step 4: Save results
        output_path = results_dir / 'beta_diversity_results.json'
        import json
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        print(f"PERMANOVA Analysis Complete. Results saved to {output_path}")
        print(f"R-squared: {results['r_squared']:.4f}")
        print(f"P-value: {results['p_value']:.4f}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == '__main__':
    main()
