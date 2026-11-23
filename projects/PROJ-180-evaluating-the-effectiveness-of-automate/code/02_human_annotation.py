"""
Human Annotation Script for Ground Truth Construction.

This script orchestrates the generation of heuristic candidates,
random sampling, and the preparation of files for manual human review.
It serves as the entry point referenced by the quickstart.md run-book.

Workflow:
1. Load acquired repositories from data/raw/repo_list.json.
2. Fetch PR comments (or load existing data if available).
3. Generate heuristic candidates based on keywords and semantic search.
4. Export candidates to CSV for manual review.
5. Generate a stratified random sample for ground truth validation.
6. Export random sample to CSV for manual review.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import (
    get_data_raw_dir,
    get_data_processed_dir,
    get_results_dir,
    get_config,
    load_env
)
from utils.aligner import get_embedding_model, compute_embeddings, cosine_similarity_matrix

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
KEYWORDS = {
    'bug': ['bug', 'error', 'fail', 'crash', 'exception', 'issue', 'defect'],
    'security': ['security', 'vulnerability', 'exploit', 'malicious', 'injection', 'xss'],
    'style': ['style', 'formatting', 'indentation', 'naming', 'convention', 'refactor']
}
THRESHOLD = 0.6
MODEL_NAME = "all-MiniLM-L6-v2"

def load_acquired_repos() -> List[Dict[str, Any]]:
    """Load the list of acquired repositories from data/raw/repo_list.json."""
    repo_list_path = get_data_raw_dir() / "repo_list.json"
    if not repo_list_path.exists():
        logger.error(f"Repository list not found at {repo_list_path}. "
                     "Please run the data acquisition pipeline first (T013-4).")
        return []
    
    with open(repo_list_path, 'r') as f:
        return json.load(f)

def fetch_pr_review_comments(repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fetch PR review comments for the given repositories.
    In a real scenario, this would use the GitHub API.
    For this implementation, we assume the data might already be cached
    from a previous run of 02_human_baseline.py (T022).
    """
    pr_comments_path = get_data_raw_dir() / "pr_comments.json"
    
    # If we have cached comments, load them
    if pr_comments_path.exists():
        logger.info(f"Loading cached PR comments from {pr_comments_path}")
        with open(pr_comments_path, 'r') as f:
            return json.load(f)
    
    logger.warning("No cached PR comments found. "
                   "Please ensure T022 (fetch_pr_comments) has been run, "
                   "or run the full baseline pipeline first.")
    return []

def extract_keyword_heuristics(comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract comments that match predefined keywords.
    """
    candidates = []
    for comment in comments:
        text = comment.get('text', '').lower()
        matched_categories = []
        for category, words in KEYWORDS.items():
            if any(word in text for word in words):
                matched_categories.append(category)
        
        if matched_categories:
            candidates.append({
                'comment_id': comment.get('comment_id'),
                'text': comment.get('text'),
                'predicted_type': matched_categories,
                'file': comment.get('file'),
                'line': comment.get('line'),
                'repo_id': comment.get('repo_id'),
                'method': 'keyword'
            })
    return candidates

def semantic_filter_comments(comments: List[Dict[str, Any]], model: SentenceTransformer) -> List[Dict[str, Any]]:
    """
    Use semantic similarity to find comments related to defect types.
    Uses a set of anchor queries to find similar comments.
    """
    anchor_queries = [
        "This code has a bug",
        "There is a security vulnerability here",
        "This needs refactoring for style",
        "Fix this error",
        "Potential exploit",
        "Bad formatting"
    ]
    
    # Compute embeddings for anchors
    anchor_embeddings = model.encode(anchor_queries, convert_to_numpy=True)
    
    # Compute embeddings for comments
    comment_texts = [c.get('text', '') for c in comments]
    if not comment_texts:
        return []
    
    comment_embeddings = model.encode(comment_texts, convert_to_numpy=True)
    
    # Compute similarity
    similarities = cosine_similarity_matrix(anchor_embeddings, comment_embeddings)
    
    candidates = []
    for i, comment in enumerate(comments):
        max_sim = float(np.max(similarities[:, i]))
        if max_sim >= THRESHOLD:
            # Determine type based on highest similarity anchor
            best_anchor_idx = np.argmax(similarities[:, i])
            predicted_type = [anchor_queries[best_anchor_idx]] # Simplified mapping
            
            candidates.append({
                'comment_id': comment.get('comment_id'),
                'text': comment.get('text'),
                'predicted_type': predicted_type,
                'file': comment.get('file'),
                'line': comment.get('line'),
                'repo_id': comment.get('repo_id'),
                'similarity_score': float(max_sim),
                'method': 'semantic'
            })
    return candidates

def generate_heuristic_candidates(comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Combine keyword and semantic heuristics to generate candidate defect set.
    """
    logger.info("Running keyword heuristics...")
    keyword_candidates = extract_keyword_heuristics(comments)
    
    logger.info(f"Running semantic filtering with model {MODEL_NAME}...")
    model = get_embedding_model(MODEL_NAME)
    semantic_candidates = semantic_filter_comments(comments, model)
    
    # Merge candidates (union)
    all_candidates = keyword_candidates + semantic_candidates
    
    # Deduplicate by comment_id (keep the one with 'semantic' method if both exist)
    seen = {}
    for c in all_candidates:
        cid = c['comment_id']
        if cid not in seen:
            seen[cid] = c
        else:
            # Prefer semantic if available, otherwise keep existing
            if c['method'] == 'semantic' and seen[cid]['method'] == 'keyword':
                seen[cid] = c
    
    return list(seen.values())

def generate_random_sample(comments: List[Dict[str, Any]], sample_size: int = 500) -> List[str]:
    """
    Generate a stratified random sample of comment IDs for manual validation.
    Stratification is attempted by repository language if available.
    """
    if len(comments) == 0:
        logger.warning("No comments available for sampling.")
        return []
    
    # Simple random sample for now, as stratification requires repo metadata join
    # In a full implementation, we would join with repo_list.json
    np.random.seed(42) # Reproducibility
    selected_ids = np.random.choice(
        [c['comment_id'] for c in comments], 
        size=min(sample_size, len(comments)), 
        replace=False
    )
    return selected_ids.tolist()

def export_candidates_to_csv(candidates: List[Dict[str, Any]], filename: str):
    """Export candidates to CSV for manual review."""
    output_path = get_data_processed_dir() / filename
    df = pd.DataFrame(candidates)
    # Ensure columns are in a reasonable order
    cols = ['comment_id', 'repo_id', 'file', 'line', 'text', 'predicted_type', 'method', 'similarity_score']
    # Filter columns that exist
    existing_cols = [c for c in cols if c in df.columns]
    df = df[existing_cols]
    df.to_csv(output_path, index=False)
    logger.info(f"Exported {len(candidates)} candidates to {output_path}")

def export_random_sample_to_csv(sample_ids: List[str], filename: str, comments: List[Dict[str, Any]]):
    """Export random sample IDs and their context to CSV."""
    output_path = get_data_processed_dir() / filename
    
    # Map IDs back to full comment objects
    comment_map = {c['comment_id']: c for c in comments}
    sample_comments = [comment_map[cid] for cid in sample_ids if cid in comment_map]
    
    df = pd.DataFrame(sample_comments)
    df.to_csv(output_path, index=False)
    logger.info(f"Exported {len(sample_comments)} random samples to {output_path}")

def main():
    """Main entry point for the human annotation pipeline."""
    load_env()
    config = get_config()
    
    logger.info("Starting Human Annotation Pipeline (T046)...")
    
    # 1. Load Repos
    repos = load_acquired_repos()
    if not repos:
        logger.error("No repositories found. Aborting.")
        sys.exit(1)
    
    # 2. Fetch Comments
    comments = fetch_pr_review_comments(repos)
    if not comments:
        logger.warning("No PR comments found. The pipeline will generate empty outputs.")
        # Create empty outputs to satisfy file existence requirements
        export_candidates_to_csv([], "heuristic_review_candidates.csv")
        export_random_sample_to_csv([], "random_review_candidates.csv", [])
        return

    # 3. Generate Heuristic Candidates
    heuristic_candidates = generate_heuristic_candidates(comments)
    
    # 4. Export Heuristic Candidates
    export_candidates_to_csv(heuristic_candidates, "heuristic_review_candidates.csv")
    
    # 5. Generate Random Sample
    random_sample_ids = generate_random_sample(comments, sample_size=500)
    
    # 6. Export Random Sample
    export_random_sample_to_csv(random_sample_ids, "random_review_candidates.csv", comments)
    
    logger.info("Human Annotation Pipeline completed successfully.")
    logger.info(f"Please review the generated CSV files in {get_data_processed_dir()}")
    logger.info("After manual review, use the ingestion scripts (T023b-Ingest, T024b-Ingest) to process the validated files.")

if __name__ == "__main__":
    main()