"""
Fuzzy matching utilities for pre-print and journal article identification.

This module provides functions to calculate similarity scores between
article titles and author lists using rapidfuzz for efficient string matching.
"""
from typing import List, Tuple, Optional
from rapidfuzz import fuzz, process
from rapidfuzz.distance import Levenshtein


def normalize_title(title: str) -> str:
    """
    Normalize a title for comparison by removing common prefixes,
    extra whitespace, and converting to lowercase.
    
    Args:
        title: The raw title string.
        
    Returns:
        Normalized title string.
    """
    if not title:
        return ""
    
    # Remove common prefixes
    prefixes = [
        "a study of ", "an analysis of ", "the effects of ",
        "investigation of ", "review of ", "survey of ",
        "towards ", "on the ", "a note on ", "notes on "
    ]
    lower_title = title.lower().strip()
    
    for prefix in prefixes:
        if lower_title.startswith(prefix):
            lower_title = lower_title[len(prefix):]
            break
    
    # Remove trailing punctuation and normalize whitespace
    lower_title = lower_title.rstrip(":.,;")
    lower_title = " ".join(lower_title.split())
    
    return lower_title


def normalize_author(author: str) -> str:
    """
    Normalize an author name for comparison.
    
    Args:
        author: The raw author name string.
        
    Returns:
        Normalized author name string.
    """
    if not author:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = author.lower().strip()
    
    # Remove common suffixes like 'jr', 'sr', 'iii'
    suffixes = [" jr", " sr", " iii", " ii", " iv", " phd", " md"]
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)]
            break
    
    # Normalize whitespace
    normalized = " ".join(normalized.split())
    
    return normalized


def calculate_title_similarity(title1: str, title2: str) -> float:
    """
    Calculate the fuzzy similarity score between two titles.
    
    Uses a combination of partial ratio and token sort ratio
    to handle variations in word order and minor differences.
    
    Args:
        title1: First title string.
        title2: Second title string.
        
    Returns:
        Similarity score between 0.0 and 100.0.
    """
    if not title1 or not title2:
        return 0.0
    
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Use weighted combination of different metrics
    partial_ratio = fuzz.partial_ratio(norm1, norm2)
    token_sort_ratio = fuzz.token_sort_ratio(norm1, norm2)
    token_set_ratio = fuzz.token_set_ratio(norm1, norm2)
    
    # Weighted average favoring token set ratio for robustness
    score = (0.3 * partial_ratio + 0.3 * token_sort_ratio + 0.4 * token_set_ratio)
    
    return score


def calculate_author_similarity(authors1: List[str], authors2: List[str]) -> float:
    """
    Calculate the similarity between two lists of authors.
    
    Matches authors from both lists using fuzzy matching and
    calculates the proportion of matched authors.
    
    Args:
        authors1: List of author names from first paper.
        authors2: List of author names from second paper.
        
    Returns:
        Similarity score between 0.0 and 100.0.
    """
    if not authors1 or not authors2:
        return 0.0
    
    # Normalize all author names
    norm_authors1 = [normalize_author(a) for a in authors1]
    norm_authors2 = [normalize_author(a) for a in authors2]
    
    # Filter out empty strings
    norm_authors1 = [a for a in norm_authors1 if a]
    norm_authors2 = [a for a in norm_authors2 if a]
    
    if not norm_authors1 or not norm_authors2:
        return 0.0
    
    # Match authors from list1 to list2
    matches = 0
    matched_indices = set()
    
    for author1 in norm_authors1:
        best_match = None
        best_score = 0
        
        for idx, author2 in enumerate(norm_authors2):
            if idx in matched_indices:
                continue
            
            score = Levenshtein.normalized_similarity(author1, author2) * 100
            if score > best_score and score >= 80:  # Threshold for author match
                best_score = score
                best_match = idx
        
        if best_match is not None:
            matches += 1
            matched_indices.add(best_match)
    
    # Calculate similarity as proportion of matched authors
    # Weight by the smaller list size to avoid penalizing for extra authors
    min_len = min(len(norm_authors1), len(norm_authors2))
    if min_len == 0:
        return 0.0
    
    similarity = (matches / min_len) * 100
    return similarity


def combine_similarity_scores(
    title_score: float, 
    author_score: float,
    title_weight: float = 0.6,
    author_weight: float = 0.4
) -> float:
    """
    Combine title and author similarity scores into a single score.
    
    Args:
        title_score: Similarity score for titles (0-100).
        author_score: Similarity score for authors (0-100).
        title_weight: Weight for title score (default 0.6).
        author_weight: Weight for author score (default 0.4).
        
    Returns:
        Combined similarity score (0-100).
    """
    if title_weight + author_weight != 1.0:
        # Normalize weights if they don't sum to 1
        total = title_weight + author_weight
        title_weight /= total
        author_weight /= total
    
    return (title_weight * title_score) + (author_weight * author_score)


def match_papers(
    preprint_title: str,
    preprint_authors: List[str],
    candidate_papers: List[dict],
    title_threshold: float = 75.0,
    author_threshold: float = 60.0,
    combined_threshold: float = 70.0
) -> List[Tuple[dict, float]]:
    """
    Match a preprint against a list of candidate journal papers.
    
    Args:
        preprint_title: Title of the preprint.
        preprint_authors: List of author names for the preprint.
        candidate_papers: List of dictionaries containing candidate paper data
                         with 'title' and 'authors' keys.
        title_threshold: Minimum title similarity score (default 75.0).
        author_threshold: Minimum author similarity score (default 60.0).
        combined_threshold: Minimum combined score (default 70.0).
        
    Returns:
        List of tuples (candidate_paper, combined_score) for matches above thresholds.
    """
    matches = []
    
    for candidate in candidate_papers:
        candidate_title = candidate.get("title", "")
        candidate_authors = candidate.get("authors", [])
        
        # Calculate individual scores
        title_score = calculate_title_similarity(preprint_title, candidate_title)
        author_score = calculate_author_similarity(preprint_authors, candidate_authors)
        
        # Check if individual thresholds are met
        if title_score < title_threshold or author_score < author_threshold:
            continue
        
        # Calculate combined score
        combined_score = combine_similarity_scores(title_score, author_score)
        
        # Check combined threshold
        if combined_score >= combined_threshold:
            matches.append((candidate, combined_score))
    
    # Sort by combined score descending
    matches.sort(key=lambda x: x[1], reverse=True)
    
    return matches


def find_best_match(
    preprint_title: str,
    preprint_authors: List[str],
    candidate_papers: List[dict],
    title_threshold: float = 75.0,
    author_threshold: float = 60.0,
    combined_threshold: float = 70.0
) -> Optional[Tuple[dict, float]]:
    """
    Find the best matching journal paper for a given preprint.
    
    Args:
        preprint_title: Title of the preprint.
        preprint_authors: List of author names for the preprint.
        candidate_papers: List of dictionaries containing candidate paper data.
        title_threshold: Minimum title similarity score.
        author_threshold: Minimum author similarity score.
        combined_threshold: Minimum combined score.
        
    Returns:
        Tuple of (best_candidate, score) if a match is found, None otherwise.
    """
    matches = match_papers(
        preprint_title, 
        preprint_authors, 
        candidate_papers,
        title_threshold,
        author_threshold,
        combined_threshold
    )
    
    if not matches:
        return None
    
    return matches[0]  # Return the best match (highest score)