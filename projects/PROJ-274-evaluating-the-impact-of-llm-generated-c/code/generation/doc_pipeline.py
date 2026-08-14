"""
Documentation Generation Pipeline CLI.

This script orchestrates the documentation generation process for a given repository.
It serves as the entry point invoked by the run-book (quickstart.md).

Usage:
    python code/generation/doc_pipeline.py --repo <repo_url> --commit <commit_hash> --output <output_path>
"""
import argparse
import logging
import sys
import os
import json
from pathlib import Path

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from doc_generation import (
    DataFetchError,
    ensure_dirs,
    fetch_real_repo_data,
    generate_documentation_fallback,
    save_generated_docs,
    log_config_and_checksum
)
from utils.monitor import monitor_execution

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs', 'doc_pipeline.log'))
    ]
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description='Generate documentation for a repository using LLMs.'
    )
    parser.add_argument(
        '--repo',
        required=True,
        help='GitHub repository URL (e.g., https://github.com/user/repo)'
    )
    parser.add_argument(
        '--commit',
        required=True,
        help='Commit hash to pin the repository state'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output path for the generated documentation (e.g., data/processed/docs/repo_docs.md)'
    )
    parser.add_argument(
        '--config',
        default=None,
        help='Path to a JSON configuration file for generation parameters (optional)'
    )

    args = parser.parse_args()

    logger.info(f"Starting documentation generation for {args.repo} at commit {args.commit}")

    try:
        # Ensure output directory exists
        output_path = Path(args.output)
        ensure_dirs(output_path.parent)

        # Fetch real repository data (will fail loudly if fetch fails)
        logger.info(f"Fetching repository data from {args.repo} at commit {args.commit}")
        repo_data = fetch_real_repo_data(args.repo, args.commit)

        if not repo_data:
            raise DataFetchError(f"Failed to fetch data for {args.repo} at {args.commit}")

        # Generate documentation using the fallback pipeline (local model)
        # This satisfies the requirement to have a working pipeline even without API keys
        logger.info("Generating documentation using local fallback model (phi-2)...")
        
        # Load config if provided, otherwise use defaults
        config = {}
        if args.config and os.path.exists(args.config):
            with open(args.config, 'r') as f:
                config = json.load(f)

        # Generate docs
        doc_content = generate_documentation_fallback(
            repo_data=repo_data,
            config=config
        )

        # Save generated docs
        logger.info(f"Saving documentation to {args.output}")
        save_generated_docs(doc_content, str(output_path))

        # Log configuration and checksum for reproducibility
        log_config_and_checksum(
            repo=args.repo,
            commit=args.commit,
            output_file=str(output_path),
            model="phi-2-local",
            config=config
        )

        logger.info(f"Documentation generation completed successfully. Output: {args.output}")
        return 0

    except DataFetchError as e:
        logger.error(f"Data fetch failed: {e}")
        # Re-raise to ensure the pipeline fails loudly as per T055
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
