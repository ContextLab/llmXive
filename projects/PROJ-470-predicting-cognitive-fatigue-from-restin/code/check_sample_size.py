import os
import sys
import json
import pandas as pd
import logging
from pathlib import Path

from utils.logging import get_logger

# Ensure we can import from the code directory if running as a script
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

def load_config(config_path="code/config.yaml"):
    """Load YAML configuration file."""
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def write_validation_report(report_path, message, status="error"):
    """Write a validation report to a file."""
    report_dir = Path(report_path).parent
    report_dir.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(f"Validation Status: {status.upper()}\n")
        f.write(f"Message: {message}\n")

def check_sample_size(config):
    """
    Enforce N >= 30 constraint as a blocking gate before analysis.
    
    Per FR-001 and SC-001, the analysis requires a minimum of 30 participants
    to ensure statistical power. This function validates the dataset size
    and exits with code 1 if the constraint is violated.
    
    Args:
        config: The loaded configuration dictionary.
        
    Returns:
        tuple: (success: bool, message: str, available_variables: list)
    """
    logger = get_logger("check_sample_size")
    
    # Determine the path to the metadata or processed data to check participant count
    # Typically, we check the manifest or the exclusion log to see how many valid participants remain
    # Or we check the raw data if available. 
    # Based on T010, we expect a manifest at data/raw/download_manifest.json or similar.
    # However, the most robust check is against the actual data that will be used for analysis.
    # The analysis script expects features derived from cleaned_eeg.fif.
    # We need to count unique participants in the cleaned data or the manifest.
    
    manifest_path = Path("data/raw/download_manifest.json")
    exclusion_log_path = Path("data/processed/participant_exclusion_log.csv")
    
    # Strategy:
    # 1. If manifest exists, check the 'participants' or 'count' field.
    # 2. If exclusion log exists, count unique participants that were NOT excluded (or count total if log tracks exclusions).
    # 3. If we have cleaned_eeg.fif, try to load header to count subjects (if multi-subject) or rely on manifest.
    
    # Since T010 is supposed to create the manifest, let's assume it tracks the valid count.
    # If the manifest is not present, we might need to infer from the exclusion log or the raw data structure.
    # For this implementation, we will look for the manifest first, then the exclusion log to calculate N.
    
    n_participants = 0
    available_variables = []
    
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Check for a count field or list of participants
            if 'participant_count' in manifest:
                n_participants = manifest['participant_count']
            elif 'participants' in manifest:
                n_participants = len(manifest['participants'])
            elif 'total_subjects' in manifest:
                n_participants = manifest['total_subjects']
                
            # Gather available variables from manifest
            if 'variables' in manifest:
                available_variables = manifest['variables']
            elif 'data_columns' in manifest:
                available_variables = manifest['data_columns']
                
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not parse manifest for count: {e}")
            # Fallback: try to count from exclusion log if it lists all participants
    
    # If manifest didn't give a clear count, try exclusion log
    # The exclusion log usually lists excluded participants. We need the total valid count.
    # If we have the raw data path from config, we could scan that, but that's expensive.
    # Let's assume the manifest is the source of truth for T010.
    # If N is still 0, we might be in a state where download failed or manifest is missing.
    
    if n_participants == 0 and exclusion_log_path.exists():
        # If we have an exclusion log, it might imply we processed some data.
        # But without a total count from download, we can't be sure of N.
        # However, if the exclusion log exists, it implies T010 ran.
        # Let's try to infer from the cleaned data if it exists.
        cleaned_eeg_path = Path("data/processed/cleaned_eeg.fif")
        if cleaned_eeg_path.exists():
            # For a single FIF file, it might contain multiple epochs/subjects.
            # MNE can load this.
            try:
                import mne
                raw = mne.io.read_raw_fif(cleaned_eeg_path, preload=False)
                # If it's a single file with multiple subjects, MNE usually handles this via annotation or separate files.
                # Assuming the project structure might have multiple files or one concatenated file.
                # If it's a single file, N=1 unless it's a concatenated dataset.
                # This is a heuristic. The manifest is the reliable source.
                # If we are here, manifest failed to give N.
                logger.warning("Could not determine N from manifest. Assuming N=1 if single file.")
                n_participants = 1 # Fallback, likely insufficient
            except Exception as e:
                logger.error(f"Could not read cleaned_eeg.fif: {e}")
    
    # Define required variables per FR-001
    required_variables = ['eeg_data', 'fatigue_rating'] # Or 'pre_fatigue', 'post_fatigue'
    missing_variables = []
    
    # Check if required variables are in available_variables
    if available_variables:
        for var in required_variables:
            if var not in available_variables:
                missing_variables.append(var)
    else:
        # If we don't know the variables, we assume they are missing or unknown
        missing_variables = required_variables
    
    min_n = 30
    
    if n_participants < min_n:
        error_msg = (
            f"CRITICAL: Sample size N={n_participants} is below the required threshold of {min_n}.\n"
            f"Analysis cannot proceed per FR-001 and SC-001.\n"
        )
        
        if missing_variables:
            error_msg += f"Missing required variables: {', '.join(missing_variables)}.\n"
        
        error_msg += f"Available variables: {', '.join(available_variables) if available_variables else 'None detected'}.\n"
        error_msg += f"Please ensure the dataset contains at least {min_n} participants with paired EEG and fatigue ratings."
        
        return False, error_msg, available_variables
    
    return True, f"Sample size check passed: N={n_participants} >= {min_n}", available_variables

def main():
    """Main entry point for sample size validation."""
    logger = get_logger("check_sample_size")
    logger.info("Starting sample size validation (T026a).")
    
    try:
        config = load_config()
        success, message, available_vars = check_sample_size(config)
        
        report_path = "data/analysis/sample_size_validation_report.txt"
        
        if not success:
            logger.error(message)
            write_validation_report(report_path, message, status="failed")
            # Exit with code 1 as per requirement
            sys.exit(1)
        else:
            logger.info(message)
            write_validation_report(report_path, message, status="passed")
            sys.exit(0)
            
    except FileNotFoundError as e:
        error_msg = f"Configuration file or data manifest not found: {e}"
        logger.error(error_msg)
        write_validation_report("data/analysis/sample_size_validation_report.txt", error_msg, status="error")
        sys.exit(1)
    except Exception as e:
        error_msg = f"Unexpected error during sample size check: {e}"
        logger.error(error_msg)
        write_validation_report("data/analysis/sample_size_validation_report.txt", error_msg, status="error")
        sys.exit(1)

if __name__ == "__main__":
    main()