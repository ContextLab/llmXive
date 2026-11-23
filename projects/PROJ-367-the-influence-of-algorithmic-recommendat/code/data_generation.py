import os
import random
import logging
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
import pandas as pd

from config import ProjectConfig

logger = logging.getLogger(__name__)

def generate_synthetic_dataset(
    n_samples: int = 1000,
    n_categories: int = 20,
    output_path: str = "data/raw/synthetic_enrollments.csv",
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate a synthetic dataset mimicking user-algorithm interactions.
    
    Creates distinct recommended_categories and enrolled_categories columns
    with temporal separation to satisfy "Causal Independence" assumption.
    
    Args:
        n_samples: Number of records to generate
        n_categories: Number of distinct categories
        output_path: Path to save the CSV file
        seed: Random seed for reproducibility
        
    Returns:
        pd.DataFrame: Generated synthetic dataset
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # Define categories
    categories = [f"Category_{i}" for i in range(n_categories)]
    
    # Generate user and session IDs
    user_ids = [f"user_{i}" for i in range(n_samples)]
    session_ids = [f"session_{i}" for i in range(n_samples)]
    
    # Generate recommended categories (algorithm-driven)
    # Simulate algorithm recommending multiple categories per session
    recommended_categories = []
    for _ in range(n_samples):
        n_recs = random.randint(2, 5)
        recs = random.choices(categories, k=n_recs)
        recommended_categories.append(recs)
    
    # Generate enrolled categories (user-driven, with some algorithmic influence)
    # Add temporal separation: later sessions show more influence
    enrolled_categories = []
    for i in range(n_samples):
        # Base preference (intrinsic)
        n_enrolled = random.randint(1, 4)
        
        # Algorithmic influence increases over time (temporal separation)
        # This satisfies the "Causal Independence" assumption by ensuring
        # the influence factor is a function of time/index, not the current recommendation
        influence_factor = min(0.8, 0.2 + (i / n_samples) * 0.6)
        
        if random.random() < influence_factor:
            # User follows algorithm recommendation
            recs = recommended_categories[i]
            # User picks 1-2 from recommendations
            n_pick = random.randint(1, min(2, len(recs)))
            picks = random.sample(recs, n_pick)
            
            # Add some intrinsic categories
            n_intrinsic = n_enrolled - len(picks)
            if n_intrinsic > 0:
                intrinsic = random.choices(categories, k=n_intrinsic)
                picks.extend(intrinsic)
            
            enrolled_categories.append(picks)
        else:
            # User follows intrinsic preference
            enrolled = random.choices(categories, k=n_enrolled)
            enrolled_categories.append(enrolled)
    
    # Create DataFrame
    df = pd.DataFrame({
        'user_id': user_ids,
        'session_id': session_ids,
        'recommended_categories': recommended_categories,
        'enrolled_categories': enrolled_categories,
        'timestamp': pd.date_range('2024-01-01', periods=n_samples, freq='H')
    })
    
    # Convert lists to JSON strings for CSV compatibility
    df['recommended_categories'] = df['recommended_categories'].apply(lambda x: str(x))
    df['enrolled_categories'] = df['enrolled_categories'].apply(lambda x: str(x))
    
    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Generated {n_samples} synthetic records saved to {output_path}")
    
    return df

def main():
    """Main entry point for synthetic data generation."""
    # Load config if needed, but using defaults for generation
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    generate_synthetic_dataset()
    logger.info("Synthetic data generation complete")

if __name__ == "__main__":
    main()