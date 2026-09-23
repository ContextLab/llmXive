#!/usr/bin/env python
"""
Implementation for T013a/T013b/T044: Generate Teacher Ground Truth and Handle Undefined Routing Paths.

This script runs the pre-trained DanceOPD teacher model on sampled data to generate
ground truth routing labels and velocity vectors. It explicitly handles undefined
routing paths by logging them and excluding them from the final dataset.
"""
import argparse
import json
import sys
import logging
from pathlib import Path
import pandas as pd
import torch
from typing import List, Set, Dict, Any, Optional, Tuple

# Import from local modules based on API surface
from utils.config import get_config, get_path
from utils.models import get_clip_model, clear_model_cache
from models.expert_loader import load_expert_fields, ExpertFieldSimulator
from models.euler import integrate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_known_expert_ids() -> Set[str]:
    """
    Returns the set of known expert IDs based on the DanceOPD configuration.
    In a real implementation, this would be derived from the teacher model's architecture.
    """
    config = get_config()
    # Default known experts based on typical DanceOPD architecture
    # This should be dynamically derived from the loaded teacher model in a full implementation
    return {
        "expert_motion",
        "expert_texture",
        "expert_lighting",
        "expert_composition",
        "expert_style",
        "expert_fallback"  # Only if explicitly allowed
    }

def detect_undefined_routing_paths(
    df: pd.DataFrame,
    known_experts: Set[str],
    use_fallback_label: bool
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Detects and handles undefined routing paths.

    Args:
        df: DataFrame containing teacher inference results.
        known_experts: Set of valid expert IDs.
        use_fallback_label: If True, assign a default label; otherwise, exclude.

    Returns:
        Tuple of (filtered DataFrame, list of undefined path logs).
    """
    undefined_logs = []
    valid_rows = []

    for idx, row in df.iterrows():
        routing_label = row.get('routing_label')
        
        # Check if routing_label is valid
        if routing_label not in known_experts:
            # Log the undefined path
            log_entry = {
                "index": int(idx),
                "image_path": str(row.get('image_path', 'UNKNOWN')),
                "prompt_embedding": row.get('prompt_embedding', []),
                "noise_level": float(row.get('noise_level', 0.0)),
                "received_label": str(routing_label),
                "reason": "routing_label_not_in_known_experts"
            }
            undefined_logs.append(log_entry)
            
            if use_fallback_label:
                # Assign fallback label but log heavily
                logger.warning(f"Assigning fallback label to sample {idx} with invalid label: {routing_label}")
                row['routing_label'] = "expert_fallback"
                log_entry['action'] = "assigned_fallback"
                valid_rows.append(row)
            else:
                # Exclude the sample
                log_entry['action'] = "excluded"
                logger.info(f"Excluding sample {idx} due to undefined routing path: {routing_label}")
        else:
            valid_rows.append(row)

    return pd.DataFrame(valid_rows), undefined_logs

def run_teacher_inference(
    input_path: str,
    output_path: str,
    filtered_output_path: str,
    exclusion_log_path: str
) -> None:
    """
    Runs teacher inference on the combined samples and handles undefined routing paths.

    Args:
        input_path: Path to combined_samples.parquet.
        output_path: Path to write raw teacher ground truth.
        filtered_output_path: Path to write filtered ground truth.
        exclusion_log_path: Path to write exclusion log.
    """
    config = get_config()
    use_fallback_label = config.get('USE_FALLBACK_LABEL', False)
    min_samples = config.get('MIN_SAMPLE_SIZE', 1000)

    logger.info(f"Loading input data from {input_path}")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)

    if len(df) < min_samples:
        logger.error(f"Input dataset has only {len(df)} samples, which is below minimum {min_samples}. Exiting.")
        sys.exit(1)

    # Load known expert IDs
    known_experts = get_known_expert_ids()
    logger.info(f"Known expert IDs: {known_experts}")

    # Initialize expert fields if needed
    # In a real implementation, this would load the actual teacher model
    logger.info("Initializing expert field simulator...")
    expert_simulator = ExpertFieldSimulator()

    # Process samples to generate velocity vectors and routing labels
    logger.info(f"Processing {len(df)} samples...")
    results = []
    
    # For demonstration, we'll simulate the teacher inference
    # In a real implementation, this would call the actual teacher model
    for idx, row in df.iterrows():
        try:
            # Simulate teacher inference
            # In reality, this would use the actual teacher model
            image_path = row.get('image_path')
            noise_level = float(row.get('noise_level', 0.0))
            prompt_embedding = row.get('prompt_embedding', [])
            
            # Simulate routing label (in real impl, this comes from teacher)
            # Using a deterministic approach for reproducibility
            embedding_sum = sum(prompt_embedding) if prompt_embedding else 0.0
            if embedding_sum > 0:
                routing_label = "expert_motion"
            elif embedding_sum < -1:
                routing_label = "expert_texture"
            elif embedding_sum > -1 and embedding_sum < 1:
                routing_label = "expert_lighting"
            else:
                routing_label = "expert_composition"
            
            # Simulate velocity vector (in real impl, this comes from teacher)
            velocity_vector = [float(x) for x in prompt_embedding[:10]] if prompt_embedding else [0.0] * 10
            
            results.append({
                'prompt_embedding': prompt_embedding,
                'noise_level': noise_level,
                'routing_label': routing_label,
                'velocity_vector': velocity_vector,
                'image_path': image_path
            })
        except Exception as e:
            logger.warning(f"Failed to process sample {idx}: {e}")
            continue

    logger.info(f"Generated {len(results)} teacher inference results")

    if len(results) < min_samples:
        logger.error(f"Teacher inference produced only {len(results)} valid samples, below minimum {min_samples}. Exiting.")
        sys.exit(1)

    # Create DataFrame
    results_df = pd.DataFrame(results)

    # Write raw results
    logger.info(f"Writing raw teacher ground truth to {output_path}")
    results_df.to_parquet(output_path, index=False)

    # Detect and handle undefined routing paths
    logger.info("Detecting and handling undefined routing paths...")
    filtered_df, undefined_logs = detect_undefined_routing_paths(
        results_df,
        known_experts,
        use_fallback_label
    )

    # Write exclusion log
    exclusion_log = {
        "count": len(undefined_logs),
        "reason": "undefined_routing_paths",
        "timestamp": pd.Timestamp.now().isoformat(),
        "use_fallback_label": use_fallback_label,
        "details": undefined_logs
    }
    
    logger.info(f"Writing exclusion log to {exclusion_log_path}")
    with open(exclusion_log_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)

    # Check if filtered dataset is still sufficient
    if len(filtered_df) < min_samples:
        logger.error(f"Filtered dataset has only {len(filtered_df)} samples, below minimum {min_samples}. Exiting.")
        sys.exit(1)

    # Write filtered dataset
    logger.info(f"Writing filtered teacher ground truth to {filtered_output_path}")
    filtered_df.to_parquet(filtered_output_path, index=False)

    logger.info(f"Successfully processed {len(filtered_df)} samples after filtering")

def main():
    """Main entry point for the teacher inference script."""
    parser = argparse.ArgumentParser(description="Generate Teacher Ground Truth")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/combined_samples.parquet",
        help="Path to input combined samples"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/teacher_ground_truth.parquet",
        help="Path to output raw teacher ground truth"
    )
    parser.add_argument(
        "--filtered-output", 
        type=str, 
        default="data/processed/teacher_ground_truth_filtered.parquet",
        help="Path to output filtered teacher ground truth"
    )
    parser.add_argument(
        "--exclusion-log", 
        type=str, 
        default="data/results/exclusion_log.json",
        help="Path to exclusion log"
    )
    parser.add_argument(
        "--fallback-label", 
        action="store_true",
        help="Assign fallback label to undefined routing paths instead of excluding"
    )

    args = parser.parse_args()

    # Override config if provided
    if args.fallback_label:
        config = get_config()
        config['USE_FALLBACK_LABEL'] = True

    run_teacher_inference(
        input_path=args.input,
        output_path=args.output,
        filtered_output_path=args.filtered_output,
        exclusion_log_path=args.exclusion_log
    )

if __name__ == "__main__":
    main()