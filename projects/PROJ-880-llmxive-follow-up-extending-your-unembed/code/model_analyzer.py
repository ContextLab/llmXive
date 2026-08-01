"""
Model analysis module for unembedding matrix operations.
Handles loading, SVD, and subspace similarity calculations.
"""
import os
import torch
import logging
import json
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, List, Set

from config import load_config, get_path, get_hyperparameter

class ModelLoadError(Exception):
    pass

class MissingModelError(Exception):
    pass

class CorruptedWeightError(Exception):
    pass

class VocabularyAlignmentError(Exception):
    """Raised when vocabulary alignment fails or intersection is insufficient."""
    pass

def load_model_weights(model_name: str, device: str = "cpu") -> torch.Tensor:
    """Load the unembedding matrix W_U from a HuggingFace model."""
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        # Load model in float32 on CPU as per constraints
        model = AutoModelForCausalLM.from_pretrained(
            model_name, 
            torch_dtype=torch.float32, 
            device_map="cpu",
            low_cpu_mem_usage=True
        )
        
        # Extract unembedding matrix (lm_head.weight)
        if hasattr(model, 'lm_head'):
            w_u = model.lm_head.weight.data
        elif hasattr(model, 'get_output_embeddings'):
            w_u = model.get_output_embeddings().weight.data
        else:
            raise MissingModelError(f"Could not find unembedding matrix in {model_name}")
        
        return w_u.to(device)
    except Exception as e:
        raise ModelLoadError(f"Failed to load {model_name}: {e}")

def load_all_models(model_names: List[str], device: str = "cpu") -> Dict[str, torch.Tensor]:
    """Load unembedding matrices for a list of models."""
    models = {}
    for name in model_names:
        print(f"Loading {name}...")
        models[name] = load_model_weights(name, device)
    return models

def get_common_vocab_ids(tokenizer_a, tokenizer_b) -> List[int]:
    """Find common token IDs between two tokenizers."""
    vocab_a = set(tokenizer_a.vocab.values()) if hasattr(tokenizer_a, 'vocab') else set(tokenizer_a.get_vocab().values())
    vocab_b = set(tokenizer_b.vocab.values()) if hasattr(tokenizer_b, 'vocab') else set(tokenizer_b.get_vocab().values())
    return list(vocab_a.intersection(vocab_b))

def create_vocab_mapping(tokenizer_a, tokenizer_b) -> Dict[int, int]:
    """Create a mapping from tokenizer_a IDs to tokenizer_b IDs for common tokens."""
    # This is a simplified deterministic mapping strategy
    # In a real implementation, we would align based on token strings
    common_tokens = []
    for token_a, id_a in tokenizer_a.get_vocab().items():
        if token_a in tokenizer_b.get_vocab():
            common_tokens.append((token_a, id_a, tokenizer_b.get_vocab()[token_a]))
    
    mapping = {id_a: id_b for _, id_a, id_b in common_tokens}
    return mapping

def align_unembedding_matrices(w_u_a: torch.Tensor, w_u_b: torch.Tensor, mapping: Dict[int, int]) -> Tuple[torch.Tensor, torch.Tensor]:
    """Align two unembedding matrices based on a vocabulary mapping."""
    # Create aligned matrices containing only common vocabulary
    common_ids_a = sorted(mapping.keys())
    common_ids_b = [mapping[i] for i in common_ids_a]
    
    aligned_a = w_u_a[common_ids_a, :]
    aligned_b = w_u_b[common_ids_b, :]
    
    return aligned_a, aligned_b

def get_model_stats(w_u: torch.Tensor) -> Dict[str, Any]:
    """Get basic statistics about a model's unembedding matrix."""
    return {
        "shape": list(w_u.shape),
        "dtype": str(w_u.dtype),
        "mean": float(w_u.mean()),
        "std": float(w_u.std()),
    }

def extract_svd_subspace(w_u: torch.Tensor, k: int = 100) -> torch.Tensor:
    """Extract the top-k singular vectors (edge spectrum) from W_U."""
    # Perform SVD
    U, S, Vh = torch.linalg.svd(w_u.float(), full_matrices=False)
    # Return the top-k right singular vectors (Vh is already V^T)
    return Vh[:k, :]

def compute_cosine_similarity_subspaces(U1: torch.Tensor, U2: torch.Tensor) -> float:
    """Compute the cosine similarity between two subspaces."""
    # Normalize rows
    U1_norm = U1 / U1.norm(dim=1, keepdim=True)
    U2_norm = U2 / U2.norm(dim=1, keepdim=True)
    
    # Compute mean cosine similarity
    # Using Frobenius norm of the product as a proxy for subspace similarity
    similarity = (U1_norm @ U2_norm.T).abs().mean().item()
    return similarity

def calculate_subspace_similarities(models: Dict[str, torch.Tensor], k: int = 100) -> List[Dict[str, Any]]:
    """Calculate pairwise subspace similarities for a set of models."""
    results = []
    model_names = list(models.keys())
    
    # Extract subspaces
    subspaces = {}
    for name, w_u in models.items():
        subspaces[name] = extract_svd_subspace(w_u, k)
    
    # Compare pairs
    for i in range(len(model_names)):
        for j in range(i + 1, len(model_names)):
            name_a, name_b = model_names[i], model_names[j]
            sim = compute_cosine_similarity_subspaces(subspaces[name_a], subspaces[name_b])
            results.append({
                "model_a": name_a,
                "model_b": name_b,
                "cosine_similarity": sim
            })
    
    return results

def validate_cross_lingual_vocab_alignment(
    tokenizer_map: Dict[str, Any], 
    min_intersection_size: int = 10000,
    output_path: Optional[Path] = None
) -> bool:
    """
    Validate that the shared vocabulary intersection between models is sufficient
    for cross-lingual similarity calculations.
    
    Args:
        tokenizer_map: Dict mapping model names to their tokenizer instances.
        min_intersection_size: Minimum required intersection size (default 10,000).
        output_path: Optional path to write warning JSON if validation fails.
        
    Returns:
        True if validation passes, False if it fails (and warning is written).
    """
    model_names = list(tokenizer_map.keys())
    if len(model_names) < 2:
        logging.warning("Insufficient models for vocabulary alignment check.")
        return True
    
    # Compute intersection across all models
    common_vocab: Set[int] = None
    
    for i, name_a in enumerate(model_names):
        tok_a = tokenizer_map[name_a]
        vocab_a = set(tok_a.get_vocab().values())
        
        if common_vocab is None:
            common_vocab = vocab_a
        else:
            common_vocab = common_vocab.intersection(vocab_a)
        
        if not common_vocab:
            break
    
    intersection_size = len(common_vocab) if common_vocab else 0
    
    logging.info(f"Shared vocabulary intersection size: {intersection_size}")
    
    if intersection_size < min_intersection_size:
        warning_msg = (
            f"CRITICAL: Vocabulary intersection size ({intersection_size}) is below "
            f"threshold ({min_intersection_size}). Cross-lingual similarity calculations "
            "may be statistically invalid."
        )
        logging.critical(warning_msg)
        
        warning_data = {
            "status": "warning",
            "intersection_size": intersection_size,
            "min_required": min_intersection_size,
            "models_checked": model_names,
            "message": warning_msg
        }
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(warning_data, f, indent=2)
            logging.info(f"Wrote vocabulary alignment warning to {output_path}")
        
        return False
    
    logging.info(f"Vocabulary alignment validation PASSED (size: {intersection_size})")
    return True

def main():
    """Run model analysis (example)."""
    config = load_config()
    k = get_hyperparameter(config, "k")
    
    # Example models (in real run, these would be provided)
    # models = load_all_models(["meta-llama/Llama-2-7b-hf", "mistralai/Mistral-7B-v0.1"], device="cpu")
    # results = calculate_subspace_similarities(models, k)
    # print(json.dumps(results, indent=2))
    print("Model analyzer ready.")

if __name__ == "__main__":
    main()
