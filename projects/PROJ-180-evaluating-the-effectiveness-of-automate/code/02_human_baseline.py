import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from utils.config import get_data_raw_dir, get_data_processed_dir, get_github_token
from utils.github_client import create_client, GitHubClient
from utils.aligner import get_embedding_model, compute_embeddings, cosine_similarity_matrix

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Keyword heuristics configuration
KEYWORD_CONFIG = {
    'bug': ['bug', 'defect', 'error', 'crash', 'fail', 'broken', 'issue', 'fix'],
    'security': ['security', 'vulnerability', 'exploit', 'auth', 'permission', 'sqli', 'xss'],
    'style': ['style', 'formatting', 'indentation', 'naming', 'convention', 'refactor', 'cleanup']
}

def load_acquired_repos() -> List[Dict[str, Any]]:
    """Load the list of acquired repositories from data/raw/repo_list.json."""
    raw_dir = get_data_raw_dir()
    repo_list_path = raw_dir / "repo_list.json"
    
    if not repo_list_path.exists():
        logger.error(f"Repo list not found at {repo_list_path}")
        return []
    
    with open(repo_list_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def fetch_pr_review_comments() -> List[Dict[str, Any]]:
    """
    Fetch PR review comments from the acquired repositories.
    This function relies on T022 having already generated data/raw/pr_comments.json.
    """
    raw_dir = get_data_raw_dir()
    comments_path = raw_dir / "pr_comments.json"
    
    if not comments_path.exists():
        # Fallback: Try to fetch via API if data is missing, though T022 should have run
        logger.warning(f"pr_comments.json not found at {comments_path}. Attempting API fetch...")
        # In a real scenario, we would call the GitHubClient here to fetch comments
        # For this implementation, we assume T022 created the file.
        # If the file is truly missing, we raise an error to avoid silent failure.
        raise FileNotFoundError(f"Required input file missing: {comments_path}. Ensure T022 has run.")
    
    with open(comments_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_keyword_heuristics(comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply keyword heuristics to identify potential defect comments.
    Returns a list of candidates with predicted_type based on keyword matching.
    """
    candidates = []
    
    for comment in comments:
        text = comment.get('text', '').lower()
        matched_types = []
        
        for ptype, keywords in KEYWORD_CONFIG.items():
            for keyword in keywords:
                if keyword in text:
                    matched_types.append(ptype)
                    break # Only count type once per comment
        
        if matched_types:
            # Assign the most relevant type (priority: security > bug > style)
            priority_order = ['security', 'bug', 'style']
            predicted_type = None
            for p in priority_order:
                if p in matched_types:
                    predicted_type = p
                    break
            
            if predicted_type:
                candidates.append({
                    'comment_id': comment.get('comment_id'),
                    'text': comment.get('text'),
                    'predicted_type': predicted_type,
                    'file': comment.get('file'),
                    'line': comment.get('line'),
                    'repo_id': comment.get('repo_id'),
                    'timestamp': comment.get('timestamp'),
                    'matched_keywords': matched_types
                })
    
    return candidates

def semantic_filter_comments(
    candidates: List[Dict[str, Any]], 
    threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Refine heuristic candidates using semantic similarity to a set of known defect descriptions.
    Uses all-MiniLM-L6-v2 for embeddings.
    """
    if not candidates:
        return []
    
    # Define a small set of seed "defect" descriptions for semantic comparison
    # These represent the semantic space of "defect" comments
    seed_defects = [
        "This is a bug that needs fixing",
        "Security vulnerability found",
        "Code style issue",
        "Error handling is missing",
        "This function crashes",
        "Authentication bypass possible",
        "Formatting inconsistent"
    ]
    
    try:
        model = get_embedding_model()
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        # Fallback: Return all heuristic candidates if semantic search fails
        # This ensures the pipeline doesn't break, though quality may be lower
        logger.warning("Returning all heuristic candidates without semantic filtering.")
        return candidates

    # Embed seed defects
    seed_embeddings = compute_embeddings(seed_defects, model)
    
    refined_candidates = []
    
    for candidate in candidates:
        text = candidate.get('text', '')
        if not text:
            continue
        
        candidate_embedding = compute_embeddings([text], model)
        
        # Compute max similarity to any seed defect
        similarities = cosine_similarity_matrix(candidate_embedding, seed_embeddings)
        max_sim = float(similarities[0].max())
        
        # If similarity is above threshold, keep it
        if max_sim >= threshold:
            refined_candidates.append(candidate)
        else:
            # Log low similarity if debugging
            # logger.debug(f"Skipping comment {candidate['comment_id']} due to low semantic similarity: {max_sim:.3f}")
            pass
    
    logger.info(f"Semantic filtering reduced candidates from {len(candidates)} to {len(refined_candidates)}")
    return refined_candidates

def generate_heuristic_candidates() -> Dict[str, Any]:
    """
    Main pipeline for T023:
    1. Load PR comments (from T022)
    2. Extract keyword heuristics
    3. Apply semantic filtering
    4. Save results to data/processed/heuristic_candidates.json
    """
    logger.info("Starting heuristic candidate generation (T023)...")
    
    # Step 1: Load data
    try:
        comments = fetch_pr_review_comments()
        logger.info(f"Loaded {len(comments)} PR comments.")
    except FileNotFoundError as e:
        logger.error(str(e))
        # We cannot proceed without input data. Fail loudly.
        raise e

    # Step 2: Extract keyword heuristics
    keyword_candidates = extract_keyword_heuristics(comments)
    logger.info(f"Generated {len(keyword_candidates)} keyword-based candidates.")

    # Step 3: Semantic filtering
    # Using a moderate threshold to balance precision and recall
    final_candidates = semantic_filter_comments(keyword_candidates, threshold=0.4)
    logger.info(f"Final candidate count after semantic filtering: {len(final_candidates)}")

    # Step 4: Save output
    processed_dir = get_data_processed_dir()
    output_path = processed_dir / "heuristic_candidates.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_candidates, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved heuristic candidates to {output_path}")
    
    return {
        "total_comments_processed": len(comments),
        "keyword_candidates": len(keyword_candidates),
        "final_candidates": len(final_candidates),
        "output_path": str(output_path)
    }

def main():
    """Entry point for the script."""
    try:
        result = generate_heuristic_candidates()
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
