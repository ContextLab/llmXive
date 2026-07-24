import os
import subprocess
import sys
import shutil
import json
import psutil
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for exclusion patterns
GENERATED_CODE_PATTERNS = [
    r'.*[/\\]target[/\\].*',  # Maven build output
    r'.*[/\\]build[/\\].*',   # Gradle build output
    r'.*[/\\]gen[/\\].*',     # Generic generated folder
    r'.*[/\\]generated-sources[/\\].*',
    r'.*[/\\]generated-test-sources[/\\].*',
    r'.*[/\\]dist[/\\].*',
    r'.*[/\\]bin[/\\].*',
    r'.*[/\\]classes[/\\].*',
    r'.*[/\\]out[/\\].*',
    r'.*_gen\.java$',         # Common generated suffix
    r'.*Test\.java$',         # Test files (optional, depending on scope)
    r'.*gen[/\\].*',
    r'.*[/\\]r[/\\].*',       # Android R.java
    r'.*[/\\]R\.java$',
]

# Regex compiled once for performance
EXCLUSION_REGEX = re.compile('|'.join(GENERATED_CODE_PATTERNS))

def get_defects4j_path() -> Path:
    """Get the path to the Defects4J installation directory."""
    path = os.environ.get('DEFECTS4J_HOME')
    if not path:
        raise EnvironmentError("DEFECTS4J_HOME environment variable not set.")
    return Path(path)

def run_defects4j_command(command: List[str]) -> subprocess.CompletedProcess:
    """Run a Defects4J CLI command and return the result."""
    d4j_path = get_defects4j_path()
    cmd = [str(d4j_path / 'dev-scripts' / 'defects4j')] + command
    logger.debug(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Defects4J command failed: {result.stderr}")
        raise RuntimeError(f"Defects4J command failed: {result.stderr}")
    return result

def list_available_projects() -> List[str]:
    """List all available projects in Defects4J."""
    result = run_defects4j_command(['list'])
    # Output is typically one project per line
    projects = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return projects

def get_project_size(project_id: str) -> int:
    """Estimate the size of a project in MB (simplified heuristic)."""
    # In a real implementation, this might query disk usage of the checkout
    # For now, we return a dummy value or fetch from a metadata file if available
    # This is a placeholder for the dynamic subset validation logic
    return 50  # Placeholder: 50MB average

def get_current_memory_usage_bytes() -> int:
    """Get current memory usage in bytes."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss

def validate_ram_limit(required_mb: int) -> bool:
    """Check if the system has enough free RAM to proceed."""
    available_mb = psutil.virtual_memory().available / (1024 * 1024)
    return available_mb >= required_mb

def select_dynamic_subset(projects: List[str], target_mb: int) -> List[str]:
    """Select a subset of projects that fits within the RAM limit."""
    selected = []
    current_size = 0
    for proj in projects:
        size = get_project_size(proj)
        if current_size + size <= target_mb:
            selected.append(proj)
            current_size += size
        else:
            logger.info(f"Reached RAM limit at project {proj}. Stopping selection.")
            break
    return selected

def download_defects4j_subset(project_ids: List[str], output_dir: Path) -> None:
    """Download and checkout specific Defects4J projects."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for proj_id in project_ids:
        logger.info(f"Checking out project {proj_id}...")
        # defects4j checkout -p <project> -v <version> -d <dir>
        # Assuming version 1 for simplicity or fetching latest
        run_defects4j_command(['checkout', '-p', proj_id, '-v', '1', '-d', str(output_dir / proj_id)])

def is_generated_or_non_java(file_path: Path, project_root: Path) -> bool:
    """
    Determine if a file should be excluded based on:
    1. Non-Java extension
    2. Being in a generated code directory
    3. Common generated file patterns
    """
    # Check extension
    if file_path.suffix != '.java':
        return True

    # Get relative path from project root to check build directories
    try:
        relative_path = file_path.relative_to(project_root)
        relative_str = str(relative_path).replace(os.sep, '/')
    except ValueError:
        # File is not under project_root, skip or handle as needed
        return True

    # Check against exclusion patterns
    if EXCLUSION_REGEX.match(relative_str):
        logger.debug(f"Excluding generated/non-Java file: {file_path}")
        return True

    return False

def filter_java_files(project_root: Path, java_files: List[Path]) -> List[Path]:
    """
    Filter a list of file paths to include only valid Java source files,
    excluding generated code and non-Java files.
    
    Args:
        project_root: The root directory of the project.
        java_files: A list of Path objects representing potential Java files.
        
    Returns:
        A list of Path objects for files that are valid Java sources.
        
    Side Effects:
        Logs excluded files at DEBUG level and excluded counts at INFO level.
    """
    valid_files = []
    excluded_count = 0
    excluded_reasons: Dict[str, int] = {}

    for file_path in java_files:
        if not file_path.exists():
            excluded_count += 1
            reason = "File does not exist"
            excluded_reasons[reason] = excluded_reasons.get(reason, 0) + 1
            continue

        if is_generated_or_non_java(file_path, project_root):
            excluded_count += 1
            reason = "Generated or non-Java"
            excluded_reasons[reason] = excluded_reasons.get(reason, 0) + 1
            continue

        valid_files.append(file_path)

    logger.info(f"Filtered {len(java_files)} files: {len(valid_files)} valid, {excluded_count} excluded.")
    for reason, count in excluded_reasons.items():
        logger.debug(f"Excluded due to {reason}: {count} files")

    return valid_files

def main():
    """
    Main entry point for testing the ingestion and filtering logic.
    This function demonstrates the exclusion logic by scanning a mock directory.
    """
    logger.info("Starting ingestion filtering demo...")
    
    # Example usage of filter_java_files
    # In a real pipeline, this would be called after cloning projects
    mock_project_root = Path("/tmp/mock_project")
    mock_project_root.mkdir(parents=True, exist_ok=True)
    
    # Create some mock files to test filtering
    (mock_project_root / "src" / "main" / "java" / "com" / "example" / "App.java").mkdir(parents=True, exist_ok=True)
    (mock_project_root / "target" / "generated-sources" / "com" / "example" / "Gen.java").mkdir(parents=True, exist_ok=True)
    (mock_project_root / "src" / "test" / "java" / "com" / "example" / "AppTest.java").mkdir(parents=True, exist_ok=True)
    (mock_project_root / "build.gradle").touch()
    
    mock_files = [
        mock_project_root / "src" / "main" / "java" / "com" / "example" / "App.java",
        mock_project_root / "target" / "generated-sources" / "com" / "example" / "Gen.java",
        mock_project_root / "src" / "test" / "java" / "com" / "example" / "AppTest.java",
        mock_project_root / "build.gradle",
        mock_project_root / "src" / "main" / "resources" / "config.xml",
    ]
    
    valid = filter_java_files(mock_project_root, mock_files)
    logger.info(f"Valid files found: {[str(f) for f in valid]}")
    
    # Cleanup
    shutil.rmtree(mock_project_root)
    logger.info("Demo completed.")

if __name__ == "__main__":
    main()