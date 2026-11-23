import os
import subprocess
import sys
from pathlib import Path
from utils.logger import get_logger, ConfigurationError

logger = get_logger(__name__)

def main() -> None:
    """
    Verifies the project directory structure was created correctly.
    Executes the equivalent of `ls -R` on the project root and logs the output.
    """
    project_root = Path("projects/PROJ-800-assessing-parcellation-sensitivity-of-hu")
    
    if not project_root.exists():
        error_msg = f"Project root does not exist: {project_root}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg)

    logger.info(f"Verifying directory structure at: {project_root}")
    
    try:
        # Execute ls -R (or dir /S on Windows) to list contents
        if sys.platform == "win32":
            # Windows command
            result = subprocess.run(
                ["dir", "/S", str(project_root)],
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout
        else:
            # Unix/Linux/macOS command
            result = subprocess.run(
                ["ls", "-R", str(project_root)],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout

        # Write output to state log (create state dir if needed, though task T001 only asks for basic structure)
        # We'll write to the project root's data/results for now as per standard convention, 
        # or just print if state isn't strictly defined yet. 
        # The task asks to capture to state/setup_verification.log.
        # We will assume 'state' is a sibling to 'projects' or inside project. 
        # Given T001 only creates specific dirs, we might need to create 'state' or use a default.
        # Let's create the state directory if it doesn't exist to be safe, or write to project root.
        # Re-reading T001: it only creates specific dirs. T002 asks to capture to state/setup_verification.log.
        # We will create the state directory here to satisfy T002's requirement.
        
        state_dir = project_root / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        log_path = state_dir / "setup_verification.log"
        
        with open(log_path, "w") as f:
            f.write(output)
        
        logger.info(f"Verification output written to: {log_path}")
        print(f"Directory structure verified. Log saved to: {log_path}")
        print("-" * 40)
        print(output)

    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to list directory contents: {e}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg) from e
    except FileNotFoundError as e:
        error_msg = f"Command not found (ls/dir): {e}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg) from e

if __name__ == "__main__":
    main()