import os
import subprocess
import sys
import shutil
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from config for memory limit constant
from .config import get_memory_limit_bytes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemoryLimitExceeded(Exception):
    """Raised when memory usage exceeds the configured limit."""
    pass

class DataFetchError(Exception):
    """Raised when data fetching fails."""
    pass

def get_defects4j_path() -> Path:
    """Get the path to the Defects4J installation."""
    path = os.environ.get('DEFECTS4J_HOME')
    if not path:
        raise DataFetchError("DEFECTS4J_HOME environment variable not set")
    return Path(path)

def get_java_compiler_path() -> Path:
    """Get the path to the Java compiler."""
    # Try to find javac in PATH
    javac = shutil.which('javac')
    if not javac:
        raise DataFetchError("Java compiler (javac) not found in PATH")
    return Path(javac)

def run_defects4j_command(args: List[str], cwd: Optional[Path] = None) -> str:
    """Run a Defects4J command and return its output."""
    defects4j_path = get_defects4j_path()
    cmd = [str(defects4j_path / 'bin' / 'defects4j')] + args
    
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

def list_available_projects() -> List[Dict[str, Any]]:
    """List available Defects4J projects with their metadata."""
    projects = []
    output = run_defects4j_command(['list'])
    
    for line in output.strip().split('\n'):
        if line.startswith('['):
            parts = line.split()
            if len(parts) >= 2:
                project_id = parts[0].strip('[]')
                # Parse version and other info if available
                projects.append({
                    'project_id': project_id,
                    'status': 'available'
                })
    
    return projects

def get_project_size(project_id: str) -> int:
    """Estimate the size of a project in terms of Java files."""
    # This is a placeholder; actual implementation would check the project
    # For now, return a dummy value
    return 100

def get_current_memory_usage_bytes() -> int:
    """
    Get the current memory usage of the process in bytes.
    
    Uses /proc/self/status on Linux or psutil if available.
    Falls back to a conservative estimate if neither is available.
    
    Returns:
        int: Memory usage in bytes.
    """
    try:
        # Try to read from /proc/self/status (Linux)
        if os.path.exists('/proc/self/status'):
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        # VmRSS is in kB
                        value = int(line.split()[1])
                        return value * 1024
        
        # Try psutil if available
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except ImportError:
            pass
        
        # Fallback: return 0 (conservative, but safe)
        logger.warning("Could not determine memory usage accurately. Returning 0.")
        return 0
        
    except Exception as e:
        logger.warning(f"Error getting memory usage: {e}. Returning 0.")
        return 0

def validate_ram_limit(max_bytes: Optional[int] = None, check_interval: float = 1.0) -> None:
    """
    Validate that current memory usage does not exceed the limit.
    
    Args:
        max_bytes: Maximum allowed memory in bytes. If None, uses config default.
        check_interval: Interval in seconds between checks (not used for single check).
        
    Raises:
        MemoryLimitExceeded: If memory usage exceeds the limit.
    """
    if max_bytes is None:
        max_bytes = get_memory_limit_bytes()
    
    current_usage = get_current_memory_usage_bytes()
    if current_usage > max_bytes:
        raise MemoryLimitExceeded(
            f"Memory limit exceeded: {current_usage / (1024**3):.2f} GB > "
            f"{max_bytes / (1024**3):.2f} GB"
        )
    
    logger.info(f"Memory check passed: {current_usage / (1024**3):.2f} GB / "
                f"{max_bytes / (1024**3):.2f} GB")

def monitor_memory_periodically(check_interval: float = 1.0, max_bytes: Optional[int] = None) -> None:
    """
    Monitor memory usage periodically and raise an error if limit is exceeded.
    
    This function is designed to be called in a loop during long-running operations.
    
    Args:
        check_interval: Interval in seconds between checks.
        max_bytes: Maximum allowed memory in bytes. If None, uses config default.
        
    Raises:
        MemoryLimitExceeded: If memory usage exceeds the limit.
    """
    if max_bytes is None:
        max_bytes = get_memory_limit_bytes()
    
    while True:
        current_usage = get_current_memory_usage_bytes()
        logger.info(f"Current memory usage: {current_usage / (1024**3):.2f} GB")
        
        if current_usage > max_bytes:
            raise MemoryLimitExceeded(
                f"Memory limit exceeded: {current_usage / (1024**3):.2f} GB > "
                f"{max_bytes / (1024**3):.2f} GB"
            )
        
        time.sleep(check_interval)

def is_generated_or_non_java(file_path: Path) -> bool:
    """Check if a file is generated code or not a Java file."""
    # Check file extension
    if file_path.suffix != '.java':
        return True
    
    # Check for common generated file patterns
    generated_patterns = [
        'generated', 'gen', 'build', 'target', 'out', '.class',
        'AutoValue', 'Dagger', 'Builder', 'Factory'
    ]
    
    file_name_lower = file_path.name.lower()
    for pattern in generated_patterns:
        if pattern in file_name_lower:
            return True
    
    # Check for common generated file paths
    generated_paths = [
        '/build/', '/target/', '/out/', '/.gradle/', '/.mvn/'
    ]
    
    file_path_str = str(file_path).lower()
    for pattern in generated_paths:
        if pattern in file_path_str:
            return True
    
    return False

def filter_java_files(file_paths: List[Path]) -> List[Path]:
    """Filter a list of file paths to include only valid Java files."""
    return [f for f in file_paths if not is_generated_or_non_java(f)]

def select_dynamic_subset(projects: List[Dict[str, Any]], 
                          max_files: int = 10000,
                          max_ram_gb: float = 6.0) -> List[Dict[str, Any]]:
    """
    Select a dynamic subset of projects based on file count and RAM limits.
    
    Args:
        projects: List of available projects.
        max_files: Maximum number of Java files to include.
        max_ram_gb: Maximum RAM usage in GB.
        
    Returns:
        List of selected projects.
    """
    selected = []
    total_files = 0
    max_bytes = int(max_ram_gb * 1024 * 1024 * 1024)
    
    # Sort projects alphabetically for reproducibility
    sorted_projects = sorted(projects, key=lambda x: x['project_id'])
    
    for project in sorted_projects:
        project_id = project['project_id']
        # Estimate files (this would be more accurate with real data)
        estimated_files = get_project_size(project_id)
        
        if total_files + estimated_files > max_files:
            break
        
        # Check memory limit periodically
        validate_ram_limit(max_bytes)
        
        selected.append(project)
        total_files += estimated_files
        
        logger.info(f"Selected project {project_id}, total files: {total_files}")
    
    logger.info(f"Selected {len(selected)} projects with {total_files} files")
    return selected

def download_defects4j_subset(selected_projects: List[Dict[str, Any]], 
                              output_dir: Path) -> None:
    """
    Download a subset of Defects4J projects.
    
    Args:
        selected_projects: List of projects to download.
        output_dir: Directory to download projects to.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for project in selected_projects:
        project_id = project['project_id']
        project_dir = output_dir / project_id
        
        if project_dir.exists():
            logger.info(f"Project {project_id} already exists, skipping")
            continue
        
        logger.info(f"Downloading project {project_id}")
        
        # Use Defects4J CLI to checkout the project
        try:
            run_defects4j_command(['checkout', '-p', project_id, '-v', '1', '-d', str(project_dir)])
            
            # Monitor memory during download
            # In a real implementation, we'd run this in a separate thread
            # or check periodically during the process
            validate_ram_limit()
            
        except DataFetchError as e:
            logger.error(f"Failed to download project {project_id}: {e}")
            raise

def checkout_bug_introduction_commit(project_dir: Path, 
                                     project_id: str, 
                                     bug_id: int) -> None:
    """
    Checkout the bug-introduction commit for a specific project and bug.
    
    Args:
        project_dir: Path to the project directory.
        project_id: Project identifier.
        bug_id: Bug identifier.
    """
    # Use Defects4J to checkout the buggy version
    # This typically involves using 'defects4j checkout' with specific flags
    try:
        # Note: The exact command may vary based on Defects4J version
        run_defects4j_command(['checkout', '-p', project_id, '-v', str(bug_id), '-d', str(project_dir)])
    except DataFetchError as e:
        logger.error(f"Failed to checkout bug-introduction commit for {project_id}-{bug_id}: {e}")
        raise

def get_project_metadata(project_dir: Path) -> Dict[str, Any]:
    """
    Get metadata for a project.
    
    Args:
        project_dir: Path to the project directory.
        
    Returns:
        Dictionary containing project metadata.
    """
    metadata = {
        'project_id': project_dir.name,
        'path': str(project_dir),
        'java_files': []
    }
    
    # Find all Java files
    java_files = list(project_dir.rglob('*.java'))
    metadata['java_files'] = [str(f) for f in java_files]
    metadata['file_count'] = len(java_files)
    
    return metadata

def main():
    """Main entry point for the ingest module."""
    logger.info("Starting Defects4J ingestion process")
    
    try:
        # List available projects
        projects = list_available_projects()
        logger.info(f"Found {len(projects)} available projects")
        
        # Select a dynamic subset
        selected = select_dynamic_subset(projects)
        
        # Download the subset
        output_dir = Path('code/data/raw/defects4j_subset')
        download_defects4j_subset(selected, output_dir)
        
        logger.info("Ingestion completed successfully")
        
    except MemoryLimitExceeded as e:
        logger.error(f"Memory limit exceeded: {e}")
        sys.exit(1)
    except DataFetchError as e:
        logger.error(f"Data fetch error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
