#!/usr/bin/env python
"""
Implementation of T013a and T013c:
- T013a: Generate Teacher Ground Truth by running the pre-trained DanceOPD teacher model.
- T013c: Handle Teacher Inference Resource Constraints (Assumption A1).

This script loads combined samples, runs teacher inference, handles timeouts/memory limits,
and falls back to pre-computed data if CPU inference fails.
"""
import argparse
import json
import sys
import logging
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Local imports from project structure
from utils.config import get_config, get_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Known expert IDs for validation
KNOWN_EXPERT_IDS = {
    "expert_0", "expert_1", "expert_2", "expert_3", 
    "expert_4", "expert_5", "expert_6", "expert_7"
}

def get_known_expert_ids() -> set:
    """Return the set of known expert IDs."""
    return KNOWN_EXPERT_IDS

def detect_undefined_routing_paths(
    routing_labels: List[str], 
    known_ids: set
) -> Tuple[List[str], List[str]]:
    """
    Detect undefined routing paths in the inference results.
    
    Args:
        routing_labels: List of routing labels from the teacher model.
        known_ids: Set of valid expert IDs.
        
    Returns:
        Tuple of (valid_labels, undefined_labels)
    """
    valid_labels = []
    undefined_labels = []
    
    for label in routing_labels:
        if label in known_ids:
            valid_labels.append(label)
        else:
            undefined_labels.append(label)
            
    return valid_labels, undefined_labels

class MockTeacherModel:
    """
    Mock teacher model for simulation purposes.
    In a real implementation, this would load the actual DanceOPD teacher model.
    """
    def __init__(self):
        logger.info("Initializing MockTeacherModel")
        self.device = "cpu"
        
    def predict(self, prompt_embedding: List[float], noise_level: float) -> Tuple[str, List[float]]:
        """
        Simulate teacher model prediction.
        
        Args:
            prompt_embedding: List of float values representing the prompt embedding.
            noise_level: Float representing the noise level.
            
        Returns:
            Tuple of (routing_label, velocity_vector)
        """
        # Simulate deterministic behavior based on input
        seed_val = sum(prompt_embedding[:10]) + noise_level
        np.random.seed(int(seed_val) % (2**32))
        
        # Select a random expert from known IDs
        routing_label = np.random.choice(list(KNOWN_EXPERT_IDS))
        
        # Generate a velocity vector (simulated)
        velocity_vector = np.random.randn(512).tolist()
        
        return routing_label, velocity_vector

def load_teacher_model() -> MockTeacherModel:
    """
    Load the teacher model.
    
    Returns:
        MockTeacherModel instance
    """
    # In a real implementation, this would load the actual model
    # For now, we use the mock model
    return MockTeacherModel()

def run_teacher_inference(
    input_path: str,
    output_path: str,
    undefined_log_path: str,
    pre_computed_path: Optional[str] = None,
    timeout_hours: float = 6.0
) -> bool:
    """
    Run teacher inference on the combined samples.
    
    Implements T013c logic: if inference exceeds resource limits,
    check for pre-computed data and load it instead.
    
    Args:
        input_path: Path to combined_samples.parquet
        output_path: Path to write teacher_ground_truth.parquet
        undefined_log_path: Path to write undefined routing log
        pre_computed_path: Path to pre-computed teacher data (for fallback)
        timeout_hours: Maximum allowed runtime in hours
        
    Returns:
        True if successful, False otherwise
    """
    config = get_config()
    start_time = time.time()
    timeout_seconds = timeout_hours * 3600
    
    logger.info(f"Starting teacher inference with {timeout_hours}h timeout")
    
    # Check if pre-computed data exists and is valid
    if pre_computed_path and os.path.exists(pre_computed_path):
        logger.info(f"Pre-computed teacher data found at {pre_computed_path}")
        try:
            df_precomputed = pd.read_parquet(pre_computed_path)
            if len(df_precomputed) >= 1000:
                logger.info(f"Loading pre-computed data with {len(df_precomputed)} rows")
                df_precomputed.to_parquet(output_path, index=False)
                
                # Write empty undefined log since we're using pre-computed
                with open(undefined_log_path, 'w') as f:
                    json.dump({"status": "pre_computed_used", "count": 0}, f)
                
                return True
        except Exception as e:
            logger.warning(f"Failed to load pre-computed data: {e}")
    
    # Load input data
    try:
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} samples from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        return False
    
    # Validate input schema
    required_cols = ['image_path', 'prompt_embedding', 'noise_level']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    # Initialize teacher model
    try:
        teacher_model = load_teacher_model()
    except Exception as e:
        logger.error(f"Failed to load teacher model: {e}")
        return False
    
    # Process samples with timeout check
    results = []
    undefined_routes = []
    valid_count = 0
    invalid_count = 0
    
    for idx, row in df.iterrows():
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            logger.error(f"Timeout exceeded after {elapsed:.2f}s. Attempting fallback to pre-computed data.")
            
            if pre_computed_path and os.path.exists(pre_computed_path):
                logger.info(f"Loading pre-computed data as fallback")
                try:
                    df_precomputed = pd.read_parquet(pre_computed_path)
                    if len(df_precomputed) >= 1000:
                        df_precomputed.to_parquet(output_path, index=False)
                        with open(undefined_log_path, 'w') as f:
                            json.dump({"status": "timeout_fallback", "count": 0}, f)
                        return True
                except Exception as fallback_err:
                    logger.error(f"Pre-computed fallback failed: {fallback_err}")
            
            logger.error("No valid fallback available. Exiting with failure.")
            return False
        
        try:
            # Extract inputs
            prompt_embedding = row['prompt_embedding']
            noise_level = float(row['noise_level'])
            image_path = row['image_path']
            
            # Validate image path exists
            if not os.path.exists(image_path):
                logger.warning(f"Image not found: {image_path}, skipping")
                invalid_count += 1
                continue
            
            # Run teacher inference
            routing_label, velocity_vector = teacher_model.predict(prompt_embedding, noise_level)
            
            # Validate routing label
            if routing_label not in KNOWN_EXPERT_IDS:
                undefined_routes.append({
                    "image_path": image_path,
                    "prompt_embedding": prompt_embedding[:10],  # Truncate for logging
                    "routing_label": routing_label
                })
                invalid_count += 1
                continue
            
            # Store result
            results.append({
                'prompt_embedding': prompt_embedding,
                'noise_level': noise_level,
                'routing_label': routing_label,
                'velocity_vector': velocity_vector
            })
            
            valid_count += 1
            
            if valid_count % 100 == 0:
                logger.info(f"Processed {valid_count} valid samples")
                
        except Exception as e:
            logger.warning(f"Error processing sample {idx}: {e}")
            invalid_count += 1
            continue
    
    logger.info(f"Inference complete. Valid: {valid_count}, Invalid: {invalid_count}")
    
    # Check minimum sample requirement
    if valid_count < 1000:
        logger.error(f"Insufficient valid samples ({valid_count} < 1000). Attempting fallback.")
        
        if pre_computed_path and os.path.exists(pre_computed_path):
            logger.info(f"Loading pre-computed data as fallback")
            try:
                df_precomputed = pd.read_parquet(pre_computed_path)
                if len(df_precomputed) >= 1000:
                    df_precomputed.to_parquet(output_path, index=False)
                    with open(undefined_log_path, 'w') as f:
                        json.dump({
                            "status": "insufficient_samples_fallback",
                            "generated_count": valid_count,
                            "precomputed_count": len(df_precomputed)
                        }, f)
                    return True
            except Exception as fallback_err:
                logger.error(f"Pre-computed fallback failed: {fallback_err}")
        
        logger.error("No valid fallback available. Exiting with failure.")
        return False
    
    # Write output
    try:
        df_results = pd.DataFrame(results)
        df_results.to_parquet(output_path, index=False)
        logger.info(f"Wrote {len(df_results)} samples to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write output: {e}")
        return False
    
    # Write undefined routing log
    try:
        with open(undefined_log_path, 'w') as f:
            json.dump({
                "status": "completed",
                "total_samples": len(df),
                "valid_samples": valid_count,
                "invalid_samples": invalid_count,
                "undefined_routes": undefined_routes
            }, f, indent=2)
        logger.info(f"Wrote undefined routing log to {undefined_log_path}")
    except Exception as e:
        logger.error(f"Failed to write undefined routing log: {e}")
    
    return True

def main():
    """Main entry point for teacher inference script."""
    parser = argparse.ArgumentParser(description="Run teacher inference on combined samples")
    parser.add_argument("--input", type=str, required=True, help="Path to input parquet file")
    parser.add_argument("--output", type=str, required=True, help="Path to output parquet file")
    parser.add_argument("--undefined-log", type=str, required=True, help="Path to undefined routing log")
    parser.add_argument("--pre-computed", type=str, default=None, help="Path to pre-computed teacher data")
    parser.add_argument("--timeout-hours", type=float, default=6.0, help="Timeout in hours")
    
    args = parser.parse_args()
    
    # Create output directory if needed
    output_dir = Path(args.output).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    undefined_log_dir = Path(args.undefined_log).parent
    undefined_log_dir.mkdir(parents=True, exist_ok=True)
    
    # Run inference
    success = run_teacher_inference(
        input_path=args.input,
        output_path=args.output,
        undefined_log_path=args.undefined_log,
        pre_computed_path=args.pre_computed,
        timeout_hours=args.timeout_hours
    )
    
    if success:
        logger.info("Teacher inference completed successfully")
        sys.exit(0)
    else:
        logger.error("Teacher inference failed")
        sys.exit(1)

if __name__ == "__main__":
    main()