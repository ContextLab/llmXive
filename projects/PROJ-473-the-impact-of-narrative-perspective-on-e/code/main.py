import os
import json
import glob
import logging
import argparse
import sys
from pathlib import Path

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import get_config
from extraction import extract_perspective_features
from matching import build_tfidf_vectors, find_top_matches, run_sensitivity_analysis_pipeline
from data_collection import validate_and_clean_responses, aggregate_reader_scores
from analysis import run_regression_analysis, apply_bonferroni_correction, calculate_vif, generate_scatter_plot, run_analysis_pipeline
from utils import scan_for_pii, compute_artifact_hash

# Configure logging to ensure directories exist before handlers are created
def setup_logging():
    config = get_config()
    log_dir = config['paths']['logs']
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'pipeline.log')
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
    except Exception as e:
        print(f"Warning: Could not create file handler for {log_file}: {e}")
        file_handler = None

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    if file_handler:
        root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger

logger = setup_logging()

def run_extraction_step(input_dir, output_file):
    """
    Runs the perspective feature extraction pipeline.
    """
    logger.info(f"Starting extraction on {input_dir}")
    
    if not os.path.exists(input_dir):
        logger.error(f"Input directory does not exist: {input_dir}")
        return False

    results = []
    files = glob.glob(os.path.join(input_dir, "*.txt"))
    if not files:
        logger.warning(f"No .txt files found in {input_dir}")
        # Try to find other common extensions if needed, but spec says txt
    
    for file_path in files:
        try:
            record = extract_perspective_features(file_path)
            if record:
                results.append(record)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Extraction complete. Wrote {len(results)} records to {output_file}")
    return True

def run_matching_step(input_file, target_file, output_file):
    """
    Runs the matching validation step (T025).
    CLI: python code/main.py match --input ... --target ... --output ...
    
    Logic:
    1. Load perspective features (stories).
    2. Load target dataset (moral_judgement_dataset.csv).
    3. Build TF-IDF vectors for stories (excluding pronouns).
    4. Match stories against target dataset using PRIMARY_MATCHING_THRESHOLD (0.30).
    5. Output results to matching_results.json.
    
    CRITICAL: This command MUST NOT run regression analysis.
    """
    logger.info("Starting matching step (T025)")
    
    if not os.path.exists(input_file):
        logger.error(f"Input file does not exist: {input_file}")
        return False
    
    if not os.path.exists(target_file):
        logger.error(f"Target file does not exist: {target_file}")
        return False

    # 1. Load perspective features
    with open(input_file, 'r', encoding='utf-8') as f:
        stories = json.load(f)
    logger.info(f"Loaded {len(stories)} stories from {input_file}")

    # 2. Load target dataset
    import pandas as pd
    try:
        target_df = pd.read_csv(target_file)
    except Exception as e:
        logger.error(f"Failed to load target CSV {target_file}: {e}")
        return False
    
    logger.info(f"Loaded {len(target_df)} records from {target_file}")

    # Prepare texts for matching
    # Stories: use raw_text (or summary if raw_text is truncated)
    # Target: use scenario_description or text_reflection if available, else first text column
    story_texts = []
    story_ids = []
    for story in stories:
        # Use raw_text if available, otherwise summary
        text = story.get('raw_text', '')
        if not text and 'summary' in story:
            text = story['summary']
        if text:
            story_texts.append(text)
            story_ids.append(story.get('story_id', 'unknown'))

    if not story_texts:
        logger.error("No valid story texts found for matching.")
        return False

    # Determine target text column
    target_text_col = None
    possible_cols = ['scenario_description', 'text_reflection', 'description', 'text']
    for col in possible_cols:
        if col in target_df.columns:
            target_text_col = col
            break
    
    if not target_text_col:
        logger.error(f"Could not find a valid text column in target CSV. Columns: {target_df.columns.tolist()}")
        return False

    target_texts = target_df[target_text_col].dropna().astype(str).tolist()
    target_ids = target_df.index.tolist() # Use index as temporary ID if no ID column

    # 3. Build TF-IDF vectors
    # Use the function from matching.py
    from matching import build_tfidf_vectors
    try:
        story_vectors, target_vectors, vectorizer = build_tfidf_vectors(
            story_texts, 
            candidate_texts=target_texts, 
            exclude_pronouns=True
        )
    except Exception as e:
        logger.error(f"TF-IDF vectorization failed: {e}")
        return False

    # 4. Match against target dataset
    # We need to find top matches for each story against the target candidates
    # find_top_matches expects query_vector, candidate_vectors, k
    # We need to run this for each story
    
    config = get_config()
    threshold = config['PRIMARY_MATCHING_THRESHOLD']
    k = config['hyperparameters']['k_matches']
    
    results = []
    unmatched_count = 0
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    for i, story_id in enumerate(story_ids):
        query_vec = story_vectors[i]
        matches = find_top_matches(query_vec, target_vectors, k=k)
        
        # Filter by threshold
        valid_matches = []
        for rank, (sim_score, target_idx) in enumerate(matches, 1):
            if sim_score >= threshold:
                # Map back to target ID
                # target_ids is index list from target_df
                # But we need to handle if target_df has a specific ID column
                # For now, use the index or a generated ID
                actual_target_id = target_ids[target_idx] if target_idx < len(target_ids) else f"target_{target_idx}"
                # If target_df has an ID column, use that
                if 'story_id' in target_df.columns:
                    actual_target_id = target_df.iloc[target_idx]['story_id']
                elif 'id' in target_df.columns:
                    actual_target_id = target_df.iloc[target_idx]['id']
                
                valid_matches.append({
                    "story_id": story_id,
                    "match_id": str(actual_target_id),
                    "similarity_score": float(sim_score),
                    "rank": rank
                })
            else:
                # Since matches are sorted by score descending, if we drop below threshold, we stop
                break
        
        if not valid_matches:
            unmatched_count += 1
            logger.debug(f"Story {story_id} had no matches above threshold {threshold}")
        else:
            results.extend(valid_matches)

    # 5. Output results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Matching complete. Found {len(results)} matches. {unmatched_count} stories unmatched.")
    logger.info(f"Wrote results to {output_file}")
    
    return True

def run_data_collection_step(input_file, output_file):
    """
    Runs the data collection validation step.
    """
    logger.info(f"Starting data collection validation on {input_file}")
    if not os.path.exists(input_file):
        logger.error(f"Input file does not exist: {input_file}")
        return False
    
    raw_data = pd.read_csv(input_file)
    cleaned = validate_and_clean_responses(raw_data)
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    cleaned.to_csv(output_file, index=False)
    logger.info(f"Data collection validation complete. Wrote {len(cleaned)} records to {output_file}")
    return True

def run_aggregation_step(features_file, responses_file, output_file):
    """
    Runs the aggregation step to align perspective features with reader responses.
    """
    logger.info(f"Starting aggregation: features={features_file}, responses={responses_file}")
    if not os.path.exists(features_file) or not os.path.exists(responses_file):
        logger.error("Missing input files for aggregation")
        return False
    
    features = aggregate_reader_scores(features_file, responses_file)
    if features is None or len(features) == 0:
        logger.error("Aggregation resulted in empty dataset")
        return False
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    features.to_csv(output_file, index=False)
    logger.info(f"Aggregation complete. Wrote {len(features)} records to {output_file}")
    return True

def run_analysis_step(input_file, output_file):
    """
    Runs the full analysis pipeline (regression, VIF, etc.).
    """
    logger.info(f"Starting analysis on {input_file}")
    if not os.path.exists(input_file):
        logger.error(f"Input file does not exist: {input_file}")
        return False
    
    results = run_analysis_pipeline(input_file)
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis complete. Wrote results to {output_file}")
    return True

def run_all_pipeline():
    """
    Runs the entire pipeline: Extraction -> Matching -> Data Collection -> Aggregation -> Analysis.
    """
    logger.info("Starting full pipeline")
    config = get_config()
    
    paths = config['paths']
    
    # 1. Extraction
    extraction_input = paths['data_raw']
    extraction_output = os.path.join(paths['data_processed'], 'perspective_features.json')
    if not run_extraction_step(extraction_input, extraction_output):
        logger.error("Extraction failed. Stopping pipeline.")
        return False
    
    # 2. Matching
    matching_input = extraction_output
    matching_target = os.path.join(paths['data_raw'], 'moral_judgement_dataset.csv')
    matching_output = os.path.join(paths['data_processed'], 'matching_results.json')
    if not run_matching_step(matching_input, matching_target, matching_output):
        logger.error("Matching failed. Stopping pipeline.")
        return False
    
    # 3. Data Collection (if raw response data exists)
    # This step might be optional depending on data availability
    # Assuming we have a raw response file if it exists
    response_raw = os.path.join(paths['data_raw'], 'reader_responses.csv')
    response_clean = os.path.join(paths['data_processed'], 'reader_response.csv')
    if os.path.exists(response_raw):
        if not run_data_collection_step(response_raw, response_clean):
            logger.warning("Data collection step failed, but continuing.")
    else:
        logger.warning("No raw response data found, skipping data collection step.")
    
    # 4. Aggregation
    agg_features = extraction_output
    agg_responses = response_clean
    agg_output = os.path.join(paths['data_processed'], 'aligned_dataset.csv')
    if os.path.exists(agg_responses):
        if not run_aggregation_step(agg_features, agg_responses, agg_output):
            logger.error("Aggregation failed. Stopping pipeline.")
            return False
    else:
        logger.warning("No cleaned response data found, skipping aggregation.")
        return False # Cannot proceed to analysis without aligned dataset
    
    # 5. Analysis
    analysis_input = agg_output
    analysis_output = os.path.join(paths['data_processed'], 'analysis_results.json')
    if not run_analysis_step(analysis_input, analysis_output):
        logger.error("Analysis failed. Stopping pipeline.")
        return False
    
    logger.info("Full pipeline completed successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Narrative Perspective Analysis Pipeline")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Extraction command
    exp_parser = subparsers.add_parser('extract', help='Run perspective extraction')
    exp_parser.add_argument('--input-dir', required=True, help='Input directory containing story files')
    exp_parser.add_argument('--output', required=True, help='Output JSON file path')
    
    # Matching command (T025)
    match_parser = subparsers.add_parser('match', help='Run matching validation (T025)')
    match_parser.add_argument('--input', required=True, help='Input JSON file (perspective features)')
    match_parser.add_argument('--target', required=True, help='Target CSV file (moral judgement dataset)')
    match_parser.add_argument('--output', required=True, help='Output JSON file (matching results)')
    
    # Data Collection command
    dc_parser = subparsers.add_parser('collect', help='Run data collection validation')
    dc_parser.add_argument('--input', required=True, help='Input CSV file (raw responses)')
    dc_parser.add_argument('--output', required=True, help='Output CSV file (cleaned responses)')
    
    # Aggregation command
    agg_parser = subparsers.add_parser('aggregate', help='Run aggregation step')
    agg_parser.add_argument('--features', required=True, help='Input JSON file (perspective features)')
    agg_parser.add_argument('--responses', required=True, help='Input CSV file (cleaned responses)')
    agg_parser.add_argument('--output', required=True, help='Output CSV file (aligned dataset)')
    
    # Analysis command
    ana_parser = subparsers.add_parser('analyze', help='Run full analysis')
    ana_parser.add_argument('--input', required=True, help='Input CSV file (aligned dataset)')
    ana_parser.add_argument('--output', required=True, help='Output JSON file (analysis results)')
    
    # All command
    all_parser = subparsers.add_parser('all', help='Run the full pipeline')
    
    args = parser.parse_args()
    
    if args.command == 'extract':
        success = run_extraction_step(args.input_dir, args.output)
    elif args.command == 'match':
        success = run_matching_step(args.input, args.target, args.output)
    elif args.command == 'collect':
        success = run_data_collection_step(args.input, args.output)
    elif args.command == 'aggregate':
        success = run_aggregation_step(args.features, args.responses, args.output)
    elif args.command == 'analyze':
        success = run_analysis_step(args.input, args.output)
    elif args.command == 'all':
        success = run_all_pipeline()
    else:
        parser.print_help()
        success = False
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()