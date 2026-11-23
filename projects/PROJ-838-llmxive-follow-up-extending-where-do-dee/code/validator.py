"""
Validator module for analyzing dataset properties and configuration parameters.

This module provides functions to validate hyperparameters and dataset characteristics
before running the main analysis pipeline.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from datasets import load_dataset

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_cutoff_depth(dataset_id: str = "NJU-LINK/TELBench", 
                          sample_size: int = 1000,
                          output_path: str = "data/processed/cutoff_depth_validation.json") -> Dict[str, Any]:
    """
    Perform a preliminary analysis of the dataset's span distribution to justify
    the cutoff_depth value (default 0.30) or recommend a different value.
    
    This function:
    1. Streams a sample of trajectories from the dataset
    2. Analyzes the distribution of span counts per trajectory
    3. Evaluates whether the current cutoff_depth=0.30 is appropriate
    4. Writes results to a JSON file
    
    Args:
        dataset_id: HuggingFace dataset identifier
        sample_size: Number of trajectories to sample for analysis
        output_path: Path to write the validation results JSON
    
    Returns:
        Dictionary containing validation results and statistics
    
    Raises:
        ValueError: If no valid trajectories are found in the dataset
        RuntimeError: If the dataset cannot be loaded
    """
    logger.info(f"Starting cutoff depth validation for dataset: {dataset_id}")
    logger.info(f"Sampling {sample_size} trajectories for analysis")
    
    # Load dataset in streaming mode to handle large datasets
    try:
        dataset = load_dataset(dataset_id, streaming=True)
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {e}")
        raise RuntimeError(f"Cannot load dataset {dataset_id}: {e}")
    
    # Extract span counts from trajectories
    span_counts = []
    truncated_count = 0
    trajectory_ids = []
    
    # Iterate through the dataset with a limit
    count = 0
    for item in dataset['train']:
        if count >= sample_size:
            break
        
        # Extract span count if available
        if 'spans' in item and isinstance(item['spans'], list):
            span_count = len(item['spans'])
            if span_count > 0:
                span_counts.append(span_count)
                trajectory_ids.append(item.get('id', f'traj_{count}'))
                
                # Track trajectories that might be too short for meaningful analysis
                # (less than 3 spans would result in < 1 span at 30% cutoff)
                if span_count < 3:
                    truncated_count += 1
            else:
                logger.warning(f"Trajectory {item.get('id', count)} has empty spans list")
        else:
            logger.warning(f"Trajectory {item.get('id', count)} missing 'spans' field or not a list")
        
        count += 1
    
    if not span_counts:
        error_msg = "No valid trajectories found in the dataset"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Calculate statistics
    span_counts_array = np.array(span_counts)
    mean_spans = float(np.mean(span_counts_array))
    median_spans = float(np.median(span_counts_array))
    min_spans = int(np.min(span_counts_array))
    max_spans = int(np.max(span_counts_array))
    std_spans = float(np.std(span_counts_array))
    
    # Current configuration
    current_cutoff_depth = 0.30
    
    # Calculate effective span counts at current cutoff
    effective_spans_at_current = np.floor(span_counts_array * current_cutoff_depth)
    mean_effective_spans = float(np.mean(effective_spans_at_current))
    median_effective_spans = float(np.median(effective_spans_at_current))
    
    # Check how many trajectories would have 0 or 1 spans at current cutoff
    zero_or_one_spans = np.sum(effective_spans_at_current <= 1)
    zero_or_one_percentage = float(zero_or_one_spans / len(span_counts) * 100)
    
    # Recommendation logic
    # If a large percentage of trajectories have very few effective spans,
    # we might want to increase cutoff_depth
    recommendation = "appropriate"
    justification_parts = []
    
    if zero_or_one_percentage > 30:
        recommendation = "increase"
        justification_parts.append(
            f"High percentage ({zero_or_one_percentage:.1f}%) of trajectories have <=1 effective spans "
            f"at cutoff_depth={current_cutoff_depth}. Consider increasing cutoff_depth to capture more context."
        )
    elif zero_or_one_percentage < 5:
        justification_parts.append(
            f"Low percentage ({zero_or_one_percentage:.1f}%) of trajectories have <=1 effective spans "
            f"at cutoff_depth={current_cutoff_depth}. Current value appears appropriate."
        )
    
    # Suggest alternative if needed
    recommended_cutoff_depth = current_cutoff_depth
    if recommendation == "increase":
        # Try to find a cutoff that keeps <=10% of trajectories with <=1 effective span
        for test_depth in [0.35, 0.40, 0.45, 0.50]:
            test_effective = np.floor(span_counts_array * test_depth)
            test_zero_or_one = np.sum(test_effective <= 1) / len(span_counts) * 100
            if test_zero_or_one <= 10:
                recommended_cutoff_depth = test_depth
                justification_parts.append(
                    f"Recommended cutoff_depth={recommended_cutoff_depth} would reduce "
                    f"trajectories with <=1 effective spans to {test_zero_or_one:.1f}%."
                )
                break
        else:
            recommended_cutoff_depth = 0.50
            justification_parts.append(
                f"Even at cutoff_depth=0.50, some trajectories may have limited spans. "
                f"Consider dataset filtering or accepting the limitation."
            )
    
    justification = " ".join(justification_parts) if justification_parts else \
        f"Current cutoff_depth={current_cutoff_depth} is appropriate for the dataset distribution."
    
    # Build result dictionary
    result = {
        "current_cutoff_depth": current_cutoff_depth,
        "recommended_cutoff_depth": recommended_cutoff_depth,
        "recommendation": recommendation,
        "justification": justification,
        "valid": recommendation == "appropriate" or recommended_cutoff_depth <= 0.50,
        "statistics": {
            "mean_spans": mean_spans,
            "median_spans": median_spans,
            "min_spans": min_spans,
            "max_spans": max_spans,
            "std_spans": std_spans,
            "sample_size": len(span_counts),
            "truncated_count": truncated_count,
            "truncated_percentage": float(truncated_count / len(span_counts) * 100) if span_counts else 0.0,
            "mean_effective_spans_at_current": mean_effective_spans,
            "median_effective_spans_at_current": median_effective_spans,
            "zero_or_one_spans_percentage": zero_or_one_percentage
        },
        "dataset_id": dataset_id,
        "analysis_timestamp": None  # Can be populated with datetime if needed
    }
    
    # Write results to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Validation results written to {output_path}")
    logger.info(f"Recommendation: {recommendation} (cutoff_depth: {current_cutoff_depth} -> {recommended_cutoff_depth})")
    
    return result

def main():
    """
    Main entry point for running the cutoff depth validation.
    """
    from config import dataset_url, ensure_directories
    
    # Ensure output directories exist
    ensure_directories()
    
    logger.info("Running cutoff depth validation...")
    try:
        result = validate_cutoff_depth(dataset_id=dataset_url)
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

if __name__ == "__main__":
    main()
