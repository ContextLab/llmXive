"""
Task T021e: Generate repo_covariates.json
Aggregates LOC, CC, and Doc Quality scores for selected repositories.
Input: data/raw/repo_selection_rubric.json (output of T021d/T021f)
Output: data/raw/repo_covariates.json
"""
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure project paths are setup
from utils.setup_paths import ensure_project_dirs

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("run_covariate_collection")

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(filepath: str, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved covariates to {filepath}")

def main():
    """
    Main entry point for T021e.
    1. Load repo_selection_rubric.json (post-gate).
    2. Extract selected repositories.
    3. Aggregate LOC, CC, and Doc Quality scores.
    4. Write to data/raw/repo_covariates.json.
    """
    # Setup paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    input_path = project_root / "data" / "raw" / "repo_selection_rubric.json"
    output_path = project_root / "data" / "raw" / "repo_covariates.json"

    # Ensure directories exist
    ensure_project_dirs()

    logger.info(f"Loading selection rubric from {input_path}")
    try:
        rubric_data = load_json_file(str(input_path))
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    if "selected_repos" not in rubric_data:
        logger.error("Input file missing 'selected_repos' key. Has T021d/T021f run?")
        sys.exit(1)

    selected_repos = rubric_data["selected_repos"]
    logger.info(f"Found {len(selected_repos)} selected repositories.")

    covariates = []
    
    # We expect the selection rubric to contain the metrics for the selected repos
    # or we need to look them up from the metrics collection if not embedded.
    # Based on T021d description: "Input: ... data/raw/doc_quality_scores.json"
    # and T021d logic: "Filter... then apply tolerance... Output: repo_selection_rubric.json"
    # The rubric likely contains the final list of repos with their metrics attached 
    # or we need to cross-reference. 
    # To be robust, we assume the rubric contains the necessary data or we load 
    # doc_quality_scores.json and repo_metrics.json if the rubric only has IDs.
    
    # Strategy: Try to find metrics in the selected_repos list first.
    # If not present, we might need to load auxiliary files.
    # However, T021d output schema is: {selected_repos: [...], tolerance_check: ...}
    # The selected_repos list likely contains the full repo objects including metrics
    # if the filtering logic passed them through. If not, we must load them.
    
    # Let's assume the selected_repos list contains objects with 'url', 'loc', 'cc', 'doc_quality'
    # If the structure is just URLs, we need to load the metrics files.
    # Given the tight coupling in Phase 2, we will attempt to load auxiliary files 
    # if the direct data is missing.

    doc_quality_path = project_root / "data" / "raw" / "doc_quality_scores.json"
    metrics_path = project_root / "data" / "raw" / "repo_metrics.json"

    doc_scores = {}
    repo_metrics = {}

    if os.path.exists(doc_quality_path):
        doc_scores = load_json_file(str(doc_quality_path))
    
    if os.path.exists(metrics_path):
        repo_metrics = load_json_file(str(metrics_path))

    for repo in selected_repos:
        repo_id = repo.get("url") or repo.get("repo_name") or repo.get("id")
        if not repo_id:
            logger.warning(f"Repository entry missing identifier: {repo}")
            continue

        # Extract metrics
        loc = None
        cc = None
        doc_quality = None

        # Try direct access first
        if "loc" in repo:
            loc = repo["loc"]
        if "cc" in repo:
            cc = repo["cc"]
        if "doc_quality" in repo:
            doc_quality = repo["doc_quality"]

        # Fallback to auxiliary files if not in the repo object
        if loc is None or cc is None:
            # Look in repo_metrics
            for m in repo_metrics.get("metrics", []):
                if m.get("url") == repo_id or m.get("repo_name") == repo_id:
                    loc = m.get("loc")
                    cc = m.get("cc")
                    break

        if doc_quality is None:
            # Look in doc_scores
            for d in doc_scores.get("scores", []):
                if d.get("url") == repo_id or d.get("repo_name") == repo_id:
                    doc_quality = d.get("score")
                    break

        if loc is None or cc is None or doc_quality is None:
            logger.warning(f"Could not find complete covariates for {repo_id}. Skipping.")
            continue

        covariates.append({
            "url": repo_id,
            "loc": loc,
            "cc": cc,
            "doc_quality_score": doc_quality
        })

    if not covariates:
        logger.error("No covariates could be extracted. Check input data integrity.")
        sys.exit(1)

    output_data = {
        "covariates": covariates,
        "count": len(covariates),
        "generated_from": str(input_path)
    }

    save_json_file(str(output_path), output_data)
    logger.info("T021e completed successfully.")

if __name__ == "__main__":
    main()