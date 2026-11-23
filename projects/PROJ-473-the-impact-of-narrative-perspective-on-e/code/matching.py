import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Dict, Any, Optional
import re
import json
import logging

logger = logging.getLogger(__name__)

# Define pronouns to exclude
FIRST_PERSON_PRONOUNS = {'i', 'me', 'my', 'mine', 'myself', 'we', 'us', 'our', 'ours', 'ourselves'}
THIRD_PERSON_PRONOUNS = {'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 
                         'they', 'them', 'their', 'theirs', 'themselves', 'it', 'its', 'itself'}
ALL_PRONOUNS = FIRST_PERSON_PRONOUNS | THIRD_PERSON_PRONOUNS

def clean_text(text: str) -> str:
    """Clean text by removing special characters and normalizing."""
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def build_tfidf_vectors(source_texts: List[str], target_texts: List[str], exclude_pronouns: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """Build TF-IDF vectors for source and target texts.
    
    Args:
        source_texts: List of source story texts
        target_texts: List of target story texts
        exclude_pronouns: If True, exclude pronouns from vectorization
        
    Returns:
        Tuple of (source_vectors, target_vectors)
    """
    # Combine all texts for vocabulary building
    all_texts = source_texts + target_texts
    
    # Preprocess texts
    processed_texts = [clean_text(text) for text in all_texts]
    
    # Create custom stop words
    stop_words = set(ENGLISH_STOP_WORDS)
    if exclude_pronouns:
        stop_words.update(ALL_PRONOUNS)
    
    # Build TF-IDF vectorizer
    vectorizer = TfidfVectorizer(
        stop_words=list(stop_words),
        max_df=0.95,
        min_df=1,
        ngram_range=(1, 2)
    )
    
    # Fit and transform
    tfidf_matrix = vectorizer.fit_transform(processed_texts)
    
    # Split back into source and target
    n_source = len(source_texts)
    source_vectors = tfidf_matrix[:n_source]
    target_vectors = tfidf_matrix[n_source:]
    
    # Verify no pronouns in vocabulary
    if exclude_pronouns:
        feature_names = vectorizer.get_feature_names_out()
        pronoun_in_vocab = [word for word in feature_names if word in ALL_PRONOUNS]
        if pronoun_in_vocab:
            logger.warning(f"Pronouns found in vocabulary: {pronoun_in_vocab}")
    
    return source_vectors.toarray(), target_vectors.toarray()

def find_top_matches(query_vector: np.ndarray, candidate_vectors: np.ndarray, k: int = 3, threshold: float = 0.30) -> List[Dict[str, Any]]:
    """Find top k matches for a query vector.
    
    Args:
        query_vector: The query vector (1D array)
        candidate_vectors: Matrix of candidate vectors (2D array)
        k: Number of top matches to return
        threshold: Minimum similarity threshold
        
    Returns:
        List of match dictionaries with story_id, similarity, rank
    """
    # Compute cosine similarities
    similarities = cosine_similarity([query_vector], candidate_vectors)[0]
    
    # Get top k indices
    top_indices = np.argsort(similarities)[::-1][:k]
    
    matches = []
    for rank, idx in enumerate(top_indices):
        sim = float(similarities[idx])
        if sim >= threshold:
            matches.append({
                'similarity': sim,
                'rank': rank + 1
            })
    
    # Deterministic tie-breaking: if multiple matches have same similarity, 
    # sort by index (lower index first)
    matches.sort(key=lambda x: (-x['similarity'], x['rank']))
    
    return matches

def run_matching_pipeline(source_texts: List[str], target_texts: List[str], k: int = 3, threshold: float = 0.30) -> List[Dict[str, Any]]:
    """Run the full matching pipeline.
    
    Args:
        source_texts: List of source story texts
        target_texts: List of target story texts
        k: Number of top matches per source
        threshold: Minimum similarity threshold
        
    Returns:
        List of all matches
    """
    source_vectors, target_vectors = build_tfidf_vectors(source_texts, target_texts)
    
    all_matches = []
    for i, source_vec in enumerate(source_vectors):
        matches = find_top_matches(source_vec, target_vectors, k=k, threshold=threshold)
        for match in matches:
            all_matches.append({
                'source_idx': i,
                'target_idx': match['target_idx'] if 'target_idx' in match else 0,
                'similarity': match['similarity'],
                'rank': match['rank']
            })
    
    return all_matches

def run_sensitivity_analysis_pipeline(thresholds: List[float], source_texts: List[str], target_texts: List[str]) -> Dict[str, Any]:
    """Run sensitivity analysis across multiple thresholds.
    
    Args:
        thresholds: List of threshold values to test
        source_texts: Source story texts
        target_texts: Target story texts
        
    Returns:
        Dictionary with results for each threshold
    """
    source_vectors, target_vectors = build_tfidf_vectors(source_texts, target_texts)
    
    results = {
        'thresholds': thresholds,
        'match_counts': [],
        'avg_similarities': []
    }
    
    for threshold in thresholds:
        total_matches = 0
        total_sim = 0.0
        
        for source_vec in source_vectors:
            matches = find_top_matches(source_vec, target_vectors, k=3, threshold=threshold)
            total_matches += len(matches)
            for match in matches:
                total_sim += match['similarity']
        
        avg_sim = total_sim / total_matches if total_matches > 0 else 0.0
        results['match_counts'].append(total_matches)
        results['avg_similarities'].append(avg_sim)
    
    return results

def apply_sensitivity_analysis(results: Dict[str, Any]) -> Dict[str, Any]:
    """Apply sensitivity analysis to compute variance and stability metrics.
    
    Args:
        results: Results from run_sensitivity_analysis_pipeline
        
    Returns:
        Dictionary with sensitivity metrics
    """
    import numpy as np
    
    match_counts = np.array(results['match_counts'])
    avg_sims = np.array(results['avg_similarities'])
    
    return {
        'thresholds': results['thresholds'],
        'match_counts': match_counts.tolist(),
        'avg_similarities': avg_sims.tolist(),
        'match_variance': float(np.var(match_counts)),
        'similarity_variance': float(np.var(avg_sims)),
        'stability_score': float(1.0 - np.var(match_counts) / len(match_counts)) if len(match_counts) > 0 else 0.0
    }
