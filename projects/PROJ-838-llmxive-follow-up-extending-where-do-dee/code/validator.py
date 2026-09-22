"""
Validator module for dataset and configuration analysis.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
from datasets import load_dataset

from config import ensure_directories, cutoff_depth, seed

logger = logging.getLogger(__name__)

def validate_cutoff_depth(dataset_id: str = "NJU-LINK/TELBench") -> Dict[str, Any]:
    """
    Perform a preliminary analysis of the dataset's span distribution to justify
    the `cutoff_depth` value (default 0.30) or recommend a different value.

    This function loads the dataset in streaming mode, samples a representative
    subset of trajectories, and analyzes the distribution of total spans per
    trajectory. It checks if `cutoff_depth` captures a meaningful "early" phase
    (e.g., before the median trajectory length is exhausted) and if it avoids
    truncating too many short trajectories.

    Args:
        dataset_id: HuggingFace dataset ID.

    Returns:
        A dictionary containing:
            - 'current_cutoff_depth': The configured cutoff depth.
            - 'recommended_cutoff_depth': The recommended value (or current if valid).
            - 'justification': A string explaining the decision.
            - 'statistics': Dict with 'mean_spans', 'median_spans', 'min_spans',
                           'max_spans', 'truncated_count', 'truncated_percentage'.
            - 'valid': Boolean indicating if the current cutoff is appropriate.
    """
    logger.info(f"Validating cutoff_depth={cutoff_depth} against dataset {dataset_id}...")
    
    # Ensure output directory exists
    ensure_directories()
    output_path = Path("data/processed/cutoff_depth_validation.json")

    try:
        # Load dataset in streaming mode to handle large sizes
        # We only need the 'spans' field for this analysis
        dataset = load_dataset(dataset_id, split="train", streaming=True)
        
        # Collect span counts from a representative sample
        # We'll take the first 1000 trajectories to estimate distribution
        # This is sufficient for statistical justification without loading full dataset
        sample_size = 1000
        span_counts = []
        
        logger.info(f"Sampling {sample_size} trajectories to analyze span distribution...")
        
        count = 0
        for item in dataset:
            if count >= sample_size:
                break
            
            # Handle potential missing 'spans' field gracefully
            spans = item.get('spans', [])
            if spans is not None:
                span_counts.append(len(spans))
            count += 1

        if not span_counts:
            raise ValueError("No valid trajectories found in dataset sample.")

        # Calculate statistics
        mean_spans = float(np.mean(span_counts))
        median_spans = float(np.median(span_counts))
        min_spans = int(np.min(span_counts))
        max_spans = int(np.max(span_counts))
        
        # Analyze the impact of the current cutoff_depth
        # Calculate how many spans are captured on average
        cutoff_spans = mean_spans * cutoff_depth
        median_cutoff_spans = median_spans * cutoff_depth
        
        # Count how many trajectories would be "short" (total spans < 3)
        # and how many would be truncated significantly
        short_trajectories = [c for c in span_counts if c < 3]
        truncated_trajectories = [c for c in span_counts if c * cutoff_depth < 1] # Effectively 0 spans captured
        
        truncated_count = len([c for c in span_counts if c < 3])
        truncated_percentage = (truncated_count / len(span_counts)) * 100

        # Decision logic for justification
        justification_parts = []
        recommended_depth = cutoff_depth
        is_valid = True

        # Check 1: Does the cutoff capture a reasonable number of spans?
        # If median_cutoff_spans < 2, we might be cutting off too early
        if median_cutoff_spans < 2:
            justification_parts.append(
                f"The current cutoff_depth ({cutoff_depth}) results in an average of "
                f"{median_cutoff_spans:.2f} spans per trajectory (based on median length {median_spans}). "
                "This may be too shallow to capture meaningful early-stage reasoning patterns. "
                "A higher cutoff (e.g., 0.40 or 0.50) might be more appropriate."
            )
            recommended_depth = max(0.40, cutoff_depth + 0.10)
            is_valid = False
        else:
            justification_parts.append(
                f"The current cutoff_depth ({cutoff_depth}) captures approximately "
                f"{median_cutoff_spans:.1f} spans per trajectory (median), which is sufficient "
                "to analyze early-stage reasoning patterns."
            )

        # Check 2: Are we truncating too many short trajectories?
        if truncated_percentage > 10:
            justification_parts.append(
                f"Note: {truncated_percentage:.1f}% of sampled trajectories have fewer than 3 spans. "
                "These will result in very small or empty graphs regardless of cutoff_depth. "
                "Consider filtering these out in downstream processing."
            )
        
        # Check 3: Is the cutoff too deep? (e.g., > 0.50 might include late-stage noise)
        if cutoff_depth > 0.50:
            justification_parts.append(
                f"The current cutoff_depth ({cutoff_depth}) is relatively deep. "
                "Ensure this does not include late-stage reasoning which may introduce noise "
                "into the 'early trajectory' analysis."
            )

        justification = " ".join(justification_parts)

        result = {
            "current_cutoff_depth": cutoff_depth,
            "recommended_cutoff_depth": recommended_depth,
            "justification": justification,
            "statistics": {
                "mean_spans": mean_spans,
                "median_spans": median_spans,
                "min_spans": min_spans,
                "max_spans": max_spans,
                "sample_size": len(span_counts),
                "truncated_count": truncated_count,
                "truncated_percentage": truncated_percentage
            },
            "valid": is_valid
        }

        # Write to disk
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)

        logger.info(f"Validation complete. Results written to {output_path}")
        logger.info(f"Recommendation: {'Use current value' if is_valid else 'Consider increasing cutoff_depth'}")

        return result

    except Exception as e:
        logger.error(f"Failed to validate cutoff depth: {e}")
        raise

def main():
    """Entry point for running the validator."""
    logging.basicConfig(level=logging.INFO)
    try:
        result = validate_cutoff_depth()
        print(json.dumps(result, indent=2))
    except Exception as e:
        logging.critical(f"Validation failed: {e}")
        raise

if __name__ == "__main__":
    main()
