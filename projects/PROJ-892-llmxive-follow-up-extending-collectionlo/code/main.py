import os
import sys
import json
import csv
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import from local modules
from config import load_config
from data_loader import (
    load_fp16_adapter_and_base_model,
    organize_reference_images,
    get_project_root,
    ensure_download_dir,
    load_and_compute_subspace_ranks
)
from generator import generate_fp16_baseline_images, generate_images
from metrics import (
    compute_lpips_distance,
    compute_image_text_similarity,
    compute_cesr_score
)
from error_handler import handle_memory_error
from state_manager import register_artifact, load_artifacts_state, save_artifacts_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def handle_oom(e: Exception) -> bool:
    """
    Handle OutOfMemory errors gracefully.
    Returns True if the operation should be skipped, False to re-raise.
    """
    if isinstance(e, (MemoryError, RuntimeError)) and "out of memory" in str(e).lower():
        logger.warning("Memory error detected. Skipping this operation.")
        handle_memory_error(e)
        return True
    return False

def run_fp16_generation(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Run FP16 baseline generation, compute metrics, and save results.
    
    This function:
    1. Loads the FP16 adapter and base model
    2. Generates baseline images for all prompts
    3. Computes CLIP similarity and LPIPS distance
    4. Saves results to data/results.csv
    5. Saves generated images to data/generated/
    
    Args:
        config: Configuration dictionary from config.yaml
        
    Returns:
        List of result dictionaries containing prompt, effect, metrics, etc.
    """
    logger.info("Starting FP16 baseline generation...")
    results = []
    
    try:
        # Load models
        logger.info("Loading FP16 adapter and base model...")
        pipe = load_fp16_adapter_and_base_model()
        
        # Organize reference images for CESR calculation
        logger.info("Organizing reference images...")
        ref_lookup = organize_reference_images()
        
        # Get prompts from config
        prompts = config.get('prompts', [])
        if not prompts:
            logger.error("No prompts found in config.yaml")
            return results
        
        # Generate baseline images
        logger.info(f"Generating {len(prompts)} baseline images...")
        generated_images = generate_fp16_baseline_images(pipe, prompts, config)
        
        if not generated_images:
            logger.warning("No images were generated.")
            return results
        
        # Process each generated image
        for img_info in generated_images:
            image_path = img_info.get('path')
            prompt = img_info.get('prompt')
            effect = img_info.get('effect')
            seed = img_info.get('seed')
            
            if not image_path or not os.path.exists(image_path):
                logger.warning(f"Image not found or invalid: {image_path}")
                continue
            
            result_entry = {
                'prompt': prompt,
                'effect': effect,
                'seed': seed,
                'quantization_level': 'FP16',
                'image_path': image_path,
                'timestamp': datetime.now().isoformat()
            }
            
            # Compute CLIP similarity (image-text)
            try:
                clip_sim = compute_image_text_similarity(image_path, prompt)
                result_entry['clip_similarity'] = clip_sim
            except Exception as e:
                logger.warning(f"Failed to compute CLIP similarity for {image_path}: {e}")
                result_entry['clip_similarity'] = None
            
            # Compute LPIPS distance (vs reference)
            try:
                lpips_dist = compute_lpips_distance(image_path, effect, ref_lookup)
                result_entry['lpips_distance'] = lpips_dist
            except Exception as e:
                logger.warning(f"Failed to compute LPIPS distance for {image_path}: {e}")
                result_entry['lpips_distance'] = None
            
            # Compute CESR (Cross-Effect Similarity Ratio)
            try:
                cesr = compute_cesr_score(image_path, effect, ref_lookup)
                result_entry['cesr_score'] = cesr
            except Exception as e:
                logger.warning(f"Failed to compute CESR for {image_path}: {e}")
                result_entry['cesr_score'] = None
            
            results.append(result_entry)
            
            # Register artifact
            try:
                register_artifact(image_path, "generated_image")
            except Exception as e:
                logger.warning(f"Failed to register artifact {image_path}: {e}")
        
        logger.info(f"Generated {len(results)} baseline images with metrics.")
        
    except MemoryError as e:
        if handle_oom(e):
            logger.error("FP16 generation failed due to memory constraints.")
            return results
        raise
    except Exception as e:
        logger.error(f"Error during FP16 generation: {e}", exc_info=True)
        raise
    
    return results

def save_results_to_csv(results: List[Dict[str, Any]], output_path: str):
    """
    Save results to a CSV file.
    
    Args:
        results: List of result dictionaries
        output_path: Path to the output CSV file
    """
    if not results:
        logger.warning("No results to save.")
        return
    
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write to CSV
    fieldnames = list(results[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Results saved to {output_path}")

def run_quantized_generation(config: Dict[str, Any], quantization_levels: List[str]) -> List[Dict[str, Any]]:
    """
    Run quantized generation for specified levels (INT8, INT4).
    
    Note: This is a placeholder for T020 implementation.
    Currently returns empty list as quantization logic is in T016.
    """
    logger.info(f"Quantized generation requested for levels: {quantization_levels}")
    # TODO: Implement quantization generation logic (T020)
    return []

def run_statistical_analysis(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run Bayesian Hierarchical Model analysis.
    
    Note: This is a placeholder for T027 implementation.
    Currently returns empty dict as analysis logic is in statistical_analysis.py.
    """
    logger.info("Statistical analysis requested.")
    # TODO: Implement statistical analysis logic (T027)
    return {}

def main():
    """
    Main entry point for the pipeline.
    
    Orchestrates:
    1. FP16 baseline generation (T014)
    2. Quantized generation (T020)
    3. Statistical analysis (T027)
    
    This task specifically focuses on T014: FP16 generation and metrics.
    """
    logger.info("Starting llmXive pipeline...")
    
    try:
        # Load configuration
        config_path = Path("code/config.yaml")
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
        
        config = load_config(config_path)
        
        # Ensure output directories exist
        results_path = Path("data/results.csv")
        generated_dir = Path("data/generated")
        generated_dir.mkdir(parents=True, exist_ok=True)
        
        # Run FP16 baseline generation (T014)
        logger.info("Executing T014: FP16 Generation and Metrics")
        fp16_results = run_fp16_generation(config)
        
        if fp16_results:
            save_results_to_csv(fp16_results, str(results_path))
            logger.info("FP16 generation completed successfully.")
        else:
            logger.warning("FP16 generation produced no results.")
        
        # Run quantized generation (T020) - placeholder
        # quantization_levels = ["INT8", "INT4"]
        # quant_results = run_quantized_generation(config, quantization_levels)
        # if quant_results:
        #     # Append to results
        #     all_results = fp16_results + quant_results
        #     save_results_to_csv(all_results, str(results_path))
        
        # Run statistical analysis (T027) - placeholder
        # analysis_results = run_statistical_analysis(config)
        # if analysis_results:
        #     analysis_path = Path("data/analysis_results.json")
        #     with open(analysis_path, 'w') as f:
        #         json.dump(analysis_results, f, indent=2)
        
        logger.info("Pipeline execution completed.")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()