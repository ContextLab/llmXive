import json
import csv
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from code.config import RESULTS_DIR, PROCESSED_DIR
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_corpus_for_retrieval(corpus_path: Optional[Path] = None) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Load corpus and metadata for retrieval simulation."""
    if corpus_path is None:
        corpus_path = PROCESSED_DIR / "corpus.json"
    
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus file not found at {corpus_path}")
    
    with open(corpus_path, 'r') as f:
        data = json.load(f)
    
    texts = [doc.get("text", "") for doc in data]
    metadata = data
    return texts, metadata

def build_tfidf_index(texts: List[str]) -> Tuple[TfidfVectorizer, np.ndarray]:
    """Build TF-IDF index from corpus texts."""
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(texts)
    return vectorizer, tfidf_matrix

def rank_documents(query_text: str, vectorizer: TfidfVectorizer, tfidf_matrix: np.ndarray, 
                   metadata: List[Dict[str, Any]], k: int = 10) -> List[Dict[str, Any]]:
    """Rank documents for a single query using TF-IDF cosine similarity."""
    query_vec = vectorizer.transform([query_text])
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    
    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:k]
    
    results = []
    for idx in top_indices:
        doc_info = metadata[idx].copy()
        doc_info["similarity_score"] = float(similarities[idx])
        doc_info["rank"] = len(results) + 1
        results.append(doc_info)
    
    return results

def run_retrieval_simulation(queries: List[Dict[str, Any]], vectorizer: TfidfVectorizer, 
                             tfidf_matrix: np.ndarray, metadata: List[Dict[str, Any]], 
                             k: int = 10) -> List[Dict[str, Any]]:
    """Run retrieval simulation for multiple queries."""
    all_results = []
    for query in queries:
        query_text = query.get("text", "")
        query_id = query.get("id", "unknown")
        
        ranked_docs = rank_documents(query_text, vectorizer, tfidf_matrix, metadata, k)
        
        for doc_info in ranked_docs:
            doc_info["query_id"] = query_id
            all_results.append(doc_info)
    
    return all_results

def save_retrieval_scores(results: List[Dict[str, Any]], output_path: Optional[Path] = None) -> None:
    """Save retrieval scores to CSV file."""
    if output_path is None:
        output_path = RESULTS_DIR / "retrieval_scores.csv"
    
    if not results:
        logger.warning("No retrieval results to save.")
        return
    
    # Flatten nested structures for CSV
    flat_results = []
    for result in results:
        flat_result = {}
        for key, value in result.items():
            if isinstance(value, (dict, list)):
                flat_result[key] = json.dumps(value)
            else:
                flat_result[key] = value
        flat_results.append(flat_result)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=flat_results[0].keys())
        writer.writeheader()
        writer.writerows(flat_results)
    
    logger.info(f"Saved {len(results)} retrieval score rows to {output_path}")

def run_pipeline(queries_path: Optional[Path] = None, corpus_path: Optional[Path] = None, 
                 output_path: Optional[Path] = None, k: int = 10) -> List[Dict[str, Any]]:
    """Main pipeline: load data, build index, run retrieval, save results."""
    logger.info("Starting retrieval simulation pipeline.")
    
    # Load data
    queries = []
    if queries_path is None:
        queries_path = PROCESSED_DIR / "queries.json"
    
    if queries_path.exists():
        with open(queries_path, 'r') as f:
            queries = json.load(f)
    else:
        logger.warning(f"Queries file not found at {queries_path}, using empty queries.")
    
    texts, metadata = load_corpus_for_retrieval(corpus_path)
    
    # Build index
    vectorizer, tfidf_matrix = build_tfidf_index(texts)
    
    # Run simulation
    results = run_retrieval_simulation(queries, vectorizer, tfidf_matrix, metadata, k)
    
    # Save results
    save_retrieval_scores(results, output_path)
    
    return results

if __name__ == "__main__":
    run_pipeline()
