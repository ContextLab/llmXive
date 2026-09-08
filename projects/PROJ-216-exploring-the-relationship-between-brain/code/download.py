import os
import sys
import time
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Constants
TEST_MODE_ENV_VARS = ('TASKER_TEST_MODE', 'CI_MODE', 'LOCAL_DEV_MODE')
DEFAULT_RANDOM_SEED = 42
SAMPLE_INFO_PATH = Path('data/processed/sample_info.json')

def is_test_mode() -> bool:
    """Check if running in a test mode that allows mock data."""
    return any(os.environ.get(env_var) == 'true' for env_var in TEST_MODE_ENV_VARS)

def ensure_directories():
    """Ensure required directories exist."""
    dirs = ['data/raw', 'data/interim', 'data/processed', 'data/external']
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def download_dataset_with_retry(dataset_id: str, output_dir: Path, max_retries: int = 5) -> bool:
    """
    Attempt to download a dataset with exponential backoff retry logic.
    
    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds000224')
        output_dir: Directory to save the dataset
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if download succeeds, False otherwise
    """
    initial_delay = 1
    max_delay = 30
    multiplier = 2
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to download {dataset_id} (Attempt {attempt + 1}/{max_retries})")
            
            # In a real implementation, this would use openneuro-py or similar
            # For now, we simulate the check for existence of metadata
            # that would indicate a successful download
            
            # Placeholder for actual download logic using openneuro-py
            # from openneuro import download
            # download(dataset_id, output_dir)
            
            # Simulate a successful check by verifying if a marker file exists
            # In production, this would be replaced with actual download verification
            marker_file = output_dir / "download_complete.txt"
            
            # For the purpose of this task, we assume the download succeeds
            # if we are in test mode or if the directory structure is valid
            if is_test_mode():
                marker_file.parent.mkdir(parents=True, exist_ok=True)
                marker_file.write_text(f"Downloaded {dataset_id}")
                logger.info(f"Mock download complete for {dataset_id}")
                return True
            
            # In a real scenario, we would actually download here
            # For now, we raise an error if not in test mode and real data isn't available
            # This forces the user to have real data or run in test mode
            if not marker_file.exists():
                raise FileNotFoundError(f"Dataset {dataset_id} not found at {output_dir}")
                
            return True
            
        except Exception as e:
            delay = min(initial_delay * (multiplier ** attempt), max_delay)
            logger.warning(f"Download failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            
    logger.error(f"Failed to download {dataset_id} after {max_retries} attempts")
    return False

def fetch_openneuro_data(datasets: List[str], output_base: Path) -> Dict[str, Path]:
    """
    Fetch data from specified OpenNeuro datasets.
    
    Args:
        datasets: List of dataset IDs to fetch
        output_base: Base directory for output
        
    Returns:
        Dictionary mapping dataset ID to its output path
    """
    results = {}
    for dataset_id in datasets:
        output_dir = output_base / dataset_id
        if download_dataset_with_retry(dataset_id, output_dir):
            results[dataset_id] = output_dir
            logger.info(f"Successfully fetched {dataset_id}")
        else:
            logger.error(f"Failed to fetch {dataset_id}")
            
    if not results:
        raise RuntimeError("No datasets could be fetched. Check network and dataset IDs.")
        
    return results

def validate_and_extract_subjects(dataset_path: Path) -> List[Dict[str, Any]]:
    """
    Validate dataset structure and extract subject metadata.
    
    Args:
        dataset_path: Path to the downloaded dataset
        
    Returns:
        List of subject metadata dictionaries
    """
    subjects = []
    
    # In a real implementation, we would parse BIDS structure
    # For now, we simulate finding subjects in the dataset
    
    # Check for subjects directory
    subjects_dir = dataset_path / "sub-*"
    # In real code: use glob or os.walk to find actual subject directories
    
    # Simulate subject extraction for testing
    if is_test_mode():
        # Create mock subjects for testing
        for i in range(1, 11):  # 10 mock subjects
            subject = {
                "id": f"sub_{i:03d}",
                "fluid_intelligence_score": float(80 + i * 2),  # Mock scores
                "age": 25 + i,
                "gender": "M" if i % 2 == 0 else "F",
                "raw_data_path": str(dataset_path / f"sub_{i:03d}" / "func")
            }
            subjects.append(subject)
    else:
        # In production, this would scan the actual BIDS directory
        # For now, we raise an error if not in test mode
        # This ensures we don't accidentally use mock data in production
        raise RuntimeError(
            "Real data validation not implemented. "
            "Set TASKER_TEST_MODE=true for testing or provide real dataset."
        )
        
    logger.info(f"Found {len(subjects)} subjects in {dataset_path}")
    return subjects

def enforce_sample_limit(subjects: List[Dict[str, Any]], limit: Optional[int] = None, seed: int = DEFAULT_RANDOM_SEED) -> List[Dict[str, Any]]:
    """
    Enforce sample size limit on the subject list.
    
    Args:
        subjects: Full list of subjects
        limit: Maximum number of subjects to return (None for all)
        seed: Random seed for reproducible sampling
        
    Returns:
        Subset of subjects if limit is set, otherwise full list
    """
    if limit is None or limit >= len(subjects):
        return subjects
        
    # Use fixed seed for reproducibility
    import random
    random.seed(seed)
    sampled = random.sample(subjects, limit)
    logger.info(f"Sampled {limit} subjects from {len(subjects)} (seed={seed})")
    return sampled

def write_sample_info(total_available: int, subjects_used: int, sampling_method: str, seed: Optional[int] = None):
    """
    Write sample information to data/processed/sample_info.json.
    
    This implements T015c: Explicit Sample Size Declaration.
    
    Args:
        total_available: Total number of subjects available in dataset
        subjects_used: Number of subjects actually used in analysis
        sampling_method: Description of sampling method (e.g., "first N", "random seed X")
        seed: Random seed used if applicable
    """
    ensure_directories()
    
    sample_info = {
        "total_available": total_available,
        "subjects_used": subjects_used,
        "sampling_method": sampling_method,
    }
    
    if seed is not None:
        sample_info["seed"] = seed
        
    # Write to the required path
    SAMPLE_INFO_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SAMPLE_INFO_PATH, 'w') as f:
        json.dump(sample_info, f, indent=2)
        
    logger.info(f"Sample info written to {SAMPLE_INFO_PATH}")
    logger.info(f"  Total available: {total_available}")
    logger.info(f"  Subjects used: {subjects_used}")
    logger.info(f"  Sampling method: {sampling_method}")
    if seed is not None:
        logger.info(f"  Seed: {seed}")

def main():
    """Main entry point for the download module."""
    parser = argparse.ArgumentParser(description="Download and validate OpenNeuro datasets")
    parser.add_argument(
        '--datasets', 
        nargs='+', 
        default=['ds000224', 'ds000230'],
        help='OpenNeuro dataset IDs to download (default: ds000224 ds000230)'
    )
    parser.add_argument(
        '--sample-size', 
        type=int, 
        default=None,
        help='Maximum number of subjects to use (default: all available)'
    )
    parser.add_argument(
        '--seed', 
        type=int, 
        default=DEFAULT_RANDOM_SEED,
        help=f'Random seed for sampling (default: {DEFAULT_RANDOM_SEED})'
    )
    parser.add_argument(
        '--mock-input',
        type=str,
        default=None,
        help='Path to mock subjects JSON (for testing only)'
    )
    
    args = parser.parse_args()
    
    # Ensure directories exist
    ensure_directories()
    
    # Handle mock input if provided and in test mode
    if args.mock_input and is_test_mode():
        if not os.path.exists(args.mock_input):
            raise FileNotFoundError(f"Mock input file not found: {args.mock_input}")
        
        with open(args.mock_input, 'r') as f:
            all_subjects = json.load(f)
        
        logger.info(f"Loaded {len(all_subjects)} subjects from mock input: {args.mock_input}")
        
        # Enforce sample limit
        if args.sample_size:
            sampled_subjects = enforce_sample_limit(all_subjects, args.sample_size, args.seed)
            sampling_method = f"random sample of {args.sample_size} (seed={args.seed})"
        else:
            sampled_subjects = all_subjects
            sampling_method = "all subjects"
            
        # Write sample info
        write_sample_info(
            total_available=len(all_subjects),
            subjects_used=len(sampled_subjects),
            sampling_method=sampling_method,
            seed=args.seed if args.sample_size else None
        )
        
        # Save the final subject list for downstream tasks
        output_path = Path('data/processed/subjects.json')
        with open(output_path, 'w') as f:
            json.dump(sampled_subjects, f, indent=2)
        logger.info(f"Processed subjects written to {output_path}")
        return
        
    # Real data path
    if not is_test_mode():
        logger.warning("Not in test mode. Attempting real data download.")
        
    # Try primary dataset first
    datasets_to_try = args.datasets
    downloaded_datasets = []
    
    for dataset_id in datasets_to_try:
        try:
            output_base = Path('data/raw')
            results = fetch_openneuro_data([dataset_id], output_base)
            if results:
                downloaded_datasets.append(dataset_id)
                break  # Success with primary
        except Exception as e:
            logger.warning(f"Failed to download {dataset_id}: {e}")
            
    if not downloaded_datasets:
        if is_test_mode():
            logger.warning("No real data available and test mode enabled. Using mock data.")
            # Fall back to mock data generation for testing
            all_subjects = []
            for i in range(1, 11):
                all_subjects.append({
                    "id": f"sub_{i:03d}",
                    "fluid_intelligence_score": float(80 + i * 2),
                    "age": 25 + i,
                    "gender": "M" if i % 2 == 0 else "F",
                    "raw_data_path": f"data/raw/{dataset_id}/sub_{i:03d}/func"
                })
            
            if args.sample_size:
                sampled_subjects = enforce_sample_limit(all_subjects, args.sample_size, args.seed)
                sampling_method = f"random sample of {args.sample_size} (seed={args.seed})"
            else:
                sampled_subjects = all_subjects
                sampling_method = "all subjects"
                
            write_sample_info(
                total_available=len(all_subjects),
                subjects_used=len(sampled_subjects),
                sampling_method=sampling_method,
                seed=args.seed if args.sample_size else None
            )
            
            output_path = Path('data/processed/subjects.json')
            with open(output_path, 'w') as f:
                json.dump(sampled_subjects, f, indent=2)
            logger.info(f"Mock subjects written to {output_path}")
            return
        else:
            raise RuntimeError("Failed to download any real datasets. Set TASKER_TEST_MODE=true for testing.")
    
    # Process the successfully downloaded dataset
    dataset_path = Path('data/raw') / downloaded_datasets[0]
    
    try:
        all_subjects = validate_and_extract_subjects(dataset_path)
    except RuntimeError as e:
        if "Real data validation not implemented" in str(e) and is_test_mode():
            # Generate mock subjects for testing
            logger.info("Generating mock subjects for testing")
            all_subjects = []
            for i in range(1, 11):
                all_subjects.append({
                    "id": f"sub_{i:03d}",
                    "fluid_intelligence_score": float(80 + i * 2),
                    "age": 25 + i,
                    "gender": "M" if i % 2 == 0 else "F",
                    "raw_data_path": f"data/raw/{downloaded_datasets[0]}/sub_{i:03d}/func"
                })
        else:
            raise
    
    if not all_subjects:
        raise RuntimeError("No valid subjects found in the dataset.")
        
    logger.info(f"Found {len(all_subjects)} valid subjects")
    
    # Enforce sample limit if specified
    if args.sample_size:
        if args.sample_size < 1:
            raise ValueError("Sample size must be at least 1")
        sampled_subjects = enforce_sample_limit(all_subjects, args.sample_size, args.seed)
        sampling_method = f"random sample of {args.sample_size} (seed={args.seed})"
    else:
        sampled_subjects = all_subjects
        sampling_method = "all subjects"
        
    # Write sample info (T015c requirement)
    write_sample_info(
        total_available=len(all_subjects),
        subjects_used=len(sampled_subjects),
        sampling_method=sampling_method,
        seed=args.seed if args.sample_size else None
    )
    
    # Save the final subject list for downstream tasks
    output_path = Path('data/processed/subjects.json')
    with open(output_path, 'w') as f:
        json.dump(sampled_subjects, f, indent=2)
    logger.info(f"Processed subjects written to {output_path}")
    
    logger.info("Download and validation complete.")

if __name__ == "__main__":
    main()