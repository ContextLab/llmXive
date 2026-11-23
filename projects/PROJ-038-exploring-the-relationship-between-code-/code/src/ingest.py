import os
import subprocess
import sys
import shutil
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('code/data/processed/ingest.log')
    ]
)
logger = logging.getLogger(__name__)

# Custom Exceptions
class MemoryLimitExceeded(Exception):
    """Raised when memory usage exceeds the configured limit."""
    pass

class DataFetchError(Exception):
    """Raised when fetching data from Defects4J fails."""
    pass

class DataIntegrityError(Exception):
    """Raised when the resulting dataset is empty after validation."""
    pass

# --- Existing Helper Functions (Preserved from previous tasks) ---

def get_defects4j_path() -> Path:
    d4j_path = os.environ.get('DEFECTS4J_HOME', '')
    if not d4j_path:
        raise DataFetchError("DEFECTS4J_HOME environment variable not set.")
    return Path(d4j_path)

def get_java_compiler_path() -> Path:
    java_home = os.environ.get('JAVA_HOME', '')
    if not java_home:
        raise DataFetchError("JAVA_HOME environment variable not set.")
    return Path(java_home) / 'bin' / 'javac'

def run_defects4j_command(args: List[str], cwd: Optional[Path] = None) -> str:
    cmd = ['defects4j'] + args
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise DataFetchError(f"Defects4J command failed: {e.stderr}")

def list_available_projects() -> List[str]:
    output = run_defects4j_command(['list'])
    # Parse output, assuming one project ID per line or formatted list
    projects = [line.strip() for line in output.splitlines() if line.strip()]
    return projects

def get_project_size(project_id: str) -> int:
    """
    Get the raw disk size of a project directory in bytes.
    Assumes project is cloned in a standard location or managed by Defects4J.
    For this implementation, we assume a standard checkout path or use 'defects4j info'.
    """
    # Attempt to get size via 'du' on the project directory if it exists locally
    # Defects4J typically stores projects in ~/.defects4j or a specific checkout dir
    # We will assume the project is checked out to code/data/raw/{project_id}
    project_dir = Path('code/data/raw') / project_id
    if not project_dir.exists():
        # If not local, we might need to fetch it first, but for size check
        # we assume it's already fetched or we use 'du -sb' on the checkout.
        # Fallback: estimate or raise error if not found.
        logger.warning(f"Project directory {project_dir} not found for size check.")
        return 0
    
    try:
        result = subprocess.run(
            ['du', '-sb', str(project_dir)],
            capture_output=True,
            text=True,
            check=True
        )
        return int(result.stdout.split()[0])
    except (subprocess.CalledProcessError, ValueError, IndexError) as e:
        logger.error(f"Could not determine size for {project_id}: {e}")
        return 0

def get_current_memory_usage_bytes() -> int:
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss
    except ImportError:
        logger.warning("psutil not installed. Memory monitoring disabled.")
        return 0

def validate_ram_limit(limit_bytes: int) -> bool:
    return get_current_memory_usage_bytes() < limit_bytes

def monitor_memory_periodically(check_interval: int = 60, limit_bytes: int = 7 * 1024**3):
    import time
    while True:
        current = get_current_memory_usage_bytes()
        logger.info(f"Current memory usage: {current / (1024**3):.2f} GB")
        if current > limit_bytes:
            raise MemoryLimitExceeded(f"Memory limit exceeded: {current} > {limit_bytes}")
        time.sleep(check_interval)

def is_generated_or_non_java(file_path: Path) -> bool:
    """
    Check if a file is generated code or non-Java.
    Returns True if it should be excluded.
    """
    if file_path.suffix != '.java':
        return True
    
    # Heuristics for generated code (common patterns)
    generated_patterns = [
        'gen', 'generated', 'build', 'target', 'out', 'classes',
        'node_modules', 'venv', '.git'
    ]
    path_str = str(file_path).lower()
    for pattern in generated_patterns:
        if pattern in path_str:
            return True
    
    return False

def filter_java_files(directory: Path) -> List[Path]:
    java_files = []
    for root, dirs, files in os.walk(directory):
        # Filter out generated directories early
        dirs[:] = [d for d in dirs if not is_generated_or_non_java(Path(root) / d)]
        
        for file in files:
            file_path = Path(root) / file
            if not is_generated_or_non_java(file_path):
                java_files.append(file_path)
    return java_files

def select_dynamic_subset(projects: List[str], max_size_bytes: int) -> List[str]:
    selected = []
    cumulative_size = 0
    # Sort alphabetically as per spec
    projects_sorted = sorted(projects)
    
    for proj in projects_sorted:
        size = get_project_size(proj)
        if cumulative_size + size > max_size_bytes:
            break
        selected.append(proj)
        cumulative_size += size
    
    logger.info(f"Selected {len(selected)} projects with total size {cumulative_size} bytes.")
    return selected

def download_defects4j_subset(project_ids: List[str]) -> None:
    for pid in project_ids:
        logger.info(f"Checking out project: {pid}")
        try:
            # defects4j checkout -p <project> -v <version>
            # Assuming version 1.0 for simplicity or fetching all
            run_defects4j_command(['checkout', '-p', pid, '-v', '1.0'], cwd='code/data/raw')
        except DataFetchError as e:
            logger.error(f"Failed to checkout {pid}: {e}")
            # Continue or fail based on strictness? Spec says raise if CLI fails.
            raise

def checkout_bug_introduction_commit(project_id: str, bug_id: str) -> None:
    """
    Checkout the specific bug-introduction commit for a project.
    Requires Defects4J to be initialized with the project.
    """
    # Defects4J command to get bug info or checkout specific commit
    # Often involves 'defects4j checkout' with specific flags or using the bug report JSON
    # For this implementation, we assume the commit is known or retrieved via defects4j info
    try:
        # Example: defects4j checkout -p project -v version -b bug_id (if supported)
        # Or retrieve commit hash from metadata and git checkout
        logger.info(f"Checking out bug-introduction commit for {project_id} bug {bug_id}")
        # Placeholder for actual logic if Defects4J CLI doesn't support direct commit checkout
        # We might need to parse 'defects4j info' JSON to get the commit hash
        info_cmd = run_defects4j_command(['info', '-p', project_id, '-v', '1.0'])
        # Parsing logic would go here to find the commit hash for the bug
        # For now, we assume the project is in the buggy state or we handle it via git
        # If the project directory exists:
        project_dir = Path('code/data/raw') / project_id
        if project_dir.exists():
            subprocess.run(['git', 'checkout', bug_id], cwd=project_dir, check=True)
    except subprocess.CalledProcessError as e:
        raise DataFetchError(f"Failed to checkout commit for {project_id}: {e}")

def get_project_metadata(project_id: str) -> Dict[str, Any]:
    # Fetch metadata from Defects4J
    try:
        output = run_defects4j_command(['info', '-p', project_id, '-v', '1.0'])
        # Parse JSON output if available, else return basic info
        return {'project_id': project_id, 'status': 'available'}
    except Exception as e:
        logger.error(f"Could not get metadata for {project_id}: {e}")
        return {}

def main():
    """
    Main entry point for the ingestion and validation pipeline.
    Orchestrates downloading, metric extraction (via other modules), labeling,
    and finally the validation step (T018).
    """
    logger.info("Starting Ingestion Pipeline...")
    
    # 1. Setup and Configuration
    # (Assume T001c, T002a etc. have set up the environment)
    
    # 2. Ingest Data (T013)
    # projects = list_available_projects()
    # subset = select_dynamic_subset(projects, max_size_bytes=1024**3) # Example limit
    # download_defects4j_subset(subset)
    
    # 3. Metric Extraction (T014b, T014c) - Assumed to be done by separate scripts
    # 4. Labeling (T015) - Assumed to be done
    
    # 5. Generate Features CSV (T017) - Assumed to be done
    features_path = Path('code/data/processed/features.csv')
    if not features_path.exists():
        logger.error("features.csv not found. Please run T017 first.")
        return
    
    # 6. Validate Features (T018)
    validate_features(features_path)

# --- T018 Implementation: validate_features ---

def validate_features(input_path: Path) -> None:
    """
    Validates the features.csv file by checking for NaN values in metric columns.
    Drops rows with NaNs, logs the exclusions, and ensures the dataset is not empty.
    
    Args:
        input_path: Path to the features.csv file.
    
    Raises:
        DataIntegrityError: If the resulting dataset is empty.
    """
    logger.info(f"Validating features file: {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise DataFetchError(f"Failed to read CSV: {e}")

    required_columns = ['file_path', 'cc', 'halstead', 'loc', 'is_buggy']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise DataIntegrityError(f"Missing required columns: {missing_cols}")

    metric_cols = ['cc', 'halstead', 'loc']
    
    # Identify rows with NaN in metric columns
    mask_nan = df[metric_cols].isna().any(axis=1)
    nan_count = mask_nan.sum()
    
    if nan_count > 0:
        logger.warning(f"Found {nan_count} rows with NaN values in metric columns. Dropping them.")
        
        # Identify dropped rows
        dropped_rows = df[mask_nan]
        dropped_paths = dropped_rows['file_path'].tolist()
        
        # Log exclusions
        exclusions_log_path = Path('code/data/processed/exclusions.log')
        with open(exclusions_log_path, 'w') as f:
            f.write(f"Exclusions Log - Generated at {pd.Timestamp.now()}\n")
            f.write(f"Reason: NaN values in metric columns (cc, halstead, loc)\n")
            f.write(f"Total Dropped: {nan_count}\n")
            f.write("-" * 80 + "\n")
            for path in dropped_paths:
                f.write(f"{path}\n")
        
        logger.info(f"Exclusion log written to: {exclusions_log_path}")
        
        # Drop the rows
        df_clean = df.dropna(subset=metric_cols)
    else:
        logger.info("No NaN values found in metric columns.")
        df_clean = df

    # Check if resulting dataset is empty
    if df_clean.empty:
        logger.error("Resulting dataset is empty after dropping NaN rows.")
        raise DataIntegrityError("DataIntegrityError: Resulting dataset is empty.")

    # Save the cleaned dataset back (overwriting or to a new file? Spec says "DROP the row" implying update)
    # We overwrite the original to ensure downstream tasks use the clean data
    df_clean.to_csv(input_path, index=False)
    logger.info(f"Validated dataset saved to {input_path} with {len(df_clean)} rows.")

    return df_clean

if __name__ == "__main__":
    main()