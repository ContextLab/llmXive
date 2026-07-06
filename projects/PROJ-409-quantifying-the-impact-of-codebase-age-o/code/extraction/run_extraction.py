import argparse
import csv
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from sibling modules using the exact API surface provided
from extraction.git_utils import clone_repository, get_all_files_in_repo, calculate_median_commit_age
from extraction.snippet_extractor import extract_snippets_from_file, ComplexityCalculator, TokenCounter
from utils.logging import get_logger, setup_logging
from utils.config import ensure_directories

# Constants for error handling
MIN_VALID_REPOS = 3
MAX_RETRIES = 3

logger = get_logger(__name__)

def process_single_repo(
    repo_url: str,
    output_dir: Path,
    extraction_log: List[Dict[str, Any]]
) -> bool:
    """
    Process a single repository: clone, extract snippets, calculate metrics.
    
    Returns True if processing succeeded, False if repo was skipped due to errors.
    """
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    repo_dir = output_dir / repo_name
    
    logger.info(f"Processing repository: {repo_url}")
    
    try:
        # Clone repository with retry logic
        success = False
        for attempt in range(MAX_RETRIES):
            try:
                clone_repository(repo_url, repo_dir)
                success = True
                break
            except Exception as e:
                logger.warning(f"Clone attempt {attempt + 1} failed for {repo_url}: {e}")
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        if not success:
            logger.error(f"Failed to clone {repo_url} after {MAX_RETRIES} attempts")
            extraction_log.append({
                "repo_url": repo_url,
                "status": "clone_failed",
                "error": str(e),
                "snippets_count": 0
            })
            return False

        # Get all Python files
        try:
            python_files = get_all_files_in_repo(repo_dir)
            if not python_files:
                logger.warning(f"No Python files found in {repo_url}")
                extraction_log.append({
                    "repo_url": repo_url,
                    "status": "no_python_files",
                    "error": "No .py files found",
                    "snippets_count": 0
                })
                return False
        except Exception as e:
            logger.error(f"Failed to list files in {repo_url}: {e}")
            extraction_log.append({
                "repo_url": repo_url,
                "status": "file_list_failed",
                "error": str(e),
                "snippets_count": 0
            })
            return False

        # Extract snippets and calculate metrics
        all_snippets = []
        complexity_calc = ComplexityCalculator()
        token_counter = TokenCounter()
        
        for file_path in python_files:
            try:
                # Calculate median commit age for this file
                median_age = calculate_median_commit_age(repo_dir, file_path)
                
                # Extract snippets
                snippets = extract_snippets_from_file(file_path)
                
                for snippet in snippets:
                    # Calculate token length and complexity
                    token_len = token_counter.count_tokens(snippet.content)
                    if token_len < 50:
                        continue
                        
                    complexity = complexity_calc.calculate(snippet.content)
                    
                    all_snippets.append({
                        "snippet_id": f"{repo_name}_{file_path.stem}_{snippet.line_start}",
                        "repo_url": repo_url,
                        "file_path": str(file_path),
                        "median_commit_age": median_age,
                        "snippet_content": snippet.content,
                        "token_count": token_len,
                        "complexity": complexity,
                        "token_length": token_len
                    })
            except Exception as e:
                logger.warning(f"Error processing {file_path} in {repo_url}: {e}")
                continue

        if not all_snippets:
            logger.warning(f"No valid snippets extracted from {repo_url}")
            extraction_log.append({
                "repo_url": repo_url,
                "status": "no_snippets",
                "error": "No snippets met token length criteria",
                "snippets_count": 0
            })
            return False

        # Write snippets to CSV
        csv_path = output_dir / f"{repo_name}_snippets.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_snippets[0].keys())
            writer.writeheader()
            writer.writerows(all_snippets)

        logger.info(f"Successfully processed {repo_url}: {len(all_snippets)} snippets")
        extraction_log.append({
            "repo_url": repo_url,
            "status": "success",
            "error": None,
            "snippets_count": len(all_snippets)
        })
        return True

    except Exception as e:
        logger.error(f"Critical error processing {repo_url}: {e}")
        extraction_log.append({
            "repo_url": repo_url,
            "status": "critical_error",
            "error": str(e),
            "snippets_count": 0
        })
        return False

def main():
    parser = argparse.ArgumentParser(description="Extract code snippets from repositories")
    parser.add_argument(
        "--repos", 
        nargs="+", 
        required=True,
        help="List of repository URLs to process"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/extracted"),
        help="Directory to store extracted data"
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=Path("data/extracted/extraction_log.json"),
        help="Path to save extraction log"
    )
    args = parser.parse_args()

    # Setup logging and directories
    setup_logging(level=logging.INFO)
    ensure_directories([args.output_dir])

    extraction_log = []
    valid_repos = 0
    total_repos = len(args.repos)

    logger.info(f"Starting extraction for {total_repos} repositories")
    logger.info(f"Minimum valid repos required: {MIN_VALID_REPOS}")

    for repo_url in args.repos:
        success = process_single_repo(repo_url, args.output_dir, extraction_log)
        if success:
            valid_repos += 1
        
        # Check if we've met the minimum requirement and can stop early
        # (Optional optimization: if we have enough valid repos and want to save time)
        if valid_repos >= MIN_VALID_REPOS and valid_repos < total_repos:
            logger.info(f"Minimum {MIN_VALID_REPOS} valid repos reached. Continuing to process remaining repos...")
            # We continue processing to get maximum data, but we've met the requirement

    # Save extraction log
    import json
    args.log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(args.log_file, 'w') as f:
        json.dump(extraction_log, f, indent=2)

    # Final summary
    logger.info(f"Extraction complete. Valid repos: {valid_repos}/{total_repos}")
    
    if valid_repos < MIN_VALID_REPOS:
        logger.error(f"Failed to meet minimum requirement of {MIN_VALID_REPOS} valid repositories")
        sys.exit(1)
    else:
        logger.info("Minimum repository requirement satisfied")
        sys.exit(0)

if __name__ == "__main__":
    main()