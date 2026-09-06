import os
import sys
import json
import csv
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def handle_oom(e: MemoryError) -> bool:
    """Handle memory errors by logging and returning a skip flag."""
    logger.warning("Quantization Failure: Out of memory. Skipping affected level.")
    return True

def load_subspace_ranks() -> Dict[str, Any]:
    """Load subspace ranks from data/subspace_ranks_merged.json."""
    from data_loader import load_subspace_ranks as loader
    return loader()

def derive_effect_from_prompt(prompt: str, subspace_ranks: Dict[str, Any]) -> str:
    """Derive effect from prompt using prefix matching."""
    prompt_lower = prompt.lower().strip()
    for effect_name, effect_data in subspace_ranks.get('effects', {}).items():
        effect_key = effect_data.get('key', effect_name).lower().strip()
        if effect_key in prompt_lower or effect_name.lower().strip() in prompt_lower:
            return effect_name
    raise ValueError(f"No effect found for prompt: {prompt}")

def run_fp16_generation(prompts: List[str], seeds: List[int], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Run FP16 generation loop."""
    from data_loader import load_fp16_adapter_and_base_model
    from generator import generate_images
    
    results = []
    
    try:
        # Load adapter and base model
        # This function now handles flexible argument passing
        adapter, base_model = load_fp16_adapter_and_base_model()
        
        # Generate images
        for prompt in prompts:
            for seed in seeds:
                try:
                    image_path = generate_images(
                        pipe=base_model,
                        prompt=prompt,
                        seed=seed,
                        output_dir=get_project_root() / "data" / "generated" / "baseline",
                        quantization_level="FP16"
                    )
                    
                    # Calculate metrics (simplified for this task)
                    results.append({
                        "prompt": prompt,
                        "seed": seed,
                        "quantization_level": "FP16",
                        "image_path": str(image_path),
                        "effect": derive_effect_from_prompt(prompt, load_subspace_ranks())
                    })
                except Exception as e:
                    logger.error(f"Error generating image for prompt '{prompt}' and seed {seed}: {e}")
                    continue
                    
    except Exception as e:
        logger.error(f"Error in FP16 generation: {e}")
        # Handle memory errors
        if isinstance(e, MemoryError):
            handle_oom(e)
        raise
    
    return results

def run_quantized_generation(prompts: List[str], seeds: List[int], config: Dict[str, Any], level: str) -> List[Dict[str, Any]]:
    """Run quantized generation loop."""
    # Placeholder for quantized generation
    results = []
    logger.info(f"Running quantized generation for level: {level}")
    # In a full implementation, this would load quantized adapters and generate images
    return results

def save_results_to_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Save results to CSV file."""
    if not results:
        logger.warning("No results to save.")
        return
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get all unique keys
    fieldnames = set()
    for result in results:
        fieldnames.update(result.keys())
    
    # Add required columns if missing
    required_columns = ['prompt', 'seed', 'quantization_level', 'similarity_score', 
                      'lpips_distance', 'cesr_score', 'image_path', 'subspace_rank', 'effect']
    for col in required_columns:
        fieldnames.add(col)
    
    # Sort fieldnames for consistency
    fieldnames = sorted(fieldnames)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def run_baseline_generation_loop() -> List[Dict[str, Any]]:
    """Run the baseline generation loop."""
    from config import load_config
    
    config = load_config()
    prompts = config.get('prompts', [])
    seeds = config.get('seeds', [])
    
    results = run_fp16_generation(prompts, seeds, config)
    
    # Save results
    results_path = get_project_root() / "data" / "results.csv"
    save_results_to_csv(results, results_path)
    
    return results

def save_analysis_results_wrapper(results: Dict[str, Any]) -> None:
    """Wrapper to save analysis results."""
    from statistical_analysis import save_analysis_results
    save_analysis_results(results)

def record_ci_timing(start_time: float, end_time: float) -> None:
    """Record CI timing information."""
    timing_data = {
        "start_time": start_time,
        "end_time": end_time,
        "duration": end_time - start_time
    }
    
    output_path = get_project_root() / "data" / "ci_report.json"
    with open(output_path, 'w') as f:
        json.dump(timing_data, f, indent=2)
    
    logger.info(f"CI timing recorded: {timing_data['duration']:.2f}s")

def main():
    """Main entry point for the pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='llmXive Automated Science Pipeline')
    parser.add_argument('--phase', type=str, required=True, 
                      choices=['prepare', 'generate', 'analyze', 'validate'],
                      help='Pipeline phase to execute')
    parser.add_argument('--level', type=str, choices=['FP16', 'INT8', 'INT4'],
                      help='Quantization level (for generate phase)')
    
    args = parser.parse_args()
    
    start_time = time.time()
    
    try:
        if args.phase == 'prepare':
            logger.info("Starting prepare phase...")
            # Run baseline generation
            run_baseline_generation_loop()
            
        elif args.phase == 'generate':
            if not args.level:
                parser.error("--level is required for generate phase")
            logger.info(f"Starting generate phase for level: {args.level}")
            # Run quantized generation
            from config import load_config
            config = load_config()
            prompts = config.get('prompts', [])
            seeds = config.get('seeds', [])
            results = run_quantized_generation(prompts, seeds, config, args.level)
            save_results_to_csv(results, get_project_root() / "data" / "results.csv")
            
        elif args.phase == 'analyze':
            logger.info("Starting analyze phase...")
            # Run statistical analysis
            from statistical_analysis import main as analysis_main
            analysis_main()
            
        elif args.phase == 'validate':
            logger.info("Starting validate phase...")
            # Run validation
            from validate_results import main as validate_main
            validate_main()
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise
    finally:
        end_time = time.time()
        record_ci_timing(start_time, end_time)
    
    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()
