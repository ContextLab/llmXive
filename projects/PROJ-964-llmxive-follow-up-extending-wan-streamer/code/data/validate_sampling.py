"""
validate_sampling.py

Validates that the stratified sampling process preserves the distribution
of turn-taking events (interruptions and pauses) as required by FR-015.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_config_summary
from utils.validators import validate_dataframe, ValidationError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config() -> Dict[str, Any]:
    """Load configuration from config.py."""
    return get_config_summary()


def load_sampled_data(path: Path) -> pd.DataFrame:
    """Load the sampled dataset."""
    if not path.exists():
        raise FileNotFoundError(f"Sampled data file not found: {path}")
    
    logger.info(f"Loading sampled data from {path}")
    if path.suffix == '.parquet':
        df = pd.read_parquet(path)
    elif path.suffix == '.csv':
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    return df


def load_original_distribution(path: Path) -> pd.DataFrame:
    """Load the original (pre-sampling) dataset distribution."""
    if not path.exists():
        raise FileNotFoundError(f"Original data file not found: {path}")
    
    logger.info(f"Loading original data from {path}")
    if path.suffix == '.parquet':
        df = pd.read_parquet(path)
    elif path.suffix == '.csv':
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    return df


def compute_distribution(df: pd.DataFrame, event_column: str = 'turn_label') -> Dict[str, float]:
    """
    Compute the distribution of events in the dataframe.
    
    Args:
        df: DataFrame containing event labels
        event_column: Name of the column containing event labels
        
    Returns:
        Dictionary mapping event labels to their proportions
    """
    if event_column not in df.columns:
        raise ValidationError(f"Event column '{event_column}' not found in dataframe")
    
    total = len(df)
    if total == 0:
        return {}
    
    counts = df[event_column].value_counts(normalize=True)
    return counts.to_dict()


def compare_distributions(
    original: Dict[str, float],
    sampled: Dict[str, float],
    tolerance: float = 0.05
) -> Tuple[bool, Dict[str, float], Dict[str, float]]:
    """
    Compare two distributions and check if they are within tolerance.
    
    Args:
        original: Distribution from original data
        sampled: Distribution from sampled data
        tolerance: Maximum allowed difference for each category
        
    Returns:
        Tuple of (is_valid, original_dist, sampled_dist)
    """
    all_keys = set(original.keys()) | set(sampled.keys())
    
    differences = {}
    is_valid = True
    
    for key in all_keys:
        orig_val = original.get(key, 0.0)
        samp_val = sampled.get(key, 0.0)
        diff = abs(orig_val - samp_val)
        differences[key] = diff
        
        if diff > tolerance:
            is_valid = False
            logger.warning(f"Distribution mismatch for '{key}': "
                         f"original={orig_val:.4f}, sampled={samp_val:.4f}, "
                         f"diff={diff:.4f} > tolerance={tolerance}")
    
    return is_valid, original, sampled


def validate_sampling_distribution(
    original_df: pd.DataFrame,
    sampled_df: pd.DataFrame,
    event_column: str = 'turn_label',
    tolerance: float = 0.05,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Validate that sampling preserves the distribution of turn-taking events.
    
    Args:
        original_df: Original (pre-sampling) dataframe
        sampled_df: Sampled (post-sampling) dataframe
        event_column: Column name for event labels
        tolerance: Maximum allowed difference in proportions
        output_path: Optional path to save validation results
        
    Returns:
        Dictionary with validation results
    """
    logger.info("Starting sampling distribution validation")
    
    # Compute distributions
    original_dist = compute_distribution(original_df, event_column)
    sampled_dist = compute_distribution(sampled_df, event_column)
    
    logger.info(f"Original distribution: {original_dist}")
    logger.info(f"Sampled distribution: {sampled_dist}")
    
    # Compare distributions
    is_valid, orig_dist, samp_dist = compare_distributions(
        original_dist, sampled_dist, tolerance
    )
    
    # Compute statistics
    result = {
        'is_valid': is_valid,
        'tolerance': tolerance,
        'original_distribution': orig_dist,
        'sampled_distribution': samp_dist,
        'original_count': len(original_df),
        'sampled_count': len(sampled_df),
        'sampling_ratio': len(sampled_df) / len(original_df) if len(original_df) > 0 else 0,
        'differences': {k: abs(orig_dist.get(k, 0) - samp_dist.get(k, 0)) 
                      for k in set(orig_dist.keys()) | set(samp_dist.keys())}
    }
    
    # Log results
    if is_valid:
        logger.info("✅ Sampling distribution validation PASSED")
    else:
        logger.warning("❌ Sampling distribution validation FAILED")
    
    # Save results if path provided
    if output_path:
        import json
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Validation results saved to {output_path}")
    
    return result


def main():
    """Main entry point for validation."""
    parser = argparse.ArgumentParser(
        description='Validate sampling distribution preservation'
    )
    parser.add_argument(
        '--original',
        type=str,
        required=True,
        help='Path to original (pre-sampling) data file'
    )
    parser.add_argument(
        '--sampled',
        type=str,
        required=True,
        help='Path to sampled (post-sampling) data file'
    )
    parser.add_argument(
        '--event-column',
        type=str,
        default='turn_label',
        help='Column name for event labels (default: turn_label)'
    )
    parser.add_argument(
        '--tolerance',
        type=float,
        default=0.05,
        help='Maximum allowed difference in proportions (default: 0.05)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/metrics/sampling_validation.json',
        help='Path to save validation results'
    )
    
    args = parser.parse_args()
    
    try:
        # Load data
        original_df = load_original_distribution(Path(args.original))
        sampled_df = load_sampled_data(Path(args.sampled))
        
        # Validate schema
        validate_dataframe(original_df, required_columns=[args.event_column])
        validate_dataframe(sampled_df, required_columns=[args.event_column])
        
        # Perform validation
        result = validate_sampling_distribution(
            original_df,
            sampled_df,
            event_column=args.event_column,
            tolerance=args.tolerance,
            output_path=Path(args.output)
        )
        
        # Exit with appropriate code
        if result['is_valid']:
            logger.info("Validation successful")
            sys.exit(0)
        else:
            logger.error("Validation failed - distribution not preserved")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()