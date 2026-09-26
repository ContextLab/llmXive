"""
Orchestration script for Phase 2 Inference: Dynamic Router Evaluation.

Workflow:
1. Load Test Split Prompts (from data/processed/prompts.csv, test split)
2. Compute Semantic Entropy for each prompt (using EntropyProxy)
3. Select Rotation Matrix Index using EntropyRouter (from clustering_report.json)
4. Generate Images using DiT with dynamic rotation (via W2A4Engine + DiTWrapper)
5. Log Metrics (entropy, selected matrix index, generation time, output path)
6. Save results to data/processed/router_inference_results.json

Dependencies:
- T006: Prompts split into train/test
- T009: EntropyProxy
- T022: Clustering report (rotation matrices)
- T024: EntropyRouter
- T025: W2A4Engine integration
- T007/T008: Model loading and activation hooks
"""

import os
import sys
import json
import logging
import csv
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project imports
from config import Config
from analysis.entropy_proxy import EntropyProxy
from analysis.router import EntropyRouter
from models.flux_wan_loader import ModelLoader
from models.dit_wrapper import DiTWrapper
from quantization.w2a4_engine import W2A4Engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_test_split_prompts(config: Config) -> List[Dict[str, Any]]:
    """
    Load the test split prompts from the preprocessed CSV.
    Expects data/processed/prompts.csv with a 'split' column.
    """
    prompts_path = config.PROCESSED_PROMPTS_PATH
    if not os.path.exists(prompts_path):
        raise FileNotFoundError(f"Test split prompts not found at {prompts_path}. "
                                "Run T006 (preprocess) first.")

    prompts = []
    with open(prompts_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('split') == 'test':
                prompts.append({
                    'id': row.get('id', ''),
                    'text': row.get('text', ''),
                    'source': row.get('source', 'unknown')
                })

    if not prompts:
        raise ValueError("No test split prompts found. Ensure T006 split data correctly.")

    logger.info(f"Loaded {len(prompts)} test split prompts.")
    return prompts

def compute_entropy_scores(prompts: List[Dict[str, Any]], config: Config) -> Dict[str, float]:
    """
    Compute semantic entropy for each prompt using the EntropyProxy.
    Returns a dict mapping prompt_id to entropy score.
    """
    logger.info("Computing semantic entropy scores...")
    proxy = EntropyProxy(config)
    results = {}

    for prompt_data in prompts:
        prompt_id = prompt_data['id']
        prompt_text = prompt_data['text']
        try:
            entropy = proxy.compute_entropy(prompt_text)
            results[prompt_id] = float(entropy)
            logger.debug(f"Prompt {prompt_id}: entropy = {entropy:.4f}")
        except Exception as e:
            logger.error(f"Failed to compute entropy for prompt {prompt_id}: {e}")
            # Fail loudly as per constraints - do not skip or use synthetic
            raise RuntimeError(f"Entropy computation failed for {prompt_id}")

    return results

def select_rotation_matrices(entropy_scores: Dict[str, float], config: Config) -> Dict[str, int]:
    """
    Use the EntropyRouter to select rotation matrix indices for each prompt.
    """
    logger.info("Selecting rotation matrices via EntropyRouter...")
    router = EntropyRouter(config)
    results = {}

    for prompt_id, entropy in entropy_scores.items():
        try:
            matrix_idx = router.select_matrix(entropy)
            results[prompt_id] = int(matrix_idx)
        except Exception as e:
            logger.error(f"Router selection failed for {prompt_id}: {e}")
            raise RuntimeError(f"Router selection failed for {prompt_id}")

    return results

def run_dit_generation_with_dynamic_rotation(
    prompts: List[Dict[str, Any]],
    matrix_selections: Dict[str, int],
    config: Config
) -> List[Dict[str, Any]]:
    """
    Generate images using DiT with dynamic rotation matrices selected by entropy.
    Returns a list of generation logs.
    """
    logger.info("Starting DiT generation with dynamic rotation...")

    # Load model
    model_loader = ModelLoader(config)
    model, device = model_loader.load_model()

    # Initialize W2A4 engine
    w2a4_engine = W2A4Engine(config)
    w2a4_engine.load_rotation_matrices_from_report()

    # Initialize DiT wrapper for activation capture (though we are using dynamic routing here)
    # The W2A4Engine handles the rotation injection logic internally based on the router selection.
    
    generation_logs = []
    total_start = time.time()

    for i, prompt_data in enumerate(prompts):
        prompt_id = prompt_data['id']
        prompt_text = prompt_data['text']
        matrix_idx = matrix_selections.get(prompt_id)

        if matrix_idx is None:
            logger.warning(f"Skipping {prompt_id}: no matrix selection found.")
            continue

        logger.info(f"[{i+1}/{len(prompts)}] Generating for {prompt_id} (Matrix: {matrix_idx})")

        try:
            start_time = time.time()
            
            # Configure engine with specific matrix index for this prompt
            w2a4_engine.set_current_matrix_index(matrix_idx)

            # Run generation
            # Note: The actual generation logic depends on the specific DiT implementation
            # in flux_wan_loader and w2a4_engine. We assume a standard interface.
            output_image_path = w2a4_engine.generate_image(prompt_text, prompt_id)
            
            end_time = time.time()
            duration = end_time - start_time

            generation_logs.append({
                'prompt_id': prompt_id,
                'prompt_text': prompt_text[:100] + "..." if len(prompt_text) > 100 else prompt_text,
                'entropy': None, # Will be filled later
                'matrix_index': matrix_idx,
                'generation_time_sec': duration,
                'output_path': output_image_path,
                'status': 'success'
            })

        except Exception as e:
            logger.error(f"Generation failed for {prompt_id}: {e}")
            generation_logs.append({
                'prompt_id': prompt_id,
                'prompt_text': prompt_text,
                'entropy': None,
                'matrix_index': matrix_idx,
                'generation_time_sec': 0.0,
                'output_path': None,
                'status': 'failed',
                'error': str(e)
            })

    total_duration = time.time() - total_start
    logger.info(f"Generation complete. Total time: {total_duration:.2f}s")

    return generation_logs

def aggregate_results(
    prompts: List[Dict[str, Any]],
    entropy_scores: Dict[str, float],
    matrix_selections: Dict[str, int],
    generation_logs: List[Dict[str, Any]],
    config: Config
) -> Dict[str, Any]:
    """
    Aggregate all results into a final report structure.
    """
    # Merge entropy and matrix selection into generation logs
    for log in generation_logs:
        pid = log['prompt_id']
        log['entropy'] = entropy_scores.get(pid)
        log['matrix_index'] = matrix_selections.get(pid)

    # Calculate summary statistics
    successful = [l for l in generation_logs if l['status'] == 'success']
    failed = [l for l in generation_logs if l['status'] == 'failed']
    
    avg_time = sum(l['generation_time_sec'] for l in successful) / len(successful) if successful else 0.0
    
    report = {
        'config': {
            'model': config.MODEL_NAME,
            'device': config.DEVICE,
            'num_test_prompts': len(prompts),
            'num_successful': len(successful),
            'num_failed': len(failed)
        },
        'summary': {
            'total_prompts': len(prompts),
            'successful_generations': len(successful),
            'failed_generations': len(failed),
            'average_generation_time_sec': avg_time
        },
        'results': generation_logs
    }

    return report

def save_results(report: Dict[str, Any], config: Config) -> None:
    """
    Save the final report to data/processed/router_inference_results.json
    """
    output_path = config.ROUTER_INFERENCE_RESULTS_PATH
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for Phase 2 Inference orchestration.
    """
    config = Config()
    logger.info("Starting Router Inference Pipeline (T027)")

    try:
        # 1. Load Test Split
        prompts = load_test_split_prompts(config)

        # 2. Compute Entropy
        entropy_scores = compute_entropy_scores(prompts, config)

        # 3. Select Matrices
        matrix_selections = select_rotation_matrices(entropy_scores, config)

        # 4. Generate Images
        generation_logs = run_dit_generation_with_dynamic_rotation(prompts, matrix_selections, config)

        # 5. Aggregate Results
        report = aggregate_results(prompts, entropy_scores, matrix_selections, generation_logs, config)

        # 6. Save Results
        save_results(report, config)

        logger.info("Pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())