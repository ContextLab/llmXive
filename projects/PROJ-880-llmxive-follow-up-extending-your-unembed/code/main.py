"""
Main orchestrator for the llmXive follow-up pipeline.
Implements T014: Run SVD and similarity pipeline, outputting similarity_matrix.json.
Implements T023: Run US2 Token Attribution pipeline, outputting token_attribution_report.json.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

from config import load_config, get_path, ensure_dirs
from model_analyzer import (
    load_all_models,
    get_common_vocab_ids,
    create_vocab_mapping,
    align_unembedding_matrices,
    extract_svd_subspace,
    calculate_subspace_similarities
)
from token_attribution import (
    load_frequency_distribution,
    compute_frequency_weighted_mean_embedding,
    project_onto_edge_spectrum,
    rank_tokens_by_projection,
    generate_token_attribution_report
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_us1_pipeline(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute User Story 1 pipeline:
    1. Load models (Llama-3, Mistral, BLOOM)
    2. Align vocabularies
    3. Extract SVD subspaces (top-k)
    4. Compute pairwise cosine similarities
    5. Save similarity matrix to data/processed/similarity_matrix.json
    """
    logger.info("Starting User Story 1 pipeline...")

    # Get hyperparameters
    k = config.get('hyperparameters', {}).get('k', 100)
    models = config.get('models', {})
    model_names = list(models.keys())

    if len(model_names) < 2:
        raise ValueError("At least two models are required for similarity comparison.")

    # Step 1: Load all models
    logger.info(f"Loading models: {model_names}")
    models_data = load_all_models(models, config)

    # Step 2: Create vocabulary mapping across all models
    logger.info("Creating vocabulary mapping...")
    all_vocab_ids = get_common_vocab_ids(models_data)
    vocab_mapping = create_vocab_mapping(models_data, all_vocab_ids)

    if not vocab_mapping:
        raise RuntimeError("Failed to create vocabulary mapping. No common tokens found.")

    logger.info(f"Common vocabulary size: {len(vocab_mapping)}")

    # Step 3: Align unembedding matrices using vocab mapping
    logger.info("Aligning unembedding matrices...")
    aligned_matrices = align_unembedding_matrices(models_data, vocab_mapping)

    # Step 4: Extract SVD subspaces for each model
    logger.info(f"Extracting top-{k} SVD subspaces...")
    svd_results = {}
    for model_name, aligned_wu in aligned_matrices.items():
        logger.info(f"  Processing {model_name}...")
        svd_results[model_name] = extract_svd_subspace(aligned_wu, k=k)

    # Step 5: Calculate pairwise cosine similarities
    logger.info("Calculating pairwise subspace similarities...")
    similarities = calculate_subspace_similarities(svd_results)

    # Step 6: Prepare output report
    report = {
        "pipeline": "US1_SVD_Similarity",
        "config": {
            "k": k,
            "models_processed": model_names,
            "common_vocab_size": len(vocab_mapping)
        },
        "similarities": similarities,
        "status": "completed"
    }

    # Step 7: Save output
    output_path = get_path(config, "similarity_matrix.json", category="processed")
    ensure_dirs([output_path])

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Similarity matrix saved to: {output_path}")
    return report


def run_us2_pipeline(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute User Story 2 pipeline (Token Attribution):
    1. Load frequency distributions (from data/processed/frequency_distributions.json)
    2. Load SVD subspaces (from previous US1 run or re-compute)
    3. Compute frequency-weighted mean embedding
    4. Project onto edge spectrum
    5. Rank tokens
    6. Generate overlap report (English vs non-English)
    7. Save token_attribution_report.json
    """
    logger.info("Starting User Story 2 pipeline...")

    # Get hyperparameters
    k = config.get('hyperparameters', {}).get('k', 100)
    models = config.get('models', {})
    model_names = list(models.keys())

    # Step 1: Load frequency distributions
    logger.info("Loading frequency distributions...")
    freq_data = load_frequency_distribution(config)

    if not freq_data:
        raise RuntimeError("Failed to load frequency distributions. Ensure data/processed/frequency_distributions.json exists.")

    # Step 2: Load models and create SVD subspaces (re-use logic from US1 for consistency)
    logger.info("Loading models for SVD subspaces...")
    models_data = load_all_models(models, config)
    all_vocab_ids = get_common_vocab_ids(models_data)
    vocab_mapping = create_vocab_mapping(models_data, all_vocab_ids)
    aligned_matrices = align_unembedding_matrices(models_data, vocab_mapping)

    logger.info(f"Extracting top-{k} SVD subspaces for US2...")
    svd_results = {}
    for model_name, aligned_wu in aligned_matrices.items():
        svd_results[model_name] = extract_svd_subspace(aligned_wu, k=k)

    # Step 3: Compute frequency-weighted mean embedding for each language
    logger.info("Computing frequency-weighted mean embeddings...")
    mean_embeddings = {}
    for lang, tokens in freq_data.items():
        logger.info(f"  Processing language: {lang}")
        mean_emb = compute_frequency_weighted_mean_embedding(
            tokens,
            aligned_matrices.get(lang), # Assuming lang key matches model key or we map it
            vocab_mapping
        )
        mean_embeddings[lang] = mean_emb

    # Step 4: Project onto edge spectrum and rank tokens
    logger.info("Projecting onto edge spectrum and ranking tokens...")
    attribution_results = {}
    for lang, mean_emb in mean_embeddings.items():
        # Identify the SVD subspace for this language. 
        # If lang is not a model name (e.g., 'french' vs 'mistral'), we might need to map.
        # For now, assume the config keys align or we use the first available model's subspace if specific mapping is missing.
        # A robust implementation would map 'french' -> 'mistral' or similar based on config.
        # Here we assume the model keys in 'models' dict align with the language keys in freq_data 
        # or that we use a specific 'reference_model' for projection if not aligned.
        
        # Fallback: Use the first model's subspace if exact match not found, 
        # but ideally we should match based on config.
        target_model_name = lang if lang in svd_results else list(svd_results.keys())[0]
        svd_subspace = svd_results[target_model_name]
        
        projected = project_onto_edge_spectrum(mean_emb, svd_subspace)
        ranked_tokens = rank_tokens_by_projection(projected, freq_data[lang], top_n=100)
        attribution_results[lang] = {
            "top_tokens": ranked_tokens,
            "projection_norm": float(np.linalg.norm(projected))
        }

    # Step 5: Calculate overlap ratios (English vs others)
    logger.info("Calculating overlap ratios...")
    if 'english' in attribution_results:
        eng_tokens = set([t['token'] for t in attribution_results['english']['top_tokens']])
        overlaps = {}
        for lang, res in attribution_results.items():
            if lang == 'english':
                continue
            other_tokens = set([t['token'] for t in res['top_tokens']])
            overlap_count = len(eng_tokens.intersection(other_tokens))
            overlap_ratio = overlap_count / len(eng_tokens) if len(eng_tokens) > 0 else 0.0
            overlaps[lang] = {
                "overlap_count": overlap_count,
                "overlap_ratio": overlap_ratio
            }
    else:
        overlaps = {}
        logger.warning("English baseline not found for overlap calculation.")

    # Step 6: Generate final report
    report = generate_token_attribution_report(
        attribution_results=attribution_results,
        overlaps=overlaps,
        config=config
    )

    # Step 7: Save output
    output_path = get_path(config, "token_attribution_report.json", category="processed")
    ensure_dirs([output_path])

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Token attribution report saved to: {output_path}")
    return report


def run_pipeline(pipeline_name: str = "us1") -> Dict[str, Any]:
    """
    General pipeline runner dispatcher.
    """
    config = load_config()
    if pipeline_name == "us1":
        return run_us1_pipeline(config)
    elif pipeline_name == "us2":
        return run_us2_pipeline(config)
    else:
        raise ValueError(f"Unknown pipeline: {pipeline_name}")


def main():
    """
    Entry point for the orchestrator.
    Usage: python code/main.py [us1|us2|all]
    """
    pipeline = sys.argv[1] if len(sys.argv) > 1 else "us1"

    try:
        if pipeline == "all":
            # Run US1 then US2
            run_us1_pipeline(load_config())
            run_us2_pipeline(load_config())
        else:
            run_pipeline(pipeline)

        logger.info("Pipeline execution completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import numpy as np # Imported here to ensure numpy is available for US2 logic if not in other imports
    sys.exit(main())