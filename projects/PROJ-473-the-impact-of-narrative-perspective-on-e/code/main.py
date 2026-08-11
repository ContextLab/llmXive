"""
Main entry point for the narrative perspective analysis pipeline.
Orchestrates extraction, matching, data collection, and analysis steps.
"""
import os
import json
import glob
import logging
import argparse
from pathlib import Path
from extraction import extract_perspective_features
from matching import run_sensitivity_analysis_pipeline
from data_collection import validate_and_clean_responses, aggregate_reader_scores
from data_loader import fetch_gutenberg_stories, load_reader_response_data
from analysis import run_analysis_pipeline
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/logs/pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_extraction_step():
    """
    Runs the perspective feature extraction on the raw corpus.
    Reads from data/raw/ and writes to data/processed/perspective_features.json
    """
    logger.info("Starting Extraction Step...")
    
    # Ensure output directory exists
    os.makedirs("data/processed", exist_ok=True)
    
    # Find all text files in data/raw
    text_files = glob.glob("data/raw/*.txt")
    
    if not text_files:
        logger.warning("No text files found in data/raw/. Skipping extraction.")
        return []
    
    logger.info(f"Found {len(text_files)} text files to process.")
    
    results = []
    for file_path in text_files:
        try:
            record = extract_perspective_features(file_path)
            if record:
                results.append(record)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    # Write results to JSON
    output_path = "data/processed/perspective_features.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Extraction complete. Wrote {len(results)} records to {output_path}")
    return results

def run_data_collection_step():
    """
    Runs the data collection and alignment step.
    Fetches/loads reader responses, validates them, and aligns with perspective features.
    Produces data/processed/aligned_dataset.csv
    """
    logger.info("Starting Data Collection & Alignment Step...")
    
    # Load perspective features (from T016)
    perspective_path = "data/processed/perspective_features.json"
    if not os.path.exists(perspective_path):
        logger.error(f"Perspective features file not found: {perspective_path}. Run extraction step first.")
        return None
    
    with open(perspective_path, 'r', encoding='utf-8') as f:
        perspective_data = json.load(f)
    
    if not perspective_data:
        logger.warning("Perspective features file is empty.")
        return None
    
    # Load reader responses (from T030)
    # The task T030 is responsible for generating data/processed/reader_response.csv
    reader_response_path = "data/processed/reader_response.csv"
    if not os.path.exists(reader_response_path):
        logger.error(f"Reader response file not found: {reader_response_path}. Run data generation step first.")
        return None
    
    responses_df = load_reader_response_data(reader_response_path)
    
    if responses_df is None or responses_df.empty:
        logger.error("Failed to load or empty reader response data.")
        return None
    
    # Validate and clean responses (T031)
    cleaned_responses, excluded_ids = validate_and_clean_responses(responses_df)
    
    if excluded_ids:
        # Log excluded participants
        log_path = "data/logs/data_collection.log"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"Excluded IDs: {excluded_ids}\n")
        logger.info(f"Excluded {len(excluded_ids)} participants due to attention check failures.")
    
    # Aggregate scores (T032)
    aligned_df = aggregate_reader_scores(perspective_data, cleaned_responses)
    
    return aligned_df

def run_analysis_step():
    """
    Runs the full analysis pipeline on the aligned dataset.
    """
    logger.info("Starting Analysis Step...")
    aligned_path = "data/processed/aligned_dataset.csv"
    
    if not os.path.exists(aligned_path):
        logger.error(f"Aligned dataset not found: {aligned_path}. Run data collection step first.")
        return False
    
    success = run_analysis_pipeline(aligned_path)
    if success:
        logger.info("Analysis step completed successfully.")
    else:
        logger.error("Analysis step failed.")
    return success

def main():
    parser = argparse.ArgumentParser(description="Narrative Perspective Analysis Pipeline")
    parser.add_argument("--step", type=str, choices=['extraction', 'collection', 'analysis', 'all'],
                        default='all', help="Which step to run")
    parser.add_argument("--config", type=str, default="code/config.py", help="Path to config file")
    
    args = parser.parse_args()
    
    # Load config if provided
    if args.config and os.path.exists(args.config):
        # In a real scenario, we might dynamically load the config module
        # For now, we assume config is already imported at the top
        logger.info(f"Using config from {args.config}")
    
    if args.step in ['extraction', 'all']:
        run_extraction_step()
    
    if args.step in ['collection', 'all']:
        run_data_collection_step()
    
    if args.step in ['analysis', 'all']:
        run_analysis_step()

if __name__ == "__main__":
    main()
