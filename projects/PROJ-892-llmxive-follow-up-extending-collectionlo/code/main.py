import os
import sys
import json
import csv
import logging
from pathlib import Path
import yaml
import torch

# Import existing public names from sibling modules
from config import load_config
from state_manager import register_artifact, compute_sha256, save_artifacts_state
from data_loader import (
    ensure_download_dir,
    download_base_model,
    download_lora_adapter,
    get_collection_lora_adapter,
    load_adapter_weights,
    save_adapter_weights,
    register_downloaded_artifact,
    get_model_info,
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
from statistical_analysis import (
    load_results_data,
    load_subspace_ranks,
    prepare_correlation_data,
    run_bayesian_hierarchical_model
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("state/pipeline.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def handle_oom(e: Exception, quantization_level: str) -> bool:
    """
    Handle MemoryError or SIGKILL (Exit Code 137) by logging and skipping.
    Returns True if the error was handled (OOM), False otherwise.
    """
    if isinstance(e, MemoryError) or (hasattr(e, 'code') and e.code == 137):
        logger.warning(f"Quantization Failure: OOM detected at {quantization_level}. Skipping.")
        return True
    return False

def run_fp16_generation(config: dict) -> Path:
    """
    Execute FP16 baseline generation, compute metrics, and save results.
    """
    logger.info("Starting FP16 Baseline Generation...")
    
    # Ensure data directories
    data_dir = Path("data")
    generated_dir = data_dir / "generated"
    references_dir = data_dir / "references"
    generated_dir.mkdir(parents=True, exist_ok=True)
    (references_dir / "fp16_refs").mkdir(parents=True, exist_ok=True)
    
    # Load model and adapter
    base_model, adapter = get_collection_lora_adapter(config)
    
    # Generate reference images
    logger.info("Generating FP16 Reference Images...")
    ref_images = generate_fp16_reference_images(
        base_model, adapter, config['prompts'], config['seed']
    )
    
    # Save references
    for prompt, img in ref_images.items():
        path = references_dir / "fp16_refs" / f"{prompt.replace(' ', '_')}.png"
        img.save(path)
        register_artifact(str(path))
    
    # Generate main batch
    logger.info("Generating FP16 Batch...")
    results = []
    try:
        generated_images = generate_images(
            base_model, adapter, config['prompts'], config['seed']
        )
        
        for prompt, img in generated_images.items():
            # Save image
            img_path = generated_dir / f"fp16_{prompt.replace(' ', '_')}.png"
            img.save(img_path)
            register_artifact(str(img_path))
            
            # Compute metrics
            clip_sim = compute_image_text_similarity(img, prompt)
            lpips_dist = compute_lpips_distance(img, references_dir / "fp16_refs" / f"{prompt.replace(' ', '_')}.png")
            
            results.append({
                'prompt': prompt,
                'quantization': 'FP16',
                'clip_similarity': clip_sim,
                'lpips_distance': lpips_dist,
                'image_path': str(img_path)
            })
    except MemoryError as e:
        if handle_oom(e, "FP16"):
            return Path("data/results_fp16_partial.csv")
        
    # Save results
    results_file = data_dir / "results.csv"
    with open(results_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
        
    register_artifact(str(results_file))
    return results_file

def run_quantized_generation(config: dict, results_file: Path) -> Path:
    """
    Execute INT8 and INT4 quantization, generation, and metrics.
    """
    logger.info("Starting Quantized Generation...")
    data_dir = Path("data")
    quantized_dir = data_dir / "quantized"
    quantized_dir.mkdir(parents=True, exist_ok=True)
    
    # Load FP16 adapter
    fp16_path = data_dir / "models" / "adapter_fp16.safetensors"
    if not fp16_path.exists():
        raise FileNotFoundError(f"FP16 adapter not found at {fp16_path}. Run T007b first.")
    
    base_model, _ = get_collection_lora_adapter(config)
    
    # Load existing results to append
    existing_results = []
    if results_file.exists():
        with open(results_file, 'r') as f:
            reader = csv.DictReader(f)
            existing_results = list(reader)
    
    # Process INT8
    for level, func in [("INT8", quantize_adapter_fp16_to_int8), ("INT4", quantize_adapter_fp16_to_int4)]:
        logger.info(f"Processing {level} quantization...")
        try:
            # Quantize
            q_adapter_path = quantized_dir / f"adapter_{level.lower()}.safetensors"
            quantize_adapter_weights = func(fp16_path, q_adapter_path)
            register_artifact(str(q_adapter_path))
            
            # Generate
            generated_images = generate_images(
                base_model, quantize_adapter_weights, config['prompts'], config['seed']
            )
            
            # Reference for comparison (FP16 refs)
            ref_dir = data_dir / "references" / "fp16_refs"
            
            for prompt, img in generated_images.items():
                img_path = data_dir / "generated" / f"{level}_{prompt.replace(' ', '_')}.png"
                img.save(img_path)
                register_artifact(str(img_path))
                
                # Compute metrics
                clip_sim = compute_image_text_similarity(img, prompt)
                lpips_dist = compute_lpips_distance(img, ref_dir / f"{prompt.replace(' ', '_')}.png")
                
                # CESR calculation
                cesr = compute_cesr_score(img, ref_dir, target_prompt=prompt)
                
                existing_results.append({
                    'prompt': prompt,
                    'quantization': level,
                    'clip_similarity': clip_sim,
                    'lpips_distance': lpips_dist,
                    'cesr_score': cesr,
                    'image_path': str(img_path)
                })
                  
        except MemoryError as e:
            if handle_oom(e, level):
                logger.warning(f"Skipping {level} due to OOM.")
                continue
            raise

    # Save updated results
    with open(results_file, 'w', newline='') as f:
        fieldnames = ['prompt', 'quantization', 'clip_similarity', 'lpips_distance', 'cesr_score', 'image_path']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_results)
        
    return results_file

def run_statistical_analysis(config: dict) -> Path:
    """
    Execute Bayesian Hierarchical Model analysis and save results.
    This implements T027: logic to execute analysis and save JSON.
    """
    logger.info("Starting Statistical Analysis (T027)...")
    
    data_dir = Path("data")
    results_file = data_dir / "results.csv"
    subspace_file = data_dir / "subspace_ranks.json"
    output_file = data_dir / "analysis_results.json"
    
    if not results_file.exists():
        logger.error("results.csv not found. Run generation tasks first.")
        raise FileNotFoundError("results.csv not found")
        
    if not subspace_file.exists():
        logger.error("subspace_ranks.json not found. Run T009 first.")
        raise FileNotFoundError("subspace_ranks.json not found")

    try:
        # Load data
        results_df = load_results_data(str(results_file))
        subspace_ranks = load_subspace_ranks(str(subspace_file))
        
        # Prepare correlation data
        corr_data = prepare_correlation_data(results_df, subspace_ranks)
        
        # Run BHM
        logger.info("Running Bayesian Hierarchical Model...")
        analysis_results = run_bayesian_hierarchical_model(results_df, corr_data)
        
        # Save results
        with open(output_file, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
            
        register_artifact(str(output_file))
        logger.info(f"Analysis results saved to {output_file}")
        
        return output_file
        
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        raise

def main():
    """
    Main entry point for the pipeline.
    Orchestrates: Setup -> FP16 Gen -> Quant Gen -> Analysis.
    """
    config = load_config("code/config.yaml")
    
    # 1. FP16 Baseline
    results_file = run_fp16_generation(config)
    
    # 2. Quantized Generation
    results_file = run_quantized_generation(config, results_file)
    
    # 3. Statistical Analysis (T027)
    analysis_file = run_statistical_analysis(config)
    
    logger.info("Pipeline completed successfully.")
    return analysis_file

if __name__ == "__main__":
    main()