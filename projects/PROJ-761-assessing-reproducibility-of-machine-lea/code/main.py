import json
import logging
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('artifacts/logs/main.log')
    ]
)
logger = logging.getLogger(__name__)

def get_docker_hash() -> Optional[str]:
    """Attempt to retrieve the Docker image hash for traceability."""
    try:
        # Check if running inside Docker
        if os.path.exists('/.dockerenv'):
            result = subprocess.run(
                ['docker', 'images', '--no-trunc'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    # Parse the second line (first data row) for IMAGE ID
                    parts = lines[1].split()
                    if len(parts) >= 3:
                        return parts[2] # IMAGE ID column
        return None
    except Exception as e:
        logger.warning(f"Could not retrieve Docker hash: {e}")
        return None

def log_environment() -> Dict[str, Any]:
    """Log environment details including Python version, OS, and Docker hash."""
    env_info = {
        'python_version': platform.python_version(),
        'os': platform.system(),
        'os_version': platform.release(),
        'architecture': platform.machine(),
        'docker_hash': get_docker_hash()
    }
    logger.info(f"Environment: {json.dumps(env_info)}")
    return env_info

def load_repro_result(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a single repro result JSON file."""
    try:
        if not file_path.exists():
            logger.warning(f"Result file not found: {file_path}")
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None

def aggregate_results(results_dir: Path) -> List[Dict[str, Any]]:
    """
    Aggregate individual ReproResult objects from the results directory
    into a single list.
    
    Expected input files: *_repro_result.json or similar pattern in results_dir.
    Based on T013, individual results might be stored per paper or a single
    file. T018 description implies merging per-paper JSONs.
    
    Logic:
    1. Scan directory for JSON files matching expected pattern (e.g., repro_*.json).
    2. Load each valid JSON.
    3. If a file is a list, extend the master list.
    4. If a file is a dict, append it.
    5. Handle missing files by logging a warning and skipping.
    6. Return the aggregated list.
    """
    aggregated = []
    if not results_dir.exists():
        logger.warning(f"Results directory does not exist: {results_dir}")
        return aggregated

    # Look for JSON files. T013 output is artifacts/reports/repro_results.json.
    # If T013 runs per paper, there might be multiple files.
    # We will look for any JSON file in the directory to be robust,
    # or specifically the main repro_results.json if it's a collection.
    
    # Strategy: Check if the main file exists. If it's a list, use it.
    # If it's a dict, treat as single.
    # If multiple files exist (e.g. per-paper), aggregate them.
    
    json_files = sorted(results_dir.glob('*.json'))
    
    if not json_files:
        logger.warning("No JSON files found in results directory.")
        return aggregated

    for file_path in json_files:
        logger.info(f"Processing result file: {file_path}")
        data = load_repro_result(file_path)
        
        if data is None:
            continue

        if isinstance(data, list):
            aggregated.extend(data)
            logger.info(f"Extended list from {file_path} ({len(data)} items)")
        elif isinstance(data, dict):
            aggregated.append(data)
            logger.info(f"Appended dict from {file_path}")
        else:
            logger.warning(f"Unexpected data type in {file_path}: {type(data)}")

    logger.info(f"Total aggregated results: {len(aggregated)}")
    return aggregated

def compile_failure_log(failure_log_path: Path) -> List[Dict[str, Any]]:
    """
    Compile the failure log from artifacts/logs/failure_log.json.
    T030b is a dependency, so this file should exist if T030b ran.
    Handle gracefully if missing (T034 requirement logic applies here too).
    """
    if not failure_log_path.exists():
        logger.warning(f"Failure log not found: {failure_log_path}. Proceeding without it.")
        return []
    
    try:
        with open(failure_log_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading failure log: {e}")
        return []

def main():
    """
    Main entry point for T018.
    1. Log environment.
    2. Aggregate results from code/reports/ (or artifacts/reports/).
    3. Compile failure log.
    4. Write final aggregated results to artifacts/reports/repro_results.json.
    """
    # Define paths
    project_root = Path.cwd()
    results_dir = project_root / 'artifacts' / 'reports'
    output_file = results_dir / 'repro_results.json'
    failure_log_path = project_root / 'artifacts' / 'logs' / 'failure_log.json'

    # Ensure output directory exists
    results_dir.mkdir(parents=True, exist_ok=True)

    # Log environment
    env_info = log_environment()

    # Aggregate results
    # T013 produces individual results or a single file.
    # T018 aggregates them.
    aggregated_results = aggregate_results(results_dir)

    # If T013 produced a single file 'repro_results.json' already,
    # we might be re-reading it. The task says "Merge per-paper JSONs".
    # Assuming T013 might have created per-paper files or a partial list.
    # If the directory contains the output file we are about to write,
    # we should be careful not to re-aggregate our own output if running twice.
    # But for this implementation, we assume the input files are distinct 
    # or the previous run's output is the source of truth if no new files exist.
    
    # If no results were found in the directory (e.g. T013 hasn't run or output is elsewhere),
    # we might need to look elsewhere, but strictly following T018:
    # "Merge per-paper JSONs into a list... output as a JSON array."
    
    # Write the aggregated results
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(aggregated_results, f, indent=2)
        logger.info(f"Successfully wrote aggregated results to {output_file}")
        print(f"Aggregation complete. Output: {output_file}")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        sys.exit(1)

    # Compile failure log (optional for T018, but good practice)
    failure_log = compile_failure_log(failure_log_path)
    if failure_log:
        logger.info(f"Loaded {len(failure_log)} failure entries.")

    return 0

if __name__ == '__main__':
    sys.exit(main())