import os
import sys
from pathlib import Path
from utils.logger import get_logger, ConfigurationError

logger = get_logger(__name__)

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not path.exists():
        logger.info(f"Creating directory: {path}")
        path.mkdir(parents=True, exist_ok=True)
    elif not path.is_dir():
        raise ConfigurationError(f"Path exists but is not a directory: {path}")

def main() -> None:
    """Create the project directory structure and verify it."""
    project_root = Path("projects/PROJ-800-assessing-parcellation-sensitivity-of-hu")
    
    # Define subdirectories
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
    ]
    code_dirs = [
        project_root / "code",
        project_root / "tests",
    ]
    
    all_dirs = data_dirs + code_dirs
    
    try:
        # Create directories
        for d in all_dirs:
            ensure_directory(d)
        
        # Verify and capture listing
        logger.info("Verifying directory structure...")
        if not project_root.exists():
            raise ConfigurationError(f"Project root does not exist: {project_root}")
        
        # Generate verification log content
        verification_log_path = Path("state/setup_verification.log")
        verification_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Execute ls -R logic manually to ensure portability and capture output
        output_lines = []
        output_lines.append(f"Directory listing for {project_root}:")
        output_lines.append("-" * 50)
        
        for root, dirs, files in os.walk(project_root):
            level = root.replace(str(project_root), '').count(os.sep)
            indent = ' ' * 2 * level
            output_lines.append(f"{indent}{os.path.basename(root)}/")
            sub_indent = ' ' * 2 * (level + 1)
            for file in files:
                output_lines.append(f"{sub_indent}{file}")
            # Ensure empty directories are listed (os.walk might skip them if they have no files)
            for d in dirs:
                pass # Handled by walk
        
        # Explicit check for required paths to ensure they are logged even if empty
        required_paths = [
            project_root / "data" / "raw",
            project_root / "data" / "processed",
            project_root / "data" / "results",
            project_root / "code",
            project_root / "tests",
        ]
        
        for req_path in required_paths:
            if req_path.is_dir() and not any(req_path.iterdir()):
                # Ensure it appears in the log if it's empty
                if str(req_path) not in "".join(output_lines):
                     rel = req_path.relative_to(project_root)
                     output_lines.append(f"\n{rel}/ (empty)")

        log_content = "\n".join(output_lines)
        
        with open(verification_log_path, 'w') as f:
            f.write(log_content)
        
        logger.info(f"Verification log written to: {verification_log_path}")
        print(log_content)
        
    except Exception as e:
        logger.error(f"Failed to setup directories: {e}", exc_info=True)
        raise ConfigurationError(f"Directory setup failed: {e}")
