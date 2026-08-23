"""
Git MV Detection Module for T012b.

Implements verification logic for 'git mv' detection using `git log --follow`.
Excludes code blocks only if the file path hash changes significantly or
the directory level changes (indicating a complete structural refactor).
"""
import subprocess
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import existing models if needed, though this task focuses on git logic
# from utils.models import CodeBlock 

class GitMvDetector:
    """
    Handles detection of file renames and structural refactors using git history.
    """

    def __init__(self, repo_path: str, logger: Optional[logging.Logger] = None):
        self.repo_path = Path(repo_path)
        self.logger = logger or logging.getLogger(__name__)
        
    def _run_git_command(self, args: List[str]) -> Tuple[str, str, int]:
        """
        Execute a git command in the repository directory.
        Returns (stdout, stderr, return_code).
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            self.logger.error(f"Git command timed out: {args}")
            return "", "Timeout", 1
        except FileNotFoundError:
            self.logger.error("Git not found in PATH")
            return "", "Git not found", 1

    def get_file_history_with_follow(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Run `git log --follow --name-status` to track file renames.
        
        Args:
            file_path: The current relative path of the file in the repo.
        
        Returns:
            List of dicts containing commit info and file paths.
        """
        # Use --follow to track renames, --name-status to see path changes
        # Format: %H (hash) %ad (date) %s (subject)
        # Then we parse the R (Rename) lines from name-status
        cmd = [
            "log",
            "--follow",
            "--name-status",
            "--format=%H|%ad|%s",
            "--date=short",
            "--",
            file_path
        ]
        
        stdout, stderr, code = self._run_git_command(cmd)
        
        if code != 0:
            if "does not exist" in stderr or "no such path" in stderr:
                self.logger.warning(f"File {file_path} does not exist in repo history.")
                return []
            self.logger.error(f"Git log failed for {file_path}: {stderr}")
            return []

        history = []
        current_commit = {}
        
        lines = stdout.strip().split('\n')
        for line in lines:
            if not line:
                continue
            
            # Commit header format: hash|date|subject
            if '|' in line and line[0] not in ['A', 'M', 'D', 'R', 'C']:
                parts = line.split('|', 2)
                if len(parts) >= 3:
                    current_commit = {
                        'hash': parts[0],
                        'date': parts[1],
                        'subject': parts[2],
                        'paths': []
                    }
                continue
            
            # Name-status lines: A, M, D, R (Rename), C (Copy)
            # R format: R100\told_path\tnew_path
            # M/A/D format: <status>\t<path>
            if line.startswith('R'):
                # Rename detected
                parts = line.split('\t')
                if len(parts) >= 3:
                    status = parts[0] # e.g., R100
                    old_path = parts[1]
                    new_path = parts[2]
                    if current_commit:
                        current_commit['paths'].append({
                            'status': status,
                            'old_path': old_path,
                            'new_path': new_path,
                            'type': 'rename'
                        })
                        # Update the tracking path for subsequent commits in history
                        # (since we are going backwards in time, the 'new_path' in the log
                        # is actually the 'old_path' for the next iteration backwards)
                        # However, for our check, we just need to know IF a rename happened
                        # that matches our criteria.
            elif line.startswith(('A', 'M', 'D', 'C')):
                parts = line.split('\t')
                if len(parts) >= 2 and current_commit:
                    current_commit['paths'].append({
                        'status': parts[0],
                        'path': parts[1],
                        'type': 'change'
                    })
            
            if current_commit and current_commit.get('paths'):
                history.append(current_commit)
                current_commit = {}
        
        return history

    def check_refactor_exclusion(self, block_id: str, current_file_path: str) -> Optional[Dict[str, Any]]:
        """
        Determine if a block should be excluded due to structural refactor.
        
        Criteria for exclusion:
        1. File path hash changes (significant rename/move).
        2. Directory level changes (e.g., moved from root to a deep subdirectory).
        
        Args:
            block_id: Unique identifier for the code block.
            current_file_path: Relative path of the file in the repo.
        
        Returns:
            Dict with exclusion details if excluded, None otherwise.
        """
        if not self.repo_path.exists():
            self.logger.error(f"Repository path does not exist: {self.repo_path}")
            return None

        history = self.get_file_history_with_follow(current_file_path)
        
        if not history:
            # If no history found, we can't verify, so we might exclude or keep based on policy.
            # Task says: "Exclude block ONLY if file path hash changes OR directory level changes".
            # If we can't verify, we cannot confirm exclusion criteria, so we keep it (conservative).
            return None

        exclusion_reason = None
        old_path = None
        new_path = None

        # Check for Renames in history
        for commit in history:
            for path_change in commit.get('paths', []):
                if path_change['type'] == 'rename':
                    old_p = path_change.get('old_path')
                    new_p = path_change.get('new_path')
                    
                    # Calculate directory depth difference
                    old_dir = Path(old_p).parent
                    new_dir = Path(new_p).parent
                    
                    old_depth = len(old_dir.parts)
                    new_depth = len(new_dir.parts)
                    
                    # Heuristic: Directory level change > 1 indicates structural refactor
                    if abs(new_depth - old_depth) > 1:
                        exclusion_reason = f"Directory level change detected: {old_depth} -> {new_depth}"
                        old_path = old_p
                        new_path = new_p
                        break
                    
                    # Heuristic: Significant path hash change (e.g., completely different name)
                    # We can check if the filename stem is completely different
                    old_name = Path(old_p).stem
                    new_name = Path(new_p).stem
                    
                    # Simple heuristic: if the longest common substring is very small
                    # Or just check if they are totally different
                    if old_name != new_name and len(set(old_name) & set(new_name)) < 2:
                        exclusion_reason = "Significant filename hash change detected"
                        old_path = old_p
                        new_path = new_p
                        break
            
            if exclusion_reason:
                break

        if exclusion_reason:
            self.logger.info(f"Excluding block {block_id}: {exclusion_reason}")
            return {
                "block_id": block_id,
                "old_path": old_path,
                "new_path": new_path,
                "reason": exclusion_reason,
                "timestamp": datetime.now().isoformat()
            }

        return None

def run_refactor_verification(
    repo_path: str,
    code_blocks_csv_path: str,
    log_path: str,
    report_path: str
) -> None:
    """
    Main entry point for T012b execution.
    
    Reads code blocks, runs git mv detection, logs exclusions, and generates a report.
    """
    # Setup logging
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("GitMvDetector")
    logger.setLevel(logging.INFO)
    
    # File handler for the specific log file
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console handler for debugging
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.info(f"Starting Git MV Detection for repo: {repo_path}")
    
    # Read code blocks
    if not os.path.exists(code_blocks_csv_path):
        logger.error(f"Code blocks file not found: {code_blocks_csv_path}")
        # Create empty report if input missing
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump({"total_blocks": 0, "excluded": 0, "exclusions": []}, f)
        return

    import csv
    blocks_to_process = []
    with open(code_blocks_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            blocks_to_process.append(row)

    logger.info(f"Processing {len(blocks_to_process)} blocks")

    detector = GitMvDetector(repo_path, logger)
    exclusions = []
    processed_count = 0

    for block in blocks_to_process:
        block_id = block.get('block_id')
        file_path = block.get('file_path')
        
        if not block_id or not file_path:
            continue
        
        exclusion = detector.check_refactor_exclusion(block_id, file_path)
        if exclusion:
            exclusions.append(exclusion)
        
        processed_count += 1
        if processed_count % 100 == 0:
            logger.info(f"Processed {processed_count}/{len(blocks_to_process)} blocks")

    # Write exclusion log (CSV format as requested: block_id, old_path, new_path, reason)
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['block_id', 'old_path', 'new_path', 'reason'])
        for exc in exclusions:
            writer.writerow([
                exc['block_id'],
                exc['old_path'],
                exc['new_path'],
                exc['reason']
            ])
    
    logger.info(f"Wrote {len(exclusions)} exclusions to {log_path}")

    # Generate validation report (JSON)
    report_data = {
        "total_blocks_processed": processed_count,
        "total_excluded": len(exclusions),
        "inclusion_rate": (processed_count - len(exclusions)) / processed_count if processed_count > 0 else 0.0,
        "exclusions": exclusions,
        "generated_at": datetime.now().isoformat()
    }

    report_path_obj = Path(report_path)
    report_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Generated validation report at {report_path}")

def main():
    """
    CLI entry point for T012b.
    Expected arguments: repo_path, code_blocks_csv, log_output, report_output
    """
    import sys
    
    if len(sys.argv) < 5:
        print("Usage: python git_mv_detector.py <repo_path> <code_blocks_csv> <log_output> <report_output>")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    code_blocks_csv = sys.argv[2]
    log_output = sys.argv[3]
    report_output = sys.argv[4]
    
    run_refactor_verification(repo_path, code_blocks_csv, log_output, report_output)

if __name__ == "__main__":
    main()
