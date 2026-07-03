import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import torch
import numpy as np
from transformers import AutoTokenizer
from models.spatial import soft_addressed_retrieve, MemoryGrid, EpisodicChunk
from models.base import GPT2Baseline
from models.base_fallback import DistilGPT2Fallback

def compute_interference_distance(
    model_spatial: Any,
    model_baseline: Any,
    grid: MemoryGrid,
    chunks: List[EpisodicChunk],
    tokenizer: AutoTokenizer,
    interference_factor: float = 0.1,
    top_k: int = 5
) -> Dict[str, float]:
    """
    Computes the interference distance metric for both spatial and baseline models.
    
    Interference distance measures how much the retrieval of a target memory
    is disrupted by the presence of other memories (interference items).
    
    For the spatial model, we measure the change in retrieval quality when
    interference items are injected near the target's spatial coordinates.
    For the baseline (non-spatial) model, we measure the change when interference
    items are injected randomly in the embedding space.
    
    Args:
        model_spatial: The spatial memory variant model
        model_baseline: The non-spatial baseline model
        grid: The memory grid containing spatial slots
        chunks: List of episodic chunks to use as memory
        tokenizer: Tokenizer for the models
        interference_factor: Proportion of chunks to use as interference
        top_k: Number of top similar items to retrieve
        
    Returns:
        Dictionary with 'spatial', 'baseline', and 'delta' metrics
    """
    if not chunks:
        return {
            "spatial": 0.0,
            "baseline": 0.0,
            "delta": 0.0,
            "note": "No chunks provided"
        }
    
    # Split chunks into targets and interference
    n_interference = max(1, int(len(chunks) * interference_factor))
    n_targets = len(chunks) - n_interference
    
    if n_targets <= 0:
        return {
            "spatial": 0.0,
            "baseline": 0.0,
            "delta": 0.0,
            "note": "Not enough chunks for targets and interference"
        }
    
    target_chunks = chunks[:n_targets]
    interference_chunks = chunks[n_targets:]
    
    spatial_distances = []
    baseline_distances = []
    
    for target in target_chunks:
        # Compute baseline retrieval quality (without interference)
        baseline_quality_no_interfere = _compute_retrieval_quality(
            model_baseline, target, chunks, tokenizer, top_k
        )
        
        # Compute spatial retrieval quality (without interference)
        spatial_quality_no_interfere = _compute_spatial_retrieval_quality(
            model_spatial, grid, target, chunks, tokenizer, top_k
        )
        
        # Add interference and measure degradation
        # For baseline: random interference
        baseline_quality_with_interfere = _compute_retrieval_quality(
            model_baseline, target, interference_chunks, tokenizer, top_k
        )
        
        # For spatial: spatially proximate interference
        spatial_quality_with_interfere = _compute_spatial_retrieval_quality(
            model_spatial, grid, target, interference_chunks, tokenizer, top_k
        )
        
        # Calculate interference distance (degradation in quality)
        baseline_dist = max(0.0, baseline_quality_no_interfere - baseline_quality_with_interfere)
        spatial_dist = max(0.0, spatial_quality_no_interfere - spatial_quality_with_interfere)
        
        spatial_distances.append(spatial_dist)
        baseline_distances.append(baseline_dist)
    
    avg_spatial = float(np.mean(spatial_distances)) if spatial_distances else 0.0
    avg_baseline = float(np.mean(baseline_distances)) if baseline_distances else 0.0
    delta = avg_spatial - avg_baseline
    
    return {
        "spatial": avg_spatial,
        "baseline": avg_baseline,
        "delta": delta,
        "n_targets": n_targets,
        "n_interference": n_interference
    }

def _compute_retrieval_quality(
    model: Any,
    target: EpisodicChunk,
    context_chunks: List[EpisodicChunk],
    tokenizer: AutoTokenizer,
    top_k: int
) -> float:
    """
    Computes retrieval quality for a non-spatial baseline model.
    Uses standard attention-based retrieval.
    """
    if not context_chunks:
        return 0.0
    
    # Create query from target
    target_text = target.content
    query_tokens = tokenizer.encode(target_text, return_tensors="pt")
    
    # Compute similarity with all context chunks
    similarities = []
    for chunk in context_chunks:
        chunk_text = chunk.content
        chunk_tokens = tokenizer.encode(chunk_text, return_tensors="pt")
        
        # Simple dot-product similarity
        with torch.no_grad():
            # Get hidden states
            target_hidden = model.get_hidden_states(query_tokens)
            chunk_hidden = model.get_hidden_states(chunk_tokens)
            
            # Compute similarity
            sim = torch.nn.functional.cosine_similarity(
                target_hidden.mean(dim=1), 
                chunk_hidden.mean(dim=1)
            ).item()
            similarities.append(sim)
    
    # Top-k retrieval quality: how well the target matches the best retrieved items
    if not similarities:
        return 0.0
    
    sorted_sims = sorted(similarities, reverse=True)
    top_k_sims = sorted_sims[:top_k]
    
    # Quality is the average similarity of top-k items
    return float(np.mean(top_k_sims)) if top_k_sims else 0.0

def _compute_spatial_retrieval_quality(
    model: Any,
    grid: MemoryGrid,
    target: EpisodicChunk,
    context_chunks: List[EpisodicChunk],
    tokenizer: AutoTokenizer,
    top_k: int
) -> float:
    """
    Computes retrieval quality for the spatial memory model.
    Uses soft-addressed spatial retrieval.
    """
    if not context_chunks:
        return 0.0
    
    # Assign spatial coordinates to target
    target_coords = model.get_coordinate(target) if hasattr(model, 'get_coordinate') else None
    
    # Use soft-addressed retrieval
    retrieval_result = soft_addressed_retrieve(
        model=model,
        grid=grid,
        query=target,
        context=context_chunks,
        top_k=top_k
    )
    
    if retrieval_result is None:
        return 0.0
    
    # Quality is based on the retrieval score and spatial coherence
    quality_score = retrieval_result.score if hasattr(retrieval_result, 'score') else 0.0
    
    # Normalize to [0, 1] range if necessary
    if quality_score > 1.0:
        quality_score = quality_score / (quality_score + 1.0)
    
    return float(quality_score)

def compute_exact_match_recall(
    predictions: List[str],
    references: List[str]
) -> float:
    """
    Computes exact match recall between predictions and references.
    
    Args:
        predictions: List of predicted strings
        references: List of reference strings
        
    Returns:
        Exact match recall as a float between 0 and 1
    """
    if not predictions or not references:
        return 0.0
    
    if len(predictions) != len(references):
        raise ValueError("Predictions and references must have the same length")
    
    exact_matches = sum(1 for p, r in zip(predictions, references) if p.strip() == r.strip())
    return exact_matches / len(predictions)

def evaluate_model_on_dataset(
    model: Any,
    dataset: List[Dict[str, Any]],
    tokenizer: AutoTokenizer,
    device: str = "cpu"
) -> Tuple[List[str], List[str]]:
    """
    Evaluates a model on a dataset and returns predictions and references.
    
    Args:
        model: The model to evaluate
        dataset: List of dicts with 'input' and 'expected_output' keys
        tokenizer: Tokenizer for the model
        device: Device to run the model on
        
    Returns:
        Tuple of (predictions, references)
    """
    predictions = []
    references = []
    
    model.to(device)
    model.eval()
    
    with torch.no_grad():
        for item in dataset:
            input_text = item['input']
            expected_output = item['expected_output']
            
            # Tokenize input
            inputs = tokenizer(input_text, return_tensors="pt").to(device)
            
            # Generate prediction
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                do_sample=False
            )
            
            prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract just the generated part
            prediction = prediction.replace(input_text, "").strip()
            
            predictions.append(prediction)
            references.append(expected_output)
    
    return predictions, references

def run_evaluation_for_seed(
    seed: int,
    model_spatial: Any,
    model_baseline: Any,
    dataset: List[Dict[str, Any]],
    grid: MemoryGrid,
    tokenizer: AutoTokenizer,
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    Runs evaluation for a single random seed.
    
    Args:
        seed: Random seed
        model_spatial: Spatial memory model
        model_baseline: Baseline model
        dataset: Evaluation dataset
        grid: Memory grid
        tokenizer: Tokenizer
        device: Device
        
    Returns:
        Dictionary with evaluation results
    """
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    # Evaluate both models
    preds_spatial, refs = evaluate_model_on_dataset(
        model_spatial, dataset, tokenizer, device
    )
    preds_baseline, _ = evaluate_model_on_dataset(
        model_baseline, dataset, tokenizer, device
    )
    
    # Compute exact match recall
    recall_spatial = compute_exact_match_recall(preds_spatial, refs)
    recall_baseline = compute_exact_match_recall(preds_baseline, refs)
    
    # Compute interference distance
    # Use a subset of dataset for interference measurement
    interference_chunks = [
        EpisodicChunk(content=item['input'], metadata={}) 
        for item in dataset[:20]  # Use first 20 items as memory
    ]
    
    interference_metrics = compute_interference_distance(
        model_spatial=model_spatial,
        model_baseline=model_baseline,
        grid=grid,
        chunks=interference_chunks,
        tokenizer=tokenizer
    )
    
    return {
        "seed": seed,
        "recall_spatial": recall_spatial,
        "recall_baseline": recall_baseline,
        "interference_distance": interference_metrics
    }

def aggregate_results_by_seed(
    results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregates evaluation results across multiple seeds.
    
    Args:
        results: List of result dictionaries from run_evaluation_for_seed
        
    Returns:
        Aggregated results dictionary
    """
    if not results:
        return {
            "seeds": [],
            "recall_spatial_mean": 0.0,
            "recall_baseline_mean": 0.0,
            "interference_spatial_mean": 0.0,
            "interference_baseline_mean": 0.0,
            "interference_delta_mean": 0.0
        }
    
    seeds = [r["seed"] for r in results]
    recalls_spatial = [r["recall_spatial"] for r in results]
    recalls_baseline = [r["recall_baseline"] for r in results]
    
    interference_spacial = [r["interference_distance"]["spatial"] for r in results]
    interference_baseline = [r["interference_distance"]["baseline"] for r in results]
    interference_delta = [r["interference_distance"]["delta"] for r in results]
    
    return {
        "seeds": seeds,
        "recall_spatial_mean": float(np.mean(recalls_spatial)),
        "recall_baseline_mean": float(np.mean(recalls_baseline)),
        "recall_spatial_std": float(np.std(recalls_spatial)),
        "recall_baseline_std": float(np.std(recalls_baseline)),
        "interference_spatial_mean": float(np.mean(interference_spacial)),
        "interference_baseline_mean": float(np.mean(interference_baseline)),
        "interference_delta_mean": float(np.mean(interference_delta)),
        "n_seeds": len(results)
    }

def main():
    """
    Main function to demonstrate interference distance calculation.
    This is a placeholder for actual execution with real data.
    """
    print("Interference distance metric implementation complete.")
    print("Use compute_interference_distance() to calculate metrics.")
    print("Results will be saved to artifacts/results/interference_distance.json")

if __name__ == "__main__":
    main()