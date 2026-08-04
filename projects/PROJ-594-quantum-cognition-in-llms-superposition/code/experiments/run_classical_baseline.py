"""
Classical Sum-of-Squares Baseline (Ablation Condition).

Implements P = ||c1||^2 + ||c2||^2 (no interference cross-term).
This serves as the primary ablation condition to isolate the contribution
of the quantum interference mechanism.
"""

import os
import sys
import json
import argparse
import random
import torch
from typing import Dict, List, Any, Tuple

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from datasets import load_dataset
from transformers import BertTokenizer, BertModel
from utils.config import get_config
from utils.logging import detect_nan_inf
from utils.framing_utils import format_associational_statement

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def load_wic_dataset(split: str = "validation") -> List[Dict[str, Any]]:
    """
    Load the WiC dataset from SuperGLUE.
    Returns a list of examples with context, target word, and labels.
    """
    try:
        dataset = load_dataset("super_glue", "wic", split=split)
        return list(dataset)
    except Exception as e:
        raise RuntimeError(f"Failed to load WiC dataset: {e}")

def get_bert_embedding(model: BertModel, tokenizer: BertTokenizer, text: str) -> torch.Tensor:
    """
    Get BERT embedding for a given text.
    Returns the mean pooling of the last hidden state.
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        last_hidden = outputs.last_hidden_state
        # Mean pooling
        attention_mask = inputs['attention_mask']
        mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
        sum_embeddings = torch.sum(last_hidden * mask_expanded, 1)
        sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
        embedding = sum_embeddings / sum_mask
    return embedding.squeeze(0)

def compute_classical_probability(c1: torch.Tensor, c2: torch.Tensor) -> float:
    """
    Compute classical probability using Sum-of-Squares: P = ||c1||^2 + ||c2||^2.
    This explicitly excludes the interference cross-term (2*Re(c1 * conj(c2))).
    
    Args:
        c1: Complex vector for context 1 (or real embedding treated as complex)
        c2: Complex vector for context 2
    
    Returns:
        Normalized probability for class 1 (True/False)
    """
    # Ensure inputs are complex
    if not torch.is_complex(c1):
        c1 = c1.to(torch.complex64)
    if not torch.is_complex(c2):
        c2 = c2.to(torch.complex64)
    
    # Sum of squares (magnitudes squared)
    mag_sq_1 = torch.abs(c1) ** 2
    mag_sq_2 = torch.abs(c2) ** 2
    
    # Total unnormalized probability
    total_prob = torch.sum(mag_sq_1) + torch.sum(mag_sq_2)
    
    # Avoid division by zero
    if total_prob == 0:
        return 0.5
    
    # Normalize to get probability for class 1 (assuming c1 corresponds to True)
    # In this ablation, we treat the magnitude of the first component as the signal
    # relative to the total magnitude.
    p_true = torch.sum(mag_sq_1) / total_prob
    return p_true.item()

def preprocess_wic_example(example: Dict[str, Any], tokenizer: BertTokenizer) -> Tuple[torch.Tensor, torch.Tensor, int]:
    """
    Preprocess a WiC example to get embeddings for the target word in both contexts.
    
    Returns:
        c1: Embedding for context 1
        c2: Embedding for context 2
        label: Ground truth label (1 if same meaning, 0 if different)
    """
    context1 = example['sentence1']
    context2 = example['sentence2']
    word = example['word']
    label = 1 if example['label'] == 1 else 0
    
    # Simple approach: use the full sentence embedding
    # A more sophisticated approach would extract the specific word embedding
    c1 = get_bert_embedding(tokenizer, tokenizer, context1)
    c2 = get_bert_embedding(tokenizer, tokenizer, context2)
    
    return c1, c2, label

def run_single_seed(seed: int) -> Dict[str, Any]:
    """
    Run the classical baseline for a single seed.
    
    Returns:
        Dictionary with accuracy, macro_f1, and seed.
    """
    set_seed(seed)
    config = get_config()
    device = torch.device(config['device'])
    
    # Load data
    data = load_wic_dataset("validation")
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertModel.from_pretrained('bert-base-uncased')
    model.to(device)
    model.eval()
    
    # Freeze model
    for param in model.parameters():
        param.requires_grad = False
    
    predictions = []
    labels = []
    
    # Process examples
    for example in data:
        c1, c2, label = preprocess_wic_example(example, tokenizer)
        c1 = c1.to(device)
        c2 = c2.to(device)
        
        # Compute classical probability
        p_true = compute_classical_probability(c1, c2)
        
        # Convert to binary prediction
        pred = 1 if p_true > 0.5 else 0
        
        predictions.append(pred)
        labels.append(label)
    
    # Calculate metrics
    accuracy = sum(1 for p, l in zip(predictions, labels) if p == l) / len(labels)
    
    # Calculate macro F1
    from sklearn.metrics import f1_score
    macro_f1 = f1_score(labels, predictions, average='macro')
    
    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "seed": seed
    }

def main():
    parser = argparse.ArgumentParser(description="Run Classical Sum-of-Squares Baseline")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    print(format_associational_statement("Starting classical baseline evaluation..."))
    print(format_associational_statement(f"Using seed: {args.seed}"))
    
    try:
        results = run_single_seed(args.seed)
        
        # Write results to file
        output_path = os.path.join(project_root, "data", "results", "classical_baseline_metrics.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(format_associational_statement(f"Results written to {output_path}"))
        print(format_associational_statement(f"Accuracy: {results['accuracy']:.4f}"))
        print(format_associational_statement(f"Macro F1: {results['macro_f1']:.4f}"))
        
    except Exception as e:
        print(f"Error running classical baseline: {e}")
        raise

if __name__ == "__main__":
    main()