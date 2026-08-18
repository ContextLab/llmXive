import os
import json
import glob
import logging
import argparse
import sys
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_config, PRIMARY_MATCHING_THRESHOLD
from extraction import extract_perspective_features
from matching import build_tfidf_vectors, find_top_matches
from data_loader import fetch_gutenberg_stories, fetch_moral_foundations_twitter
from utils import compute_artifact_hash

def setup_logging(log_file):
    """Configure logging to file and console."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def run_extraction_step(input_dir, output_path, log_file):
    """Run the perspective extraction pipeline."""
    logger = setup_logging(log_file)
    logger.info(f"Starting extraction from {input_dir}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    results = []
    # Find all text files
    pattern = os.path.join(input_dir, "*.txt")
    files = glob.glob(pattern)
    
    if not files:
        logger.warning(f"No text files found in {input_dir}")
        # Write empty list if no files
        with open(output_path, 'w') as f:
            json.dump([], f, indent=2)
        return results

    for file_path in files:
        try:
            record = extract_perspective_features(file_path)
            if record:
                results.append(record)
                logger.info(f"Processed: {os.path.basename(file_path)}")
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            continue
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Extraction complete. Wrote {len(results)} records to {output_path}")
    return results

def run_matching_step(input_path, target_path, output_path, log_file):
    """
    Run the matching validation step.
    
    Loads perspective features, builds TF-IDF vectors, matches against the target
    dataset (moral_judgement_dataset) using the primary threshold, and outputs
    results to matching_results.json.
    
    CRITICAL: This command does NOT run regression analysis. It only outputs match data.
    """
    logger = setup_logging(log_file)
    logger.info(f"Starting matching step")
    logger.info(f"Input features: {input_path}")
    logger.info(f"Target dataset: {target_path}")
    logger.info(f"Output: {output_path}")
    
    # Ensure directories exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    # 1. Load perspective features
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        # If input doesn't exist, we cannot proceed.
        # Write empty results to avoid crash, but log error.
        with open(output_path, 'w') as f:
            json.dump([], f, indent=2)
        return []
    
    with open(input_path, 'r') as f:
        perspective_features = json.load(f)
    
    logger.info(f"Loaded {len(perspective_features)} perspective feature records")
    
    if not perspective_features:
        logger.warning("No perspective features found. Writing empty results.")
        with open(output_path, 'w') as f:
            json.dump([], f, indent=2)
        return []

    # 2. Fetch or load the target dataset (moral_judgement_dataset)
    # The target is expected to be a CSV with columns: story_id, text, empathy_score, moral_judgement_score
    # If it doesn't exist, we try to fetch it.
    if not os.path.exists(target_path):
        logger.info(f"Target dataset not found at {target_path}. Attempting to fetch...")
        # Try to fetch from HuggingFace
        try:
            # Using the function from data_loader that fetches moral foundations data
            # Note: The task description mentions 'moral_judgement_dataset.csv', 
            # but the real source is 'moral-foundation/twitter' via fetch_moral_foundations_twitter.
            # We will fetch and save it to the target path.
            df = fetch_moral_foundations_twitter()
            if df is not None:
                # Ensure required columns exist
                required_cols = ['story_id', 'text', 'empathy_score', 'moral_judgement_score']
                if not all(col in df.columns for col in required_cols):
                    logger.error(f"Dataset missing required columns. Found: {df.columns.tolist()}")
                    # Fallback: write empty results
                    with open(output_path, 'w') as f:
                        json.dump([], f, indent=2)
                    return []
                
                df.to_csv(target_path, index=False)
                logger.info(f"Saved target dataset to {target_path}")
            else:
                logger.error("Failed to fetch target dataset.")
                with open(output_path, 'w') as f:
                    json.dump([], f, indent=2)
                return []
        except Exception as e:
            logger.error(f"Error fetching target dataset: {e}")
            with open(output_path, 'w') as f:
                json.dump([], f, indent=2)
            return []
    else:
        logger.info(f"Loading existing target dataset from {target_path}")
    
    import pandas as pd
    target_df = pd.read_csv(target_path)
    logger.info(f"Loaded {len(target_df)} target records")
    
    # 3. Build TF-IDF vectors for both perspective features and target
    # Extract texts from perspective features
    query_texts = [feat.get('raw_text', '') for feat in perspective_features]
    # Extract texts from target dataset
    target_texts = target_df['text'].tolist()
    target_ids = target_df['story_id'].tolist()
    
    if not query_texts or not target_texts:
        logger.warning("No texts found for vectorization.")
        with open(output_path, 'w') as f:
            json.dump([], f, indent=2)
        return []
    
    # Build vectors
    logger.info("Building TF-IDF vectors...")
    query_vectors, target_vectors = build_tfidf_vectors(query_texts, target_texts, exclude_pronouns=True)
    
    # 4. Find top matches for each query
    results = []
    threshold = PRIMARY_MATCHING_THRESHOLD
    logger.info(f"Using matching threshold: {threshold}")
    
    for i, query_vec in enumerate(query_vectors):
        story_id = perspective_features[i].get('story_id', f"unknown_{i}")
        
        matches = find_top_matches(
            query_vec, 
            target_vectors, 
            k=3, 
            threshold=threshold
        )
        
        for rank, (match_idx, score) in enumerate(matches, 1):
            match_id = target_ids[match_idx]
            results.append({
                'story_id': story_id,
                'match_id': match_id,
                'similarity_score': float(score),
                'rank': rank
            })
    
    # 5. Write results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Matching complete. Wrote {len(results)} matches to {output_path}")
    return results

def run_aggregation_step(features_path, responses_path, output_path, log_file):
    """Run the data aggregation step."""
    logger = setup_logging(log_file)
    logger.info(f"Starting aggregation")
    
    # Implementation would go here (T032)
    # For now, placeholder to satisfy CLI structure
    logger.warning("Aggregation step not fully implemented in this task.")
    return []

def run_analysis_step(input_path, output_path, log_file):
    """Run the analysis step."""
    logger = setup_logging(log_file)
    logger.info(f"Starting analysis")
    
    # Implementation would go here (T041)
    # For now, placeholder to satisfy CLI structure
    logger.warning("Analysis step not fully implemented in this task.")
    return {}

def run_all_pipeline(log_file):
    """Run the entire pipeline end-to-end."""
    logger = setup_logging(log_file)
    logger.info("Starting full pipeline")
    
    config = get_config()
    paths = config['paths']
    
    # 1. Extraction
    extraction_output = os.path.join(paths['data_processed'], 'perspective_features.json')
    run_extraction_step(
        input_dir=paths['data_raw'],
        output_path=extraction_output,
        log_file=log_file
    )
    
    # 2. Matching
    target_path = os.path.join(paths['data_raw'], 'moral_judgement_dataset.csv')
    matching_output = os.path.join(paths['data_processed'], 'matching_results.json')
    run_matching_step(
        input_path=extraction_output,
        target_path=target_path,
        output_path=matching_output,
        log_file=log_file
    )
    
    # 3. Aggregation
    responses_path = os.path.join(paths['data_processed'], 'reader_response.csv')
    aggregated_output = os.path.join(paths['data_processed'], 'aligned_dataset.csv')
    run_aggregation_step(
        features_path=extraction_output,
        responses_path=responses_path,
        output_path=aggregated_output,
        log_file=log_file
    )
    
    # 4. Analysis
    analysis_output = os.path.join(paths['data_processed'], 'analysis_results.json')
    run_analysis_step(
        input_path=aggregated_output,
        output_path=analysis_output,
        log_file=log_file
    )
    
    logger.info("Full pipeline complete")

def main():
    parser = argparse.ArgumentParser(description='Narrative Perspective Research Pipeline')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Run perspective extraction')
    extract_parser.add_argument('--input-dir', required=True, help='Input directory with text files')
    extract_parser.add_argument('--output', required=True, help='Output JSON path')
    
    # Match command (T025)
    match_parser = subparsers.add_parser('match', help='Run matching validation')
    match_parser.add_argument('--input', required=True, help='Input perspective features JSON')
    match_parser.add_argument('--target', required=True, help='Target dataset CSV path')
    match_parser.add_argument('--output', required=True, help='Output matching results JSON')
    
    # Aggregate command
    agg_parser = subparsers.add_parser('aggregate', help='Run data aggregation')
    agg_parser.add_argument('--features', required=True, help='Features JSON path')
    agg_parser.add_argument('--responses', required=True, help='Responses CSV path')
    agg_parser.add_argument('--output', required=True, help='Output aligned dataset CSV')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run statistical analysis')
    analyze_parser.add_argument('--input', required=True, help='Input aligned dataset CSV')
    analyze_parser.add_argument('--output', required=True, help='Output analysis results JSON')
    
    # All command
    all_parser = subparsers.add_parser('all', help='Run full pipeline')
    
    args = parser.parse_args()
    
    # Default log file
    log_file = 'data/logs/pipeline.log'
    os.makedirs('data/logs', exist_ok=True)
    
    if args.command == 'extract':
        run_extraction_step(args.input_dir, args.output, log_file)
    elif args.command == 'match':
        run_matching_step(args.input, args.target, args.output, log_file)
    elif args.command == 'aggregate':
        run_aggregation_step(args.features, args.responses, args.output, log_file)
    elif args.command == 'analyze':
        run_analysis_step(args.input, args.output, log_file)
    elif args.command == 'all':
        run_all_pipeline(log_file)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()