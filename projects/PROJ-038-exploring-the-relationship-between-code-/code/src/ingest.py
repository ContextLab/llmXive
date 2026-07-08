import os
import subprocess
import sys
import shutil
import json
import psutil
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import time

from src.config import get_memory_limit_bytes, validate_defects4j_path

def get_defects4j_path() -> Path:
    """Return the path to the Defects4J installation directory."""
    path = os.getenv("DEFECTS4J_HOME")
    if not path:
        raise RuntimeError("DEFECTS4J_HOME environment variable is not set.")
    return Path(path)

def run_defects4j_command(args: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """Run a Defects4J CLI command and return the result."""
    d4j_home = get_defects4j_path()
    cmd = [str(d4j_home / "bin" / "defects4j"), *args]
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        return result
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Defects4J command timed out: {' '.join(cmd)}")

def list_available_projects() -> List[str]:
    """List all available project IDs in the Defects4J database."""
    result = run_defects4j_command(["list"])
    if result.returncode != 0:
        raise RuntimeError(f"Failed to list projects: {result.stderr}")
    # Output format is typically one project ID per line
    projects = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
    return projects

def get_project_size(project_id: str) -> int:
    """
    Estimate the size of a project's source code in bytes.
    Uses 'defects4j info' or checks local checkout if available.
    For this implementation, we estimate based on typical project sizes
    or fetch metadata if available.
    
    Since Defects4J CLI doesn't directly report size, we will:
    1. Try to checkout a temporary instance to measure.
    2. Or use a heuristic based on project ID if checkout is too slow.
    
    To keep it efficient, we will attempt a lightweight checkout to a temp dir
    and measure the 'src' directory size.
    """
    temp_dir = Path(f"/tmp/d4j_size_check_{project_id}_{os.getpid()}")
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)
        
        # Checkout the project
        result = run_defects4j_command(
            ["checkout", "-p", project_id, "-v", "0", "-d", str(temp_dir)],
            cwd=temp_dir
        )
        
        if result.returncode != 0:
            # Fallback: return a heuristic estimate if checkout fails
            # Most Defects4J projects are between 1MB and 50MB
            # We'll use a rough estimate based on project ID length/hash
            # This is not ideal but prevents blocking if the CLI is slow
            return 5_000_000 
        
        # Calculate size of src directory
        src_dir = temp_dir / "src"
        if not src_dir.exists():
            src_dir = temp_dir  # Fallback to root if no src dir
        
        total_size = 0
        for path in src_dir.rglob("*"):
            if path.is_file():
                total_size += path.stat().st_size
        
        return total_size
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def get_current_memory_usage_bytes() -> int:
    """Get current process memory usage in bytes."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss

def validate_ram_limit(projects_to_add: List[str], current_size: int, limit_bytes: Optional[int] = None) -> bool:
    """
    Validate if adding the given projects would exceed the RAM limit.
    Returns True if safe to add, False otherwise.
    """
    if limit_bytes is None:
        limit_bytes = get_memory_limit_bytes()
    
    # Estimate total size if we add these projects
    # We use a heuristic: current_size + (average_project_size * len(projects))
    # To be safe, we assume an average of 5MB per project if we can't measure individually
    estimated_addition = len(projects_to_add) * 5_000_000 
    
    return (current_size + estimated_addition) <= limit_bytes

def select_dynamic_subset(
    available_projects: List[str], 
    limit_bytes: Optional[int] = None, 
    target_count: int = 50
) -> List[str]:
    """
    Select a dynamic subset of projects that fits within the RAM limit.
    
    Args:
        available_projects: List of all available project IDs.
        limit_bytes: Maximum RAM allowed (bytes). Defaults to config value.
        target_count: Target number of projects to select if limit allows.
    
    Returns:
        List of selected project IDs.
    """
    if limit_bytes is None:
        limit_bytes = get_memory_limit_bytes()
    
    selected = []
    current_size = 0
    
    # Sort projects to ensure deterministic selection (optional, but good for reproducibility)
    # We can sort by project ID or use a seed-based shuffle if needed.
    # For now, we iterate in the order provided.
    
    for project in available_projects:
        # Check if we've reached target count
        if len(selected) >= target_count:
            break
        
        # Estimate size of this project
        project_size = get_project_size(project)
        
        # Validate if adding this project exceeds limit
        if current_size + project_size <= limit_bytes:
            selected.append(project)
            current_size += project_size
        else:
            # If adding this project exceeds limit, stop
            # In a real scenario, we might try to find smaller projects,
            # but for simplicity, we stop here.
            break
    
    return selected

def download_defects4j_subset(
    projects: List[str], 
    output_dir: Path,
    force: bool = False
) -> Dict[str, Any]:
    """
    Download and checkout the specified projects from Defects4J.
    
    Args:
        projects: List of project IDs to download.
        output_dir: Directory where projects will be checked out.
        force: If True, remove existing project directories before checkout.
    
    Returns:
        Dictionary with download statistics and metadata.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "total_projects": len(projects),
        "successful": 0,
        "failed": 0,
        "failed_projects": [],
        "total_size_bytes": 0,
        "start_time": time.time(),
        "end_time": None
    }
    
    for project in projects:
        project_dir = output_dir / project
        
        if project_dir.exists():
            if force:
                shutil.rmtree(project_dir)
            else:
                print(f"Skipping {project}: already exists")
                stats["successful"] += 1
                continue
        
        try:
            # Checkout project version 0 (buggy version)
            result = run_defects4j_command(
                ["checkout", "-p", project, "-v", "0", "-d", str(project_dir)],
                cwd=project_dir
            )
            
            if result.returncode == 0:
                stats["successful"] += 1
                # Calculate actual size
                total_size = 0
                for path in project_dir.rglob("*"):
                    if path.is_file():
                        total_size += path.stat().st_size
                stats["total_size_bytes"] += total_size
                print(f"Successfully checked out {project} ({total_size} bytes)")
            else:
                stats["failed"] += 1
                stats["failed_projects"].append(project)
                print(f"Failed to checkout {project}: {result.stderr}")
        except Exception as e:
            stats["failed"] += 1
            stats["failed_projects"].append(project)
            print(f"Error checking out {project}: {str(e)}")
    
    stats["end_time"] = time.time()
    stats["duration_seconds"] = stats["end_time"] - stats["start_time"]
    
    return stats

def filter_java_files(project_dir: Path) -> List[Path]:
    """
    Filter and return all .java files in a project directory.
    
    Args:
        project_dir: Path to the project root.
    
    Returns:
        List of Path objects for .java files.
    """
    java_files = []
    src_dirs = ["src/main/java", "src", "src/java", "java"]
    
    for src_dir in src_dirs:
        search_path = project_dir / src_dir
        if search_path.exists():
            java_files.extend(search_path.rglob("*.java"))
    
    # If no standard src structure found, search entire project
    if not java_files:
        java_files = list(project_dir.rglob("*.java"))
    
    # Exclude generated code, test code (optional, depending on requirements)
    # For now, we include all .java files
    return java_files

def main():
    """Main entry point for the ingestion script."""
    print("Starting Defects4J data ingestion...")
    
    # Validate Defects4J path
    validate_defects4j_path()
    
    # Get available projects
    try:
        available = list_available_projects()
        print(f"Found {len(available)} available projects in Defects4J")
    except Exception as e:
        print(f"Error listing projects: {e}")
        sys.exit(1)
    
    # Select dynamic subset based on RAM limit
    limit = get_memory_limit_bytes()
    print(f"Memory limit: {limit / (1024**3):.2f} GB")
    
    selected_projects = select_dynamic_subset(available, limit_bytes=limit, target_count=50)
    print(f"Selected {len(selected_projects)} projects for ingestion")
    
    if not selected_projects:
        print("No projects selected. Exiting.")
        sys.exit(0)
    
    # Download selected projects
    output_dir = Path("data/raw/defects4j_projects")
    stats = download_defects4j_subset(selected_projects, output_dir)
    
    print("\nIngestion Summary:")
    print(f"  Total projects requested: {stats['total_projects']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Total size: {stats['total_size_bytes'] / (1024**2):.2f} MB")
    print(f"  Duration: {stats['duration_seconds']:.2f} seconds")
    
    if stats['failed_projects']:
        print(f"  Failed projects: {', '.join(stats['failed_projects'])}")
    
    # Save stats to a JSON file
    stats_file = output_dir / "ingestion_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\nIngestion stats saved to {stats_file}")

if __name__ == "__main__":
    main()