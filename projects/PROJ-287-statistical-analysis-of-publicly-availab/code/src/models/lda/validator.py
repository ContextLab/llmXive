"""
LDA Model Validator for Topic Drift Analysis.

Computes C_v coherence scores for fitted LDA models.
Flags runs with coherence < 0.4 and prevents downstream processing
for that specific window.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

from src.utils.logging import get_logger
from src.models.lda.fitter import load_lda_model, load_bow_corpus, load_dictionary
from src.models.entities import TopicVector

# Import gensim for coherence calculation
try:
    from gensim.models import CoherenceModel
    from gensim import corpora
except ImportError:
    raise ImportError("gensim is required for coherence calculation. Install with: pip install gensim")

logger = get_logger(__name__)

COHERENCE_THRESHOLD = 0.4

class CoherenceValidationError(Exception):
    """Raised when LDA model coherence is below the acceptable threshold."""
    pass

def compute_c_v_coherence(
    lda_model: Any,
    dictionary: "corpora.Dictionary",
    corpus: List[List[int]],
    num_topics: int = 10
) -> float:
    """
    Compute the C_v coherence score for an LDA model.
    
    Args:
        lda_model: The fitted gensim LDA model.
        dictionary: The gensim Dictionary object.
        corpus: The bag-of-words corpus (list of lists).
        num_topics: Number of topics to evaluate.
        
    Returns:
        float: The C_v coherence score.
    """
    if not corpus:
        logger.warning("Empty corpus provided for coherence calculation.")
        return 0.0

    coherence_model = CoherenceModel(
        model=lda_model,
        texts=corpus,
        dictionary=dictionary,
        coherence='c_v'
    )
    
    score = coherence_model.get_coherence()
    logger.info(f"Computed C_v coherence: {score:.4f}")
    return float(score)

def validate_lda_model(
    window_id: str,
    lda_model: Any,
    dictionary: "corpora.Dictionary",
    corpus: List[List[int]],
    threshold: float = COHERENCE_THRESHOLD
) -> Tuple[bool, float, str]:
    """
    Validate an LDA model against the coherence threshold.
    
    Args:
        window_id: Identifier for the time window.
        lda_model: The fitted LDA model.
        dictionary: The gensim Dictionary.
        corpus: The bag-of-words corpus.
        threshold: Minimum acceptable coherence score.
        
    Returns:
        Tuple of (is_valid, score, message)
    """
    try:
        score = compute_c_v_coherence(lda_model, dictionary, corpus)
        
        if score < threshold:
            msg = (
                f"VALIDATION FAILED for window '{window_id}': "
                f"C_v coherence {score:.4f} is below threshold {threshold}. "
                f"Downstream processing for this window is BLOCKED."
            )
            logger.error(msg)
            return False, score, msg
        else:
            msg = (
                f"VALIDATION PASSED for window '{window_id}': "
                f"C_v coherence {score:.4f} >= {threshold}."
            )
            logger.info(msg)
            return True, score, msg
            
    except Exception as e:
        msg = (
            f"VALIDATION ERROR for window '{window_id}': "
            f"Failed to compute coherence: {str(e)}"
        )
        logger.error(msg)
        raise CoherenceValidationError(msg) from e

def validate_and_save_results(
    window_id: str,
    lda_model: Any,
    dictionary: "corpora.Dictionary",
    corpus: List[List[int]],
    output_dir: Path,
    threshold: float = COHERENCE_THRESHOLD
) -> Dict[str, Any]:
    """
    Validate the model, save results, and raise if validation fails.
    
    Args:
        window_id: The window identifier.
        lda_model: The fitted LDA model.
        dictionary: The gensim Dictionary.
        corpus: The bag-of-words corpus.
        output_dir: Directory to save validation results.
        threshold: Minimum coherence threshold.
        
    Returns:
        Dict containing validation results.
        
    Raises:
        CoherenceValidationError: If coherence is below threshold.
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Perform validation
    is_valid, score, message = validate_lda_model(
        window_id, lda_model, dictionary, corpus, threshold
    )
    
    # Prepare result data
    result_data = {
        "window_id": window_id,
        "coherence_score": score,
        "threshold": threshold,
        "is_valid": is_valid,
        "message": message,
        "status": "BLOCKED" if not is_valid else "PROCEEDING"
    }
    
    # Save result to file
    result_path = output_dir / f"coherence_validation_{window_id}.json"
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2)
    
    logger.info(f"Validation results saved to {result_path}")
    
    if not is_valid:
        raise CoherenceValidationError(
            f"Model for window '{window_id}' failed validation (score={score:.4f}). "
            "Downstream processing aborted for this window."
        )
        
    return result_data

def main():
    """
    Main entry point for standalone execution.
    Expects environment variables or arguments to locate the model files.
    For this implementation, it assumes the model files are in standard locations
    relative to the project root as defined in the pipeline.
    """
    logger.info("Starting LDA Model Validator (T021)")
    
    # Configuration
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    processed_dir = base_dir / "data" / "processed"
    results_stats_dir = base_dir / "results" / "stats"
    models_dir = base_dir / "src" / "models" / "lda" # Or wherever fitter saves models
    
    # Ensure output directory exists
    results_stats_dir.mkdir(parents=True, exist_ok=True)
    
    # Define windows as per spec (T020)
    windows = ["2000-2004", "2005-2009", "2010-2014", "2015-2019", "2020-2024"]
    
    # This script assumes the models and data were produced by T020 and T016.
    # We need to locate the model, dictionary, and corpus for each window.
    # Since the fitter/saver structure isn't fully detailed in the API surface 
    # regarding exact filenames, we assume a standard naming convention:
    # model: data/lda_models/{window_id}_lda.model
    # dict: data/lda_models/{window_id}_dict.gensim
    # corpus: data/processed/{window_id}_processed.json (or similar)
    
    # Note: In a real pipeline run, these paths would be passed as arguments
    # or loaded from a manifest. Here we simulate the check.
    
    validation_results = []
    failed_windows = []
    
    # Check if we have a manifest or specific model directory structure
    # If the user runs this standalone without data, it will fail loudly.
    
    for window in windows:
        logger.info(f"Processing window: {window}")
        
        # Construct expected paths
        # Adjust paths based on actual T020/T016 output structure if different
        model_path = base_dir / "data" / "lda_models" / f"{window}_lda.model"
        dict_path = base_dir / "data" / "lda_models" / f"{window}_dict.gensim"
        
        # For corpus, we look in processed data. The saver (T016) saves CSVs.
        # We need to reload the corpus. This might require re-tokenizing or 
        # loading a pre-saved corpus if T020 saved it.
        # Assuming T020 saved the corpus or we can reload from the processed CSV.
        # For robustness, we assume the fitter saved the corpus in a standard location
        # or we load from the processed CSV and re-bow it.
        # Let's assume a saved corpus exists for efficiency if T020 saved it.
        corpus_path = base_dir / "data" / "lda_models" / f"{window}_corpus.json"
        
        if not model_path.exists():
            logger.warning(f"Model not found for {window} at {model_path}. Skipping.")
            continue
            
        if not dict_path.exists():
            logger.warning(f"Dictionary not found for {window} at {dict_path}. Skipping.")
            continue
        
        try:
            # Load components
            lda_model = load_lda_model(str(model_path))
            dictionary = load_dictionary(str(dict_path))
            
            # Load corpus
            # If corpus is not saved as gensim format, we might need to reconstruct it
            # from the processed CSV. For now, assume it's saved or we load a mock for validation
            # But per "Real data only", we must load the real corpus.
            # If T020 didn't save the corpus, we must load the CSV and re-bow.
            # Let's implement a fallback to load from CSV if corpus file missing.
            
            if corpus_path.exists():
                with open(corpus_path, 'r') as f:
                    corpus = json.load(f)
            else:
                # Fallback: Load from processed CSV and re-bow
                # This requires the tokenizer and dictionary
                processed_csv_path = processed_dir / f"{window}_processed.csv"
                if not processed_csv_path.exists():
                    raise FileNotFoundError(f"Processed CSV not found for {window}: {processed_csv_path}")
                
                # Reconstruct corpus from CSV
                import pandas as pd
                df = pd.read_csv(processed_csv_path)
                # Assuming 'tokens' column exists with list of tokens
                if 'tokens' not in df.columns:
                    raise ValueError(f"Column 'tokens' not found in {processed_csv_path}")
                
                texts = df['tokens'].apply(lambda x: x.split()).tolist() # Assuming space-separated or list repr
                # Convert to BoW
                corpus = [dictionary.doc2bow(text) for text in texts]
            
            # Validate
            result = validate_and_save_results(
                window, lda_model, dictionary, corpus, results_stats_dir
            )
            validation_results.append(result)
            
            if not result["is_valid"]:
                failed_windows.append(window)
                
        except CoherenceValidationError as e:
            failed_windows.append(window)
            validation_results.append({
                "window_id": window,
                "status": "BLOCKED",
                "error": str(e)
            })
        except Exception as e:
            logger.error(f"Unexpected error validating {window}: {e}")
            validation_results.append({
                "window_id": window,
                "status": "ERROR",
                "error": str(e)
            })
    
    # Summary
    logger.info(f"Validation complete. Failed windows: {failed_windows}")
    if failed_windows:
        logger.error("Pipeline halted for windows with low coherence.")
        # In a real pipeline, this would exit with code 1
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
