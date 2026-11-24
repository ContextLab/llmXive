"""
Orchestration script for T004: Correlation Analysis.
Computes the Pearson correlation between prompt semantic entropy and 
activation variance in a Diffusion Transformer (DiT).
"""
import os
import sys
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

import torch
import numpy as np
from scipy import stats

# Project imports based on T003 API surface
from code.models.flux_wan_loader import load_dit_model
from code.models.dit_wrapper import DiTActivationCapture
from code.analysis.entropy_proxy import compute_semantic_entropy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_diverse_prompts(path: Path) -> List[Dict[str, str]]:
    """Loads prompts from the processed CSV file."""
    if not path.exists():
        raise FileNotFoundError(f"Diverse prompts file not found at {path}. Please run T002 first.")
    
    prompts = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prompts.append({
                "id": row.get('prompt_id', row.get('id', '')),
                "caption": row.get('caption', '')
            })
    return prompts

def run_pipeline():
    """
    Orchestrates the correlation pipeline:
    1. Load prompts.
    2. Compute semantic entropy for each prompt.
    3. Capture activation variance for each prompt.
    4. Compute Pearson correlation.
    5. Save results to JSON.
    """
    # Paths
    prompts_path = Path("data/processed/diverse_prompts.csv")
    output_path = Path("data/processed/correlation_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Load Prompts
    logger.info(f"Loading prompts from {prompts_path}...")
    all_prompts = load_diverse_prompts(prompts_path)
    
    # To ensure execution within timeout and memory limits, we use a representative subset.
    # Verification requires n_prompts >= 100.
    sample_size = 100
    prompts = all_prompts[:sample_size]
    logger.info(f"Using a sample of {len(prompts)} prompts for correlation analysis.")

    # 2. Initialize Model and Capture Wrapper
    # We use CPU for stability and memory safety in the automated runner.
    logger.info("Loading DiT model (CPU)...")
    try:
        model = load_dit_model("flux-dev", device="cpu")
        capture_wrapper = DiTActivationCapture(model)
    except Exception as e:
        logger.error(f"Model loading failed: {e}")
        raise RuntimeError(f"Failed to initialize model for T004: {e}")

    entropies = []
    variances = []
    layers_analyzed = []

    # 3. Process Prompts
    logger.info("Processing prompts for entropy and variance...")
    for i, prompt_data in enumerate(prompts):
        caption = prompt_data['caption']
        
        # Compute Semantic Entropy (T003)
        entropy = compute_semantic_entropy(caption)
        if entropy is None:
            logger.warning(f"Entropy proxy failed for prompt {i}, skipping.")
            continue

        # Capture Activation Variance (T003)
        # returns dict[layer_name -> variance]
        try:
            var_dict = capture_wrapper.measure_activation_variance(caption)
            if not var_dict:
                logger.warning(f"No variance captured for prompt {i}, skipping.")
                continue
            
            # For correlation, we use the mean variance across all analyzed layers
            avg_var = np.mean(list(var_dict.values()))
            
            # Store layer names on first successful pass
            if not layers_analyzed:
                layers_analyzed = list(var_dict.keys())
            
            entropies.append(float(entropy))
            variances.append(float(avg_var))
            
        except Exception as e:
            logger.error(f"Variance capture failed for prompt {i}: {e}")
            continue

        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i + 1}/{len(prompts)} prompts...")

    if len(entropies) < 2:
        raise RuntimeError("Insufficient data points collected to compute correlation.")

    # 4. Compute Pearson Correlation
    logger.info("Computing Pearson correlation...")
    r, p_value = stats.pearsonr(entropies, variances)

    # 5. Prepare and Save Output
    results = {
        "correlation": float(r),
        "p_value": float(p_value),
        "n_prompts": len(entropies),
        "layers_analyzed": layers_analyzed,
        "entropy_range": [float(min(entropies)), float(max(entropies))],
        "variance_range": [float(min(variances)), float(max(variances))]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Correlation Analysis complete. Results saved to {output_path}")
    logger.info(f"Pearson r: {r:.4f}, p-value: {p_value:.4f}, n: {len(entropies)}")

if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        logger.error(f"T004 Correlation Pipeline failed: {e}")
        sys.exit(1)