"""
Evaluation metrics for the Memory Palaces project.

This module implements exact-match recall calculation and other evaluation
metrics required for User Story 1.
"""

import json
import os
import csv
import math
import gc
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset

# Import from project modules
from models.loading import load_model
from models.base import GPT2Baseline
from models.spatial import soft_addressed_retrieve
from models.memory_slot import MemoryGrid
from models.episodic_chunk import EpisodicChunk

# Ensure single-core execution
os.environ["OMP_NUM_THREADS"] = "1"
torch.set_num_threads(1)

RESULTS_DIR = Path("artifacts/results")
CHECKPOINT_DIR = Path("artifacts/checkpoints")

def ensure_results_dir():
    """Ensure the results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def compute_exact_match_recall(predictions: List[str], references: List[str]) -> float:
    """
    Compute exact-match recall.
    
    Args:
        predictions: List of predicted answers
        references: List of ground truth answers
        
    Returns:
        Exact-match recall score (fraction of exact matches)
    """
    if not predictions or not references:
        return 0.0
    
    if len(predictions) != len(references):
        raise ValueError(f"Predictions and references must have same length: "
                       f"{len(predictions)} vs {len(references)}")
    
    exact_matches = sum(1 for pred, ref in zip(predictions, references) 
                      if pred.strip().lower() == ref.strip().lower())
    
    return exact_matches / len(references)

def evaluate_model_on_dataset(
    model: Any,
    tokenizer: AutoTokenizer,
    dataset: Any,
    variant: str,
    memory_grid: Optional[MemoryGrid] = None
) -> Tuple[List[str], List[str]]:
    """
    Evaluate model on a dataset and return predictions and references.
    
    Args:
        model: The model to evaluate (spatial or baseline)
        tokenizer: Tokenizer for the model
        dataset: HuggingFace dataset to evaluate on
        variant: One of 'spatial', 'baseline', 'control'
        memory_grid: Memory grid for spatial variant (optional)
        
    Returns:
        Tuple of (predictions, references)
    """
    predictions = []
    references = []
    
    device = next(model.parameters()).device
    
    # Process dataset samples
    for idx, sample in enumerate(dataset):
        # For bAbI Task 3, we use the story and question
        if 'story' in sample and 'question' in sample:
            context = sample['story']
            question = sample['question']
            expected = sample['answer']
        elif 'sentence1' in sample and 'sentence2' in sample:
            # Story Cloze format
            context = f"{sample['sentence1']} {sample['sentence2']}"
            question = sample['sentence3']  # The continuation
            expected = sample['sentence4']  # The correct ending
        else:
            continue
        
        # Prepare input
        input_text = f"Context: {context}\nQuestion: {question}"
        
        # For spatial variant, we might use memory retrieval
        if variant == 'spatial' and memory_grid is not None:
            # Create episodic chunk from context
            chunk = EpisodicChunk(
                content=context,
                timestamp=time.time(),
                chunk_id=f"chunk_{idx}"
            )
            
            # Assign coordinate (this would normally be done during training)
            # For evaluation, we assume coordinates are already assigned
            
            # Retrieve from memory
            retrieval_result = soft_addressed_retrieve(
                query=question,
                memory_grid=memory_grid,
                top_k=1
            )
            
            # Augment input with retrieved memory
            if retrieval_result and retrieval_result.chunks:
                retrieved_content = retrieval_result.chunks[0].content
                input_text = f"Context: {context}\nRetrieved: {retrieved_content}\nQuestion: {question}"
        
        # Tokenize and generate
        inputs = tokenizer(input_text, return_tensors="pt").to(device)
        
        # Generate with limited length
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=20,
                num_return_sequences=1,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode prediction
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract just the generated part (after the input)
        prediction = generated[len(input_text):].strip()
        
        predictions.append(prediction)
        references.append(expected)
        
        # Clean up to avoid memory buildup
        del inputs, outputs, generated
        gc.collect()
        
        # Progress indicator
        if (idx + 1) % 10 == 0:
            print(f"  Processed {idx + 1}/{len(dataset)} samples")
    
    return predictions, references

def run_evaluation_for_seed(
    seed: int,
    dataset_name: str,
    variant: str,
    checkpoint_path: Optional[str] = None
) -> float:
    """
    Run evaluation for a single seed.
    
    Args:
        seed: Random seed for reproducibility
        dataset_name: Name of dataset to evaluate on
        variant: Model variant ('spatial', 'baseline', 'control')
        checkpoint_path: Path to model checkpoint (optional)
        
    Returns:
        Exact-match recall score
    """
    # Set seed
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
    
    # Load dataset
    print(f"Loading dataset: {dataset_name}")
    if dataset_name == "babi_task3":
        dataset = load_dataset("babi", "task3_10k", split="test")
    elif dataset_name == "lambada":
        dataset = load_dataset("lambada", split="test")
    elif dataset_name == "story_cloze":
        dataset = load_dataset("story_cloze", "2016", split="test")
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    # Load model
    print(f"Loading model variant: {variant}")
    if checkpoint_path and Path(checkpoint_path).exists():
        model = load_model(checkpoint_path, variant)
    else:
        # Try to find checkpoint in default location
        default_checkpoint = CHECKPOINT_DIR / f"{variant}_seed_{seed}"
        if default_checkpoint.exists():
            model = load_model(str(default_checkpoint), variant)
        else:
            raise FileNotFoundError(f"No checkpoint found for {variant} seed {seed}")
    
    tokenizer = AutoTokenizer.from_pretrained("gpt2-medium")
    
    # Initialize memory grid for spatial variant
    memory_grid = None
    if variant == "spatial":
        memory_grid = MemoryGrid(grid_size=(8, 8))
    
    # Evaluate
    print(f"Evaluating on {dataset_name}...")
    predictions, references = evaluate_model_on_dataset(
        model, tokenizer, dataset, variant, memory_grid
    )
    
    # Compute recall
    recall = compute_exact_match_recall(predictions, references)
    print(f"  Seed {seed} recall: {recall:.4f}")
    
    # Cleanup
    del model, predictions, references
    gc.collect()
    
    return recall

def aggregate_results_by_seed(
    results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate results by seed and compute statistics.
    
    Args:
        results: List of result dictionaries with 'seed' and 'accuracy'
        
    Returns:
        Aggregated results with mean and std
    """
    if not results:
        return {
            "seeds": [],
            "accuracies": [],
            "mean": 0.0,
            "std": 0.0
        }
    
    seeds = [r["seed"] for r in results]
    accuracies = [r["accuracy"] for r in results]
    
    mean_acc = sum(accuracies) / len(accuracies)
    
    if len(accuracies) > 1:
        variance = sum((x - mean_acc) ** 2 for x in accuracies) / len(accuracies)
        std_acc = math.sqrt(variance)
    else:
        std_acc = 0.0
    
    return {
        "seeds": seeds,
        "accuracies": accuracies,
        "mean": mean_acc,
        "std": std_acc
    }

def log_slot_occupancy_distribution(
    memory_grid: MemoryGrid,
    epoch: int,
    output_dir: Optional[Path] = None
):
    """Log slot occupancy distribution per epoch."""
    if output_dir is None:
        output_dir = Path("artifacts/metrics")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    occupancy = [slot.count for slot in memory_grid.slots]
    output_file = output_dir / f"slot_occupancy_epoch_{epoch}.json"
    
    with open(output_file, 'w') as f:
        json.dump(occupancy, f)

def log_coordinate_variance(
    memory_grid: MemoryGrid,
    epoch: int,
    output_dir: Optional[Path] = None
):
    """Log coordinate variance per epoch."""
    if output_dir is None:
        output_dir = Path("artifacts/metrics")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    x_coords = [slot.x for slot in memory_grid.slots if slot.count > 0]
    y_coords = [slot.y for slot in memory_grid.slots if slot.count > 0]
    
    if x_coords:
        x_mean = sum(x_coords) / len(x_coords)
        y_mean = sum(y_coords) / len(y_coords)
        x_var = sum((x - x_mean) ** 2 for x in x_coords) / len(x_coords)
        y_var = sum((y - y_mean) ** 2 for y in y_coords) / len(y_coords)
    else:
        x_var = 0.0
        y_var = 0.0
    
    output_file = output_dir / f"coordinate_variance_epoch_{epoch}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            "x_variance": x_var,
            "y_variance": y_var,
            "epoch": epoch
        }, f)

def compute_interference_distance(
    memory_grid: MemoryGrid,
    similar_pairs: List[Tuple[EpisodicChunk, EpisodicChunk]]
) -> float:
    """
    Compute interference distance metric.
    
    Args:
        memory_grid: The memory grid
        similar_pairs: Pairs of semantically similar chunks
        
    Returns:
        Average Manhattan distance between similar items
    """
    if not similar_pairs:
        return 0.0
    
    total_distance = 0
    count = 0
    
    for chunk1, chunk2 in similar_pairs:
        # Find slots for these chunks
        slot1 = None
        slot2 = None
        
        for slot in memory_grid.slots:
            if slot.chunk and slot.chunk.chunk_id == chunk1.chunk_id:
                slot1 = slot
            if slot.chunk and slot.chunk.chunk_id == chunk2.chunk_id:
                slot2 = slot
        
        if slot1 and slot2:
            manhattan_dist = abs(slot1.x - slot2.x) + abs(slot1.y - slot2.y)
            total_distance += manhattan_dist
            count += 1
    
    return total_distance / count if count > 0 else 0.0

def main():
    """
    Main evaluation script for T015.
    
    This script evaluates trained models across multiple seeds and
    computes exact-match recall, storing results in artifacts/results/recall_accuracy.json.
    """
    ensure_results_dir()
    
    # Configuration
    seeds = list(range(5))  # Range of seeds as required
    datasets = ["babi_task3"]  # Primary dataset for US1
    variants = ["spatial", "baseline", "control"]
    
    all_results = []
    
    for variant in variants:
        for dataset in datasets:
            for seed in seeds:
                print(f"\n=== Evaluating {variant} on {dataset} with seed {seed} ===")
                
                try:
                    accuracy = run_evaluation_for_seed(
                        seed=seed,
                        dataset_name=dataset,
                        variant=variant
                    )
                    
                    all_results.append({
                        "seed": seed,
                        "variant": variant,
                        "dataset": dataset,
                        "accuracy": accuracy
                    })
                    
                except Exception as e:
                    print(f"Error evaluating seed {seed}: {e}")
                    # Continue with other seeds
                    continue
    
    # Aggregate results by variant and dataset
    output_data = {}
    
    for variant in variants:
        for dataset in datasets:
            variant_results = [
                r for r in all_results 
                if r["variant"] == variant and r["dataset"] == dataset
            ]
            
            if variant_results:
                aggregated = aggregate_results_by_seed(variant_results)
                output_data[f"{variant}_{dataset}"] = aggregated
    
    # Write results
    output_file = RESULTS_DIR / "recall_accuracy.json"
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nResults written to {output_file}")
    print(f"Total evaluations: {len(all_results)}")
    
    # Also write per-seed breakdown
    seeds_by_variant = {}
    for variant in variants:
        for dataset in datasets:
            key = f"{variant}_{dataset}"
            if key in output_data:
                seeds_by_variant[key] = {
                    "seeds": output_data[key]["seeds"],
                    "accuracies": output_data[key]["accuracies"],
                    "mean": output_data[key]["mean"],
                    "std": output_data[key]["std"]
                }
    
    # Save individual variant results for statistical analysis
    for key, data in seeds_by_variant.items():
        variant_file = RESULTS_DIR / f"recall_{key}.json"
        with open(variant_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    return output_data

if __name__ == "__main__":
    main()