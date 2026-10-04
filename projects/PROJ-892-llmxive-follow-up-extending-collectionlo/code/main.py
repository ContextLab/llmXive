import os
import sys
import json
import csv
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def load_config() -> Dict[str, Any]:
    """Load configuration from code/config.yaml."""
    config_path = get_project_root() / "code" / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def handle_oom(error: Exception) -> bool:
    """Handle OutOfMemory errors."""
    if "memory" in str(error).lower() or "cuda" in str(error).lower():
        logger.warning(f"Memory error detected: {error}")
        return True
    return False

def load_subspace_ranks() -> Dict[str, Any]:
    """Load subspace ranks from data/subspace_ranks_merged.json."""
    from data_loader import load_subspace_ranks_merged
    return load_subspace_ranks_merged()

def derive_effect_from_prompt(prompt: str, subspace_ranks: Dict[str, Any]) -> Optional[str]:
    """Derive effect name from prompt using prefix matching."""
    normalized_prompt = prompt.lower().strip()
    
    for effect_name in subspace_ranks.keys():
        normalized_effect = effect_name.lower().strip()
        if normalized_prompt.startswith(normalized_effect) or normalized_effect in normalized_prompt:
            return effect_name
    
    return None

def run_fp16_generation(prompts: List[str], seeds: List[int], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Run FP16 generation loop."""
    from generator import generate_fp16_baseline_images
    from data_loader import load_fp16_adapter_and_base_model
    
    logger.info("Loading FP16 adapter and base model...")
    adapter_path, base_model_path = load_fp16_adapter_and_base_model()
    
    logger.info(f"Generating {len(prompts)} images with {len(seeds)} seeds...")
    results = generate_fp16_baseline_images(prompts, seeds, adapter_path, base_model_path, config)
    
    return results

def run_quantized_generation(adapter_path: Path, prompts: List[str], seeds: List[int], 
                           quantization_level: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Run quantized generation loop."""
    from generator import generate_images_for_adapters
    
    logger.info(f"Generating images with {quantization_level} adapter...")
    results = generate_images_for_adapters(adapter_path, prompts, seeds, quantization_level, config)
    
    return results

def save_results_to_csv(results: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """Save results to CSV."""
    if output_path is None:
        output_path = get_project_root() / "data" / "results.csv"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not results:
        logger.warning("No results to save")
        return output_path
    
    # Ensure all required columns exist
    required_columns = ['prompt', 'seed', 'quantization_level', 'similarity_score', 
                      'lpips_distance', 'cesr_score', 'image_path', 'subspace_rank', 'effect']
    
    # Load subspace ranks for joining
    subspace_ranks = load_subspace_ranks()
    
    for result in results:
        # Derive effect from prompt
        effect = derive_effect_from_prompt(result.get('prompt', ''), subspace_ranks)
        result['effect'] = effect
        
        # Get subspace rank
        if effect and effect in subspace_ranks:
            rank_info = subspace_ranks[effect]
            result['subspace_rank'] = rank_info.get('rank', 0) if isinstance(rank_info, dict) else 0
        else:
            result['subspace_rank'] = 0  # Default if not found
    
    # Write CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=required_columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Results saved to {output_path}")
    
    # Register in state
    from data_loader import register_downloaded_artifact
    register_downloaded_artifact("results_csv", output_path)
    
    return output_path

def run_baseline_generation_loop() -> List[Dict[str, Any]]:
    """Run baseline generation loop and save results."""
    config = load_config()
    
    # Get prompts and seeds
    prompts = config.get('prompts', [])
    seeds = config.get('seeds', [42])
    
    logger.info(f"Running baseline generation with {len(prompts)} prompts and {len(seeds)} seeds")
    
    # Run generation
  # Run generation
    results = run_fp16_generation(prompts, seeds, config)
    
    # Save results
    save_results_to_csv(results)
    
    return results

def run_quantized_generation_loop() -> List[Dict[str, Any]]:
    """Run quantized generation loop and append results."""
    config = load_config()
    
    # Get prompts and seeds
    prompts = config.get('prompts', [])
    seeds = config.get('seeds', [42])
    
    # Load adapter
    from data_loader import load_fp16_adapter_and_base_model
    adapter_path, _ = load_fp16_adapter_and_base_model()
    
    all_results = []
    
    for level in ['int8', 'int4']:
        logger.info(f"Running quantized generation for {level}...")
        try:
            results = run_quantized_generation(adapter_path, prompts, seeds, level, config)
            all_results.extend(results)
        except Exception as e:
            logger.error(f"Quantized generation failed for {level}: {e}")
            # Skip this level as per FR-008
            continue
    
    # Append results to existing CSV
    if all_results:
        from data_loader import get_project_root
        output_path = get_project_root() / "data" / "results.csv"
        
        # Load existing results
        if output_path.exists():
            existing_df = pd.read_csv(output_path)
            new_df = pd.DataFrame(all_results)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df.to_csv(output_path, index=False)
        else:
            save_results_to_csv(all_results)
    
    return all_results

def save_analysis_results_wrapper() -> Path:
    """Wrapper to save analysis results."""
    from statistical_analysis import save_analysis_results, run_bayesian_hierarchical_model, load_results_data, load_subspace_ranks, prepare_bayesian_dataset, aggregate_cesr_to_effect_level
    import pandas as pd
    
    # Load data
    results_df = load_results_data()
    subspace_ranks = load_subspace_ranks()
    
    # Prepare dataset
    dataset = prepare_bayesian_dataset(results_df, subspace_ranks)
    aggregated = aggregate_cesr_to_effect_level(results_df)
    
    # Run model
    model_results = run_bayesian_hierarchical_model(aggregated)
    
    # Save
    return save_analysis_results(model_results)

def record_ci_timing() -> Dict[str, Any]:
    """Record CI timing information."""
    timing_data = {
        "start_time": time.time(),
        "end_time": time.time(),
        "duration_seconds": time.time() - time.time()
    }
    
    output_path = get_project_root() / "data" / "ci_report.json"
    with open(output_path, "w") as f:
        json.dump(timing_data, f, indent=2)
    
    logger.info(f"CI timing recorded: {timing_data['duration_seconds']:.2f}s")
    return timing_data

def main():
    """Main entry point for the pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLMxive Research Pipeline")
    parser.add_argument('--phase', type=str, choices=['prepare', 'analyze', 'full'], 
                      default='full', help='Pipeline phase to execute')
    parser.add_argument('--config', type=str, default=None, help='Path to config file')
    
    args = parser.parse_args()
    
    start_time = time.time()
    
    try:
        if args.phase in ['prepare', 'full']:
            logger.info("=== Phase: Prepare ===")
            # Run baseline generation
            run_baseline_generation_loop()
            
            # Run quantized generation
            run_quantized_generation_loop()
            
            logger.info("Preparation phase completed")
        
        if args.phase in ['analyze', 'full']:
            logger.info("=== Phase: Analyze ===")
            # Run statistical analysis
            save_analysis_results_wrapper()
            
            logger.info("Analysis phase completed")
        
        # Record timing
        record_ci_timing()
        
        end_time = time.time()
        logger.info(f"Pipeline completed in {end_time - start_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
