import subprocess
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .logging_config import get_logger

# Logger instance
logger = get_logger(__name__)

class GitMvDetector:
    """
    Detects file renames (git mv) and structural refactors for specific code blocks.
    Uses `git log --follow` to track file history.
    """

    def __init__(self, repo_path: str, log_path: Optional[str] = None):
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository path not found: {repo_path}")
        
        self.log_path = Path(log_path) if log_path else self.repo_path.parent / "logs" / "refactor_exclusions.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize logger for this specific task if needed, or use global
        self.logger = logging.getLogger("git_mv_detector")
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_path)
            formatter = logging.Formatter('%(message)s') # Format: block_id, old_path, new_path, reason
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _run_git_command(self, args: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str]:
        """Runs a git command and returns (success, output)."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd or self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip()
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def get_file_history(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Retrieves the history of a file using `git log --follow`.
        Returns a list of commits with paths involved.
        """
        # Use --follow to detect renames
        success, output = self._run_git_command([
            "log", "--follow", "--name-status", "--format=%H|%ci", "--", file_path
        ])
        
        if not success:
            return []

        history = []
        lines = output.split('\n')
        current_commit = None
        
        for line in lines:
            if not line.strip():
                continue
            
            if line.startswith('commit '):
                # Extract commit hash and date from format %H|%ci
                parts = line.split('|')
                if len(parts) >= 2:
                    current_commit = {
                        "hash": parts[0].replace("commit ", ""),
                        "date": parts[1] if len(parts) > 1 else "",
                        "changes": []
                    }
                    history.append(current_commit)
            elif current_commit and line[0] in ['A', 'M', 'D', 'R']:
                # Parse status and paths
                parts = line.split('\t')
                if len(parts) >= 2:
                    status = parts[0]
                    old_path = parts[1]
                    new_path = parts[2] if len(parts) > 2 else old_path
                    
                    current_commit["changes"].append({
                        "status": status,
                        "old_path": old_path,
                        "new_path": new_path
                    })

        return history

    def calculate_path_hash(self, path: str) -> str:
        """Calculates a simple hash of the path string to detect structural changes."""
        return str(hash(path))

    def get_directory_level(self, path: str) -> int:
        """Returns the directory depth of a path."""
        return len(Path(path).parts) - 1

    def detect_refactor(self, block_id: str, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Checks if the file_path associated with block_id has been renamed or refactored.
        Returns exclusion info if a refactor is detected, None otherwise.
        
        Criteria for exclusion:
        1. File path hash changes (indicates rename).
        2. Directory level changes significantly (indicates structural refactor).
        """
        if not os.path.exists(self.repo_path / file_path):
            # File might not exist in current HEAD if it was deleted, but we check history
            pass

        history = self.get_file_history(file_path)
        
        if not history:
            # No history found, assume no rename for this check
            return None

        # Check the most recent commit that modified this file
        latest_commit = history[-1] if history else None
        
        if not latest_commit:
            return None

        # Check for 'R' (Rename) status in the latest commit
        for change in latest_commit.get("changes", []):
            if change["status"].startswith("R"):
                old_path = change["old_path"]
                new_path = change["new_path"]
                
                # Calculate directory levels
                old_level = self.get_directory_level(old_path)
                new_level = self.get_directory_level(new_path)
                
                # Determine reason
                reason = "Rename detected"
                if abs(old_level - new_level) > 1:
                    reason = "Structural refactor (directory level change)"
                
                return {
                    "block_id": block_id,
                    "old_path": old_path,
                    "new_path": new_path,
                    "reason": reason
                }

        # If no explicit rename, check if the file path in history differs from current
        # This handles cases where git log --follow might not flag a simple rename as 'R' in all contexts
        # but the path string itself changed over time.
        # However, `--follow` usually keeps the path constant if it's just a rename tracked.
        # We rely on the 'R' status primarily.
        
        return None

    def log_exclusion(self, exclusion_info: Dict[str, Any]):
        """Logs the exclusion to the refactor_exclusions.log file."""
        log_entry = f"{exclusion_info['block_id']}, {exclusion_info['old_path']}, {exclusion_info['new_path']}, {exclusion_info['reason']}"
        self.logger.info(log_entry)

def run_refactor_verification(
    code_blocks_path: str,
    repo_path: str,
    output_log_path: str,
    output_report_path: str
) -> Dict[str, Any]:
    """
    Runs the git mv detection verification on a list of code blocks.
    
    Args:
        code_blocks_path: Path to the CSV containing code blocks (data/raw/code_blocks.csv).
        repo_path: Path to the git repository.
        output_log_path: Path to write the exclusion log.
        output_report_path: Path to write the validation report JSON.
        
    Returns:
        A dictionary with summary statistics.
    """
    import csv
    from pathlib import Path

    detector = GitMvDetector(repo_path, log_path=output_log_path)
    
    excluded_blocks = []
    total_blocks = 0
    processed_blocks = 0

    try:
        with open(code_blocks_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_blocks += 1
                block_id = row.get('block_id')
                file_path = row.get('file_path')
                
                if not block_id or not file_path:
                    continue
                
                processed_blocks += 1
                
                exclusion = detector.detect_refactor(block_id, file_path)
                
                if exclusion:
                    detector.log_exclusion(exclusion)
                    excluded_blocks.append(exclusion)
    except FileNotFoundError:
        logger.error(f"Code blocks file not found: {code_blocks_path}")
        return {"error": "Code blocks file not found"}
    except Exception as e:
        logger.error(f"Error processing blocks: {e}")
        return {"error": str(e)}

    # Generate Report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_blocks_processed": total_blocks,
        "blocks_excluded": len(excluded_blocks),
        "exclusions": excluded_blocks
    }

    with open(output_report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Verification complete. Excluded {len(excluded_blocks)} blocks. Report saved to {output_report_path}")
    
    return report

def main():
    """
    Entry point for running the refactor verification script.
    Expects environment variables or hardcoded paths for demonstration.
    """
    # Default paths relative to project root if run from root
    base_path = Path(__file__).parent.parent.parent
    code_blocks_path = base_path / "data" / "raw" / "code_blocks.csv"
    repo_path = base_path / "data" / "temp_repos" / "sample_repo" # This would be populated by T011
    output_log_path = base_path / "data" / "logs" / "refactor_exclusions.log"
    output_report_path = base_path / "data" / "logs" / "refactor_validation_report.json"

    # If the repo path doesn't exist, we can't run the full verification
    # but we can still demonstrate the function structure.
    if not repo_path.exists():
        print(f"Warning: Repository path {repo_path} does not exist. Skipping full verification.")
        print("This script is designed to run after T011 clones repositories.")
        return

    run_refactor_verification(
        str(code_blocks_path),
        str(repo_path),
        str(output_log_path),
        str(output_report_path)
    )

if __name__ == "__main__":
    main()
