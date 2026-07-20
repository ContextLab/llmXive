"""
LDA Model Validator for Topic Drift Analysis.

This module implements validation logic for Latent Dirichlet Allocation (LDA) models,
specifically computing c_v coherence scores to ensure topic quality before downstream
processing. It prevents analysis of windows where topic coherence falls below the
required threshold (0.4).
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

from src.utils.logging import get_logger
from src.utils.manifest import load_reproducibility_manifest, save_reproducibility_manifest
from src.models.lda.saver import load_topic_vectors_from_proportions

# Import required scikit-learn components
try:
    from gensim import corpora, models
    from gensim.models import CoherenceModel
    GENSIM_AVAILABLE = True
except ImportError:
    GENSIM_AVAILABLE = False
    get_logger(__name__).warning("Gensim not available. Coherence calculation disabled.")

# Import from local project structure
# Note: We need to load tokenized data to compute coherence
from src.data.preprocess.tokenizer import load_preprocessed_data

logger = get_logger(__name__)

COHERENCE_THRESHOLD = 0.4


def compute_c_v_coherence(
    tokenized_documents: List[List[str]],
    topic_model: Any,
    dictionary: Optional[corpora.Dictionary] = None,
    num_top_words: int = 10
) -> float:
    """
    Compute c_v coherence score for an LDA model.

    Args:
        tokenized_documents: List of tokenized documents (list of lists of strings).
        topic_model: Trained LDA model (gensim.models.LdaModel or compatible).
        dictionary: Gensim Dictionary object. If None, will be inferred or created.
        num_top_words: Number of top words to consider for coherence calculation.

    Returns:
        float: c_v coherence score.

    Raises:
        RuntimeError: If gensim is not available or coherence calculation fails.
    """
    if not GENSIM_AVAILABLE:
        raise RuntimeError(
            "Cannot compute coherence: gensim is not installed. "
            "Please add 'gensim' to requirements.txt and install."
        )

    try:
        # Ensure we have a dictionary
        if dictionary is None:
            logger.warning("No dictionary provided, creating one from documents.")
            dictionary = corpora.Dictionary(tokenized_documents)

        # Create corpus if not already in gensim format
        if not isinstance(tokenized_documents[0], list) or not all(
            isinstance(word, str) for doc in tokenized_documents for word in doc
        ):
            # Assume documents are already in (id, freq) format or convert
            # For simplicity, assume input is list of lists of strings
            pass

        # Compute coherence
        coherence_model = CoherenceModel(
            model=topic_model,
            texts=tokenized_documents,
            dictionary=dictionary,
            coherence='c_v'
        )

        coherence_score = coherence_model.get_coherence()
        logger.info(f"Computed c_v coherence: {coherence_score:.4f}")
        return coherence_score

    except Exception as e:
        logger.error(f"Failed to compute coherence: {e}")
        raise RuntimeError(f"Coherence calculation failed: {e}")


def validate_lda_model(
    window_name: str,
    coherence_score: float,
    threshold: float = COHERENCE_THRESHOLD
) -> Tuple[bool, str]:
    """
    Validate an LDA model based on its coherence score.

    Args:
        window_name: Name/identifier of the time window.
        coherence_score: The computed c_v coherence score.
        threshold: Minimum acceptable coherence score.

    Returns:
        Tuple of (is_valid, message)
    """
    if coherence_score < threshold:
        msg = (
            f"Window '{window_name}' FAILED validation: "
            f"coherence {coherence_score:.4f} < threshold {threshold}. "
            "Downstream processing BLOCKED for this window."
        )
        logger.error(msg)
        return False, msg
    else:
        msg = (
            f"Window '{window_name}' PASSED validation: "
            f"coherence {coherence_score:.4f} >= threshold {threshold}."
        )
        logger.info(msg)
        return True, msg


def validate_and_save_results(
    window_name: str,
    coherence_score: float,
    is_valid: bool,
    output_dir: str = "results/stats",
    manifest_path: str = "results/manifest.json"
) -> Dict[str, Any]:
    """
    Validate results and save to statistics file and update manifest.

    Args:
        window_name: Name of the time window.
        coherence_score: Computed coherence score.
        is_valid: Whether the model passed validation.
        output_dir: Directory to save validation results.
        manifest_path: Path to the reproducibility manifest.

    Returns:
        Dictionary containing validation results.
    """
    results = {
        "window": window_name,
        "coherence_score": coherence_score,
        "threshold": COHERENCE_THRESHOLD,
        "is_valid": is_valid,
        "status": "passed" if is_valid else "failed"
    }

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Save individual window results
    results_file = Path(output_dir) / f"validation_{window_name}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Saved validation results to {results_file}")

    # Update manifest if it exists
    if Path(manifest_path).exists():
        try:
            manifest = load_reproducibility_manifest(manifest_path)
            if "validation_results" not in manifest:
                manifest["validation_results"] = {}

            manifest["validation_results"][window_name] = {
                "coherence_score": coherence_score,
                "is_valid": is_valid,
                "status": "passed" if is_valid else "failed"
            }

            save_reproducibility_manifest(manifest, manifest_path)
            logger.info(f"Updated manifest at {manifest_path}")
        except Exception as e:
            logger.error(f"Failed to update manifest: {e}")
    else:
        logger.warning(f"Manifest not found at {manifest_path}, skipping update.")

    return results


def main():
    """
    Main entry point for running the validator on all windows.

    This function:
    1. Loads processed data for each of the 5 windows
    2. Loads topic models (from T020)
    3. Computes c_v coherence for each window
    4. Validates against threshold (0.4)
    5. Blocks downstream processing if validation fails
    6. Saves results to results/stats/ and updates manifest
    """
    logger.info("Starting LDA model validation for all windows.")

    windows = [
        "2000-2004",
        "2005-2009",
        "2010-2014",
        "2015-2019",
        "2020-2024"
    ]

    all_results = {}
    any_failed = False

    for window in windows:
        logger.info(f"Processing window: {window}")

        try:
            # Load tokenized data for this window
            # Path structure: data/processed/processed_{window}.csv
            data_path = Path(f"data/processed/processed_{window}.csv")
            if not data_path.exists():
                logger.error(f"Data file not found: {data_path}")
                all_results[window] = {
                    "status": "error",
                    "message": f"Data file not found: {data_path}"
                }
                any_failed = True
                continue

            # Load preprocessed data
            tokenized_docs = load_preprocessed_data(data_path)
            logger.info(f"Loaded {len(tokenized_docs)} documents for {window}")

            if len(tokenized_docs) == 0:
                logger.error(f"No documents found for window {window}")
                all_results[window] = {
                    "status": "error",
                    "message": "No documents found"
                }
                any_failed = True
                continue

            # Load topic model for this window
            # Expected path: results/stats/topic_vectors_{window}.json
            # We need to reconstruct the model or load it from saved state
            # For now, we assume the model was saved in a way that allows reloading
            # This depends on how T020 saves the models

            model_path = Path(f"results/stats/lda_model_{window}.pkl")
            if not model_path.exists():
                # Alternative: try to load from topic vectors and reconstruct
                logger.warning(f"Model file not found: {model_path}")
                # We'll need to handle this case - perhaps the model wasn't saved
                # In a real scenario, T020 should save the model
                all_results[window] = {
                    "status": "error",
                    "message": f"Model file not found: {model_path}"
                }
                any_failed = True
                continue

            # Load the model (implementation depends on how it was saved)
            # This is a placeholder - actual implementation depends on T020's output
            try:
                import pickle
                with open(model_path, 'rb') as f:
                    topic_model = pickle.load(f)
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                all_results[window] = {
                    "status": "error",
                    "message": f"Failed to load model: {e}"
                }
                any_failed = True
                continue

            # Create dictionary from documents
            dictionary = corpora.Dictionary(tokenized_docs)

            # Compute coherence
            coherence = compute_c_v_coherence(tokenized_docs, topic_model, dictionary)

            # Validate
            is_valid, message = validate_lda_model(window, coherence)

            # Save results
            results = validate_and_save_results(window, coherence, is_valid)
            all_results[window] = results

            if not is_valid:
                any_failed = True

        except Exception as e:
            logger.error(f"Error processing window {window}: {e}")
            all_results[window] = {
                "status": "error",
                "message": str(e)
            }
            any_failed = True

    # Final summary
    if any_failed:
        logger.error("VALIDATION FAILED: One or more windows did not meet coherence threshold.")
        logger.error("Downstream processing is BLOCKED for failed windows.")
    else:
        logger.info("VALIDATION SUCCESS: All windows passed coherence threshold.")

    # Save summary
    summary = {
        "total_windows": len(windows),
        "passed": sum(1 for r in all_results.values() if r.get("is_valid") == True),
        "failed": sum(1 for r in all_results.values() if r.get("is_valid") == False),
        "errors": sum(1 for r in all_results.values() if r.get("status") == "error"),
        "windows": all_results
    }

    summary_path = Path("results/stats/validation_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Validation summary saved to {summary_path}")

    return summary