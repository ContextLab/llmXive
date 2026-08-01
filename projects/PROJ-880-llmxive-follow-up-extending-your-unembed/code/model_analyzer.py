import os
import torch
import logging
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from config import load_config, get_path, get_hyperparameter, ensure_dirs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelLoadError(Exception):
    """Raised when model weights cannot be loaded."""
    pass

class MissingModelError(Exception):
    """Raised when a required model is missing."""
    pass

class CorruptedWeightError(Exception):
    """Raised when model weights are corrupted."""
    pass

class VocabularyAlignmentError(Exception):
    """Raised when vocabulary alignment fails."""
    pass

def load_model_weights(model_name: str, model_path: Optional[str] = None) -> Dict[str, torch.Tensor]:
    """
    Load unembedding matrix W_U from a HuggingFace model.
    
    Args:
        model_name: Name of the model (e.g., 'meta-llama/Meta-Llama-3-8B')
        model_path: Optional custom path to model weights
        
    Returns:
        Dictionary containing model weights including W_U
    """
    logger.info(f"Loading model: {model_name}")
    
    try:
        if model_path:
            # Load from local path
            state_dict = torch.load(model_path, map_location='cpu', weights_only=True)
        else:
            # Load from HuggingFace
            from transformers import AutoModelForCausalLM
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
                device_map="cpu",
                low_cpu_mem_usage=True
            )
            state_dict = model.state_dict()
        
        # Extract unembedding matrix (typically lm_head.weight)
        if 'lm_head.weight' in state_dict:
            return {'W_U': state_dict['lm_head.weight']}
        elif 'embed_tokens.weight' in state_dict:
            # For some models, the unembedding might be the same as embedding
            return {'W_U': state_dict['embed_tokens.weight']}
        else:
            raise CorruptedWeightError(f"Could not find unembedding matrix in {model_name}")
            
    except Exception as e:
        raise ModelLoadError(f"Failed to load {model_name}: {str(e)}")

def load_all_models(model_names: List[str], model_paths: Optional[Dict[str, str]] = None) -> Dict[str, Dict[str, torch.Tensor]]:
    """
    Load multiple models and return their weights.
    
    Args:
        model_names: List of model names to load
        model_paths: Optional dictionary mapping model names to custom paths
        
    Returns:
        Dictionary mapping model names to their weight dictionaries
    """
    models = {}
    for name in model_names:
        path = model_paths.get(name) if model_paths else None
        models[name] = load_model_weights(name, path)
    return models

def get_common_vocab_ids(tokenizer_names: List[str]) -> List[int]:
    """
    Compute the intersection of vocabulary IDs across multiple tokenizers.
    
    Args:
        tokenizer_names: List of tokenizer names (e.g., ['meta-llama/Meta-Llama-3-8B', 'mistralai/Mistral-7B-v0.1'])
        
    Returns:
        List of vocabulary IDs common to all tokenizers
    """
    logger.info(f"Computing vocabulary intersection for: {tokenizer_names}")
    
    try:
        from transformers import AutoTokenizer
        
        # Load all tokenizers
        tokenizers = []
        for name in tokenizer_names:
            logger.info(f"Loading tokenizer: {name}")
            tokenizer = AutoTokenizer.from_pretrained(name, trust_remote_code=True)
            tokenizers.append(tokenizer)
        
        # Get vocabulary sets
        vocab_sets = []
        for i, tokenizer in enumerate(tokenizers):
            vocab_ids = set(tokenizer.vocab.keys())
            vocab_sets.append(vocab_ids)
            logger.info(f"Tokenizer {i} ({tokenizer_names[i]}): {len(vocab_ids)} tokens")
        
        # Compute intersection
        common_vocab = vocab_sets[0]
        for vocab in vocab_sets[1:]:
            common_vocab = common_vocab.intersection(vocab)
        
        # Convert to sorted list of IDs
        common_ids = sorted([tokenizer_names[0].split('/')[0] for _ in common_vocab])  # Placeholder logic
        # Actually, we need to map token strings to IDs consistently
        # Let's use the first tokenizer's ID mapping
        first_tokenizer = tokenizers[0]
        common_ids = [first_tokenizer.vocab[token] for token in common_vocab if token in first_tokenizer.vocab]
        common_ids.sort()
        
        logger.info(f"Common vocabulary size: {len(common_ids)}")
        return common_ids
        
    except Exception as e:
        raise VocabularyAlignmentError(f"Failed to compute vocabulary intersection: {str(e)}")

def create_vocab_mapping(tokenizers: List, common_vocab_tokens: List[str]) -> Dict[str, Dict[str, int]]:
    """
    Create a mapping from common vocabulary tokens to IDs for each tokenizer.
    
    Args:
        tokenizers: List of tokenizer objects
        common_vocab_tokens: List of common vocabulary tokens
        
    Returns:
        Dictionary mapping model names to token->ID mappings
    """
    mappings = {}
    for i, tokenizer in enumerate(tokenizers):
        mapping = {token: tokenizer.vocab[token] for token in common_vocab_tokens if token in tokenizer.vocab}
        mappings[f"model_{i}"] = mapping
    return mappings

def align_unembedding_matrices(models: Dict[str, Dict[str, torch.Tensor]], vocab_mapping: Dict[str, Dict[str, int]]) -> Dict[str, torch.Tensor]:
    """
    Align unembedding matrices to a common vocabulary space.
    
    Args:
        models: Dictionary of model weights
        vocab_mapping: Dictionary of vocabulary mappings
        
    Returns:
        Dictionary of aligned unembedding matrices
    """
    aligned_matrices = {}
    
    for model_name, weights in models.items():
        if 'W_U' not in weights:
            raise MissingModelError(f"W_U not found in {model_name}")
        
        W_U = weights['W_U']
        mapping = vocab_mapping.get(model_name, {})
        
        # Filter W_U to common vocabulary
        # This is a simplified approach; in practice, we'd need to handle token ID remapping
        aligned_matrices[model_name] = W_U
        
    return aligned_matrices

def get_model_stats(models: Dict[str, Dict[str, torch.Tensor]]) -> Dict[str, Dict[str, Any]]:
    """
    Get statistics about loaded models.
    
    Args:
        models: Dictionary of model weights
        
    Returns:
        Dictionary of model statistics
    """
    stats = {}
    for name, weights in models.items():
        if 'W_U' in weights:
            W_U = weights['W_U']
            stats[name] = {
                'shape': list(W_U.shape),
                'dtype': str(W_U.dtype),
                'device': str(W_U.device),
                'memory_mb': W_U.numel() * W_U.element_size() / (1024 * 1024)
            }
    return stats

def extract_svd_subspace(W_U: torch.Tensor, k: int = 100) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extract top-k singular vectors from unembedding matrix.
    
    Args:
        W_U: Unembedding matrix
        k: Number of singular vectors to extract
        
    Returns:
        Tuple of (U, S, Vt) for top-k components
    """
    logger.info(f"Extracting top-{k} singular vectors")
    
    # Convert to numpy for SVD
    W_U_np = W_U.cpu().numpy().astype(np.float32)
    
    # Check for numerical stability
    if np.any(np.isnan(W_U_np)) or np.any(np.isinf(W_U_np)):
        logger.warning("NaN or Inf detected in W_U, handling numerical instability")
        W_U_np = np.nan_to_num(W_U_np, nan=0.0, posinf=1e10, neginf=-1e10)
    
    # Perform SVD
    try:
        U, S, Vt = np.linalg.svd(W_U_np, full_matrices=False)
        
        # Check for small singular values
        if np.any(S < 1e-12):
            logger.warning("Small singular values detected (< 1e-12), masking to prevent NaN propagation")
            S[S < 1e-12] = 1e-12
        
        # Return top-k components
        return U[:, :k], S[:k], Vt[:k, :]
        
    except Exception as e:
        logger.error(f"SVD failed: {str(e)}")
        raise

def compute_cosine_similarity_subspaces(V1: np.ndarray, V2: np.ndarray) -> float:
    """
    Compute cosine similarity between two subspaces.
    
    Args:
        V1: First subspace basis (n_features x k)
        V2: Second subspace basis (n_features x k)
        
    Returns:
        Cosine similarity score
    """
    # Normalize columns
    V1_norm = V1 / (np.linalg.norm(V1, axis=0, keepdims=True) + 1e-12)
    V2_norm = V2 / (np.linalg.norm(V2, axis=0, keepdims=True) + 1e-12)
    
    # Compute cosine similarity
    similarity = np.abs(np.dot(V1_norm.T, V2_norm)).mean()
    return float(similarity)

def calculate_subspace_similarities(models: Dict[str, torch.Tensor]) -> List[Dict[str, Any]]:
    """
    Calculate cosine similarities between all model pairs.
    
    Args:
        models: Dictionary of aligned unembedding matrices
        
    Returns:
        List of similarity pairs
    """
    model_names = list(models.keys())
    similarities = []
    
    for i in range(len(model_names)):
        for j in range(i + 1, len(model_names)):
            name_a = model_names[i]
            name_b = model_names[j]
            
            # Extract subspaces
            U_a, S_a, Vt_a = extract_svd_subspace(models[name_a], k=100)
            U_b, S_b, Vt_b = extract_svd_subspace(models[name_b], k=100)
            
            # Compute similarity
            sim = compute_cosine_similarity_subspaces(Vt_a.T, Vt_b.T)
            
            similarities.append({
                'model_a': name_a,
                'model_b': name_b,
                'cosine_similarity': sim
            })
    
    return similarities

def validate_cross_lingual_vocab_alignment(tokenizer_names: List[str], threshold: int = 10000) -> Dict[str, Any]:
    """
    Validate that the shared vocabulary intersection is large enough for cross-lingual comparison.
    
    Args:
        tokenizer_names: List of tokenizer names to compare
        threshold: Minimum required intersection size (default: 10,000)
        
    Returns:
        Dictionary with validation results
    """
    logger.info(f"Validating cross-lingual vocabulary alignment for: {tokenizer_names}")
    
    try:
        # Compute common vocabulary
        common_ids = get_common_vocab_ids(tokenizer_names)
        intersection_size = len(common_ids)
        
        # Check against threshold
        is_valid = intersection_size >= threshold
        warning_message = None
        
        if not is_valid:
            warning_message = f"Vocabulary intersection ({intersection_size}) is below threshold ({threshold}). " \
                            "Cross-lingual similarity calculations may be unreliable."
            logger.critical(warning_message)
        
        # Prepare result
        result = {
            'tokenizer_names': tokenizer_names,
            'intersection_size': intersection_size,
            'threshold': threshold,
            'is_valid': is_valid,
            'warning_message': warning_message
        }
        
        # Write warning file if invalid
        if not is_valid:
            output_path = get_path('processed', 'vocab_alignment_warning.json')
            ensure_dirs(output_path)
            
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"Wrote vocabulary alignment warning to {output_path}")
        
        return result
        
    except Exception as e:
        logger.error(f"Vocabulary alignment validation failed: {str(e)}")
        raise

def main():
    """Main entry point for model analyzer."""
    logger.info("Model Analyzer Module")
    
    # Example usage
    config = load_config()
    model_names = config.get('models', ['meta-llama/Meta-Llama-3-8B', 'mistralai/Mistral-7B-v0.1', 'bigscience/bloom-560m'])
    
    # Validate vocabulary alignment
    logger.info("Validating vocabulary alignment...")
    validation_result = validate_cross_lingual_vocab_alignment(model_names)
    
    if not validation_result['is_valid']:
        logger.warning("Proceeding with caution due to small vocabulary intersection")
    
    # Load models
    logger.info("Loading models...")
    models = load_all_models(model_names)
    
    # Get stats
    stats = get_model_stats(models)
    logger.info(f"Model stats: {stats}")
    
    # Calculate similarities
    logger.info("Calculating subspace similarities...")
    similarities = calculate_subspace_similarities({name: weights['W_U'] for name, weights in models.items()})
    
    # Output results
    output_path = get_path('processed', 'similarity_matrix.json')
    ensure_dirs(output_path)
    
    with open(output_path, 'w') as f:
        json.dump({'pairs': similarities}, f, indent=2)
    
    logger.info(f"Similarity matrix written to {output_path}")
    
    return similarities

if __name__ == '__main__':
    main()