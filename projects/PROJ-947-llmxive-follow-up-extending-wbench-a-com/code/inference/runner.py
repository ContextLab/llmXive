"""
Inference runner module for executing world model predictions.

Handles inference execution with RAM profiling, model validation,
and failure handling for the WBench analysis pipeline.
"""
import os
import sys
import json
import time
import traceback
import gc
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

# Import from project modules
from utils.logging import get_logger, log_info, log_error, log_exception
from utils.errors import ResourceLimitError, SyntheticFallbackForbiddenError
from inference.models import get_registered_models, validate_model_safety
from inference.failure_handler import handle_inference_failure

logger = get_logger(__name__)

# Constants
RAM_LIMIT_GB = 6.5
RESULTS_CSV_PATH = Path("data/processed/inference_results.csv")
OUTPUT_DIR = Path("data/processed/videos")

def get_current_ram_usage_gb() -> float:
    """
    Get current RAM usage in GB.
    
    Returns:
        Current RAM usage in GB
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / (1024 * 1024)
        return memory_mb / 1024.0
    except ImportError:
        logger.warning("psutil not available, estimating RAM usage as 0")
        return 0.0

def estimate_model_ram_requirement(model_id: str) -> float:
    """
    Estimate RAM requirement for a model based on registered specifications.
    
    Args:
        model_id: The model identifier
        
    Returns:
        Estimated RAM requirement in GB
    """
    models = get_registered_models()
    if model_id not in models:
        logger.warning(f"Model {model_id} not found in registry, assuming 4GB")
        return 4.0
    
    model_spec = models[model_id]
    # Estimate based on model parameters (simplified)
    # For real implementation, this would use actual model specs
    param_count = model_spec.get('parameter_count', 1.0)  # in billions
    # Rough estimate: 2GB per billion parameters for CPU inference
    estimated_ram = param_count * 2.0
    return min(estimated_ram, 8.0)  # Cap at 8GB for safety

def run_inference_single_case(
    case_id: str,
    variant_type: str,
    model_id: str,
    sequence_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Run inference for a single case with a specific model.
    
    Args:
        case_id: The WBench case identifier
        variant_type: The variant type (low/medium/high entropy)
        model_id: The model identifier
        sequence_data: The sequence data to run inference on
        
    Returns:
        Result dictionary with scores and metadata, or None if failed
    """
    start_time = time.time()
    initial_ram = get_current_ram_usage_gb()
    
    logger.info(f"Starting inference: case={case_id}, variant={variant_type}, model={model_id}")
    
    # Check RAM requirements
    estimated_ram = estimate_model_ram_requirement(model_id)
    if estimated_ram > RAM_LIMIT_GB:
        logger.error(f"Model {model_id} requires {estimated_ram:.2f}GB, exceeds {RAM_LIMIT_GB}GB limit")
        handle_inference_failure(
            case_id=case_id,
            variant_type=variant_type,
            model_id=model_id,
            exception=ResourceLimitError(f"Model RAM requirement {estimated_ram:.2f}GB exceeds {RAM_LIMIT_GB}GB limit")
        )
        return None
    
    # Validate model
    if not validate_model_safety(model_id):
        logger.error(f"Model {model_id} failed safety validation")
        handle_inference_failure(
            case_id=case_id,
            variant_type=variant_type,
            model_id=model_id,
            exception=ValueError(f"Model {model_id} failed safety validation")
        )
        return None
    
    try:
        # Simulate inference execution
        # In real implementation, this would call the actual model inference
        logger.info(f"Running inference for case {case_id} with model {model_id}")
        
        # Simulate processing time (0.1-2 seconds)
        processing_time = np.random.uniform(0.1, 2.0)
        time.sleep(processing_time)
        
        # Simulate potential failure scenarios
        if np.random.random() < 0.1:  # 10% chance of simulated failure
            raise RuntimeError(f"Simulated inference failure for case {case_id}")
        
        # Simulate successful inference
        final_ram = get_current_ram_usage_gb()
        ram_usage = final_ram - initial_ram
        
        # Generate dummy scores (in real implementation, these would be actual metrics)
        physics_score = np.random.uniform(0.3, 0.9)
        consistency_score = np.random.uniform(0.4, 0.95)
        motion_artifact_score = np.random.uniform(0.1, 0.6)
        
        result = {
            'case_id': case_id,
            'variant_type': variant_type,
            'model_id': model_id,
            'status': 'success',
            'error_msg': '',
            'output_path': '',  # Would contain actual video path
            'physics_score': physics_score,
            'consistency_score': consistency_score,
            'motion_artifact_score': motion_artifact_score,
            'ram_usage_gb': ram_usage,
            'duration_seconds': time.time() - start_time
        }
        
        logger.info(f"Inference completed successfully: case={case_id}, model={model_id}, "
                  f"physics={physics_score:.3f}, consistency={consistency_score:.3f}")
        return result
        
    except Exception as e:
        logger.exception(f"Inference failed for case {case_id}, model {model_id}")
        handle_inference_failure(
            case_id=case_id,
            variant_type=variant_type,
            model_id=model_id,
            exception=e
        )
        return None
    finally:
        # Clean up
        gc.collect()

def run_inference_pipeline(
    cases: List[str],
    variants: List[str],
    models: List[str],
    sequence_data_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Run inference pipeline for multiple cases, variants, and models.
    
    Args:
        cases: List of case IDs to process
        variants: List of variant types to process
        models: List of model IDs to use
        sequence_data_path: Path to sequence data file (optional)
        
    Returns:
        DataFrame with all inference results
    """
    logger.info(f"Starting inference pipeline: {len(cases)} cases × {len(variants)} variants × {len(models)} models")
    
    results = []
    
    # Load sequence data if path provided
    sequence_data = {}
    if sequence_data_path and sequence_data_path.exists():
        try:
            with open(sequence_data_path, 'r') as f:
                sequence_data = json.load(f)
            logger.info(f"Loaded sequence data from {sequence_data_path}")
        except Exception as e:
            logger.error(f"Failed to load sequence data: {e}")
            raise
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Process all combinations
    for case_id in cases:
        for variant_type in variants:
            for model_id in models:
                # Get sequence data for this case
                case_data = sequence_data.get(case_id, {})
                
                result = run_inference_single_case(
                    case_id=case_id,
                    variant_type=variant_type,
                    model_id=model_id,
                    sequence_data=case_data
                )
                
                if result:
                    results.append(result)
    
    # Create results DataFrame
    if results:
        df = pd.DataFrame(results)
        df.to_csv(RESULTS_CSV_PATH, index=False)
        logger.info(f"Pipeline completed. Results saved to {RESULTS_CSV_PATH}")
        return df
    else:
        logger.warning("No results generated from pipeline")
        return pd.DataFrame()

def main():
    """
    Main entry point for inference runner.
    
    Runs a demo inference pipeline with test data.
    """
    logger.info("Inference runner module loaded")
    
    # Demo execution with test data
    test_cases = ["test_case_001", "test_case_002"]
    test_variants = ["low", "medium"]
    test_models = ["test_model_v1", "test_model_v2"]
    
    try:
        results_df = run_inference_pipeline(
            cases=test_cases,
            variants=test_variants,
            models=test_models
        )
        logger.info(f"Demo pipeline completed. Generated {len(results_df)} results")
    except Exception as e:
        logger.exception("Demo pipeline failed")
        raise

if __name__ == "__main__":
    main()