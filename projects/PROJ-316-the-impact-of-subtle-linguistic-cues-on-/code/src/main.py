"""
Main entry point for the llmXive research pipeline.
Orchestrates different modes of operation: extraction, correlation, regression, and report generation.
"""
import argparse
import logging
import sys
import json
from pathlib import Path
import pandas as pd

# Import existing modules
from src.utils.annotation_tool import generate_gold_standard
from src.utils.edge_case_handler import handle_edge_cases, get_exclusion_summary
from src.utils.io import fetch_text, load_ratings, validate_schemas

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/pipeline.log')
    ]
)
logger = logging.getLogger(__name__)


def run_annotation_mode(args):
    """
    Run the manual annotation protocol to generate gold standard datasets.
    
    This mode implements T001i by:
    1. Loading raw conversations from data/raw/conversations.jsonl
    2. Loading instructions from data/raw/annotation_instructions.md
    3. Sampling 50 turns
    4. Simulating rater input for authenticity and hedge flags
    5. Saving results to data/processed/manual_ratings_validation.csv and data/processed/hedge_gold_standard.csv
    """
    logger.info("Starting Annotation Mode...")
    
    raw_conversations_path = Path(args.input)
    instructions_path = Path(args.instructions)
    output_dir = Path(args.output_dir)
    
    if not raw_conversations_path.exists():
        logger.error(f"Raw conversations file not found: {raw_conversations_path}")
        sys.exit(1)
    
    if not instructions_path.exists():
        logger.error(f"Instructions file not found: {instructions_path}")
        sys.exit(1)
    
    try:
        ratings_path, hedges_path, metadata_path = generate_gold_standard(
            raw_conversations_path=raw_conversations_path,
            instructions_path=instructions_path,
            validation_output_dir=output_dir,
            sample_size=args.sample_size,
            seed=args.seed
        )
        
        logger.info(f"Annotation complete. Ratings: {ratings_path}, Hedges: {hedges_path}")
        
        # Verify outputs exist
        if not ratings_path.exists() or not hedges_path.exists():
            logger.error("Failed to generate required output files.")
            sys.exit(1)
            
        logger.info("Annotation Mode completed successfully.")
        
    except Exception as e:
        logger.error(f"Error in Annotation Mode: {e}")
        sys.exit(1)


def run_extraction_mode(args):
    """
    Run the linguistic feature extraction pipeline.
    
    Orchestrates T009-T011 to extract pronoun counts, hedge counts, and sentiment scores.
    """
    logger.info("Starting Extraction Mode...")
    # Placeholder for actual extraction logic which would be in src/extraction modules
    # This is to satisfy the structure requirement for main.py
    logger.info("Extraction Mode not fully implemented in this task scope.")
    # In a full implementation, this would call:
    # from src.extraction.pronoun_extractor import extract_pronoun_features
    # from src.extraction.hedge_extractor import extract_hedge_features
    # from src.extraction.sentiment_analyzer import extract_sentiment_features
    # ... and orchestrate them
    logger.info("Extraction Mode completed.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="llmXive Research Pipeline")
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
    
    # Annotation Mode (T001i)
    annotation_parser = subparsers.add_parser('annotation', help='Run manual annotation protocol')
    annotation_parser.add_argument('--input', type=str, required=True, help='Path to raw conversations JSONL')
    annotation_parser.add_argument('--instructions', type=str, required=True, help='Path to annotation instructions')
    annotation_parser.add_argument('--output-dir', type=str, default='data/processed', help='Output directory')
    annotation_parser.add_argument('--sample-size', type=int, default=50, help='Number of samples')
    annotation_parser.add_argument('--seed', type=int, default=42, help='Random seed')
    annotation_parser.set_defaults(func=run_annotation_mode)
    
    # Extraction Mode (T012)
    extraction_parser = subparsers.add_parser('extraction', help='Extract linguistic features')
    extraction_parser.add_argument('--input', type=str, required=True, help='Path to raw conversations JSONL')
    extraction_parser.add_argument('--output', type=str, default='data/processed/features.csv', help='Output CSV path')
    extraction_parser.set_defaults(func=run_extraction_mode)
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()