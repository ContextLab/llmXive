"""
LDA Fitter for Topic Modeling across temporal windows.

Implements iterative fitting of Latent Dirichlet Allocation (LDA) models
for each of the five defined 5-year windows (2000–2004, 2005–2009,
2010–2014, 2015–2019, 2020–2024).
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

from src.utils.logging import get_logger
from src.utils.manifest import save_reproducibility_manifest
from src.models.entities import TopicVector

# Define the fixed windows as per specification
TIME_WINDOWS = [
    ("2000-2004", 2000, 2004),
    ("2005-2009", 2005, 2009),
    ("2010-2014", 2010, 2014),
    ("2015-2019", 2015, 2019),
    ("2020-2024", 2020, 2024),
]

# Default parameters
DEFAULT_K = 10
DEFAULT_MAX_ITER = 20
DEFAULT_RANDOM_SEED = 42
DEFAULT_MIN_DF = 2
DEFAULT_MAX_DF = 0.95

logger = get_logger(__name__)


def load_processed_data_by_window(
    data_dir: Path,
    window_name: str
) -> Optional[pd.DataFrame]:
    """
    Load processed CSV data for a specific window from data/processed/.
    
    Args:
        data_dir: Path to the data/processed directory
        window_name: The window identifier (e.g., '2000-2004')
        
    Returns:
        DataFrame with processed abstracts or None if file not found
    """
    file_path = data_dir / f"abstracts_{window_name}.csv"
    
    if not file_path.exists():
        logger.warning(f"Processed data file not found: {file_path}")
        return None
        
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} records for window {window_name}")
        
        # Validate required columns
        required_cols = ['processed_text', 'year']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
            
        return df
    except Exception as e:
        logger.error(f"Error loading data for window {window_name}: {e}")
        return None


def fit_lda_model(
    documents: List[str],
    k: int = DEFAULT_K,
    max_iter: int = DEFAULT_MAX_ITER,
    random_state: Optional[int] = None,
    min_df: int = DEFAULT_MIN_DF,
    max_df: float = DEFAULT_MAX_DF
) -> Tuple[LatentDirichletAllocation, CountVectorizer, np.ndarray]:
    """
    Fit an LDA model on the provided documents.
    
    Args:
        documents: List of preprocessed text documents
        k: Number of topics
        max_iter: Maximum iterations for LDA
        random_state: Random seed for reproducibility
        min_df: Minimum document frequency for vectorizer
        max_df: Maximum document frequency for vectorizer
        
    Returns:
        Tuple of (fitted LDA model, vectorizer, document-topic matrix)
    """
    if len(documents) == 0:
        raise ValueError("Cannot fit LDA model on empty document list")
        
    if len(documents) < k:
        logger.warning(f"Document count ({len(documents)}) is less than k ({k}). "
                     "Consider reducing k or using more data.")
    
    # Initialize vectorizer
    vectorizer = CountVectorizer(
        max_df=max_df,
        min_df=min_df,
        max_features=10000,  # Limit vocabulary size for efficiency
        stop_words=None,     # Stopwords already removed in preprocessing
        dtype=np.int32
    )
    
    try:
        doc_term_matrix = vectorizer.fit_transform(documents)
    except ValueError as e:
        logger.error(f"Vectorization failed: {e}")
        raise
    
    logger.info(f"Vocabulary size: {len(vectorizer.vocabulary_)}")
    logger.info(f"Document-term matrix shape: {doc_term_matrix.shape}")
    
    # Initialize and fit LDA
    lda_model = LatentDirichletAllocation(
        n_components=k,
        max_iter=max_iter,
        learning_method='online',  # More memory efficient for large datasets
        random_state=random_state,
        n_jobs=-1,                 # Use all available CPU cores
        verbose=0
    )
    
    logger.info(f"Fitting LDA model with k={k}, max_iter={max_iter}...")
    doc_topic_dist = lda_model.fit_transform(doc_term_matrix)
    logger.info("LDA fitting completed.")
    
    return lda_model, vectorizer, doc_topic_dist


def extract_topic_vectors(
    lda_model: LatentDirichletAllocation,
    vectorizer: CountVectorizer,
    top_n_words: int = 20
) -> Dict[str, List[TopicVector]]:
    """
    Extract topic vectors (word distributions) from the fitted LDA model.
    
    Args:
        lda_model: Fitted LDA model
        vectorizer: Fitted CountVectorizer
        top_n_words: Number of top words to extract per topic
        
    Returns:
        Dictionary mapping window names to lists of TopicVector objects
    """
    feature_names = vectorizer.get_feature_names_out()
    topic_vectors = {}
    
    for topic_idx in range(lda_model.n_components):
        topic_dist = lda_model.components_[topic_idx]
        top_indices = topic_dist.argsort()[-top_n_words:][::-1]
        
        words = [feature_names[i] for i in top_indices]
        weights = [float(topic_dist[i]) for i in top_indices]
        
        topic_vector = TopicVector(
            topic_id=topic_idx,
            words=words,
            weights=weights,
            distribution=topic_dist / topic_dist.sum()  # Normalize
        )
        
        if topic_idx not in topic_vectors:
            topic_vectors[topic_idx] = []
        topic_vectors[topic_idx].append(topic_vector)
    
    return topic_vectors


def fit_lda_for_all_windows(
    data_dir: Path,
    output_dir: Path,
    k: int = DEFAULT_K,
    max_iter: int = DEFAULT_MAX_ITER,
    random_state: int = DEFAULT_RANDOM_SEED,
    min_df: int = DEFAULT_MIN_DF,
    max_df: float = DEFAULT_MAX_DF
) -> Dict[str, Dict[str, Any]]:
    """
    Fit LDA models for all defined time windows and save results.
    
    Args:
        data_dir: Path to data/processed directory
        output_dir: Path to results/stats directory
        k: Number of topics
        max_iter: Maximum LDA iterations
        random_state: Random seed
        min_df: Minimum document frequency
        max_df: Maximum document frequency
        
    Returns:
        Dictionary containing fit results for each window
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    manifest_data = {
        "task_id": "T020",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "parameters": {
            "k": k,
            "max_iter": max_iter,
            "random_state": random_state,
            "min_df": min_df,
            "max_df": max_df
        },
        "windows": {}
    }
    
    for window_name, start_year, end_year in TIME_WINDOWS:
        logger.info(f"Processing window: {window_name} ({start_year}-{end_year})")
        
        # Load data
        df = load_processed_data_by_window(data_dir, window_name)
        if df is None or len(df) == 0:
            logger.warning(f"Skipping window {window_name}: No data available")
            manifest_data["windows"][window_name] = {
                "status": "skipped",
                "reason": "No data available"
            }
            continue
        
        # Filter documents with sufficient content
        documents = df['processed_text'].dropna().tolist()
        valid_docs = [doc for doc in documents if isinstance(doc, str) and len(doc.strip()) > 0]
        
        if len(valid_docs) < k:
            logger.warning(f"Skipping window {window_name}: Insufficient documents ({len(valid_docs)} < {k})")
            manifest_data["windows"][window_name] = {
                "status": "skipped",
                "reason": f"Insufficient documents: {len(valid_docs)} < {k}"
            }
            continue
        
        try:
            # Fit LDA model
            lda_model, vectorizer, doc_topic_dist = fit_lda_model(
                documents=valid_docs,
                k=k,
                max_iter=max_iter,
                random_state=random_state,
                min_df=min_df,
                max_df=max_df
            )
            
            # Extract and save topic vectors
            topic_vectors = extract_topic_vectors(lda_model, vectorizer)
            
            # Save topic vectors to JSON
            vector_file = output_dir / f"topic_vectors_{window_name}.json"
            vector_data = {
                "window": window_name,
                "k": k,
                "vocabulary_size": len(vectorizer.vocabulary_),
                "num_documents": len(valid_docs),
                "topics": []
            }
            
            for topic_id, vectors in topic_vectors.items():
                for v in vectors:
                    vector_data["topics"].append({
                        "topic_id": v.topic_id,
                        "words": v.words,
                        "weights": v.weights,
                        "distribution": v.distribution.tolist()
                    })
            
            with open(vector_file, 'w', encoding='utf-8') as f:
                json.dump(vector_data, f, indent=2)
            
            # Save document-topic distribution
            doc_topic_file = output_dir / f"doc_topic_dist_{window_name}.npy"
            np.save(doc_topic_file, doc_topic_dist)
            
            # Record success
            results[window_name] = {
                "status": "success",
                "num_documents": len(valid_docs),
                "vocabulary_size": len(vectorizer.vocabulary_),
                "model_path": str(vector_file),
                "doc_topic_path": str(doc_topic_file)
            }
            
            manifest_data["windows"][window_name] = {
                "status": "success",
                "num_documents": len(valid_docs),
                "vocabulary_size": len(vectorizer.vocabulary_),
                "file_checksums": {
                    "topic_vectors": vector_file.name,
                    "doc_topic_dist": doc_topic_file.name
                }
            }
            
            logger.info(f"Completed window {window_name}: {len(valid_docs)} docs, "
                      f"{len(vectorizer.vocabulary_)} vocab, {k} topics")
            
        except Exception as e:
            logger.error(f"Failed to fit LDA for window {window_name}: {e}")
            results[window_name] = {
                "status": "failed",
                "error": str(e)
            }
            manifest_data["windows"][window_name] = {
                "status": "failed",
                "error": str(e)
            }
    
    # Save manifest
    manifest_file = output_dir / "lda_fitter_manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2)
    
    logger.info(f"LDA fitting complete. Manifest saved to {manifest_file}")
    return results


def main():
    """Main entry point for LDA fitting pipeline."""
    logger.info("Starting LDA fitting for all time windows")
    
    # Configuration
    project_root = Path(__file__).parent.parent.parent.parent
    data_dir = project_root / "data" / "processed"
    output_dir = project_root / "results" / "stats"
    
    # Load config if available
    try:
        from src.utils.config import get_config_dict
        config = get_config_dict()
        k = config.get("lda_k", DEFAULT_K)
        max_iter = config.get("lda_max_iter", DEFAULT_MAX_ITER)
        random_state = config.get("random_seed", DEFAULT_RANDOM_SEED)
    except Exception:
        logger.warning("Using default LDA parameters")
        k = DEFAULT_K
        max_iter = DEFAULT_MAX_ITER
        random_state = DEFAULT_RANDOM_SEED
    
    # Run fitting
    results = fit_lda_for_all_windows(
        data_dir=data_dir,
        output_dir=output_dir,
        k=k,
        max_iter=max_iter,
        random_state=random_state
    )
    
    # Report summary
    success_count = sum(1 for r in results.values() if r["status"] == "success")
    total_count = len(results)
    logger.info(f"LDA fitting complete: {success_count}/{total_count} windows succeeded")
    
    if success_count == 0:
        raise RuntimeError("No LDA models were successfully fitted")
    
    return results


if __name__ == "__main__":
    main()