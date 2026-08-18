import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Dict, Any, Optional
import re
import json
import os
import logging
import pandas as pd

def build_tfidf_vectors(stories: List[Dict[str, Any]], exclude_pronouns: bool = True) -> Tuple[np.ndarray, TfidfVectorizer]:
    """
    Build TF-IDF vectors for stories, optionally excluding pronouns.
    """
    logger = logging.getLogger(__name__)
    
    # Extract text from stories
    texts = [story.get('raw_text', '') for story in stories]
    
    # Define pronouns to exclude
    pronouns = ['i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours', 
               'he', 'him', 'his', 'she', 'her', 'hers', 
               'they', 'them', 'their', 'theirs']
    
    # Custom stop words
    custom_stop_words = set(ENGLISH_STOP_WORDS)
    if exclude_pronouns:
        custom_stop_words.update(pronouns)
    
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(stop_words=list(custom_stop_words))
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    # Verify no pronouns in vocabulary
    if exclude_pronouns:
        vocab = set(vectorizer.get_feature_names_out())
        remaining_pronouns = [p for p in pronouns if p in vocab]
        if remaining_pronouns:
            logger.warning(f"Pronouns still in vocabulary: {remaining_pronouns}")
    
    return tfidf_matrix.toarray(), vectorizer

def find_top_matches(query_vector: np.ndarray, candidate_vectors: np.ndarray, k: int = 3) -> List[Tuple[int, float]]:
    """
    Find top-k matches for a query vector among candidate vectors.
    Returns list of (index, similarity_score) tuples.
    """
    similarities = cosine_similarity([query_vector], candidate_vectors)[0]
    top_indices = np.argsort(similarities)[::-1][:k]
    return [(int(idx), float(similarities[idx])) for idx in top_indices]

def run_matching_pipeline(
    features_path: str,
    target_path: str,
    output_path: str
) -> List[Dict[str, Any]]:
    """
    Run the matching pipeline: load features, build vectors, match against target.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Running matching pipeline: {features_path} + {target_path} -> {output_path}")
    
    # Load perspective features
    with open(features_path, 'r') as f:
        features = json.load(f)
    
    # Load target dataset
    target_df = pd.read_csv(target_path)
    
    # Build TF-IDF vectors for features
    feature_vectors, vectorizer = build_tfidf_vectors(features)
    
    # Build TF-IDF vectors for target (using same vectorizer)
    target_texts = target_df['text'].tolist()  # Assuming 'text' column exists
    target_vectors = vectorizer.transform(target_texts).toarray()
    
    # Find matches for each feature
    results = []
    for i, feature in enumerate(features):
        query_vector = feature_vectors[i]
        matches = find_top_matches(query_vector, target_vectors, k=3)
        
        for rank, (idx, score) in enumerate(matches):
            if score >= 0.3:  # Primary threshold
                result = {
                    'story_id': feature['story_id'],
                    'match_id': target_df.iloc[idx]['story_id'],
                    'similarity_score': score,
                    'rank': rank + 1
                }
                results.append(result)
            else:
                logger.info(f"Unmatched: {feature['story_id']} (score: {score})")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Matching complete. {len(results)} matches saved to {output_path}")
    return results

def run_sensitivity_analysis_pipeline(
    matching_results_path: str,
    thresholds_path: str,
    dataset_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Run sensitivity analysis on matching thresholds.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Running sensitivity analysis: {matching_results_path} + {thresholds_path} + {dataset_path} -> {output_path}")
    
    # Load matching results
    with open(matching_results_path, 'r') as f:
        matching_results = json.load(f)
    
    # Load thresholds
    with open(thresholds_path, 'r') as f:
        thresholds_data = json.load(f)
    thresholds = thresholds_data['thresholds']
    
    # Load aligned dataset
    df = pd.read_csv(dataset_path)
    
    # For each threshold, filter and analyze
    results = {
        'thresholds': thresholds,
        'slopes': [],
        'sample_sizes': [],
        'slope_variance': None
    }
    
    for threshold in thresholds:
        # Filter matches
        filtered = [m for m in matching_results if m['similarity_score'] >= threshold]
        
        # Join with dataset
        # Assuming filtered matches have 'story_id'
        filtered_df = pd.DataFrame(filtered)
        joined = pd.merge(filtered_df, df, on='story_id', how='inner')
        
        sample_size = len(joined)
        results['sample_sizes'].append(sample_size)
        
        if sample_size < 5:
            results['slopes'].append(None)
            continue
        
        # Run regression (simplified for sensitivity analysis)
        try:
            from analysis import run_regression_analysis
            # Save temporary CSV
            temp_path = f"data/processed/temp_sweep_{threshold}.csv"
            joined.to_csv(temp_path, index=False)
            regression_results = run_regression_analysis(temp_path)
            results['slopes'].append(regression_results['slope'])
        except Exception as e:
            logger.error(f"Regression failed at threshold {threshold}: {e}")
            results['slopes'].append(None)
    
    # Calculate slope variance
    valid_slopes = [s for s in results['slopes'] if s is not None]
    if len(valid_slopes) > 1:
        results['slope_variance'] = float(np.var(valid_slopes))
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity analysis complete. Results saved to {output_path}")
    return results

def apply_sensitivity_analysis(
    matching_results: List[Dict[str, Any]],
    thresholds: List[float]
) -> Dict[str, Any]:
    """
    Apply sensitivity analysis to matching results.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Applying sensitivity analysis to {len(matching_results)} matches")
    
    results = {
        'thresholds': thresholds,
        'slopes': [],
        'sample_sizes': [],
        'slope_variance': None
    }
    
    for threshold in thresholds:
        filtered = [m for m in matching_results if m['similarity_score'] >= threshold]
        results['sample_sizes'].append(len(filtered))
        # Placeholder for slope calculation
        results['slopes'].append(None)
    
    return results
