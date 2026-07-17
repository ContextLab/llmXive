import os
import torch
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, List, Set

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelLoadError(Exception):
    """Base exception for model loading failures."""
    pass

class MissingModelError(ModelLoadError):
    """Raised when a model file is missing."""
    pass

class CorruptedWeightError(ModelLoadError):
    """Raised when model weights are corrupted or invalid."""
    pass

def load_config() -> Dict[str, Any]:
    """Load configuration from code/config.py."""
    try:
        from config import K_SVD, SEED, MODEL_PATHS
        return {
            'k': K_SVD,
            'seed': SEED,
            'model_paths': MODEL_PATHS
        }
    except ImportError:
        logger.warning("config.py not found, using defaults")
        return {
            'k': 100,
            'seed': 42,
            'model_paths': {
                'llama3': 'meta-llama/Meta-Llama-3-8B',
                'mistral': 'mistralai/Mistral-7B-v0.1',
                'bloom': 'bigscience/bloom-560m'
            }
        }

def load_model_weights(model_name: str, model_path: str) -> torch.Tensor:
    """
    Load the unembedding matrix W_U from a HuggingFace model.
    Uses CPU-only float32 loading to stay within memory constraints.
    
    Args:
        model_name: Name of the model (for logging)
        model_path: Path or HF identifier for the model
        
    Returns:
        torch.Tensor: The unembedding matrix W_U (vocab_size x hidden_dim)
    """
    logger.info(f"Loading unembedding matrix for {model_name} from {model_path}")
    
    try:
        # Lazy import to avoid heavy imports if not needed
        from transformers import AutoModelForCausalLM
        
        # Load model in float32 on CPU only
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float32,
            device_map="cpu",
            low_cpu_mem_usage=True
        )
        
        # Extract the unembedding matrix (lm_head.weight)
        # For most models, this is the output projection matrix
        if hasattr(model, 'lm_head'):
            w_u = model.lm_head.weight.detach().float().cpu().numpy()
        elif hasattr(model, 'get_output_embeddings'):
            # Fallback for some model architectures
            embed_layer = model.get_output_embeddings()
            if embed_layer is not None:
                w_u = embed_layer.weight.detach().float().cpu().numpy()
            else:
                raise MissingModelError(f"No output embeddings found in {model_name}")
        else:
            raise MissingModelError(f"Could not find unembedding matrix in {model_name}")
        
        logger.info(f"Loaded W_U for {model_name}: shape {w_u.shape}")
        return w_u
        
    except FileNotFoundError as e:
        raise MissingModelError(f"Model files not found for {model_name}: {e}")
    except Exception as e:
        raise CorruptedWeightError(f"Failed to load weights for {model_name}: {e}")

def load_all_models() -> Dict[str, np.ndarray]:
    """
    Load unembedding matrices for all configured models.
    
    Returns:
        Dict mapping model name to W_U matrix
    """
    config = load_config()
    models = {}
    
    for model_name, model_path in config['model_paths'].items():
        try:
            models[model_name] = load_model_weights(model_name, model_path)
        except ModelLoadError as e:
            logger.error(f"Skipping {model_name}: {e}")
            # Continue with other models instead of failing entirely
            continue
    
    if not models:
        raise ModelLoadError("No models were successfully loaded")
        
    return models

def get_common_vocab_ids(model_matrices: Dict[str, np.ndarray]) -> List[int]:
    """
    Identify common token IDs across all model vocabularies.
    This assumes token IDs correspond to the same semantic tokens when they match.
    
    Args:
        model_matrices: Dict of model_name -> W_U matrix
        
    Returns:
        List of common token IDs
    """
    if not model_matrices:
        return []
        
    # Get vocab sizes for each model
    vocab_sizes = {name: matrix.shape[0] for name, matrix in model_matrices.items()}
    min_vocab_size = min(vocab_sizes.values())
    
    # Common IDs are those present in all vocabularies
    # We take the intersection of [0, min_vocab_size)
    common_ids = list(range(min_vocab_size))
    
    logger.info(f"Found {len(common_ids)} common vocabulary IDs across models")
    logger.info(f"Vocab sizes: {vocab_sizes}")
    
    return common_ids

def create_vocab_mapping(model_matrices: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """
    Create vocabulary mapping layer to align token IDs between models.
    Returns mapping matrices that can be applied to align W_U matrices.
    
    Args:
        model_matrices: Dict of model_name -> W_U matrix
        
    Returns:
        Dict mapping model_name -> alignment indices for common vocab
    """
    common_ids = get_common_vocab_ids(model_matrices)
    
    if not common_ids:
        raise ValueError("No common vocabulary IDs found between models")
    
    # For each model, create an index array of common IDs
    # This will be used to slice W_U to only include common tokens
    mappings = {}
    for model_name in model_matrices.keys():
        # Since we're using common IDs directly, the mapping is just the IDs themselves
        mappings[model_name] = np.array(common_ids)
    
    logger.info(f"Created vocabulary mapping for {len(mappings)} models")
    return mappings

def align_unembedding_matrices(
    model_matrices: Dict[str, np.ndarray],
    vocab_mappings: Dict[str, np.ndarray]
) -> Dict[str, np.ndarray]:
    """
    Align unembedding matrices to a common vocabulary space.
    
    Args:
        model_matrices: Dict of model_name -> W_U matrix
        vocab_mappings: Dict of model_name -> common token IDs
        
    Returns:
        Dict of aligned W_U matrices (all have same vocab dimension)
    """
    aligned = {}
    
    for model_name, matrix in model_matrices.items():
        if model_name not in vocab_mappings:
            raise ValueError(f"No vocabulary mapping for {model_name}")
        
        common_ids = vocab_mappings[model_name]
        
        # Slice the matrix to only include common token rows
        aligned_matrix = matrix[common_ids, :]
        
        aligned[model_name] = aligned_matrix
        logger.info(f"Aligned {model_name}: {matrix.shape} -> {aligned_matrix.shape}")
    
    return aligned

def get_model_stats(model_matrices: Dict[str, np.ndarray]) -> Dict[str, Dict[str, Any]]:
    """
    Compute basic statistics for each model's unembedding matrix.
    
    Args:
        model_matrices: Dict of model_name -> W_U matrix
        
    Returns:
        Dict of model stats
    """
    stats = {}
    
    for model_name, matrix in model_matrices.items():
        stats[model_name] = {
            'shape': list(matrix.shape),
            'dtype': str(matrix.dtype),
            'mean': float(np.mean(matrix)),
            'std': float(np.std(matrix)),
            'min': float(np.min(matrix)),
            'max': float(np.max(matrix)),
            'non_zero_ratio': float(np.count_nonzero(matrix) / matrix.size)
        }
    
    return stats

def extract_svd_subspace(
    matrix: np.ndarray,
    k: int,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Extract the top-k singular vectors (edge spectrum subspace) from a matrix.
    Uses randomized SVD for efficiency on large matrices.
    
    Args:
        matrix: Input matrix (vocab_size x hidden_dim)
        k: Number of singular vectors to extract
        seed: Random seed for reproducibility
        
    Returns:
        np.ndarray: Top-k left singular vectors (vocab_size x k)
    """
    if seed is not None:
        np.random.seed(seed)
    
    logger.info(f"Computing SVD subspace (k={k}) for matrix of shape {matrix.shape}")
    
    # Use randomized SVD for efficiency
    # U shape: (vocab_size, k)
    # We only need the left singular vectors for subspace comparison
    try:
        # Use scipy's randomized_svd for better performance on large matrices
        from scipy.sparse.linalg import svds
        
        # svds returns k smallest by default, so we need to get largest
        # We'll use the full SVD for small k relative to matrix size
        if k < min(matrix.shape) / 2:
            # Use randomized approach
            from sklearn.utils.extmath import randomized_svd
            U, s, Vt = randomized_svd(
                matrix, 
                n_components=k, 
                n_iter=5,
                random_state=seed
            )
        else:
            # Fall back to full SVD for small matrices or large k
            U, s, Vt = np.linalg.svd(matrix, full_matrices=False)
            U = U[:, :k]
        
        # Ensure consistent sign (first element of each column positive)
        signs = np.sign(U[0, :])
        signs[signs == 0] = 1
        U = U * signs
        
        logger.info(f"Extracted subspace of shape {U.shape}")
        return U
        
    except ImportError:
        # Fallback to numpy if sklearn not available
        logger.warning("sklearn not available, using numpy SVD")
        U, s, Vt = np.linalg.svd(matrix, full_matrices=False)
        U = U[:, :k]
        
        # Sign normalization
        signs = np.sign(U[0, :])
        signs[signs == 0] = 1
        U = U * signs
        
        return U

def compute_cosine_similarity_subspaces(
    subspace_a: np.ndarray,
    subspace_b: np.ndarray,
    method: str = "canonical"
) -> float:
    """
    Compute cosine similarity between two subspaces.
    
    Args:
        subspace_a: First subspace basis (n x k)
        subspace_b: Second subspace basis (n x k)
        method: Method for comparison - "canonical" (principal angles) or "simple" (mean cosine)
        
    Returns:
        float: Similarity score between 0 and 1
    """
    if subspace_a.shape != subspace_b.shape:
        raise ValueError(f"Subspaces must have same shape: {subspace_a.shape} vs {subspace_b.shape}")
    
    if subspace_a.shape[1] == 0:
        return 0.0
    
    # Normalize columns to unit length
    norm_a = np.linalg.norm(subspace_a, axis=0, keepdims=True)
    norm_b = np.linalg.norm(subspace_b, axis=0, keepdims=True)
    
    # Avoid division by zero
    norm_a = np.where(norm_a == 0, 1, norm_a)
    norm_b = np.where(norm_b == 0, 1, norm_b)
    
    subspace_a_norm = subspace_a / norm_a
    subspace_b_norm = subspace_b / norm_b
    
    if method == "simple":
        # Simple mean cosine similarity between corresponding vectors
        cosines = np.sum(subspace_a_norm * subspace_b_norm, axis=0)
        return float(np.mean(np.abs(cosines)))
    
    elif method == "canonical":
        # Canonical angles approach: similarity = mean of cosines of principal angles
        # Compute projection matrix
        # P = U_a^T * U_b
        projection = np.dot(subspace_a_norm.T, subspace_b_norm)
        
        # Singular values of projection are cosines of principal angles
        singular_values = np.linalg.svd(projection, compute_uv=False)
        
        # Similarity is the mean of the singular values (cosines of principal angles)
        similarity = float(np.mean(np.abs(singular_values)))
        return similarity
    
    else:
        raise ValueError(f"Unknown method: {method}. Use 'simple' or 'canonical'")

def calculate_subspace_similarities(
    aligned_matrices: Dict[str, np.ndarray],
    k: int,
    seed: int,
    reference_model: str = "bloom"
) -> Dict[str, Dict[str, float]]:
    """
    Calculate cosine similarities between subspace bases of English models vs BLOOM.
    This task MUST utilize the vocabulary mapping layer to ensure valid comparison
    across models with different vocabularies.
    
    Args:
        aligned_matrices: Dict of aligned W_U matrices (common vocab)
        k: Number of singular vectors
        seed: Random seed
        reference_model: Model to use as reference for comparison
        
    Returns:
        Dict of similarity scores between model pairs
    """
    if reference_model not in aligned_matrices:
        raise ValueError(f"Reference model {reference_model} not found in aligned matrices")
    
    # Extract SVD subspace for each model
    subspaces = {}
    for model_name, matrix in aligned_matrices.items():
        logger.info(f"Extracting subspace for {model_name}")
        subspace = extract_svd_subspace(matrix, k=k, seed=seed)
        subspaces[model_name] = subspace
    
    # Calculate similarities with reference model
    similarities = {}
    ref_subspace = subspaces[reference_model]
    
    for model_name, subspace in subspaces.items():
        if model_name == reference_model:
            continue
        
        similarity = compute_cosine_similarity_subspaces(
            ref_subspace,
            subspace,
            method="canonical"
        )
        
        pair_key = f"{reference_model}_vs_{model_name}"
        similarities[pair_key] = similarity
        logger.info(f"Similarity {pair_key}: {similarity:.4f}")
    
    # Also calculate pairwise similarities between non-reference models
    model_names = list(subspaces.keys())
    for i, model_a in enumerate(model_names):
        for model_b in model_names[i+1:]:
            if model_a == reference_model or model_b == reference_model:
                continue
            
            similarity = compute_cosine_similarity_subspaces(
                subspaces[model_a],
                subspaces[model_b],
                method="canonical"
            )
            
            pair_key = f"{model_a}_vs_{model_b}"
            similarities[pair_key] = similarity
            logger.info(f"Similarity {pair_key}: {similarity:.4f}")
    
    return similarities

def main():
    """Main entry point for the model analyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze model unembedding matrices")
    parser.add_argument('--config', type=str, default='code/config.py', help='Path to config')
    parser.add_argument('--output', type=str, default='data/processed/similarity_report.json', help='Output file')
    parser.add_argument('--k', type=int, default=100, help='Number of singular vectors')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()
    
    # Load models
    logger.info("Loading models...")
    models = load_all_models()
    
    # Create vocabulary mapping
    logger.info("Creating vocabulary mapping...")
    vocab_mappings = create_vocab_mapping(models)
    
    # Align matrices
    logger.info("Aligning matrices...")
    aligned = align_unembedding_matrices(models, vocab_mappings)
    
    # Calculate similarities
    logger.info("Calculating subspace similarities...")
    similarities = calculate_subspace_similarities(aligned, k=args.k, seed=args.seed)
    
    # Save results
    import json
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        'k': args.k,
        'seed': args.seed,
        'similarities': similarities,
        'model_stats': get_model_stats(aligned)
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return result

if __name__ == "__main__":
    main()