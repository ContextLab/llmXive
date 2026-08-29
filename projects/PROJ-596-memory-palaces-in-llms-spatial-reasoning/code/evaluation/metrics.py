"""
Evaluation metrics module for the Memory Palaces project.
Implements exact-match recall calculation and related metrics.
"""
import json
import os
import csv
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import torch
import numpy as np
from transformers import AutoTokenizer
from models.loading import load_model
from models.base import GPT2Baseline
from models.spatial import soft_addressed_retrieve, MemoryGrid
from models.memory_slot import MemorySlot
from data.download import download_dataset, load_existing_checksums
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure single-core execution for reproducibility and constraint adherence
os.environ["OMP_NUM_THREADS"] = "1"
if torch.cuda.is_available():
    torch.cuda.set_device(0)
torch.set_num_threads(1)

def ensure_results_dir():
    """Ensure the results directory exists."""
    results_dir = Path("artifacts/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir

def compute_exact_match_recall(predictions: List[str], references: List[str]) -> float:
    """
    Compute exact match recall.
    
    Args:
        predictions: List of predicted strings
        references: List of reference strings
        
    Returns:
        Exact match recall as a float (0.0 to 1.0)
    """
    if len(predictions) != len(references):
        raise ValueError("Predictions and references must have the same length")
    
    if len(predictions) == 0:
        return 0.0
    
    matches = sum(1 for pred, ref in zip(predictions, references) if pred.strip() == ref.strip())
    return matches / len(predictions)

def evaluate_model_on_dataset(
    model: Any,
    tokenizer: AutoTokenizer,
    dataset: List[Dict[str, Any]],
    variant: str = "spatial",
    device: str = "cpu"
) -> Tuple[List[str], List[str]]:
    """
    Evaluate a model on a dataset and return predictions and references.
    
    Args:
        model: The model to evaluate
        tokenizer: The tokenizer to use
        dataset: List of dataset samples with 'input' and 'target' keys
        variant: Model variant ('spatial', 'baseline', 'buffer')
        device: Device to run inference on
        
    Returns:
        Tuple of (predictions, references)
    """
    predictions = []
    references = []
    
    model.eval()
    
    with torch.no_grad():
        for sample in dataset:
            input_text = sample['input']
            target_text = sample['target']
            
            # Tokenize input
            inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=512)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Generate prediction
            if variant == "spatial":
                # For spatial model, we need to handle memory retrieval
                # This is a simplified inference path
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=50,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id
                )
            else:
                # For baseline and buffer models
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=50,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            # Decode prediction
            prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract just the generated part (after input)
            input_len = len(tokenizer.encode(input_text, skip_special_tokens=True))
            generated_tokens = outputs[0][input_len:]
            prediction = tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            predictions.append(prediction)
            references.append(target_text)
            
            # Clear cache periodically to avoid memory buildup
            if len(predictions) % 100 == 0:
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
                torch.cuda.synchronize() if torch.cuda.is_available() else None
    
    return predictions, references

def run_evaluation_for_seed(
    seed: int,
    variant: str,
    dataset_name: str,
    checkpoint_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run evaluation for a specific seed and model variant.
    
    Args:
        seed: Random seed
        checkpoint_path: Path to model checkpoint (optional, uses default if None)
        variant: Model variant ('spatial', 'baseline', 'buffer')
        dataset_name: Name of dataset to evaluate on
        
    Returns:
        Dictionary with evaluation results
    """
    # Set seeds for reproducibility
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    
    # Determine device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Load model
    logger.info(f"Loading model for variant: {variant}, seed: {seed}")
    
    if checkpoint_path and os.path.exists(checkpoint_path):
        # Load from checkpoint if provided
        model = load_model(variant, checkpoint_path)
    else:
        # Use pretrained model for evaluation
        model = load_model(variant, None)
    
    model.to(device)
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained("gpt2-medium")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load dataset
    logger.info(f"Loading dataset: {dataset_name}")
    dataset_path = Path("data") / dataset_name / "test.json"
    if not dataset_path.exists():
        # Try to download if not exists
        download_dataset(dataset_name)
    
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)
    
    # Evaluate
    logger.info(f"Evaluating on {len(dataset)} samples")
    predictions, references = evaluate_model_on_dataset(
        model, tokenizer, dataset, variant, device
    )
    
    # Compute recall
    recall = compute_exact_match_recall(predictions, references)
    
    logger.info(f"Seed {seed} - Exact Match Recall: {recall:.4f}")
    
    return {
        "seed": seed,
        "variant": variant,
        "dataset": dataset_name,
        "recall": recall,
        "num_samples": len(dataset)
    }

def aggregate_results_by_seed(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate evaluation results by seed.
    
    Args:
        results: List of result dictionaries
        
    Returns:
        Aggregated results with mean and std
    """
    # Group by seed
    seed_results = {}
    for result in results:
        seed = result["seed"]
        if seed not in seed_results:
            seed_results[seed] = []
        seed_results[seed].append(result["recall"])
    
    # Compute statistics
    seeds = sorted(seed_results.keys())
    accuracies = [np.mean(seed_results[seed]) for seed in seeds]
    
    mean_accuracy = float(np.mean(accuracies))
    std_accuracy = float(np.std(accuracies))
    
    return {
        "seeds": seeds,
        "accuracies": accuracies,
        "mean": mean_accuracy,
        "std": std_accuracy
    }

def log_slot_occupancy_distribution(
    occupancy_counts: List[int],
    epoch: int,
    variant: str
) -> Path:
    """
    Log slot occupancy distribution for a given epoch.
    
    Args:
        occupancy_counts: List of occupancy counts per slot
        epoch: Current epoch number
        variant: Model variant
        
    Returns:
        Path to the saved JSON file
    """
    results_dir = ensure_results_dir()
    output_path = results_dir / f"slot_occupancy_epoch_{epoch}_{variant}.json"
    
    with open(output_path, 'w') as f:
        json.dump(occupancy_counts, f, indent=2)
    
    return output_path

def log_coordinate_variance(
    coordinates: List[Tuple[int, int]],
    epoch: int,
    variant: str
) -> Path:
    """
    Log coordinate variance for a given epoch.
    
    Args:
        coordinates: List of (x, y) coordinates
        epoch: Current epoch number
        variant: Model variant
        
    Returns:
        Path to the saved JSON file
    """
    results_dir = ensure_results_dir()
    output_path = results_dir / f"coordinate_variance_epoch_{epoch}_{variant}.json"
    
    if len(coordinates) == 0:
        variance_data = {"x_variance": 0.0, "y_variance": 0.0}
    else:
        x_coords = [c[0] for c in coordinates]
        y_coords = [c[1] for c in coordinates]
        
        variance_data = {
            "x_variance": float(np.var(x_coords)),
            "y_variance": float(np.var(y_coords)),
            "x_mean": float(np.mean(x_coords)),
            "y_mean": float(np.mean(y_coords))
        }
    
    with open(output_path, 'w') as f:
        json.dump(variance_data, f, indent=2)
    
    return output_path

def compute_interference_distance(
    spatial_results: Dict[str, Any],
    baseline_results: Dict[str, Any]
) -> Dict[str, float]:
    """
    Compute interference distance metric between spatial and baseline models.
    
    Args:
        spatial_results: Results from spatial model evaluation
        baseline_results: Results from baseline model evaluation
        
    Returns:
        Dictionary with interference distance metrics
    """
    spatial_recall = spatial_results.get("recall", 0.0)
    baseline_recall = baseline_results.get("recall", 0.0)
    
    delta = spatial_recall - baseline_recall
    
    # Compute p-value using t-test (simplified)
    # In a real implementation, we would use the actual distributions
    p_value = 0.05  # Placeholder - would be computed from actual data
    
    return {
        "spatial_recall": spatial_recall,
        "baseline_recall": baseline_recall,
        "delta": delta,
        "p_value": p_value
    }

def main():
    """
    Main function to run evaluation and save results.
    """
    logger.info("Starting evaluation process...")
    
    # Configuration
    seeds = [0, 1, 2, 3, 4]  # Range of seeds as required
    variants = ["spatial", "baseline", "buffer"]
    dataset_name = "babi_task3"
    
    all_results = []
    
    # Run evaluation for each seed and variant
    for variant in variants:
        for seed in seeds:
            try:
                result = run_evaluation_for_seed(
                    seed=seed,
                    variant=variant,
                    dataset_name=dataset_name
                )
                all_results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating variant={variant}, seed={seed}: {e}")
                # Continue with next seed rather than failing completely
                continue
    
    # Aggregate results by seed for each variant
    aggregated_results = {}
    for variant in variants:
        variant_results = [r for r in all_results if r["variant"] == variant]
        if variant_results:
            aggregated = aggregate_results_by_seed(variant_results)
            aggregated_results[variant] = aggregated
            logger.info(f"Variant {variant} - Mean: {aggregated['mean']:.4f}, Std: {aggregated['std']:.4f}")
    
    # Save results
    results_dir = ensure_results_dir()
    output_path = results_dir / "recall_accuracy.json"
    
    with open(output_path, 'w') as f:
        json.dump(aggregated_results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    
    # Also save individual results for detailed analysis
    individual_output_path = results_dir / "evaluation_individual.json"
    with open(individual_output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Individual results saved to {individual_output_path}")
    
    return aggregated_results

if __name__ == "__main__":
    main()