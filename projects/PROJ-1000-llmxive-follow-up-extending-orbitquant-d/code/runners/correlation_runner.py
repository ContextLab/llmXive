"""
Modular runner for T017: Correlation Analysis.

Refactors logic from code/run_correlation.py into a class-based structure
for easier testing and maintenance.

Usage:
    python code/runners/correlation_runner.py
"""
import os
import sys
import json
import logging
import csv
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Project imports
from config import Config
from analysis.entropy_proxy import EntropyProxy
from models.flux_wan_loader import ModelLoader
from models.dit_wrapper import create_dit_wrapper, ActivationCapture
from utils.gpu_offload import check_gpu_availability, GPUOffloadError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CorrelationRunner:
    """
    Orchestrates the correlation analysis pipeline:
    1. Load prompts
    2. Compute semantic entropy
    3. Run DiT generation with activation capture
    4. Compute variance
    5. Calculate correlation
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.entropy_proxy = EntropyProxy(self.config)
        self.model_loader = ModelLoader(self.config)
        self.results: List[Dict[str, Any]] = []
        
    def load_prompts(self, prompt_file: Optional[str] = None) -> List[Dict[str, str]]:
        """Load prompts from CSV."""
        path = Path(prompt_file or self.config.DIVERSE_PROMPTS_PATH)
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")
        
        prompts = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                prompts.append({
                    'id': row.get('id', ''),
                    'caption': row.get('caption', '')
                })
        
        logger.info(f"Loaded {len(prompts)} prompts from {path}")
        return prompts

    def compute_entropy_scores(self, prompts: List[Dict[str, str]]) -> Dict[str, float]:
        """Compute semantic entropy for each prompt."""
        logger.info("Computing semantic entropy scores...")
        entropy_map = {}
        
        for item in prompts:
            pid = item['id']
            caption = item['caption']
            try:
                entropy = self.entropy_proxy.compute_entropy(caption)
                entropy_map[pid] = entropy
                logger.debug(f"Prompt {pid}: entropy={entropy:.4f}")
            except Exception as e:
                logger.warning(f"Failed to compute entropy for {pid}: {e}")
                entropy_map[pid] = 0.0 # Fallback to 0 if proxy fails (handled by proxy logic)
        
        return entropy_map

    def run_dit_generation_and_capture_variance(
        self, 
        prompts: List[Dict[str, str]], 
        entropy_map: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Run DiT generation for each prompt and capture activation variances.
        Uses GPU offload logic if necessary.
        """
        logger.info("Initializing DiT model for variance capture...")
        
        # Check GPU availability
        if not check_gpu_availability():
            logger.warning("GPU not available. Triggering offload logic if configured.")
            # The offload logic in T041 handles the actual re-execution
            # Here we just ensure we don't crash on CPU if not intended
            if self.config.FORCE_GPU:
                raise GPUOffloadError("GPU required but not available.")

        # Load model
        model = self.model_loader.load_model()
        if model is None:
            raise RuntimeError("Failed to load DiT model.")

        # Setup hooks
        layers = self.config.DIT_LAYERS_TO_CAPTURE
        captures = ActivationCapture(model, layers)
        
        variance_map = {}
        
        logger.info(f"Starting generation loop for {len(prompts)} prompts...")
        
        for item in prompts:
            pid = item['id']
            caption = item['caption']
            
            try:
                # Reset captures
                captures.reset()
                
                # Run generation (this triggers hooks)
                # We use a dummy generation or a very short one for variance capture
                # depending on the model capabilities defined in flux_wan_loader
                _ = self.model_loader.generate_one(model, caption, num_steps=10)
                
                # Get variance from captured activations
                # Aggregating across layers as per T017 logic
                layer_vars = captures.get_layer_variances()
                if not layer_vars:
                    logger.warning(f"No activations captured for {pid}")
                    variance_map[pid] = 0.0
                    continue
                
                # Compute mean variance across layers or max variance
                total_var = sum(layer_vars.values()) / len(layer_vars)
                variance_map[pid] = total_var
                
                logger.debug(f"Prompt {pid}: variance={total_var:.6f}")
                
            except Exception as e:
                logger.error(f"Generation failed for {pid}: {e}", exc_info=True)
                variance_map[pid] = 0.0

        return variance_map

    def aggregate_variances(
        self, 
        entropy_map: Dict[str, float], 
        variance_map: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Combine entropy and variance data."""
        results = []
        common_ids = set(entropy_map.keys()) & set(variance_map.keys())
        
        for pid in common_ids:
            results.append({
                'id': pid,
                'entropy': entropy_map[pid],
                'variance': variance_map[pid]
            })
        
        logger.info(f"Aggregated {len(results)} data points.")
        return results

    def compute_correlation(self, data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Compute Pearson correlation between entropy and variance."""
        import numpy as np
        from scipy import stats

        if len(data) < 2:
            logger.error("Not enough data points for correlation.")
            return {'correlation': 0.0, 'p_value': 1.0}

        entropies = np.array([d['entropy'] for d in data])
        variances = np.array([d['variance'] for d in data])

        # Handle constant values
        if np.std(entropies) == 0 or np.std(variances) == 0:
            logger.warning("Zero variance in data. Correlation undefined.")
            return {'correlation': 0.0, 'p_value': 1.0}

        corr, p_val = stats.pearsonr(entropies, variances)
        
        logger.info(f"Correlation: {corr:.4f}, p-value: {p_val:.6f}")
        return {
            'correlation': float(corr),
            'p_value': float(p_val),
            'n_samples': len(data)
        }

    def save_results(
        self, 
        data: List[Dict[str, Any]], 
        stats: Dict[str, float], 
        output_path: Optional[str] = None
    ):
        """Save correlation results to JSON."""
        path = Path(output_path or self.config.CORRELATION_RESULTS_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            'summary': stats,
            'data_points': data
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Results saved to {path}")

    def run(self):
        """Execute the full pipeline."""
        start_time = time.time()
        
        # 1. Load Prompts
        prompts = self.load_prompts()
        if not prompts:
            raise ValueError("No prompts loaded.")

        # 2. Compute Entropy
        entropy_map = self.compute_entropy_scores(prompts)

        # 3. Run Generation & Capture Variance
        variance_map = self.run_dit_generation_and_capture_variance(prompts, entropy_map)

        # 4. Aggregate
        data = self.aggregate_variances(entropy_map, variance_map)

        # 5. Compute Correlation
        stats = self.compute_correlation(data)

        # 6. Save
        self.save_results(data, stats)

        elapsed = time.time() - start_time
        logger.info(f"Pipeline completed in {elapsed:.2f} seconds.")
        return stats

def main():
    config = Config()
    runner = CorrelationRunner(config)
    try:
        runner.run()
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
