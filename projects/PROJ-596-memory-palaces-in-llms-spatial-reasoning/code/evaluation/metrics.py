"""
Evaluation metrics module for the Memory Palaces project.

Implements exact-match recall calculation and other structural metrics.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer
import logging

# Local imports matching the API surface
from models.base import GPT2MediumBaseline
from models.base_fallback import DistilGPT2Fallback
from models.loading import load_model

logger = logging.getLogger(__name__)

def compute_exact_match_recall(predictions: List[str], references: List[str]) -> float:
    """
    Compute exact match recall: percentage of predictions that exactly match references.
    
    Args:
        predictions: List of predicted strings
        references: List of ground truth strings
        
    Returns:
        Exact match recall as a float between 0.0 and 1.0
    """
    if len(predictions) != len(references):
        raise ValueError(f"Prediction and reference lengths must match: {len(predictions)} vs {len(references)}")
    
    if len(predictions) == 0:
        return 0.0
    
    exact_matches = sum(1 for pred, ref in zip(predictions, references) if pred.strip() == ref.strip())
    return exact_matches / len(predictions)

def evaluate_model_on_dataset(
    model: Any,
    tokenizer: AutoTokenizer,
    dataloader: DataLoader,
    device: str,
    max_new_tokens: int = 50
) -> Tuple[List[str], List[str]]:
    """
    Run inference on a dataset and collect predictions and references.
    
    Args:
        model: The loaded model (GPT2MediumBaseline or DistilGPT2Fallback)
        tokenizer: The tokenizer
        dataloader: DataLoader for the dataset
        device: Device to run inference on ('cpu' or 'cuda')
        max_new_tokens: Maximum tokens to generate
        
    Returns:
        Tuple of (predictions, references) lists
    """
    model.eval()
    predictions = []
    references = []
    
    with torch.no_grad():
        for batch in dataloader:
            # Extract inputs
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            
            # For bAbI Task 3, the answer is typically the last token or a specific span
            # We'll generate the completion and extract the answer
            outputs = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id
            )
            
            # Decode predictions
            for i, output in enumerate(outputs):
                # Remove input tokens from the output
                generated_ids = output[len(input_ids[i]):]
                pred_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
                predictions.append(pred_text.strip())
                
                # Get reference from batch (assuming it's included)
                if 'labels' in batch:
                    ref_ids = batch['labels'][i]
                    # Filter out -100 (padding in labels)
                    ref_ids = ref_ids[ref_ids != -100]
                    ref_text = tokenizer.decode(ref_ids, skip_special_tokens=True)
                    references.append(ref_text.strip())
                else:
                    # Fallback: use the last token as reference (for bAbI)
                    # This is a simplification; real implementation would extract from dataset
                    references.append("")  # Placeholder if labels not available
                    
    return predictions, references

def evaluate_seed(
    seed: int,
    model_type: str = "gpt2-medium",
    dataset_name: str = "babi",
    data_dir: str = "data/processed",
    output_dir: str = "artifacts/results"
) -> Dict[str, Any]:
    """
    Evaluate a model on a dataset for a specific random seed.
    
    Args:
        seed: Random seed for reproducibility
        model_type: Type of model to load ("gpt2-medium" or "distilgpt2")
        dataset_name: Name of the dataset ("babi", "lambada", or "story_cloze")
        data_dir: Directory containing processed data
        output_dir: Directory to store results
        
    Returns:
        Dictionary with evaluation results
    """
    logger.info(f"Evaluating seed {seed} with {model_type} on {dataset_name}")
    
    # Set random seeds
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    # Load model
    model, tokenizer = load_model(model_type, device="cpu")  # Use CPU for safety
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    
    # Load dataset (simplified - in real implementation, would load from data_dir)
    # For now, we'll use a mock dataset structure
    try:
        from datasets import load_dataset
        if dataset_name == "babi":
            dataset = load_dataset("babi", "task3_10k", split="test")
        elif dataset_name == "lambada":
            dataset = load_dataset("lambada", split="test")
        elif dataset_name == "story_cloze":
            dataset = load_dataset("story_cloze", "2016", split="validation")
        else:
            raise ValueError(f"Unknown dataset: {dataset_name}")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        # Return failure result
        return {
            "seed": seed,
            "model_type": model_type,
            "dataset": dataset_name,
            "accuracy": None,
            "error": str(e)
        }
    
    # Create a simple dataset wrapper for bAbI
    class BabIDataset(Dataset):
        def __init__(self, dataset, tokenizer, max_length=512):
            self.dataset = dataset
            self.tokenizer = tokenizer
            self.max_length = max_length
            
        def __len__(self):
            return len(self.dataset)
            
        def __getitem__(self, idx):
            item = self.dataset[idx]
            # For bAbI Task 3, we need to format the query
            text = item["input"]  # Assuming "input" field contains the query
            labels = item["output"] if "output" in item else ""
            
            encoding = self.tokenizer(
                text,
                max_length=self.max_length,
                padding="max_length",
                truncation=True,
                return_tensors="pt"
            )
            
            # Create labels for loss computation (shifted input)
            labels_encoding = self.tokenizer(
                text + " " + labels,
                max_length=self.max_length,
                padding="max_length",
                truncation=True,
                return_tensors="pt"
            )
            
            return {
                "input_ids": encoding["input_ids"].squeeze(0),
                "attention_mask": encoding["attention_mask"].squeeze(0),
                "labels": labels_encoding["input_ids"].squeeze(0)
            }
    
    # Create dataloader
    ds = BabIDataset(dataset, tokenizer)
    dataloader = DataLoader(ds, batch_size=4, shuffle=False)
    
    # Evaluate
    predictions, references = evaluate_model_on_dataset(
        model, tokenizer, dataloader, device, max_new_tokens=20
    )
    
    # Calculate exact match recall
    accuracy = compute_exact_match_recall(predictions, references)
    
    result = {
        "seed": seed,
        "model_type": model_type,
        "dataset": dataset_name,
        "accuracy": accuracy,
        "num_samples": len(predictions)
    }
    
    logger.info(f"Seed {seed} accuracy: {accuracy:.4f}")
    return result

def run_evaluation(
    seeds: List[int],
    model_type: str = "gpt2-medium",
    dataset_name: str = "babi",
    output_dir: str = "artifacts/results"
) -> Dict[str, Any]:
    """
    Run evaluation across multiple seeds and aggregate results.
    
    Args:
        seeds: List of random seeds to evaluate
        model_type: Type of model to use
        dataset_name: Dataset to evaluate on
        output_dir: Directory to store results
        
    Returns:
        Aggregated results dictionary
    """
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    results = []
    for seed in seeds:
        result = evaluate_seed(seed, model_type, dataset_name, "data/processed", output_dir)
        results.append(result)
    
    # Aggregate results
    accuracies = [r["accuracy"] for r in results if r["accuracy"] is not None]
    aggregated = {
        "seeds": seeds,
        "accuracies": accuracies,
        "mean_accuracy": float(np.mean(accuracies)) if accuracies else None,
        "std_accuracy": float(np.std(accuracies)) if accuracies else None,
        "model_type": model_type,
        "dataset": dataset_name,
        "num_seeds": len(seeds)
    }
    
    # Write to file
    output_path = Path(output_dir) / "recall_accuracy.json"
    with open(output_path, "w") as f:
        json.dump(aggregated, f, indent=2)
    
    logger.info(f"Results written to {output_path}")
    return aggregated

def main():
    """Main entry point for evaluation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate model on dataset")
    parser.add_argument("--seeds", type=int, nargs="+", default=[-4, -3, -2, -1, 0],
                      help="Random seeds to evaluate")
    parser.add_argument("--model-type", type=str, default="gpt2-medium",
                      choices=["gpt2-medium", "distilgpt2"],
                      help="Model type to evaluate")
    parser.add_argument("--dataset", type=str, default="babi",
                      choices=["babi", "lambada", "story_cloze"],
                      help="Dataset to evaluate on")
    parser.add_argument("--output-dir", type=str, default="artifacts/results",
                      help="Output directory for results")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    results = run_evaluation(
        seeds=args.seeds,
        model_type=args.model_type,
        dataset_name=args.dataset,
        output_dir=args.output_dir
    )
    
    print(f"Evaluation complete. Mean accuracy: {results['mean_accuracy']:.4f}")
    return results

if __name__ == "__main__":
    main()