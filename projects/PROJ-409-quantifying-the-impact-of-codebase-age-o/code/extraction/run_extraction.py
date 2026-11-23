import argparse
import csv
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from sibling modules based on provided API surface
from extraction.git_utils import clone_repository, get_all_files_in_repo, calculate_median_commit_age
from extraction.snippet_extractor import extract_snippets_from_directory, TokenCounter, ComplexityCalculator
from utils.logging import get_logger, setup_logging
from utils.config import ensure_directories

logger = get_logger(__name__)

def process_single_repo(
    repo_url: str,
    output_dir: Path,
    min_snippets: int = 100,
    max_repos: Optional[int] = None
) -> bool:
    """
    Process a single repository: clone, extract snippets, calculate ages, and save to CSV.
    
    Returns True if the repo was processed successfully, False if it was skipped due to errors.
    """
    logger.info(f"Processing repository: {repo_url}")
    temp_dir = None
    
    try:
        # Clone the repository
        logger.debug(f"Cloning {repo_url}...")
        temp_dir = clone_repository(repo_url)
        if not temp_dir or not temp_dir.exists():
            logger.error(f"Failed to clone repository: {repo_url}")
            return False
        
        # Get all Python files
        logger.debug(f"Scanning for Python files in {temp_dir}...")
        python_files = get_all_files_in_repo(temp_dir, ext=".py")
        
        if not python_files:
            logger.warning(f"No Python files found in {repo_url}. Skipping.")
            return False
        
        logger.info(f"Found {len(python_files)} Python files in {repo_url}")
        
        # Initialize data collection
        all_snippets = []
        valid_files_count = 0
        
        # Process each file
        for file_path in python_files:
            try:
                # Calculate median commit age for this file
                median_age = calculate_median_commit_age(temp_dir, file_path)
                
                # Extract snippets
                snippets = extract_snippets_from_directory(
                    repo_dir=temp_dir,
                    file_path=file_path,
                    min_tokens=50
                )
                
                if not snippets:
                    continue
                
                valid_files_count += 1
                
                for snippet in snippets:
                    # Enrich snippet with repo and file metadata
                    enriched_snippet = {
                        'snippet_id': f"{repo_url.replace('/', '_')}_{file_path.replace('/', '_')}_{snippet['function_name']}_{snippet['start_line']}",
                        'repo_url': repo_url,
                        'file_path': str(file_path),
                        'median_commit_age': median_age,
                        'snippet_content': snippet['content'],
                        'token_count': snippet['token_count'],
                        'complexity': snippet['complexity'],
                        'token_length': snippet['token_count']  # Explicitly adding token_length as per T010.1
                    }
                    all_snippets.append(enriched_snippet)
                    
            except Exception as e:
                logger.warning(f"Error processing file {file_path} in {repo_url}: {e}")
                continue
        
        if not all_snippets:
            logger.warning(f"No valid snippets extracted from {repo_url}. Skipping.")
            return False
        
        # Write to CSV
        output_file = output_dir / f"extraction_{Path(repo_url).name.replace('/', '_')}.csv"
        if output_file.exists():
            output_file.unlink()
            
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['snippet_id', 'repo_url', 'file_path', 'median_commit_age', 
                         'snippet_content', 'token_count', 'complexity', 'token_length']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_snippets)
        
        logger.info(f"Successfully processed {repo_url}: {len(all_snippets)} snippets extracted "
                   f"from {valid_files_count} files. Saved to {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Critical error processing repository {repo_url}: {e}", exc_info=True)
        return False
    finally:
        # Cleanup temp directory
        if temp_dir and temp_dir.exists():
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to remove temp directory {temp_dir}: {e}")

def main():
    """
    CLI entry point for the extraction pipeline.
    Orchestrates repo cloning, snippet extraction, age calculation, and complexity calculation.
    Implements error handling to skip inaccessible repos while ensuring a minimum of 3 valid repos.
    """
    parser = argparse.ArgumentParser(description="Extract Python snippets from repositories")
    parser.add_argument(
        "--repos",
        type=str,
        nargs="+",
        required=True,
        help="List of repository URLs to process"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/extracted",
        help="Directory to save output CSV files"
    )
    parser.add_argument(
        "--min-valid-repos",
        type=int,
        default=3,
        help="Minimum number of valid repos to process before stopping (default: 3)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    ensure_directories([Path(args.output_dir)])
    
    logger.info(f"Starting extraction pipeline for {len(args.repos)} repositories")
    logger.info(f"Minimum valid repos required: {args.min_valid_repos}")
    
    valid_repos_count = 0
    failed_repos = []
    start_time = time.time()
    
    for repo_url in args.repos:
        # Check if we have enough valid repos
        if valid_repos_count >= args.min_valid_repos:
            logger.info(f"Minimum valid repos ({args.min_valid_repos}) reached. Stopping processing.")
            break
        
        success = process_single_repo(repo_url, Path(args.output_dir))
        
        if success:
            valid_repos_count += 1
        else:
            failed_repos.append(repo_url)
            logger.warning(f"Repository {repo_url} was skipped due to errors.")
    
    elapsed_time = time.time() - start_time
    
    logger.info("=" * 60)
    logger.info(f"Extraction pipeline completed in {elapsed_time:.2f} seconds")
    logger.info(f"Successfully processed: {valid_repos_count} repositories")
    logger.info(f"Failed/Skipped: {len(failed_repos)} repositories")
    
    if failed_repos:
        logger.warning("Failed repositories:")
        for repo in failed_repos:
            logger.warning(f"  - {repo}")
    
    # Final validation
    if valid_repos_count < args.min_valid_repos:
        logger.error(f"CRITICAL: Only {valid_repos_count} valid repos processed. "
                    f"Minimum required: {args.min_valid_repos}")
        sys.exit(1)
    else:
        logger.info(f"SUCCESS: Minimum requirement met with {valid_repos_count} valid repositories.")
        sys.exit(0)

if __name__ == "__main__":
    main()