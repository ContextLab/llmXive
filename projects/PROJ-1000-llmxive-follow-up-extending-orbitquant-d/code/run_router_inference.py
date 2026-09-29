"""
Orchestration script for Phase 2 Inference (User Story 2).
Implements the dynamic rotation router workflow:
1. Load Test Split Prompts
2. Compute Entropy Scores
3. Load Pre-optimized Rotation Matrices (from T028)
4. Select Matrix based on Entropy
5. Generate Images with Dynamic Rotation
6. Log Metrics
"""

import os
import sys
import json
import logging
import csv
import time
import torch
import numpy as np
from pathlib import Path

# Local imports matching the API surface
from config import Config
from analysis.entropy_proxy import EntropyProxy
from analysis.load_matrices import load_matrices_from_path, verify_matrices
from analysis.router import EntropyRouter
from models.flux_wan_loader import ModelLoader
from models.dit_wrapper import DiTWrapper, ActivationCapture
from quantization.w2a4_engine import W2A4Engine
from evaluation.metrics import compute_clip_score, compute_mse
from evaluation.timing import compute_statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RouterInferencePipeline:
    def __init__(self, config: Config):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Initialize components
        self.entropy_proxy = EntropyProxy(config)
        self.matrix_loader = None
        self.router = None
        self.dit_wrapper = None
        self.quantization_engine = None
        self.model_loader = None

    def load_test_split_prompts(self, path: str) -> list:
        """Load test split prompts from CSV."""
        logger.info(f"Loading test split prompts from {path}")
        prompts = []
        if not os.path.exists(path):
            raise FileNotFoundError(f"Test split file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                prompts.append({
                    'id': row.get('id', str(len(prompts))),
                    'prompt': row.get('prompt', row.get('caption', '')),
                    'source': row.get('source', 'unknown')
                })
        logger.info(f"Loaded {len(prompts)} prompts from test split")
        return prompts

    def compute_entropy_scores(self, prompts: list) -> dict:
        """Compute semantic entropy for each prompt."""
        logger.info("Computing entropy scores for prompts...")
        entropy_scores = {}
        for i, p in enumerate(prompts):
            if i % 10 == 0:
                logger.info(f"Processing prompt {i}/{len(prompts)}")
            entropy = self.entropy_proxy.compute_entropy(p['prompt'])
            entropy_scores[p['id']] = entropy
        logger.info(f"Computed entropy for {len(entropy_scores)} prompts")
        return entropy_scores

    def select_rotation_matrices(self, entropy_scores: dict) -> dict:
        """Select rotation matrices based on entropy scores."""
        logger.info("Selecting rotation matrices via router...")
        if self.router is None:
            raise RuntimeError("Router not initialized. Call load_matrices first.")
        
        matrix_selections = {}
        for pid, entropy in entropy_scores.items():
            matrix_idx = self.router.route(entropy)
            matrix_selections[pid] = {
                'entropy': entropy,
                'matrix_index': matrix_idx
            }
        logger.info(f"Selected matrices for {len(matrix_selections)} prompts")
        return matrix_selections

    def run_dit_generation_with_dynamic_rotation(self, prompts: list, matrix_selections: dict) -> list:
        """Run DiT generation with dynamic rotation matrix selection."""
        logger.info("Starting DiT generation with dynamic rotation...")
        if self.dit_wrapper is None or self.quantization_engine is None:
            raise RuntimeError("DiT wrapper or quantization engine not initialized.")
        
        results = []
        
        # Setup activation capture for variance logging if needed
        capture = ActivationCapture()
        self.dit_wrapper.register_capture(capture)
        
        for i, p in enumerate(prompts):
            pid = p['id']
            prompt_text = p['prompt']
            
            if i % 5 == 0:
                logger.info(f"Generating image {i}/{len(prompts)} for prompt: {prompt_text[:50]}...")
            
            # Get selected matrix
            selection = matrix_selections.get(pid)
            if not selection:
                logger.warning(f"No matrix selection for {pid}, skipping")
                continue
            
            matrix_idx = selection['matrix_index']
            
            # Start timing
            start_time = time.time()
            
            try:
                # Generate image with specific rotation matrix
                # The W2A4Engine will use the selected matrix for this generation
                self.quantization_engine.set_active_matrix(matrix_idx)
                
                # Run generation (simplified - actual generation logic depends on model loader)
                # This assumes the DiT wrapper handles the generation loop
                generated_image, latent_stats = self.dit_wrapper.generate(
                    prompt=prompt_text,
                    guidance_scale=self.config.guidance_scale,
                    num_inference_steps=self.config.num_inference_steps,
                    device=self.device
                )
                
                end_time = time.time()
                inference_time = end_time - start_time
                
                # Compute metrics
                # Note: We need a reference image for MSE. 
                # In a real scenario, we might compare against a baseline or use FID/CLIP.
                # For this script, we log the generation stats and timing.
                
                result = {
                    'id': pid,
                    'prompt': prompt_text,
                    'matrix_index': matrix_idx,
                    'entropy': matrix_selections[pid]['entropy'],
                    'inference_time_sec': inference_time,
                    'status': 'success',
                    'latent_stats': latent_stats if latent_stats else {}
                }
                
                # If we have a reference image (from T005/T006), compute MSE
                # Placeholder for now - assumes reference path exists
                ref_path = self.config.data_paths.get('reference_images')
                if ref_path and os.path.exists(ref_path):
                    # Compute MSE would go here
                    pass

            except Exception as e:
                logger.error(f"Generation failed for {pid}: {e}")
                result = {
                    'id': pid,
                    'prompt': prompt_text,
                    'matrix_index': matrix_idx,
                    'status': 'failed',
                    'error': str(e)
                }
            
            results.append(result)
            
            # Clear memory if needed
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
        logger.info(f"Completed generation for {len(results)} prompts")
        return results

    def aggregate_results(self, results: list) -> dict:
        """Aggregate results into a summary report."""
        logger.info("Aggregating results...")
        
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']
        
        avg_time = np.mean([r['inference_time_sec'] for r in successful]) if successful else 0
        
        # Group by matrix index
        matrix_usage = {}
        for r in successful:
            idx = r['matrix_index']
            if idx not in matrix_usage:
                matrix_usage[idx] = {'count': 0, 'total_time': 0}
            matrix_usage[idx]['count'] += 1
            matrix_usage[idx]['total_time'] += r['inference_time_sec']
        
        # Compute average time per matrix
        for idx in matrix_usage:
            matrix_usage[idx]['avg_time'] = matrix_usage[idx]['total_time'] / matrix_usage[idx]['count']
        
        summary = {
            'total_prompts': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'average_inference_time_sec': avg_time,
            'matrix_usage_distribution': matrix_usage,
            'detailed_results': results
        }
        
        logger.info(f"Aggregation complete: {len(successful)} success, {len(failed)} failed")
        return summary

    def save_results(self, summary: dict, output_path: str):
        """Save results to JSON."""
        logger.info(f"Saving results to {output_path}")
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)
        logger.info("Results saved successfully")

    def initialize_components(self):
        """Initialize all required components."""
        logger.info("Initializing pipeline components...")
        
        # Load Matrices (T028 dependency)
        matrices_path = self.config.data_paths.get('clustering_report')
        if not matrices_path:
            raise FileNotFoundError("Clustering report path not found in config")
        
        self.matrix_loader = load_matrices_from_path(matrices_path)
        self.router = EntropyRouter(self.matrix_loader, self.config)
        
        # Load Model
        self.model_loader = ModelLoader(self.config)
        self.dit_wrapper = self.model_loader.get_model()
        
        # Initialize Quantization Engine
        self.quantization_engine = W2A4Engine(self.config, self.matrix_loader)
        
        logger.info("All components initialized successfully")

def main():
    """Main entry point for Router Inference Pipeline."""
    logger.info("Starting Router Inference Pipeline (T029)...")
    
    config = Config()
    pipeline = RouterInferencePipeline(config)
    
    try:
        # 1. Initialize
        pipeline.initialize_components()
        
        # 2. Load Test Split
        test_path = config.data_paths.get('test_prompts')
        if not test_path:
            # Fallback to default location
            test_path = str(Path(config.data_root) / "processed" / "prompts_test.csv")
        
        prompts = pipeline.load_test_split_prompts(test_path)
        
        if not prompts:
            logger.error("No prompts loaded. Exiting.")
            return
        
        # 3. Compute Entropy
        entropy_scores = pipeline.compute_entropy_scores(prompts)
        
        # 4. Select Matrices
        matrix_selections = pipeline.select_rotation_matrices(entropy_scores)
        
        # 5. Generate Images
        results = pipeline.run_dit_generation_with_dynamic_rotation(prompts, matrix_selections)
        
        # 6. Aggregate
        summary = pipeline.aggregate_results(results)
        
        # 7. Save
        output_path = str(Path(config.data_root) / "processed" / "router_inference_results.json")
        pipeline.save_results(summary, output_path)
        
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()