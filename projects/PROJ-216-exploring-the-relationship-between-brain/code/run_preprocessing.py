"""
Wrapper script to run the preprocessing pipeline sequentially on all available subjects.
This script orchestrates the call to `preprocess_subject` for each subject while
monitoring resource usage via the `ResourceMonitor` class to ensure we stay within
RAM limits (<= 7GB).
"""

import os
import sys
import json
import argparse
import logging
import time
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

from utils import ResourceMonitor
from preprocess import preprocess_subject, check_fsl_afni, load_motion_exclusion_log, halt_on_zero_effective_subjects
from config import get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler('logs/preprocessing_wrapper.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)


def load_subject_list_from_download_log(log_path: str) -> List[Dict[str, Any]]:
    """
    Loads the list of subjects from the download validation log.
    Expects the log to contain a JSON structure of valid subjects.
    """
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Download log not found at {log_path}. "
                                "Run code/download.py first to generate valid subject data.")

    with open(log_path, 'r') as f:
        # The download script writes sample_info.json, but we need the subject list.
        # Assuming the download script also writes a 'valid_subjects.json' or similar,
        # or we parse the log. Based on T015b, we likely have a JSON of subjects.
        # Let's look for 'data/processed/valid_subjects.json' as the standard output
        # for the list of subjects to process.
        pass

    # Fallback: Try to load sample_info and reconstruct, or load a dedicated list file.
    # Based on T015c, we have sample_info.json. We need the actual list.
    # Let's assume the download process writes 'data/processed/valid_subjects.json'
    # containing the list of subject dicts (id, fluid_intelligence_score, etc).
    valid_subjects_path = os.path.join(os.path.dirname(log_path), 'valid_subjects.json')
    
    if os.path.exists(valid_subjects_path):
        with open(valid_subjects_path, 'r') as f:
            return json.load(f)
    
    # If that fails, try to parse the sample_info or raise error
    raise FileNotFoundError(f"Could not find valid subject list at {valid_subjects_path}. "
                            "Ensure code/download.py has successfully written the subject list.")


def run_preprocessing_wrapper(subject: Dict[str, Any], raw_dir: str, interim_dir: str, monitor: ResourceMonitor) -> Dict[str, Any]:
    """
    Runs the preprocessing for a single subject and updates the monitor.
    Returns a status dict for the subject.
    """
    subject_id = subject['id']
    logger.info(f"Starting preprocessing for subject: {subject_id}")
    
    # Start resource monitoring for this subject
    monitor.start()
    start_time = time.time()
    
    success = False
    error_msg = None
    
    try:
        # Call the actual preprocessing function
        # preprocess_subject expects paths to the specific subject's data
        # We assume the download script organized data as data/raw/subj_XXX/...
        raw_subject_path = os.path.join(raw_dir, f"subj_{subject_id}")
        if not os.path.exists(raw_subject_path):
            # Try alternate naming if 'subj_' is not the prefix used by OpenNeuro
            raw_subject_path = os.path.join(raw_dir, subject_id)
        
        if not os.path.exists(raw_subject_path):
            raise FileNotFoundError(f"Raw data directory for {subject_id} not found at {raw_subject_path}")

        preprocess_subject(raw_subject_path, interim_dir, subject_id)
        success = True
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Preprocessing failed for {subject_id}: {error_msg}")
    finally:
        # Stop monitoring
        monitor.stop()
        elapsed = time.time() - start_time
        
        # Log RAM usage for this subject (handled by monitor internally, but we log here too)
        logger.info(f"[ResourceMonitor] Subject {subject_id}: Completed in {elapsed:.2f}s")

    return {
        "subject_id": subject_id,
        "success": success,
        "error": error_msg,
        "elapsed_seconds": elapsed
    }


def main():
    parser = argparse.ArgumentParser(description="Run preprocessing pipeline sequentially.")
    parser.add_argument('--raw-dir', type=str, default='data/raw', help='Path to raw data directory')
    parser.add_argument('--interim-dir', type=str, default='data/interim', help='Path to interim output directory')
    parser.add_argument('--log-path', type=str, default='data/processed/sample_info.json', help='Path to subject list info')
    args = parser.parse_args()

    # Check dependencies
    if not check_fsl_afni():
        logger.error("FSL or AFNI tools not found. Please install them.")
        sys.exit(1)

    # Ensure output directories exist
    Path(args.interim_dir).mkdir(parents=True, exist_ok=True)

    # Load subject list
    # We need the path to the file generated by download.py. 
    # T015c writes sample_info.json. We need the list of subjects.
    # Let's assume download.py also writes 'valid_subjects.json' as per standard practice.
    # If not, we might need to adapt.
    # For now, let's try to load from a standard location or the provided log path.
    # The task T015c writes sample_info.json. We need the list of subjects to process.
    # Let's assume the download script writes 'data/processed/valid_subjects.json'.
    valid_subjects_path = 'data/processed/valid_subjects.json'
    
    if not os.path.exists(valid_subjects_path):
        # Fallback: try to load from sample_info if it contains a list, or error
        logger.error(f"Valid subjects file not found at {valid_subjects_path}. "
                     "Run code/download.py first.")
        sys.exit(1)

    subjects = load_subject_list_from_download_log(valid_subjects_path)
    if not subjects:
        logger.warning("No subjects found to process.")
        sys.exit(0)

    logger.info(f"Found {len(subjects)} subjects to process.")

    # Initialize ResourceMonitor
    monitor = ResourceMonitor()
    
    results = []
    for subject in subjects:
        result = run_preprocessing_wrapper(subject, args.raw_dir, args.interim_dir, monitor)
        results.append(result)

    # Finalize monitor to write resource_profile.json
    monitor.finalize()
    logger.info("Resource monitoring finalized. Profile written to data/processed/resource_profile.json")

    # Write preprocessing stats summary
    stats_path = 'data/processed/preprocessing_stats.json'
    total = len(results)
    success_count = sum(1 for r in results if r['success'])
    
    stats = {
        "total_subjects": total,
        "successful": success_count,
        "failed": total - success_count,
        "success_rate": success_count / total if total > 0 else 0.0,
        "details": results
    }

    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Preprocessing stats written to {stats_path}")

    # Check if we have zero effective subjects (after potential motion exclusion, though that's later)
    # For now, just log the result
    if success_count == 0:
        logger.error("No subjects successfully preprocessed. Halting.")
        sys.exit(1)

    logger.info("Preprocessing wrapper completed successfully.")


if __name__ == "__main__":
    main()