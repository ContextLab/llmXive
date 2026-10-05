import subprocess
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

def setup_logging(log_path: str):
    """Setup logging configuration."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class GitMvDetector:
    """
    Detects file renames (git mv) using `git log --follow`.
    Identifies structural refactors by checking path hash changes or directory level changes.
    """

    def __init__(self, repo_path: str, log_path: str):
        self.repo_path = Path(repo_path)
        self.log_path = Path(log_path)
        self.logger = setup_logging(str(self.log_path))
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository path not found: {self.repo_path}")

    def _run_git_command(self, args: List[str], cwd: Optional[Path] = None) -> Tuple[str, str, int]:
        """Run a git command and return stdout, stderr, and return code."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd or self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            self.logger.error(f"Git command failed: {e}")
            return "", str(e), 1

    def _get_file_history(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Get the history of a file including renames using `git log --follow`.
        Returns a list of commits with file paths involved.
        """
        # Use --follow to track renames
        stdout, stderr, rc = self._run_git_command(
            ["log", "--follow", "--name-only", "--pretty=format:%H|%s", "--", file_path]
        )
        
        if rc != 0:
            self.logger.warning(f"Git log failed for {file_path}: {stderr}")
            return []

        history = []
        lines = stdout.strip().split('\n')
        current_commit = None
        
        for line in lines:
            if not line:
                continue
            if '|' in line:
                # Commit header
                parts = line.split('|', 1)
                current_commit = {
                    "hash": parts[0],
                    "message": parts[1] if len(parts) > 1 else "",
                    "files": []
                }
                history.append(current_commit)
            elif current_commit is not None:
                current_commit["files"].append(line)
        
        return history

    def _get_current_path_for_block(self, file_path: str) -> Optional[str]:
        """
        Determine the current path of a file by checking if it exists in the working tree
        or by tracing its history if it was renamed.
        """
        # Check if file exists at current path
        if (self.repo_path / file_path).exists():
            return file_path

        # If not, try to find it in history
        history = self._get_file_history(file_path)
        if not history:
            return None

        # The last entry in history usually contains the current path if renamed
        # We look for the most recent file path in the history chain
        all_files = []
        for commit in history:
            all_files.extend(commit["files"])
        
        # Get unique files in reverse order (newest first)
        seen = set()
        unique_files = []
        for f in reversed(all_files):
            if f not in seen:
                seen.add(f)
                unique_files.append(f)
        
        if unique_files:
            # The first unique file (newest) is likely the current path
            return unique_files[0]
        
        return None

    def _check_directory_level_change(self, old_path: str, new_path: str) -> bool:
        """
        Check if the directory level has changed significantly (structural refactor).
        Returns True if the directory structure has changed (e.g., moved to different root).
        """
        old_parts = Path(old_path).parts
        new_parts = Path(new_path).parts
        
        # If the number of directory levels differs significantly or root changes
        if len(old_parts) != len(new_parts):
            return True
        
        # Check if the top-level directory is different
        if len(old_parts) > 0 and len(new_parts) > 0:
            if old_parts[0] != new_parts[0]:
                return True
        
        return False

    def _calculate_path_hash(self, file_path: str) -> str:
        """Calculate a hash based on the file path structure."""
        import hashlib
        return hashlib.md5(file_path.encode()).hexdigest()

    def detect_refactor(self, block_id: str, original_file_path: str) -> Optional[Dict[str, Any]]:
        """
        Detect if a code block's file has been renamed or refactored.
        
        Returns:
            Dict with block_id, old_path, new_path, reason if a refactor is detected.
            None if no refactor detected.
        """
        current_path = self._get_current_path_for_block(original_file_path)
        
        if current_path is None:
            # File doesn't exist in git history at all
            self.logger.info(f"Block {block_id}: File {original_file_path} not found in git history.")
            return None

        if current_path == original_file_path:
            # No rename detected
            return None

        # Check if it's a rename or a structural refactor
        old_hash = self._calculate_path_hash(original_file_path)
        new_hash = self._calculate_path_hash(current_path)
        
        is_directory_change = self._check_directory_level_change(original_file_path, current_path)
        
        reason_parts = []
        if old_hash != new_hash:
            reason_parts.append("Path hash changed")
        if is_directory_change:
            reason_parts.append("Directory level changed (structural refactor)")
        
        if not reason_parts:
            reason_parts.append("File renamed")

        exclusion = {
            "block_id": block_id,
            "old_path": original_file_path,
            "new_path": current_path,
            "reason": "; ".join(reason_parts)
        }
        
        self.logger.info(f"Detected refactor for block {block_id}: {original_file_path} -> {current_path} ({exclusion['reason']})")
        return exclusion

    def process_blocks(self, blocks_csv_path: str) -> List[Dict[str, Any]]:
        """
        Process a CSV of code blocks and detect refactors for each.
        
        Args:
            blocks_csv_path: Path to the CSV file with columns: block_id, file_path, ...
        
        Returns:
            List of exclusion records for blocks that were refactored.
        """
        exclusions = []
        
        if not Path(blocks_csv_path).exists():
            self.logger.error(f"Blocks CSV not found: {blocks_csv_path}")
            return exclusions

        import csv
        with open(blocks_csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                block_id = row.get('block_id')
                file_path = row.get('file_path')
                
                if not block_id or not file_path:
                    self.logger.warning(f"Skipping row with missing block_id or file_path: {row}")
                    continue

                exclusion = self.detect_refactor(block_id, file_path)
                if exclusion:
                    exclusions.append(exclusion)
        
        return exclusions

    def save_exclusions_log(self, exclusions: List[Dict[str, Any]], log_path: str):
        """Save exclusions to a log file in CSV format."""
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['block_id', 'old_path', 'new_path', 'reason'])
            writer.writeheader()
            for exc in exclusions:
                writer.writerow(exc)
        
        self.logger.info(f"Saved {len(exclusions)} exclusions to {log_path}")

    def save_validation_report(self, exclusions: List[Dict[str, Any]], total_blocks: int, report_path: str):
        """Save a JSON validation report."""
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        report = {
            "total_blocks_processed": total_blocks,
            "blocks_excluded": len(exclusions),
            "exclusions": exclusions,
            "timestamp": subprocess.run(["date", "-Iseconds"], capture_output=True, text=True).stdout.strip()
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Saved validation report to {report_path}")


def run_refactor_verification(
    blocks_csv_path: str,
    repo_path: str,
    log_path: str,
    report_path: str
) -> Dict[str, Any]:
    """
    Run the full refactor verification pipeline.
    
    Args:
        blocks_csv_path: Path to code_blocks.csv
        repo_path: Path to the git repository
        log_path: Path to save the exclusions log
        report_path: Path to save the validation report
    
    Returns:
        Dictionary with verification results.
    """
    detector = GitMvDetector(repo_path, log_path)
    
    exclusions = detector.process_blocks(blocks_csv_path)
    
    total_blocks = 0
    if Path(blocks_csv_path).exists():
        import csv
        with open(blocks_csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            total_blocks = sum(1 for _ in reader)
    
    detector.save_exclusions_log(exclusions, log_path)
    detector.save_validation_report(exclusions, total_blocks, report_path)
    
    return {
        "total_blocks_processed": total_blocks,
        "blocks_excluded": len(exclusions),
        "exclusions": exclusions
    }


def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Detect git mv refactors for code blocks")
    parser.add_argument("--blocks-csv", required=True, help="Path to code_blocks.csv")
    parser.add_argument("--repo-path", required=True, help="Path to git repository")
    parser.add_argument("--log-path", default="data/logs/refactor_exclusions.log", help="Path to exclusions log")
    parser.add_argument("--report-path", default="data/logs/refactor_validation_report.json", help="Path to validation report")
    
    args = parser.parse_args()
    
    result = run_refactor_verification(
        args.blocks_csv,
        args.repo_path,
        args.log_path,
        args.report_path
    )
    
    print(f"Processed {result['total_blocks_processed']} blocks, excluded {result['blocks_excluded']}")
    return 0


if __name__ == "__main__":
    exit(main())
