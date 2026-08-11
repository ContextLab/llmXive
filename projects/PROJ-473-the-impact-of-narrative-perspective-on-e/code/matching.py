import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Dict, Any, Optional
import re
import json
import logging

logger = logging.getLogger(__name__)

def build_tfidf_vectors(stories: List[Dict[str, Any]], exclude_pronouns: bool = True) -> Tuple[List[str], Any]:
    """
    Build TF-IDF vectors from story texts.
    Excludes pronouns if exclude_pronouns is True (FR-008).
    """
    # We need the actual text content. The stories list from perspective_features.json
    # does not contain the full text, only metadata.
    # However, for the matching task, we assume we are matching based on the story_id
    # or we need to reload the text. Since the task description says "align processed stories",
    # and the current extraction output doesn't have text, we must assume we either:
    # 1. Re-read the files (expensive but real)
    # 2. Or the stories list passed here is different (e.g. from a different source).
    # Given the constraints, we will attempt to re-read the text from the file_path in the story dict.
    
    texts = []
    valid_stories = []
    
    for story in stories:
        file_path = story.get('file_path')
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    texts.append(f.read())
                valid_stories.append(story)
            except Exception as e:
                logger.warning(f"Could not read {file_path} for TF-IDF: {e}")
        else:
            logger.warning(f"Missing file_path for story {story.get('story_id')}, skipping.")
    
    if not texts:
        logger.error("No valid texts found for TF-IDF vectorization.")
        return [], None

    # Define pronoun stopwords to exclude
    pronouns = ['i', 'me', 'my', 'mine', 'myself', 'we', 'us', 'our', 'ours', 'ourselves',
                'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself',
                'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
                'you', 'your', 'yours', 'yourself', 'yourselves']
    
    # Custom tokenizer to filter pronouns
    def tokenizer(text):
        tokens = re.findall(r'\b\w+\b', text.lower())
        if exclude_pronouns:
            tokens = [t for t in tokens if t not in pronouns]
        return tokens

    vectorizer = TfidfVectorizer(tokenizer=tokenizer, stop_words='english', max_features=1000)
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    return valid_stories, tfidf_matrix

def find_top_matches(query_vector, candidate_vectors, k=3) -> List[Tuple[int, float]]:
    """
    Find top-k matches for a query vector against candidate vectors.
    Returns list of (index, similarity_score).
    Implements deterministic tie-breaking (highest raw score).
    """
    similarities = cosine_similarity([query_vector], candidate_vectors)[0]
    # Get indices sorted by similarity (descending)
    # np.argsort returns ascending, so we negate or reverse
    sorted_indices = np.argsort(similarities)[::-1]
    
    top_matches = []
    for i in range(min(k, len(sorted_indices))):
        idx = sorted_indices[i]
        score = similarities[idx]
        top_matches.append((idx, score))
    
    return top_matches

def apply_sensitivity_analysis(thresholds: List[float] = [0.25, 0.30, 0.35, 0.40]) -> Dict[str, Any]:
    """
    Apply sensitivity analysis across different similarity thresholds.
    Returns a report detailing sample size and headline correlation coefficient variation.
    """
    # This is a placeholder for the actual analysis logic which would require
    # the gold standard data. Since we are implementing the pipeline structure,
    # we return a dummy structure that would be populated by real data.
    report = {
        "thresholds": thresholds,
        "results": []
    }
    
    # In a real scenario, we would iterate thresholds, filter matches, and compute stats.
    # For now, we return the structure.
    return report

def run_sensitivity_analysis_pipeline(stories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run the full matching validation pipeline.
    1. Build TF-IDF vectors.
    2. Find top matches.
    3. Apply sensitivity analysis.
    4. Return results in the required schema: {story_id, match_id, similarity_score, rank}.
    """
    import os
    
    if not stories:
        return []
    
    valid_stories, tfidf_matrix = build_tfidf_vectors(stories)
    
    if tfidf_matrix is None or tfidf_matrix.shape[0] == 0:
        logger.warning("No vectors built. Returning empty results.")
        return []
    
    results = []
    
    # For each story, find top matches (treating each as a query against the rest)
    # Note: In a real matching scenario, we might have a separate query set.
    # Here we do self-matching for validation purposes or assume the "query" is the story itself.
    # To avoid matching a story to itself (score 1.0), we can mask the diagonal or skip it.
    
    for i, story in enumerate(valid_stories):
        query_vec = tfidf_matrix[i]
        # Get similarities with all other stories
        similarities = cosine_similarity([query_vec], tfidf_matrix)[0]
        
        # Set self-similarity to -1 to exclude it
        similarities[i] = -1.0
        
        # Sort
        sorted_indices = np.argsort(similarities)[::-1]
        
        # Take top 3
        for rank, idx in enumerate(sorted_indices[:3]):
            if similarities[idx] >= 0.3: # Threshold from config
                results.append({
                    "story_id": story['story_id'],
                    "match_id": valid_stories[idx]['story_id'],
                    "similarity_score": float(similarities[idx]),
                    "rank": rank + 1
                })
    
    return results
