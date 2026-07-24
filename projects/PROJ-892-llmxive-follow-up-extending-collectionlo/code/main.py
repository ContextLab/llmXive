import os
import sys
import json
import csv
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from existing project modules based on API surface
from data_loader import (
    ensure_download_dir,
    compute_sha256,
    load_artifacts_state,
    save_artifacts_state,
    register_downloaded_artifact,
    download_base_model,
    download_lora_adapter,
    get_collection_lora_adapter,
    load_adapter_weights,
    save_adapter_weights,
    get_model_info,
    compute_subspace_ranks,
    apply_quantization,
    quantize_adapter_fp16_to_int8,
    quantize_adapter_fp16_to_int4
)
from generator import (
    generate_images,
    generate_reference_image,
    generate_fp16_reference_images,
    generate_images_for_adapters
)
from metrics import (
    extract_clip_image_embedding,
    extract_clip_text_embedding,
    compute_cosine_similarity,
    compute_lpips_distance,
    compute_image_text_similarity,
    batch_compute_image_text_similarity,
    compute_cesr_score,
    compute_lpips_matrix
)
from state_manager import (
    ensure_state_dir,
    compute_sha256 as state_compute_sha256,
    load_artifacts_state as state_load_artifacts_state,
    save_artifacts_state as state_save_artifacts_state,
    register_artifact,
    verify_artifact,
    get_artifact_hash
)
from statistical_analysis import (
    load_results_data,
    load_subspace_ranks as load_subspace_ranks_stats,
    prepare_correlation_data,
    run_bayesian_hierarchical_model
)
from config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('state/pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

def handle_oom(exception: Exception, quantization_level: str) -> bool:
    """
    Handle Out-Of-Memory (OOM) exceptions for a specific quantization level.
    
    This is the sole mechanism for OOM handling as per FR-008.
    
    Args:
        exception: The exception that was raised (MemoryError or subprocess error)
        quantization_level: The quantization level being processed (e.g., 'int8', 'int4')
        
    Returns:
        bool: True if the error was handled and processing should continue, 
              False if the error was critical and processing should stop.
    """
    if isinstance(exception, MemoryError):
        logger.warning(f"Quantization Failure: MemoryError encountered at {quantization_level} level. "
                     f"Skipping this level and continuing with the pipeline.")
        return True
    
    # Check for subprocess Exit Code 137 (SIGKILL)
    if hasattr(exception, 'code') and exception.code == 137:
        logger.warning(f"Quantization Failure: Subprocess terminated with Exit Code 137 (SIGKILL) "
                     f"at {quantization_level} level. Skipping this level and continuing.")
        return True
    
    # Check for subprocess.CalledProcessError with exit code 137
    if isinstance(exception, subprocess.CalledProcessError) and exception.returncode == 137:
        logger.warning(f"Quantization Failure: Subprocess terminated with Exit Code 137 (SIGKILL) "
                     f"at {quantization_level} level. Skipping this level and continuing.")
        return True
    
    # For any other exception, log and re-raise
    logger.error(f"Unexpected error at {quantization_level} level: {str(exception)}")
    return False

def run_fp16_generation(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Run FP16 baseline generation pipeline.
    
    Args:
        config: Configuration dictionary loaded from config.yaml
        
    Returns:
        List of result dictionaries containing generation metrics
    """
    logger.info("Starting FP16 baseline generation...")
    
    # Ensure directories exist
    ensure_download_dir()
    ensure_state_dir()
    
    # Download base model and adapter if needed
    try:
        download_base_model()
        download_lora_adapter()
    except Exception as e:
        logger.error(f"Failed to download models: {e}")
        raise
    
    # Generate FP16 reference images
    try:
        generate_fp16_reference_images(config)
    except Exception as e:
        logger.error(f"Failed to generate FP16 reference images: {e}")
        raise
    
    # Generate images for all prompts
    results = []
    try:
        results = generate_images_for_adapters(config, "fp16")
    except Exception as e:
        logger.error(f"Failed to generate FP16 images: {e}")
        raise
    
    logger.info(f"FP16 generation complete. Generated {len(results)} images.")
    return results

def run_quantized_generation(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Run quantized generation pipeline with OOM handling.
    
    This function implements the core OOM handling logic per FR-008.
    
    Args:
        config: Configuration dictionary loaded from config.yaml
        
    Returns:
        List of result dictionaries containing generation metrics for successful quantization levels
    """
    logger.info("Starting quantized generation pipeline...")
    
    quantization_levels = [
        ("int8", quantize_adapter_fp16_to_int8),
        ("int4", quantize_adapter_fp16_to_int4)
    ]
    
    all_results = []
    
    for level_name, quantization_func in quantization_levels:
        logger.info(f"Processing quantization level: {level_name}")
        
        try:
            # Apply quantization
            quantization_func()
            
            # Generate images with quantized adapter
            results = generate_images_for_adapters(config, level_name)
            all_results.extend(results)
            
            logger.info(f"Successfully completed {level_name} quantization level.")
            
        except MemoryError as e:
            if handle_oom(e, level_name):
                logger.warning(f"Skipped {level_name} level due to OOM. Continuing with next level.")
                continue
            else:
                logger.error(f"Critical OOM error at {level_name} level. Aborting pipeline.")
                raise
                
        except subprocess.CalledProcessError as e:
            if handle_oom(e, level_name):
                logger.warning(f"Skipped {level_name} level due to SIGKILL. Continuing with next level.")
                continue
            else:
                logger.error(f"Critical subprocess error at {level_name} level. Aborting pipeline.")
                raise
                
        except Exception as e:
            logger.error(f"Unexpected error at {level_name} level: {str(e)}")
            # For non-OOM errors, we should fail fast
            raise
    
    logger.info(f"Quantized generation complete. Successfully processed {len(all_results)} images.")
    return all_results

def run_statistical_analysis(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run Bayesian Hierarchical Model analysis.
    
    Args:
        config: Configuration dictionary loaded from config.yaml
        
    Returns:
        Dictionary containing analysis results
    """
    logger.info("Starting statistical analysis...")
    
    try:
        # Load results data
        results_data = load_results_data()
        
        # Load subspace ranks if available
        try:
            subspace_ranks = load_subspace_ranks_stats()
        except FileNotFoundError:
            logger.warning("Subspace ranks file not found. Skipping correlation analysis.")
            subspace_ranks = None
        
        # Prepare data for correlation analysis
        if subspace_ranks:
            correlation_data = prepare_correlation_data(results_data, subspace_ranks)
        else:
            correlation_data = None
        
        # Run Bayesian Hierarchical Model
        bhm_results = run_bayesian_hierarchical_model(results_data, correlation_data)
        
        logger.info("Statistical analysis complete.")
        return bhm_results
        
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        raise

def main():
    """
    Main entry point for the quantization robustness pipeline.
    
    This function orchestrates the entire pipeline:
    1. FP16 baseline generation
    2. Quantized generation with OOM handling
    3. Statistical analysis
    
    All OOM handling is performed by handle_oom() as per FR-008.
    """
    logger.info("=== Starting Quantization Robustness Pipeline ===")
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Phase 1: FP16 Baseline Generation
    try:
        fp16_results = run_fp16_generation(config)
        logger.info(f"FP16 generation produced {len(fp16_results)} results.")
    except Exception as e:
        logger.error(f"FP16 generation failed: {e}")
        sys.exit(1)
    
    # Phase 2: Quantized Generation with OOM Handling
    try:
        quantized_results = run_quantized_generation(config)
        logger.info(f"Quantized generation produced {len(quantized_results)} results.")
    except Exception as e:
        logger.error(f"Quantized generation failed: {e}")
        sys.exit(1)
    
    # Combine all results
    all_results = fp16_results + quantized_results
    
    # Save results to CSV
    try:
        results_path = Path("data/results.csv")
        with open(results_path, 'w', newline='') as csvfile:
            fieldnames = all_results[0].keys() if all_results else []
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)
        
        logger.info(f"Results saved to {results_path}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
    
    # Phase 3: Statistical Analysis
    try:
        analysis_results = run_statistical_analysis(config)
        
        # Save analysis results
        analysis_path = Path("data/analysis_results.json")
        with open(analysis_path, 'w') as jsonfile:
            json.dump(analysis_results, jsonfile, indent=2, default=str)
        
        logger.info(f"Analysis results saved to {analysis_path}")
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        # Don't exit here - pipeline can continue without analysis
    
    logger.info("=== Pipeline Complete ===")

if __name__ == "__main__":
    main()