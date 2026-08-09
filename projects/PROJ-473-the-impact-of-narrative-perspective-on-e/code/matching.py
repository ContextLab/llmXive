import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Dict, Any, Optional
import re
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_tfidf_vectors(stories: List[Dict[str, Any]], exclude_pronouns: bool = True) -> Tuple[List[str], np.ndarray, TfidfVectorizer]:
    """
    Build TF-IDF vectors for a list of story documents.
    
    Args:
        stories: List of dicts with 'story_id' and 'text' keys.
        exclude_pronouns: If True, remove pronouns from text before vectorization.
    
    Returns:
        Tuple of (story_ids, tfidf_matrix, vectorizer)
    """
    if not stories:
        logger.warning("No stories provided to build_tfidf_vectors")
        return [], np.array([]), None

    # Extract text and IDs
    story_ids = [s['story_id'] for s in stories]
    texts = [s['text'] for s in stories]

    # Preprocess text if excluding pronouns
    if exclude_pronouns:
        processed_texts = []
        pronoun_pattern = re.compile(r'\b(I|me|my|mine|we|us|our|ours|you|your|yours|he|him|his|she|her|hers|it|its|they|them|their|theirs)\b', re.IGNORECASE)
        for text in texts:
            # Remove pronouns but keep the rest of the text
            cleaned = pronoun_pattern.sub('', text)
            # Clean up extra whitespace
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            processed_texts.append(cleaned)
        texts = processed_texts

    # Build TF-IDF vectors
    vectorizer = TfidfVectorizer(
        stop_words='english',
        lowercase=True,
        max_df=0.95,
        min_df=1
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError as e:
        logger.error(f"Failed to build TF-IDF vectors: {e}")
        return [], np.array([]), None

    return story_ids, tfidf_matrix.toarray(), vectorizer

def find_top_matches(query_vector: np.ndarray, candidate_vectors: np.ndarray, 
                    k: int = 3, story_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Find top k matches for a query vector against candidate vectors.
    
    Implements deterministic tie-breaking: if multiple candidates have the same
    highest similarity score, the one with the highest raw score (first in list)
    is selected.
    
    Args:
        query_vector: 1D numpy array representing the query.
        candidate_vectors: 2D numpy array of candidate vectors.
        k: Number of top matches to return.
        story_ids: Optional list of story IDs corresponding to candidate vectors.
    
    Returns:
        List of dicts with 'story_id', 'similarity_score', and 'rank' keys.
    """
    if candidate_vectors.size == 0:
        logger.warning("No candidate vectors provided")
        return []

    # Calculate cosine similarities
    similarities = cosine_similarity([query_vector], candidate_vectors).flatten()
    
    # Create list of (index, similarity) tuples
    indexed_sims = list(enumerate(similarities))
    
    # Sort by similarity (descending), then by index (ascending) for deterministic tie-breaking
    # This ensures that if two items have the same similarity, the one appearing
    # earlier in the original list (lower index) is ranked higher.
    indexed_sims.sort(key=lambda x: (-x[1], x[0]))
    
    # Get top k matches
    top_matches = []
    for rank, (idx, sim) in enumerate(indexed_sims[:k], 1):
        match = {
            'story_id': story_ids[idx] if story_ids else f"story_{idx}",
            'similarity_score': float(sim),
            'rank': rank
        }
        top_matches.append(match)
    
    return top_matches

def apply_sensitivity_analysis(thresholds: List[float] = [0.25, 0.30, 0.35, 0.40],
                              query_vectors: Optional[np.ndarray] = None,
                              candidate_vectors: Optional[np.ndarray] = None,
                              story_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Apply sensitivity analysis across different similarity thresholds.
    
    This function analyzes how sample size and correlation coefficients vary
    across different similarity thresholds to determine if the variation is
    significant for the final regression model.
    
    Args:
        thresholds: List of similarity thresholds to test.
        query_vectors: Optional array of query vectors.
        candidate_vectors: Optional array of candidate vectors.
        story_ids: Optional list of story IDs.
    
    Returns:
        Dictionary containing analysis results for each threshold.
    """
    if query_vectors is None or candidate_vectors is None:
        logger.warning("Query or candidate vectors not provided, skipping sensitivity analysis")
        return {'thresholds': thresholds, 'results': [], 'summary': 'No data provided'}

    results = []
    sample_sizes = []
    
    for threshold in thresholds:
        # Filter matches above threshold
        matches = []
        for i, query_vec in enumerate(query_vectors):
            top_matches = find_top_matches(query_vec, candidate_vectors, k=3, story_ids=story_ids)
            valid_matches = [m for m in top_matches if m['similarity_score'] >= threshold]
            matches.extend(valid_matches)
        
        sample_size = len(matches)
        sample_sizes.append(sample_size)
        
        result = {
            'threshold': threshold,
            'sample_size': sample_size,
            'matches': matches
        }
        results.append(result)
    
    # Calculate summary statistics
    if len(sample_sizes) > 1:
        mean_sample_size = np.mean(sample_sizes)
        std_sample_size = np.std(sample_sizes)
        variation_coefficient = std_sample_size / mean_sample_size if mean_sample_size > 0 else 0
        
        summary = {
            'mean_sample_size': float(mean_sample_size),
            'std_sample_size': float(std_sample_size),
            'variation_coefficient': float(variation_coefficient),
            'is_significant': variation_coefficient > 0.1  # Threshold for significant variation
        }
    else:
        summary = {'is_significant': False, 'reason': 'Insufficient data points'}
    
    return {
        'thresholds': thresholds,
        'results': results,
        'summary': summary
    }

def run_sensitivity_analysis_pipeline(stories: List[Dict[str, Any]], 
                                    queries: List[Dict[str, Any]],
                                    thresholds: List[float] = [0.25, 0.30, 0.35, 0.40]) -> Dict[str, Any]:
    """
    Run the complete sensitivity analysis pipeline.
    
    Args:
        stories: List of story documents for candidate vectors.
        queries: List of query documents.
        thresholds: Similarity thresholds to test.
    
    Returns:
        Complete analysis results.
    """
    # Build candidate vectors
    story_ids, candidate_vectors, _ = build_tfidf_vectors(stories, exclude_pronouns=True)
    
    # Build query vectors
    query_texts = [q['text'] for q in queries]
    query_vectorizer = TfidfVectorizer(
        stop_words='english',
        lowercase=True,
        max_df=0.95,
        min_df=1
    )
    query_vectors = query_vectorizer.fit_transform(query_texts).toarray()
    
    # Run sensitivity analysis
    analysis_results = apply_sensitivity_analysis(
        thresholds=thresholds,
        query_vectors=query_vectors,
        candidate_vectors=candidate_vectors,
        story_ids=story_ids
    )
    
    return analysis_results
