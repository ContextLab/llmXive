import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Determine the project root directory."""
    # Assume the script is in code/setup/verify_structure.py
    # Project root is two levels up
    current_file = Path(__file__).resolve()
    return current_file.parent.parent

def verify_directories(root: Path) -> List[str]:
    """Verify that all required directories exist."""
    required_dirs = [
        "code",
        "tests",
        "data",
        "code/lib",
        "code/data",
        "code/models",
        "code/evaluation",
        "data/results",
        "data/logs",
        "data/intermediate",
        "data/config"
    ]

    missing = []
    for dir_name in required_dirs:
        dir_path = root / dir_name
        if not dir_path.is_dir():
            missing.append(dir_name)
            logger.warning(f"Missing directory: {dir_path}")
        else:
            logger.info(f"Verified directory: {dir_path}")

    return missing

def run_tree_command(root: Path) -> str:
    """Run the 'tree' command and return its output."""
    try:
        # Run tree command, ignoring errors if tree is not installed
        result = subprocess.run(
            ['tree', '-a', '-L', '3', str(root)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout
        else:
            logger.warning(f"Tree command failed: {result.stderr}")
            # Fallback: generate a simple directory listing
            return generate_fallback_tree(root)
    except FileNotFoundError:
        logger.warning("Tree command not found, using fallback")
        return generate_fallback_tree(root)
    except subprocess.TimeoutExpired:
        logger.error("Tree command timed out")
        return generate_fallback_tree(root)

def generate_fallback_tree(root: Path) -> str:
    """Generate a simple directory tree representation."""
    lines = [f"{root.name}/"]
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip hidden directories except .git
        dirnames[:] = [d for d in dirnames if not d.startswith('.') or d == '.git']
        
        level = len(Path(dirpath).relative_to(root).parts)
        indent = '    ' * level
        lines.append(f"{indent}{Path(dirpath).name}/")
        
        sub_indent = '    ' * (level + 1)
        for filename in sorted(filenames):
            if not filename.startswith('.'):
                lines.append(f"{sub_indent}{filename}")
        
        if level >= 3:
            dirnames.clear()  # Stop descending deeper

    return '\n'.join(lines)

def write_verification_report(root: Path, missing_dirs: List[str], tree_output: str) -> None:
    """Write the verification report to data/logs/structure_verification.txt."""
    logs_dir = root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = logs_dir / "structure_verification.txt"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("PROJECT STRUCTURE VERIFICATION REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Project Root: {root}\n")
        f.write(f"Verification Time: {logging.Formatter('%Y-%m-%d %H:%M:%S').format(logging.LogRecord('', '', '', '', (), None, None))}\n\n")
        
        f.write("-" * 40 + "\n")
        f.write("DIRECTORY VERIFICATION\n")
        f.write("-" * 40 + "\n")
        
        if missing_dirs:
            f.write(f"FAILED: {len(missing_dirs)} missing directories:\n")
            for d in missing_dirs:
                f.write(f"  - {d}\n")
        else:
            f.write("PASSED: All required directories exist.\n")
        
        f.write("\n")
        f.write("-" * 40 + "\n")
        f.write("DIRECTORY TREE\n")
        f.write("-" * 40 + "\n")
        f.write(tree_output)
        f.write("\n")
        f.write("=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")
    
    logger.info(f"Verification report written to: {report_path}")

def main():
    """Main entry point for structure verification."""
    root = get_project_root()
    logger.info(f"Starting structure verification at: {root}")
    
    # Verify directories
    missing = verify_directories(root)
    
    # Get tree output
    tree_output = run_tree_command(root)
    
    # Write report
    write_verification_report(root, missing, tree_output)
    
    # Return exit code
    if missing:
        logger.error(f"Verification failed: {len(missing)} missing directories")
        sys.exit(1)
    else:
        logger.info("Verification completed successfully")
        sys.exit(0)

if __name__ == "__main__":
    main()
