import os
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np

from datasets import load_dataset
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from hdbscan import HDBSCAN

from code.config import (
    PROJECT_ROOT,
    PROCESSED_DIR,
    RESULTS_DIR,
    RANDOM_SEED,
    MAX_DOCS,
    BERTOPIC_MIN_CLUSTER_SIZE,
    BERTOPIC_WINDOW_SIZE,
    BERTOPIC_MAX_MEMORY_MB,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_corpus_for_bertopic() -> List[str]:
    """
    Load the HotpotQA corpus for BERTopic processing.
    Returns a list of document texts (abstracts/summaries).
    """
    logger.info("Loading HotpotQA corpus for BERTopic...")
    
    try:
        # Load the fullwiki split as per project specs
        dataset = load_dataset("hotpot_qa", "fullwiki", split="train")
        
        # Extract text from 'question' and 'answer' or 'context' if available
        # HotpotQA structure: questions, answers, context (list of dicts)
        # We construct a document text from the question and the context snippets
        corpus = []
        
        count = 0
        for item in dataset:
            if count >= MAX_DOCS:
                break
            
            question = item.get("question", "")
            # Construct a document representation: Question + Context
            # Context is a list of [title, paragraph_text]
            context_texts = []
            for ctx in item.get("context", []):
                if isinstance(ctx, list) and len(ctx) >= 2:
                    context_texts.append(f"{ctx[0]}: {ctx[1]}")
            
            doc_text = f"{question} {' '.join(context_texts)}"
            
            if doc_text.strip():
                corpus.append(doc_text)
                count += 1
            else:
                logger.warning(f"Skipping empty document at index {count}")
        
        logger.info(f"Loaded {len(corpus)} documents for BERTopic (max {MAX_DOCS}).")
        return corpus

    except Exception as e:
        logger.error(f"Failed to load HotpotQA corpus: {e}")
        raise


def run_bertopic_model(
    corpus: List[str],
    min_cluster_size: int = BERTOPIC_MIN_CLUSTER_SIZE,
    window_size: int = BERTOPIC_WINDOW_SIZE,
    max_memory_mb: int = BERTOPIC_MAX_MEMORY_MB,
    reduce_corpus: bool = False
) -> Tuple[Optional[BERTopic], Dict[str, Any]]:
    """
    Run BERTopic on the corpus with memory pressure fallback.
    
    Fallback Mechanism:
    If memory pressure is detected (simulated by corpus size or explicit flag),
    the function reduces the effective corpus size and window size to ensure
    execution within CPU constraints.
    
    Args:
        corpus: List of document texts.
        min_cluster_size: Minimum size for a cluster.
        window_size: Window size for n-gram vectorization.
        max_memory_mb: Estimated max memory in MB allowed.
        reduce_corpus: Force reduction of corpus size.
    
    Returns:
        Tuple of (trained BERTopic model, metadata dict)
    """
    logger.info(f"Starting BERTopic run with {len(corpus)} documents.")
    
    # Fallback Logic: Reduce resources if corpus is too large or forced
    effective_corpus = corpus
    effective_window = window_size
    effective_min_cluster = min_cluster_size
    reduced = False

    # Heuristic: If corpus > 300 docs, reduce to 300 to save RAM
    if len(corpus) > 300 or reduce_corpus:
        logger.warning(f"Corpus size ({len(corpus)}) exceeds safe threshold. Reducing to 300.")
        effective_corpus = corpus[:300]
        effective_window = max(2, window_size - 2) # Reduce n-gram window
        effective_min_cluster = max(5, min_cluster_size - 5) # Larger clusters, fewer topics
        reduced = True

    # Heuristic: If window is large, reduce it to save memory in vectorizer
    if effective_window > 5:
        logger.warning(f"Window size {effective_window} is large. Reducing to 3.")
        effective_window = 3
        reduced = True

    if reduced:
        logger.info(f"Fallback triggered: Corpus {len(corpus)} -> {len(effective_corpus)}, "
                    f"Window {window_size} -> {effective_window}, "
                    f"Min Cluster {min_cluster_size} -> {effective_min_cluster}")

    try:
        # Initialize CountVectorizer with reduced window
        vectorizer = CountVectorizer(
            ngram_range=(1, effective_window),
            stop_words="english",
            min_df=2
        )

        # Initialize HDBSCAN with reduced parameters for memory efficiency
        hdbscan_model = HDBSCAN(
            min_cluster_size=effective_min_cluster,
            metric="euclidean",
            cluster_selection_method="eom",
            prediction_data=True
        )

        # Initialize BERTopic
        # Using 'all-MiniLM-L6-v2' as it is lightweight and CPU-friendly
        topic_model = BERTopic(
            language="english",
            calculate_probabilities=True,
            vectorizer_model=vectorizer,
            hdbscan_model=hdbscan_model,
            verbose=True
        )

        logger.info("Fitting BERTopic model...")
        topics, probs = topic_model.fit_transform(effective_corpus)

        metadata = {
            "original_corpus_size": len(corpus),
            "effective_corpus_size": len(effective_corpus),
            "window_size_used": effective_window,
            "min_cluster_size_used": effective_min_cluster,
            "fallback_applied": reduced,
            "n_topics": len(set(topics)) - (1 if -1 in topics else 0),
            "status": "success"
        }

        return topic_model, metadata

    except MemoryError:
        logger.error("MemoryError during BERTopic execution. Fallback insufficient.")
        return None, {"status": "failed", "reason": "MemoryError"}
    except Exception as e:
        logger.error(f"Unexpected error during BERTopic execution: {e}")
        return None, {"status": "failed", "reason": str(e)}


def extract_topic_embeddings(
    topic_model: Optional[BERTopic],
    corpus: List[str]
) -> Dict[str, Any]:
    """
    Extract topic embeddings and representative documents.
    """
    if topic_model is None:
        logger.warning("No topic model provided. Returning empty embeddings.")
        return {
            "topic_embeddings": {},
            "topic_document_counts": {},
            "status": "skipped"
        }

    topic_info = {}
    topic_counts = {}

    # Extract info for each topic
    for topic_id in topic_model.get_topic_info()["Topic"].unique():
        if topic_id == -1:
            continue # Skip noise
        
        # Get topic words
        topic_words = topic_model.get_topic(topic_id)
        if topic_words:
            topic_info[str(topic_id)] = [word for word, score in topic_words[:5]]
            topic_counts[str(topic_id)] = len(topic_model.get_topic_freq(topic_id))

    # Extract topic representations (embeddings) if available
    # BERTopic doesn't always expose raw embeddings directly without re-computing,
    # but we can return the topic frequency and representative words as the primary signal.
    # If the model has a UMAP/embedding component, we could access it, but for CPU constraints
    # we rely on the topic-word distribution.
    
    return {
        "topic_info": topic_info,
        "topic_counts": topic_counts,
        "status": "success"
    }


def save_bertopic_results(
    topic_model: Optional[BERTopic],
    corpus: List[str],
    metadata: Dict[str, Any],
    embeddings_data: Dict[str, Any]
) -> str:
    """
    Save BERTopic results to a JSON file in data/results/.
    """
    output_path = RESULTS_DIR / "bertopic_results.json"
    
    result_data = {
        "metadata": metadata,
        "embeddings_data": embeddings_data,
        "topics_summary": topic_model.get_topic_info().to_dict() if topic_model else {}
    }

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, default=str)
        logger.info(f"Saved BERTopic results to {output_path}")
        return str(output_path)
    except Exception as e:
        logger.error(f"Failed to save BERTopic results: {e}")
        raise


def run_pipeline() -> None:
    """
    Main entry point for the neural baseline pipeline.
    Executes loading, modeling with fallback, and saving.
    """
    logger.info("=== Starting Neural Baseline Pipeline ===")
    
    # 1. Load Corpus
    corpus = load_corpus_for_bertopic()
    if not corpus:
        logger.error("Corpus is empty. Aborting.")
        return

    # 2. Run Model with Fallback
    # Parameters can be tuned based on system constraints
    model, metadata = run_bertopic_model(
        corpus=corpus,
        min_cluster_size=10,
        window_size=4,
        max_memory_mb=2048
    )

    if model is None:
        logger.error("Model training failed. Aborting.")
        # Save failure metadata
        save_bertopic_results(None, corpus, metadata, {})
        return

    # 3. Extract Embeddings/Info
    embeddings_data = extract_topic_embeddings(model, corpus)

    # 4. Save Results
    save_bertopic_results(model, corpus, metadata, embeddings_data)

    logger.info("=== Neural Baseline Pipeline Complete ===")


if __name__ == "__main__":
    run_pipeline()