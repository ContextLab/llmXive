"""
Modular runner for T037: Code cleanup and refactoring of `code/` into modular runners.
This script refactors the router inference pipeline (T029) into a clean, modular runner.
It orchestrates: Load Test Split -> Compute Entropy -> Load Matrices -> Select Matrix ->
Generate Images -> Log Metrics.
"""
import os
import sys
import json
import logging
import csv
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from existing API surface
from config import Config
from analysis.entropy_proxy import EntropyProxy
from analysis.load_matrices import MatrixLoader
from analysis.router import EntropyRouter
from models.flux_wan_loader import ModelLoader
from models.dit_wrapper import DiTWrapper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RouterInferenceRunner:
    """
    Modular runner for the Router Inference pipeline.
    Encapsulates logic for T029 refactoring.
    """
    def __init__(self, config: Config):
        self.config = config
        self.entropy_proxy = EntropyProxy(config)
        self.matrix_loader = MatrixLoader(config)
        self.router = EntropyRouter(config)
        self.model_loader = ModelLoader(config)
        self.di_t_wrapper = None

    def load_prompts(self) -> List[Dict[str, Any]]:
        """Load test split prompts."""
        path = Path(self.config.paths.processed_data) / "prompts_test.csv"
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}. Run T006b first.")
        
        prompts = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                prompts.append({"id": row.get('id', ''), "text": row.get('text', '')})
        return prompts

    def compute_entropy(self, prompts: List[Dict[str, Any]]) -> Dict[str, float]:
        """Compute entropy for all prompts."""
        logger.info(f"Computing entropy for {len(prompts)} prompts...")
        scores = {}
        for i, p in enumerate(prompts):
            if i % 10 == 0:
                logger.info(f"Processing {i}/{len(prompts)}")
            scores[p["id"]] = self.entropy_proxy.compute_entropy(p["text"])
        return scores

    def load_matrices(self) -> Dict[str, Any]:
        """Load pre-computed rotation matrices."""
        logger.info("Loading rotation matrices...")
        # Uses T022b output
        matrices = self.matrix_loader.load_matrices_from_path(
            Path(self.config.paths.processed_data) / "clustering_report.json"
        )
        return matrices

    def setup_model(self):
        """Initialize the DiT model."""
        logger.info("Initializing DiT model for router inference...")
        self.di_t_wrapper = self.model_loader.load_model()
        self.di_t_wrapper.enable_variance_capture() # Optional, for logging

    def run_inference(self, prompts: List[Dict[str, Any]], 
                      entropy_scores: Dict[str, float], 
                      matrices: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run inference with dynamic matrix selection.
        For each prompt:
          1. Get entropy
          2. Router selects matrix index
          3. Apply matrix during generation
          4. Log metrics
        """
        logger.info("Starting Router Inference...")
        if not self.di_t_wrapper:
            self.setup_model()
        
        results = []
        batch_size = self.config.hyperparameters.batch_size
        
        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} prompts)")
            
            batch_results = self.di_t_wrapper.generate_with_dynamic_rotation(
                batch, 
                entropy_scores, 
                self.router, 
                matrices
            )
            results.extend(batch_results)
        
        return results

    def save_results(self, results: List[Dict[str, Any]], output_path: Optional[str] = None):
        """Save inference results."""
        if output_path is None:
            output_path = Path(self.config.paths.processed_data) / "router_inference_results.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")

    def run(self):
        """Run the full router inference pipeline."""
        logger.info("Starting Router Inference Runner...")
        
        # 1. Load Prompts
        prompts = self.load_prompts()
        logger.info(f"Loaded {len(prompts)} prompts.")
        
        # 2. Compute Entropy
        entropy_scores = self.compute_entropy(prompts)
        
        # 3. Load Matrices
        matrices = self.load_matrices()
        
        # 4. Run Inference
        results = self.run_inference(prompts, entropy_scores, matrices)
        
        # 5. Save Results
        self.save_results(results)
        
        logger.info("Router Inference Runner completed successfully.")
        return results

def main():
    """Entry point for the modular router inference runner."""
    config = Config()
    runner = RouterInferenceRunner(config)
    
    try:
        results = runner.run()
        logger.info(f"Processed {len(results)} prompts.")
    except Exception as e:
        logger.error(f"Router Inference pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()