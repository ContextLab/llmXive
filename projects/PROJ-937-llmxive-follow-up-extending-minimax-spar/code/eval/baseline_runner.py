"""
Baseline Runner for Dense Attention (Full Context) evaluation.

This module implements the ground truth baseline execution for the llmXive
sparse attention study. It runs the MiniMax model with full context (no sparsity,
no Index Branch) to generate baseline metrics (Exact Match, F1, Perplexity)
against which heuristic-based sparse attention methods will be compared.

Satisfies FR-004: Baseline generation for ground truth comparison.
"""

import os
import sys
import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import torch
import numpy as np
from tqdm import tqdm

# Project imports based on API surface
from utils.config import Config, enforce_cpu, set_random_seed, get_default_config
from utils.logger import setup_logger, get_structured_logger, log_resource_usage
from models.mini_max_wrapper import MiniMaxConfig, MiniMaxWrapper, create_minimax_wrapper
from data.loader import download_and_verify_ruler
from data.preprocess import stream_dataset_chunks, PreprocessConfig
from eval.metrics import calculate_exact_match, calculate_f1, calculate_perplexity, evaluate_predictions

# Constants
BASELINE_OUTPUT_DIR = Path("results")
BASELINE_RESULTS_FILE = BASELINE_OUTPUT_DIR / "dense_baseline_metrics.json"
DEFAULT_MAX_SAMPLES = 50  # Limit for baseline run to respect time/memory constraints
DEFAULT_BATCH_SIZE = 1

logger = setup_logger("baseline_runner")

class DenseAttentionRunner:
    """
    Executes the model in Dense Attention mode (Full Context).
    No sparsity heuristics are applied. No Index Branch is used.
    """

    def __init__(self, config: Config, model_wrapper: MiniMaxWrapper):
        self.config = config
        self.model = model_wrapper
        self.device = self.config.device
        self.logger = get_structured_logger("baseline_runner")
        
        # Ensure output directory exists
        BASELINE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def run_inference(self, dataset_iterator: List[Dict[str, Any]], max_samples: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Run full inference on the provided dataset samples.
        
        Args:
            dataset_iterator: List of dataset samples (dicts with 'input', 'expected_output', etc.)
            max_samples: Maximum number of samples to process (for testing/resource limits)
            
        Returns:
            List of result dictionaries containing predictions and metrics.
        """
        results = []
        samples_to_process = dataset_iterator[:max_samples] if max_samples else dataset_iterator
        
        self.logger.info(f"Starting dense baseline inference on {len(samples_to_process)} samples")
        
        with torch.no_grad():
            for idx, sample in enumerate(tqdm(samples_to_process, desc="Dense Baseline Inference")):
                try:
                    # Prepare input
                    input_text = sample.get("input", "")
                    expected_output = sample.get("expected_output", "")
                    task_id = sample.get("task_id", f"sample_{idx}")
                    
                    # Run full context inference (Dense Attention)
                    # The model wrapper handles the full context window without sparsity
                    start_time = time.time()
                    
                    # Ensure model is in eval mode
                    self.model.model.eval()
                    
                    # Tokenize and prepare inputs
                    input_ids = self.model.tokenizer.encode(
                        input_text, 
                        return_tensors="pt", 
                        truncation=True, 
                        max_length=self.model.config.max_context_length
                    ).to(self.device)
                    
                    # Generate response (full context, no sparse masking)
                    output = self.model.model.generate(
                        input_ids,
                        max_new_tokens=self.model.config.max_new_tokens,
                        do_sample=False,  # Deterministic for baseline
                        temperature=1.0,
                        top_p=1.0,
                        pad_token_id=self.model.tokenizer.eos_token_id
                    )
                    
                    generation_time = time.time() - start_time
                    
                    # Decode output
                    generated_text = self.model.tokenizer.decode(
                        output[0, input_ids.shape[1]:], 
                        skip_special_tokens=True
                    )
                    
                    # Calculate metrics
                    em_score = calculate_exact_match(expected_output, generated_text)
                    f1_score = calculate_f1(expected_output, generated_text)
                    
                    # Calculate perplexity on the generated text (conditional on input)
                    # For perplexity, we evaluate the model's probability of the target sequence
                    try:
                        # Concatenate input and target for perplexity calculation
                        full_text = input_text + expected_output
                        full_ids = self.model.tokenizer.encode(
                            full_text,
                            return_tensors="pt",
                            truncation=True,
                            max_length=self.model.config.max_context_length
                        ).to(self.device)
                        
                        # Split into input and target parts
                        target_ids = full_ids[:, input_ids.shape[1]:]
                        if target_ids.shape[1] == 0:
                            # Fallback if target is empty or truncated
                            ppl = 1.0
                        else:
                            # Calculate loss on target tokens
                            outputs = self.model.model(
                                input_ids=full_ids,
                                labels=target_ids
                            )
                            loss = outputs.loss
                            ppl = torch.exp(loss).item()
                    except Exception as ppl_error:
                        self.logger.warning(f"Perplexity calculation failed for sample {task_id}: {ppl_error}")
                        ppl = float('inf')
                    
                    result = {
                        "task_id": task_id,
                        "input_length": len(input_ids[0]),
                        "generation_length": len(output[0]) - len(input_ids[0]),
                        "prediction": generated_text.strip(),
                        "expected": expected_output.strip(),
                        "exact_match": em_score,
                        "f1_score": f1_score,
                        "perplexity": ppl,
                        "generation_time_sec": generation_time,
                        "mode": "dense_baseline"
                    }
                    
                    results.append(result)
                    
                    # Log resource usage periodically
                    if (idx + 1) % 10 == 0:
                        log_resource_usage(self.logger)
                        
                except Exception as e:
                    self.logger.error(f"Error processing sample {idx} ({task_id}): {e}")
                    results.append({
                        "task_id": task_id,
                        "error": str(e),
                        "mode": "dense_baseline"
                    })
                    
        return results

    def aggregate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate metrics from all results.
        
        Returns:
            Dictionary with aggregated metrics (mean, std, etc.)
        """
        valid_results = [r for r in results if "error" not in r]
        
        if not valid_results:
            return {
                "total_samples": len(results),
                "successful_samples": 0,
                "failed_samples": len(results),
                "avg_exact_match": 0.0,
                "avg_f1_score": 0.0,
                "avg_perplexity": 0.0,
                "avg_generation_time": 0.0
            }
        
        em_scores = [r["exact_match"] for r in valid_results]
        f1_scores = [r["f1_score"] for r in valid_results]
        ppl_scores = [r["perplexity"] for r in valid_results if r["perplexity"] != float('inf')]
        times = [r["generation_time_sec"] for r in valid_results]
        
        aggregated = {
            "total_samples": len(results),
            "successful_samples": len(valid_results),
            "failed_samples": len(results) - len(valid_results),
            "avg_exact_match": float(np.mean(em_scores)),
            "std_exact_match": float(np.std(em_scores)),
            "avg_f1_score": float(np.mean(f1_scores)),
            "std_f1_score": float(np.std(f1_scores)),
            "avg_perplexity": float(np.mean(ppl_scores)) if ppl_scores else float('inf'),
            "std_perplexity": float(np.std(ppl_scores)) if ppl_scores else 0.0,
            "avg_generation_time_sec": float(np.mean(times)),
            "mode": "dense_baseline"
        }
        
        return aggregated

    def save_results(self, results: List[Dict[str, Any]], aggregated: Dict[str, Any]):
        """
        Save detailed results and aggregated metrics to disk.
        """
        output_data = {
            "metadata": {
                "model": self.model.config.model_name,
                "device": self.device,
                "mode": "dense_attention_full_context",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "config": self.config.to_dict()
            },
            "aggregated_metrics": aggregated,
            "detailed_results": results
        }
        
        with open(BASELINE_RESULTS_FILE, "w") as f:
            json.dump(output_data, f, indent=2)
        
        self.logger.info(f"Baseline results saved to {BASELINE_RESULTS_FILE}")

def run_baseline_experiment(
    dataset_name: str = "ruler",
    subset_size: int = DEFAULT_MAX_SAMPLES,
    seed: int = 42,
    max_context_length: int = 4096
) -> Dict[str, Any]:
    """
    Main entry point for running the dense attention baseline experiment.
    
    This function:
    1. Sets up the environment (CPU, seed)
    2. Loads the RULER dataset
    3. Initializes the MiniMax model in dense mode
    4. Runs inference on the dataset
    5. Calculates and saves metrics
    
    Args:
        dataset_name: Name of the dataset to use (default: ruler)
        subset_size: Number of samples to process
        seed: Random seed for reproducibility
        max_context_length: Maximum context length for the model
        
    Returns:
        Dictionary containing aggregated baseline metrics
    """
    # Setup
    enforce_cpu()
    set_random_seed(seed)
    config = get_default_config()
    config.max_context_length = max_context_length
    
    logger.info("Starting Dense Attention Baseline Experiment")
    logger.info(f"Configuration: {config.to_dict()}")
    
    # Download and verify dataset
    logger.info("Downloading and verifying RULER dataset...")
    try:
        data_path = download_and_verify_ruler()
        logger.info(f"Dataset verified at {data_path}")
    except Exception as e:
        logger.error(f"Failed to download/verify dataset: {e}")
        raise
    
    # Load dataset samples
    logger.info("Loading dataset samples...")
    from data.ruler_loader import load_ruler_dataset
    try:
        dataset = load_ruler_dataset(data_path, limit=subset_size)
        logger.info(f"Loaded {len(dataset)} samples")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise
    
    # Initialize model
    logger.info("Initializing MiniMax model in dense mode...")
    model_config = MiniMaxConfig(
        model_name="MiniMax-M3",  # Or appropriate model identifier
        device="cpu",
        max_context_length=max_context_length,
        max_new_tokens=128,
        use_sparse_attention=False,  # Explicitly disable sparsity
        use_index_branch=False       # Explicitly disable Index Branch
    )
    
    try:
        model = create_minimax_wrapper(model_config)
        logger.info("Model initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize model: {e}")
        raise
    
    # Create runner
    runner = DenseAttentionRunner(config, model)
    
    # Run inference
    logger.info("Running dense attention inference...")
    results = runner.run_inference(dataset, max_samples=subset_size)
    
    # Aggregate metrics
    logger.info("Aggregating metrics...")
    aggregated = runner.aggregate_metrics(results)
    
    # Save results
    runner.save_results(results, aggregated)
    
    logger.info("Baseline experiment completed successfully")
    return aggregated

def main():
    """
    CLI entry point for the baseline runner.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Dense Attention Baseline for llmXive")
    parser.add_argument("--dataset", type=str, default="ruler", help="Dataset name")
    parser.add_argument("--samples", type=int, default=DEFAULT_MAX_SAMPLES, help="Number of samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--context-length", type=int, default=4096, help="Max context length")
    
    args = parser.parse_args()
    
    try:
        metrics = run_baseline_experiment(
            dataset_name=args.dataset,
            subset_size=args.samples,
            seed=args.seed,
            max_context_length=args.context_length
        )
        
        print("\n=== Dense Attention Baseline Results ===")
        print(f"Total Samples: {metrics['total_samples']}")
        print(f"Successful: {metrics['successful_samples']}")
        print(f"Failed: {metrics['failed_samples']}")
        print(f"Avg Exact Match: {metrics['avg_exact_match']:.4f}")
        print(f"Avg F1 Score: {metrics['avg_f1_score']:.4f}")
        print(f"Avg Perplexity: {metrics['avg_perplexity']:.4f}")
        print(f"Avg Generation Time: {metrics['avg_generation_time_sec']:.2f}s")
        print(f"Results saved to: {BASELINE_RESULTS_FILE}")
        
    except Exception as e:
        logger.error(f"Baseline experiment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()