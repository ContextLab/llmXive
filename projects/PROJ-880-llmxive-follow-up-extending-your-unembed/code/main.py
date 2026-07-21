import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List
from config import load_config, get_path, ensure_dirs
from model_analyzer import calculate_subspace_similarities, load_all_models, get_common_vocab_ids, create_vocab_mapping, align_unembedding_matrices, extract_svd_subspace

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_us1_pipeline(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrates the User Story 1 pipeline:
    1. Loads unembedding matrices for Llama-3, Mistral, and BLOOM.
    2. Aligns vocabularies across models.
    3. Computes SVD to extract edge spectrum subspaces (top-k singular vectors).
    4. Calculates cosine similarity between subspaces.
    5. Outputs results to data/processed/similarity_matrix.json.
    """
    ensure_dirs(config)
    
    results = {}
    output_path = get_path(config, 'similarity_matrix_path')
    ensure_dirs(config, paths=[output_path])

    try:
        # Step 1: Load Models
        logger.info("Loading models (Llama-3, Mistral, BLOOM)...")
        models = load_all_models(config)
        if not models:
            raise ValueError("No models were loaded. Check model paths in config.")

        # Step 2: Vocabulary Mapping
        logger.info("Computing common vocabulary intersection...")
        vocab_ids = get_common_vocab_ids(models)
        if len(vocab_ids) == 0:
            raise ValueError("No common vocabulary found between models.")
        
        # Create mapping for alignment
        vocab_mapping = create_vocab_mapping(models, vocab_ids)
        
        # Align matrices
        aligned_matrices = {}
        for model_name, (matrix, tokenizer) in models.items():
            aligned_matrices[model_name] = align_unembedding_matrices(matrix, vocab_mapping, model_name)

        # Step 3: SVD Extraction
        logger.info("Extracting SVD subspaces (top-k)...")
        k = config.get('hyperparameters', {}).get('k', 100)
        svd_results = {}
        for model_name, matrix in aligned_matrices.items():
            logger.info(f"Computing SVD for {model_name}...")
            U, S, Vt = extract_svd_subspace(matrix, k=k)
            svd_results[model_name] = {
                'U': U, # Shape: (vocab_common, k)
                'S': S,
                'Vt': Vt
            }

        # Step 4: Compute Similarities
        logger.info("Calculating pairwise cosine similarities...")
        model_names = list(svd_results.keys())
        pairs = []
        
        for i in range(len(model_names)):
            for j in range(i + 1, len(model_names)):
                name_a = model_names[i]
                name_b = model_names[j]
                
                U_a = svd_results[name_a]['U']
                U_b = svd_results[name_b]['U']
                
                similarity = calculate_subspace_similarities(U_a, U_b)
                
                pairs.append({
                    "model_a": name_a,
                    "model_b": name_b,
                    "cosine_similarity": float(similarity)
                })
                logger.info(f"Similarity {name_a} vs {name_b}: {similarity:.6f}")

        # Step 5: Write Output
        output_data = {"pairs": pairs}
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)

        results['status'] = 'success'
        results['output_file'] = str(output_path)
        results['pairs_count'] = len(pairs)
        
        logger.info(f"US1 Pipeline completed successfully. Output: {output_path}")

    except Exception as e:
        logger.error(f"US1 Pipeline failed: {e}", exc_info=True)
        results['status'] = 'failed'
        results['error'] = str(e)

    return results

def run_us3_pipeline(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrates the User Story 3 pipeline:
    1. Runs the statistical permutation test.
    2. Runs the external WALS validation.
    3. Saves results to data/processed/ with appropriate error handling for missing data.
    """
    # Note: This function is kept for compatibility with T030/T035 requirements
    # but T014 specifically focuses on US1 execution via main.py.
    # The actual US3 implementation is handled by statistical_test.py and external_validation.py
    # and can be invoked via --us3 flag if implemented.
    return {'status': 'skipped', 'reason': 'T014 focuses on US1 execution'}

def main():
    """
    Main entry point for the llmXive pipeline.
    Supports running the full pipeline or specific user story pipelines via CLI args.
    
    Usage:
      python code/main.py --us1       # Run SVD and similarity pipeline (T014)
      python code/main.py --us3       # Run statistical validation (T030)
      python code/main.py             # Default: Run US1 (MVP)
    """
    config = load_config()
    
    # Simple CLI argument parsing for pipeline selection
    run_us1 = '--us1' in sys.argv
    run_us3 = '--us3' in sys.argv
    
    if not any([run_us1, run_us3]):
        # Default: run US1 (MVP) as per T014 requirement
        run_us1 = True

    overall_status = {'status': 'success', 'details': []}

    if run_us1:
        logger.info("Running User Story 1 pipeline (SVD & Similarity)...")
        us1_results = run_us1_pipeline(config)
        overall_status['details'].append({'story': 'US1', 'results': us1_results})
        if us1_results.get('status') == 'failed':
            overall_status['status'] = 'partial_failure'
            logger.error("US1 pipeline failed.")

    if run_us3:
        logger.info("Running User Story 3 pipeline (Statistical Validation)...")
        # Placeholder for US3 execution if dependencies were fully resolved in this task context
        # In a full run, this would call statistical_test and external_validation
        us3_results = run_us3_pipeline(config)
        overall_status['details'].append({'story': 'US3', 'results': us3_results})

    # Save overall run summary
    summary_path = get_path(config, 'run_summary_path')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(overall_status, f, indent=2)

    logger.info("Pipeline execution finished.")
    return 0 if overall_status['status'] == 'success' else 1

if __name__ == '__main__':
    sys.exit(main())
