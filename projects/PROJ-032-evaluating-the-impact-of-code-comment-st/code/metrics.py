import os
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import subprocess
import json
import re
import statistics
import csv

# Import shared utilities from utils
from utils import configure_logging, MemoryMonitor, CommitSampler

logger = logging.getLogger(__name__)

def calc_churn(repo_path: Union[str, Path]) -> float:
    """
    Calculate the total churn (lines changed) for a repository.
    
    Parses `git log --numstat` to calculate total lines added and deleted
    per commit, then aggregates to the repository level.
    
    Args:
        repo_path: Path to the local git repository.
        
    Returns:
        Total churn as a float (sum of all lines added and deleted).
        
    Raises:
        RuntimeError: If git log fails or no history is found.
        MemoryError: If memory usage exceeds limits (checked via MemoryMonitor).
    """
    repo_path = Path(repo_path)
    if not repo_path.exists():
        raise FileNotFoundError(f"Repository path not found: {repo_path}")
    
    # Check memory before proceeding
    monitor = MemoryMonitor()
    if not monitor.check_limit(limit_gb=7):
        raise MemoryError("Memory limit exceeded during churn calculation.")

    logger.info(f"Calculating churn for repository: {repo_path}")
    
    try:
        # Run git log --numstat to get lines changed per commit
        # --numstat gives: added<tab>deleted<tab>filename
        # We use --no-renames to simplify parsing and avoid rename detection overhead
        cmd = [
            "git",
            "-C", str(repo_path),
            "log",
            "--numstat",
            "--no-renames",
            "--format="  # No commit headers, just numstat blocks
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=300  # 5 minute timeout for large repos
        )
        
        output = result.stdout
        
        if not output.strip():
            # Check if repo has any commits
            check_cmd = ["git", "-C", str(repo_path), "rev-list", "--count", "HEAD"]
            count_result = subprocess.run(check_cmd, capture_output=True, text=True)
            if count_result.stdout.strip() == "0":
                logger.warning(f"Repository {repo_path} has no commits. Churn = 0.")
                return 0.0
            else:
                # Repo has commits but log returned nothing (unlikely but possible)
                logger.warning(f"git log --numstat returned empty for {repo_path}.")
                return 0.0

        total_churn = 0.0
        lines_processed = 0
        
        # Parse numstat output
        # Format: added<tab>deleted<tab>filename
        # Lines starting with '-' for added/deleted mean binary files (we skip binary for churn metric usually, 
        # or treat as 0. For this metric, we'll skip binary files as they don't contribute to "lines of code" churn)
        for line in output.splitlines():
            lines_processed += 1
            parts = line.split('\t')
            
            if len(parts) < 3:
                # Skip malformed lines or empty lines
                continue
                
            added_str, deleted_str, filename = parts[0], parts[1], parts[2]
            
            # Skip binary files (marked as '-' in numstat)
            if added_str == '-' or deleted_str == '-':
                continue
            
            try:
                added = int(added_str) if added_str.isdigit() else 0
                deleted = int(deleted_str) if deleted_str.isdigit() else 0
                total_churn += (added + deleted)
            except ValueError:
                # Skip lines that don't parse as integers
                continue
                
        logger.info(f"Processed {lines_processed} lines for {repo_path}. Total churn: {total_churn}")
        return float(total_churn)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed for {repo_path}: {e.stderr}")
        raise RuntimeError(f"Git log failed for {repo_path}: {e.stderr}")
    except subprocess.TimeoutExpired:
        logger.error(f"Git command timed out for {repo_path}")
        raise RuntimeError(f"Git log timed out for {repo_path}")

def calc_complexity_for_file(file_path: Path) -> float:
    return 0.0

def calc_complexity(repo_path: Union[str, Path]) -> float:
    return 0.0

def get_complexity_breakdown(repo_path: Union[str, Path]) -> Dict[str, Any]:
    return {}

def calc_readability(comments: List[str]) -> float:
    return 0.0

def calc_sentiment(comments: List[str]) -> float:
    return 0.0

def calc_density(comments: List[str], total_lines: int) -> float:
    return 0.0

def calc_quality_rate(repo_path: Union[str, Path], manual_labels_path: Union[str, Path] = "data/manual_labels.csv", sample_size: int = 10) -> Dict[str, Any]:
    """
    Calculate the quality rate of a repository based on pylint analysis of sampled commits.
    
    This function:
    1. Samples commits using CommitSampler.
    2. Runs pylint on each sampled commit to detect error-level warnings.
    3. Calculates the ratio of commits with error-level warnings.
    4. Validates against manual labels (if available) and computes 95% CI.
    
    Args:
        repo_path: Path to the local git repository.
        manual_labels_path: Path to the CSV file containing manual labels.
        sample_size: Number of commits to sample.
        
    Returns:
        A dictionary containing:
            - quality_rate: The ratio of commits with error-level warnings.
            - sample_size: Number of commits sampled.
            - error_count: Number of commits with errors.
            - validation: Dict with 'accuracy', 'ci_lower', 'ci_upper' if manual labels exist.
    """
    repo_path = Path(repo_path)
    manual_labels_path = Path(manual_labels_path)
    
    if not repo_path.exists():
        raise FileNotFoundError(f"Repository path not found: {repo_path}")
    
    logger.info(f"Calculating quality rate for repository: {repo_path}")
    
    # Step 1: Get all commits
    try:
        cmd = ["git", "-C", str(repo_path), "rev-list", "HEAD"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        all_commits = [c.strip() for c in result.stdout.splitlines() if c.strip()]
        
        if not all_commits:
            logger.warning(f"Repository {repo_path} has no commits.")
            return {
                "quality_rate": 0.0,
                "sample_size": 0,
                "error_count": 0,
                "validation": None
            }
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get commits for {repo_path}: {e.stderr}")
        raise RuntimeError(f"Git rev-list failed for {repo_path}: {e.stderr}")
    
    # Step 2: Sample commits
    sampler = CommitSampler()
    sampled_commits = sampler.sample_commits(all_commits, n=sample_size)
    
    if not sampled_commits:
        logger.warning(f"No commits sampled for {repo_path}.")
        return {
            "quality_rate": 0.0,
            "sample_size": 0,
            "error_count": 0,
            "validation": None
        }
    
    # Step 3: Run pylint on each sampled commit
    error_count = 0
    error_details = []
    
    for commit in sampled_commits:
        try:
            # Checkout the commit
            checkout_cmd = ["git", "-C", str(repo_path), "checkout", commit]
            subprocess.run(checkout_cmd, capture_output=True, check=True, timeout=60)
            
            # Run pylint on the repository
            # We run pylint on the current state of the repo at this commit
            pylint_cmd = [
                "pylint",
                "--errors-only",
                "--output-format=json",
                "--disable=all",
                "--enable=E",  # Only enable error-level messages
                str(repo_path)
            ]
            
            pylint_result = subprocess.run(
                pylint_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Parse pylint output
            if pylint_result.returncode != 0 and pylint_result.stdout.strip():
                # Pylint returns non-zero if errors are found
                try:
                    errors = json.loads(pylint_result.stdout)
                    if errors:
                        error_count += 1
                        error_details.append({
                            "commit": commit,
                            "errors": len(errors)
                        })
                except json.JSONDecodeError:
                    # If output is not valid JSON but returncode is non-zero, assume errors
                    error_count += 1
                    error_details.append({
                        "commit": commit,
                        "errors": "Unknown (parse error)"
                    })
            
            # Reset to HEAD after each commit to avoid state issues
            reset_cmd = ["git", "-C", str(repo_path), "checkout", "HEAD"]
            subprocess.run(reset_cmd, capture_output=True, check=True, timeout=60)
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout analyzing commit {commit} in {repo_path}")
            continue
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to checkout or run pylint for commit {commit}: {e.stderr}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error processing commit {commit}: {e}")
            continue
    
    # Step 4: Calculate quality rate
    quality_rate = error_count / len(sampled_commits) if sampled_commits else 0.0
    
    result = {
        "quality_rate": quality_rate,
        "sample_size": len(sampled_commits),
        "error_count": error_count,
        "validation": None
    }
    
    # Step 5: Validate against manual labels if available
    if manual_labels_path.exists():
        try:
            # Load manual labels
            manual_labels = {}
            with open(manual_labels_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Assuming the CSV has columns: commit_hash, label (bug_fix or not_bug_fix)
                    # We map 'bug_fix' to 'error' for comparison purposes
                    commit_hash = row.get('commit_hash', '').strip()
                    label = row.get('label', '').strip().lower()
                    if commit_hash:
                        # Map manual label to our error definition
                        # If manual label is 'bug_fix', we consider it an error
                        manual_labels[commit_hash] = (label == 'bug_fix')
            
            # Compare our detected errors with manual labels for the sampled commits
            tp, fp, tn, fn = 0, 0, 0, 0
            
            for commit in sampled_commits:
                predicted_error = any(d['commit'] == commit for d in error_details)
                actual_error = manual_labels.get(commit, None)
                
                if actual_error is not None:
                    if predicted_error and actual_error:
                        tp += 1
                    elif predicted_error and not actual_error:
                        fp += 1
                    elif not predicted_error and actual_error:
                        fn += 1
                    elif not predicted_error and not actual_error:
                        tn += 1
            
            # Calculate accuracy
            total_valid = tp + fp + tn + fn
            accuracy = (tp + tn) / total_valid if total_valid > 0 else 0.0
            
            # Calculate 95% CI for accuracy using Wilson score interval
            if total_valid > 0:
                z = 1.96  # 95% confidence
                p = accuracy
                n = total_valid
                
                denominator = 1 + (z**2)/n
                center = (p + (z**2)/(2*n)) / denominator
                margin = (z / denominator) * ((p*(1-p)/n) + (z**2)/(4*n**2))**0.5
                
                ci_lower = max(0, center - margin)
                ci_upper = min(1, center + margin)
                
                result["validation"] = {
                    "accuracy": accuracy,
                    "ci_lower": ci_lower,
                    "ci_upper": ci_upper,
                    "tp": tp,
                    "fp": fp,
                    "tn": tn,
                    "fn": fn,
                    "total_valid": total_valid
                }
                logger.info(f"Validation for {repo_path}: Accuracy={accuracy:.4f}, 95% CI=[{ci_lower:.4f}, {ci_upper:.4f}]")
            else:
                result["validation"] = {
                    "accuracy": None,
                    "ci_lower": None,
                    "ci_upper": None,
                    "message": "No overlapping commits between sample and manual labels"
                }
                
        except Exception as e:
            logger.error(f"Failed to validate quality rate for {repo_path}: {e}")
            result["validation"] = {
                "error": str(e)
            }
    
    return result

def main():
    """
    Main entry point for testing calc_quality_rate.
    """
    configure_logging()
    repo_path = Path("data/raw/test_repo")  # Example path
    if repo_path.exists():
        result = calc_quality_rate(repo_path)
        print(json.dumps(result, indent=2))
    else:
        print(f"Test repository not found at {repo_path}. Please clone a repo first.")

if __name__ == "__main__":
    main()
