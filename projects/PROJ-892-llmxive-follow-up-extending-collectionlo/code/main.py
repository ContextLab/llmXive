import os
import sys
import json
import csv
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing project modules
from config import load_config
from data_loader import (
    load_fp16_adapter_and_base_model,
    load_pipeline_for_cpu,
    get_collection_lora_adapter,
    load_adapter_weights
)
from generator import (
    generate_fp16_baseline_images,
    generate_images_for_adapters,
    generate_fp16_reference_images
)
from metrics import (
    compute_cosine_similarity,
    compute_lpips_distance,
    compute_cesr_score,
    compute_lpips_distance_from_paths
)
from error_handler import handle_memory_error
from state_manager import (
    ensure_state_dir,
    compute_sha256,
    load_artifacts_state,
    save_artifacts_state,
    register_artifact
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

def handle_oom(e: MemoryError) -> bool:
    """
    Handle Out-Of-Memory errors by logging and returning a skip flag.
    Uses logic from T008b.
    """
    logger.error("Quantization Failure: Memory Error detected")
    handle_memory_error(e)
    return True  # Signal to skip this level

def run_fp16_generation(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Run FP16 baseline generation (User Story 1).
    Dependencies: T010b, T011, T012, T013
    """
    logger.info("Starting FP16 baseline generation...")
    results = []

    try:
        # Load models (T010b)
        pipe, adapter_weights = load_fp16_adapter_and_base_model()
        logger.info("Models loaded successfully.")

        # Generate images (T011)
        generated_images = generate_fp16_baseline_images(pipe, config)
        logger.info(f"Generated {len(generated_images)} FP16 baseline images.")

        # Compute metrics (T012, T013)
        for item in generated_images:
            prompt = item['prompt']
            seed = item['seed']
            image_path = item['image_path']

            # CLIP Similarity
            similarity = compute_cosine_similarity(image_path, prompt)

            # LPIPS (Self-consistency check against references)
            # Assuming references are in data/references/fp16_refs/
            ref_paths = [str(p) for p in Path('data/references/fp16_refs').glob(f'*{prompt}*.png')]
            lpips = 0.0
            if ref_paths:
                lpips = compute_lpips_distance_from_paths(image_path, ref_paths[0])

            results.append({
                'prompt': prompt,
                'seed': seed,
                'quantization_level': 'fp16',
                'similarity_score': similarity,
                'lpips_distance': lpips,
                'cesr_score': None,  # Calculated in US2
                'image_path': image_path
            })

        # Save intermediate results
        save_results_to_csv(results, 'data/results.csv')
        logger.info("FP16 results saved.")

    except MemoryError as e:
        if handle_oom(e):
            logger.warning("Skipping FP16 generation due to OOM.")
            return []
        raise

    return results

def run_quantized_generation(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Run Quantized (INT8/INT4) generation (User Story 2).
    Dependencies: T016, T017, T018, T019
    """
    logger.info("Starting Quantized generation...")
    results = []
    quantization_levels = ['int8', 'int4']

    # Load references for CESR (T011d)
    # Assuming this is handled by metrics or data_loader
    from data_loader import organize_reference_images
    ref_lookup = organize_reference_images()

    for level in quantization_levels:
        logger.info(f"Processing quantization level: {level}")
        try:
            # Load quantized adapter
            adapter_path = f"data/quantized/adapter_{level}.safetensors"
            if not os.path.exists(adapter_path):
                logger.warning(f"Quantized adapter {adapter_path} not found. Skipping {level}.")
                continue

            # Load pipeline with quantized weights
            # Note: Actual loading logic depends on how T016 saves the weights
            # Assuming load_pipeline_for_cpu can handle the quantized path
            pipe = load_pipeline_for_cpu(adapter_path)

            # Generate images (T017)
            generated_images = generate_images_for_adapters(pipe, config, level)
            logger.info(f"Generated {len(generated_images)} images for {level}.")

            for item in generated_images:
                prompt = item['prompt']
                seed = item['seed']
                image_path = item['image_path']

                # CLIP Similarity
                similarity = compute_cosine_similarity(image_path, prompt)

                # LPIPS vs FP16 Baseline (T019)
                # Find corresponding FP16 image
                fp16_item = next((r for r in results if r['prompt'] == prompt and r['seed'] == seed and r['quantization_level'] == 'fp16'), None)
                lpips = 0.0
                if fp16_item:
                    lpips = compute_lpips_distance_from_paths(image_path, fp16_item['image_path'])

                # CESR (T018)
                cesr = compute_cesr_score(image_path, prompt, ref_lookup)

                results.append({
                    'prompt': prompt,
                    'seed': seed,
                    'quantization_level': level,
                    'similarity_score': similarity,
                    'lpips_distance': lpips,
                    'cesr_score': cesr,
                    'image_path': image_path
                })

        except MemoryError as e:
            if handle_oom(e):
                logger.warning(f"Skipping {level} generation due to OOM.")
                continue
            raise
        except Exception as e:
            logger.error(f"Error processing {level}: {e}")
            continue

    return results

def run_statistical_analysis(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run Bayesian Hierarchical Model analysis (User Story 3).
    Dependencies: T023, T024, T025, T026
    """
    logger.info("Starting Statistical Analysis...")
    from statistical_analysis import main as analysis_main
    return analysis_main()

def save_results_to_csv(results: List[Dict[str, Any]], filepath: str):
    """
    Append results to CSV file.
    Schema: prompt, seed, quantization_level, similarity_score, lpips_distance, cesr_score, image_path
    """
    file_exists = os.path.isfile(filepath)
    with open(filepath, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['prompt', 'seed', 'quantization_level', 'similarity_score', 'lpips_distance', 'cesr_score', 'image_path'])
        if not file_exists:
            writer.writeheader()
        writer.writerows(results)
    
    # Register in state
    if os.path.exists(filepath):
        hash_val = compute_sha256(filepath)
        state = load_artifacts_state()
        register_artifact(state, filepath, hash_val, 'results_csv')
        save_artifacts_state(state)
        logger.info(f"Registered {filepath} with hash {hash_val}")

def main():
    """
    Main entry point for the pipeline.
    Orchestrates US1, US2, US3 execution.
    """
    start_time = time.time()
    logger.info("Pipeline started.")

    config = load_config()
    all_results = []

    # 1. Run FP16 Baseline (US1)
    fp16_results = run_fp16_generation(config)
    all_results.extend(fp16_results)

    # 2. Run Quantized Generation (US2)
    # Note: T020 specifically implements the logic to run this and append to CSV
    quantized_results = run_quantized_generation(config)
    all_results.extend(quantized_results)

    # Save combined results
    save_results_to_csv(all_results, 'data/results.csv')

    # 3. Run Statistical Analysis (US3)
    try:
        analysis_results = run_statistical_analysis(config)
        # Save analysis results
        with open('data/analysis_results.json', 'w') as f:
            json.dump(analysis_results, f, indent=2)
        logger.info("Statistical analysis saved.")
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")

    # 4. Generate CI Report (Timing)
    end_time = time.time()
    duration = end_time - start_time
    ci_report = {
        'duration_seconds': duration,
        'status': 'completed' if duration <= 21600 else 'timeout_warning', # 6 hours
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open('data/ci_report.json', 'w') as f:
        json.dump(ci_report, f, indent=2)
    logger.info(f"CI Report generated. Duration: {duration}s")

    logger.info("Pipeline completed successfully.")
    return 0

if __name__ == '__main__':
    sys.exit(main())