import csv
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Set, Optional

# Import config and logging utilities
from config import get_processed_data_dir, get_raw_data_dir, get_code_dir
from logging_config import setup_logging, get_logger, log_exclusion

# Configure logging for this module
logger = get_logger(__name__)

def load_cleaning_log(cleaning_log_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load the cleaning log CSV produced by T016.
    
    Args:
        cleaning_log_path: Path to the cleaning log CSV. Defaults to data/processed/cleaning_log.csv.
        
    Returns:
        List of dictionaries representing rows in the cleaning log.
    """
    if cleaning_log_path is None:
        cleaning_log_path = get_processed_data_dir() / "cleaning_log.csv"
        
    if not cleaning_log_path.exists():
        logger.error(f"Cleaning log not found at {cleaning_log_path}")
        raise FileNotFoundError(f"Cleaning log not found at {cleaning_log_path}")
        
    with open(cleaning_log_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def load_ratings(ratings_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load the ratings CSV produced by T014 or T015.
    
    Args:
        ratings_path: Path to the ratings CSV. Defaults to data/raw/ratings.csv.
        
    Returns:
        List of dictionaries representing rating records.
    """
    if ratings_path is None:
        ratings_path = get_raw_data_dir() / "ratings.csv"
        
    if not ratings_path.exists():
        logger.error(f"Ratings file not found at {ratings_path}")
        raise FileNotFoundError(f"Ratings file not found at {ratings_path}")
        
    with open(ratings_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def load_stimuli(stimuli_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load the stimuli CSV produced by T013.
    
    Args:
        stimuli_path: Path to the stimuli CSV. Defaults to data/raw/stimuli.csv.
        
    Returns:
        List of dictionaries representing stimulus records.
    """
    if stimuli_path is None:
        stimuli_path = get_raw_data_dir() / "stimuli.csv"
        
    if not stimuli_path.exists():
        logger.error(f"Stimuli file not found at {stimuli_path}")
        raise FileNotFoundError(f"Stimuli file not found at {stimuli_path}")
        
    with open(stimuli_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def apply_listwise_deletion(
    ratings: List[Dict[str, Any]],
    cleaning_log: List[Dict[str, Any]],
    stimuli: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Apply listwise deletion to the ratings dataset based on exclusion flags in the cleaning log.
    
    This function:
    1. Identifies participants marked for exclusion in the cleaning log.
    2. Removes all ratings associated with those participants from the dataset.
    3. Logs the exclusion reasons for transparency.
    
    Args:
        ratings: List of rating records.
        cleaning_log: List of cleaning log entries containing exclusion flags and reasons.
        stimuli: List of stimulus records (used to verify total stimulus count).
        
    Returns:
        Filtered list of ratings with excluded participants removed.
    """
    # Create a set of excluded participant IDs from the cleaning log
    excluded_participants: Set[str] = set()
    exclusion_details: Dict[str, str] = {}
    
    for entry in cleaning_log:
        # Check if the participant is marked for exclusion
        is_excluded = entry.get('excluded', '').lower() == 'true'
        if is_excluded:
            p_id = entry.get('participant_id')
            if p_id:
                excluded_participants.add(p_id)
                reason = entry.get('reason', 'Unknown reason')
                exclusion_details[p_id] = reason
                
    # Log the exclusions
    if excluded_participants:
        logger.info(f"Applying listwise deletion: {len(excluded_participants)} participants excluded.")
        for p_id, reason in exclusion_details.items():
            log_exclusion(p_id, reason, "data/processed/cleaning_log.csv")
            logger.debug(f"Excluding participant {p_id}: {reason}")
    else:
        logger.info("No participants marked for exclusion in cleaning log.")
        
    # Filter ratings to exclude participants
    cleaned_ratings = [
        rating for rating in ratings
        if rating.get('participant_id') not in excluded_participants
    ]
    
    logger.info(f"Listwise deletion complete. Retained {len(cleaned_ratings)} ratings from {len(ratings) - len(cleaned_ratings)} removed.")
    
    return cleaned_ratings

def log_exclusion_reason(
    participant_id: str,
    reason: str,
    cleaning_log_path: Path
) -> None:
    """
    Log an exclusion reason to the cleaning log.
    
    Args:
        participant_id: The ID of the excluded participant.
        reason: The reason for exclusion.
        cleaning_log_path: Path to the cleaning log file.
    """
    # This function is primarily used for logging during the cleaning process.
    # For T020, we rely on the existing cleaning_log.csv from T016.
    # However, if additional exclusions are needed here, they can be appended.
    logger.warning(f"Excluding participant {participant_id}: {reason}")

def run_primary_lmm(cleaned_ratings: List[Dict[str, Any]], stimuli: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run the primary Linear Mixed-Effects Model (LMM).
    
    Args:
        cleaned_ratings: Filtered ratings data.
        stimuli: Stimuli metadata.
        
    Returns:
        Dictionary containing model results.
    """
    # Placeholder for actual LMM implementation (T021)
    # This function will be fleshed out in T021
    logger.info("Running primary LMM...")
    return {
        "model_type": "LMM",
        "status": "placeholder",
        "note": "Implementation deferred to T021"
    }

def run_tukey_post_hoc(model_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run Tukey-corrected post-hoc pairwise comparisons.
    
    Args:
        model_results: Results from the primary LMM.
        
    Returns:
        Dictionary containing post-hoc test results.
    """
    # Placeholder for Tukey post-hoc (T024)
    logger.info("Running Tukey post-hoc tests...")
    return {
        "test_type": "Tukey",
        "status": "placeholder",
        "note": "Implementation deferred to T024"
    }

def save_analysis_results(results: Dict[str, Any], output_path: Optional[Path] = None) -> None:
    """
    Save analysis results to a JSON file.
    
    Args:
        results: Dictionary of analysis results.
        output_path: Path to the output file. Defaults to data/processed/analysis_results.json.
    """
    if output_path is None:
        output_path = get_processed_data_dir() / "analysis_results.json"
        
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
        
    logger.info(f"Analysis results saved to {output_path}")

def main() -> None:
    """
    Main entry point for the LMM pipeline preprocessing and analysis.
    
    This function:
    1. Loads the cleaning log from T016.
    2. Loads ratings and stimuli data.
    3. Applies listwise deletion to remove excluded participants.
    4. Runs the primary LMM (T021).
    5. Runs Tukey post-hoc tests if applicable (T024).
    6. Saves results to analysis_results.json.
    """
    # Setup logging
    setup_logging()
    
    try:
        # Load data
        logger.info("Loading cleaning log...")
        cleaning_log = load_cleaning_log()
        
        logger.info("Loading ratings...")
        ratings = load_ratings()
        
        logger.info("Loading stimuli...")
        stimuli = load_stimuli()
        
        # Apply listwise deletion (T020 core logic)
        logger.info("Applying listwise deletion...")
        cleaned_ratings = apply_listwise_deletion(ratings, cleaning_log, stimuli)
        
        if not cleaned_ratings:
            logger.error("No ratings remaining after listwise deletion. Aborting analysis.")
            sys.exit(1)
        
        # Run primary LMM (T021)
        logger.info("Running primary LMM...")
        model_results = run_primary_lmm(cleaned_ratings, stimuli)
        
        # Run Tukey post-hoc (T024)
        logger.info("Running Tukey post-hoc...")
        post_hoc_results = run_tukey_post_hoc(model_results)
        
        # Combine results
        final_results = {
            "preprocessing": {
                "total_ratings_initial": len(ratings),
                "total_ratings_final": len(cleaned_ratings),
                "participants_excluded": len([r for r in cleaning_log if r.get('excluded', '').lower() == 'true'])
            },
            "model": model_results,
            "post_hoc": post_hoc_results
        }
        
        # Save results (T025)
        logger.info("Saving analysis results...")
        save_analysis_results(final_results)
        
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        raise

if __name__ == "__main__":
    main()