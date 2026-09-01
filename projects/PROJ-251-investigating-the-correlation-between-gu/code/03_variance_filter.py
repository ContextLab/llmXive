"""
T032a: Global Unsupervised Variance Filter

Identifies and filters taxa based on variance thresholds.
Removes taxa with variance < 1e-9.
Ensures at least k taxa remain (default k=10), otherwise keeps all available.
Raises NoFeaturesError if the filtered set is empty.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_processed_path, get_min_sample_size
from utils.logging_config import get_logger

logger = get_logger(__name__)

class NoFeaturesError(Exception):
    """Raised when no features remain after variance filtering."""
    pass

def load_preprocessed_data() -> pd.DataFrame:
    """Load the preprocessed dataset."""
    input_path = get_processed_path() / "cleared_with_diversity.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading preprocessed data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} samples")
    return df

def identify_zero_variance_taxa(df: pd.DataFrame, threshold: float = 1e-9) -> List[str]:
    """
    Identify taxa columns with variance below the threshold.
    
    Args:
        df: DataFrame containing subject data
        threshold: Variance threshold (default 1e-9)
    
    Returns:
        List of taxon names with variance < threshold
    """
    # Identify taxon columns (exclude metadata columns)
    metadata_cols = ['subject_id', 'titer_baseline', 'titer_post', 'log_titer', 'shannon_diversity']
    # Identify CLR columns if present, or raw abundance columns
    clr_cols = [col for col in df.columns if col.endswith('_clr')]
    abundance_cols = [col for col in df.columns if col not in metadata_cols and not col.endswith('_clr')]
    
    # Prefer CLR columns for correlation analysis
    taxon_cols = clr_cols if clr_cols else abundance_cols
    
    logger.info(f"Identified {len(taxon_cols)} taxon columns for variance filtering")
    
    zero_var_taxa = []
    for col in taxon_cols:
        # Calculate variance
        var = df[col].var()
        if var < threshold:
            zero_var_taxa.append(col)
            logger.debug(f"Taxon '{col}' has variance {var:.2e} < {threshold}")
    
    return zero_var_taxa

def filter_zero_variance_taxa(df: pd.DataFrame, zero_var_taxa: List[str], min_taxa: int = 10) -> List[str]:
    """
    Filter out zero-variance taxa, ensuring minimum number of taxa remain.
    
    Args:
        df: DataFrame containing subject data
        zero_var_taxa: List of taxa to remove
        min_taxa: Minimum number of taxa to retain (default 10)
    
    Returns:
        List of remaining taxon names
    
    Raises:
        NoFeaturesError: If no taxa remain after filtering
    """
    taxon_cols = [col for col in df.columns if col.endswith('_clr') or (col not in ['subject_id', 'titer_baseline', 'titer_post', 'log_titer', 'shannon_diversity'] and not col.endswith('_clr'))]
    
    # Start with all taxa
    filtered_taxa = [t for t in taxon_cols if t not in zero_var_taxa]
    
    logger.info(f"After variance filtering: {len(filtered_taxa)} taxa remain")
    
    # Edge case: If fewer than min_taxa remain, keep all available
    if len(filtered_taxa) < min_taxa:
        logger.warning(f"Only {len(filtered_taxa)} taxa remain (below min_taxa={min_taxa}). Keeping all available taxa.")
        filtered_taxa = [t for t in taxon_cols if t not in zero_var_taxa]
    
    # Edge case: If empty, raise error
    if len(filtered_taxa) == 0:
        raise NoFeaturesError("No features remain after variance filtering")
    
    return filtered_taxa

def save_results(filtered_taxa: List[str], output_path: Path) -> None:
    """Save the list of variance-filtered taxa to JSON."""
    result = {
        "taxa": filtered_taxa,
        "count": len(filtered_taxa),
        "description": "Taxa with variance >= 1e-9 (or all available if < 10)"
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved variance-filtered taxa list to {output_path} ({len(filtered_taxa)} taxa)")

def run_variance_filter() -> List[str]:
    """
    Execute the variance filtering pipeline.
    
    Returns:
        List of filtered taxon names
    """
    # Load data
    df = load_preprocessed_data()
    
    # Identify zero-variance taxa
    zero_var_taxa = identify_zero_variance_taxa(df)
    logger.info(f"Identified {len(zero_var_taxa)} zero-variance taxa")
    
    # Filter taxa
    filtered_taxa = filter_zero_variance_taxa(df, zero_var_taxa)
    
    # Save results
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "variance_filtered_taxa.json"
    save_results(filtered_taxa, output_path)
    
    return filtered_taxa

def main():
    """Main entry point for the variance filter script."""
    try:
        logger.info("Starting variance filtering pipeline (T032a)")
        filtered_taxa = run_variance_filter()
        logger.info(f"Variance filtering complete. {len(filtered_taxa)} taxa retained.")
        return 0
    except NoFeaturesError as e:
        logger.error(f"No features error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
