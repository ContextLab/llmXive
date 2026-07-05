"""
LDA Model Validator for Topic Drift Analysis.

This module computes the c_v coherence score for LDA models and validates
them against a minimum threshold to ensure topic quality before downstream
processing.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
from gensim import corpora, models
from gensim.models.coherencemodel import CoherenceModel

from src.utils.logging import get_logger
from src.utils.config import get_config_dict

# Configure module logger
logger = get_logger(__name__)

# Default coherence threshold
DEFAULT_COHERENCE_THRESHOLD = 0.4
DEFAULT_NUM_TOPICS = 10


def compute_c_v_coherence(
    lda_model: models.LdaModel,
    dictionary: corpora.Dictionary,
    corpus: List[List[int]],
    num_topics: Optional[int] = None
) -> float:
    """
    Compute the c_v coherence score for an LDA model.

    Args:
        lda_model: The trained LDA model.
        dictionary: The Gensim dictionary used for training.
        corpus: The Gensim corpus (list of bag-of-words vectors).
        num_topics: Optional override for the number of topics. Uses model's num_topics if None.

    Returns:
        float: The c_v coherence score.

    Raises:
        ValueError: If the model or corpus is invalid.
    """
    if lda_model is None:
        raise ValueError("LDA model cannot be None")
    if dictionary is None:
        raise ValueError("Dictionary cannot be None")
    if corpus is None or len(corpus) == 0:
        raise ValueError("Corpus cannot be empty")

    if num_topics is None:
        num_topics = lda_model.num_topics

    try:
        coherence_model = CoherenceModel(
            model=lda_model,
            texts=corpus,
            dictionary=dictionary,
            coherence='c_v'
        )
        coherence_score = coherence_model.get_coherence()
        logger.info(f"Computed c_v coherence score: {coherence_score:.4f}")
        return float(coherence_score)
    except Exception as e:
        logger.error(f"Error computing coherence score: {e}", exc_info=True)
        raise


def validate_lda_model(
    lda_model: models.LdaModel,
    dictionary: corpora.Dictionary,
    corpus: List[List[int]],
    threshold: float = DEFAULT_COHERENCE_THRESHOLD,
    window_name: str = "unknown"
) -> Dict[str, Any]:
    """
    Validate an LDA model against the coherence threshold.

    Args:
        lda_model: The trained LDA model.
        dictionary: The Gensim dictionary.
        corpus: The Gensim corpus.
        threshold: Minimum acceptable coherence score.
        window_name: Name of the time window for logging.

    Returns:
        Dict containing validation results:
            - 'valid': bool indicating if the model passes validation
            - 'coherence_score': float score
            - 'threshold': float threshold used
            - 'window': str window name
            - 'num_topics': int number of topics
            - 'message': str status message
    """
    logger.info(f"Validating LDA model for window: {window_name}")

    result = {
        'window': window_name,
        'valid': False,
        'coherence_score': None,
        'threshold': threshold,
        'num_topics': lda_model.num_topics,
        'message': ''
    }

    try:
        coherence_score = compute_c_v_coherence(lda_model, dictionary, corpus)
        result['coherence_score'] = coherence_score

        if coherence_score >= threshold:
            result['valid'] = True
            result['message'] = f"Model passed validation (score: {coherence_score:.4f} >= {threshold})"
            logger.info(f"Validation PASSED for {window_name}: {result['message']}")
        else:
            result['valid'] = False
            result['message'] = f"Model FAILED validation (score: {coherence_score:.4f} < {threshold})"
            logger.warning(f"Validation FAILED for {window_name}: {result['message']}")

    except Exception as e:
        result['message'] = f"Validation ERROR: {str(e)}"
        logger.error(f"Validation ERROR for {window_name}: {e}", exc_info=True)

    return result


def validate_and_save_results(
    validation_results: List[Dict[str, Any]],
    output_path: str,
    fail_fast: bool = True
) -> bool:
    """
    Save validation results to a JSON file and determine if processing should continue.

    Args:
        validation_results: List of validation result dictionaries.
        output_path: Path to save the JSON results file.
        fail_fast: If True, raises an exception if any model fails validation.

    Returns:
        bool: True if all models passed (or fail_fast is False), False if any failed.

    Raises:
        RuntimeError: If fail_fast is True and any model failed validation.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2, ensure_ascii=False)

    logger.info(f"Validation results saved to {output_file}")

    # Check for failures
    failed_windows = [r['window'] for r in validation_results if not r['valid']]

    if failed_windows:
        error_msg = f"Validation failed for windows: {', '.join(failed_windows)}"
        logger.error(error_msg)

        if fail_fast:
            raise RuntimeError(error_msg)
        return False

    logger.info("All windows passed validation")
    return True


def main():
    """
    Main entry point for standalone validation execution.
    This function expects pre-computed LDA models, dictionaries, and corpora
    to be available in the data/processed directory structure.
    """
    logger.info("Starting LDA model validation process")

    config = get_config_dict()
    coherence_threshold = config.get('coherence_threshold', DEFAULT_COHERENCE_THRESHOLD)
    windows = config.get('windows', ['2000-2004', '2005-2009', '2010-2014', '2015-2019', '2020-2024'])

    # Define paths
    base_path = Path(config.get('data_path', 'data/processed'))
    results_path = Path(config.get('results_path', 'results/stats'))
    validation_output = results_path / 'validation_results.json'

    all_results = []
    failed_windows = []

    for window in windows:
        window_path = base_path / window
        if not window_path.exists():
            logger.warning(f"Window directory not found: {window_path}. Skipping.")
            continue

        # Load model, dictionary, and corpus
        model_path = window_path / 'lda_model.pkl'
        dict_path = window_path / 'dictionary.gensim'
        corpus_path = window_path / 'corpus.gensim'

        if not all(p.exists() for p in [model_path, dict_path, corpus_path]):
            logger.warning(f"Missing model artifacts for window {window}. Skipping.")
            continue

        try:
            # Load artifacts
            lda_model = models.LdaModel.load(str(model_path))
            dictionary = corpora.Dictionary.load(str(dict_path))
            corpus = corpora.MmCorpus(str(corpus_path))
            corpus_list = list(corpus)

            # Validate
            result = validate_lda_model(
                lda_model,
                dictionary,
                corpus_list,
                threshold=coherence_threshold,
                window_name=window
            )
            all_results.append(result)

            if not result['valid']:
                failed_windows.append(window)

        except Exception as e:
            logger.error(f"Error processing window {window}: {e}", exc_info=True)
            all_results.append({
                'window': window,
                'valid': False,
                'coherence_score': None,
                'threshold': coherence_threshold,
                'num_topics': None,
                'message': f"Processing error: {str(e)}"
            })
            failed_windows.append(window)

    # Save results
    if all_results:
        validate_and_save_results(all_results, str(validation_output), fail_fast=False)

    # Final status
    if failed_windows:
        logger.error(f"Final status: {len(failed_windows)} window(s) failed validation.")
        # In a real pipeline, this would trigger a halt of downstream processing
        # For this script, we log and exit with error code
        exit(1)
    else:
        logger.info("Final status: All windows passed validation.")
        exit(0)


if __name__ == '__main__':
    main()
