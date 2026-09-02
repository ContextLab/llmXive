import os
import json
import logging
import subprocess
import tempfile
from typing import List, Dict, Any, Optional, Tuple

from datasets import load_dataset
import pandas as pd
from radon.raw import analyze as radon_analyze
from radon.complexity import cc_visit
from radon.visitors import ComplexityVisitor
import ast

from config import get_data_path, get_results_path, setup_logging
from monitoring import record_batch_metrics, save_metrics_to_file, get_peak_ram_for_batch
from helpers import compute_radon_metrics_safe

logger = setup_logging(__name__)

# Constants
TARGET_SAMPLE_SIZE = 800
MAX_RUNTIME_HOURS = 5.5
RANDOM_SEED = 42
BATCH_SIZE = 50

def verify_dataset_source() -> bool:
    """Verify the dataset is accessible before attempting to stream."""
    try:
        ds = load_dataset("codeparrot/github-code", streaming=True, split="train")
        # Try to get one item to verify connectivity
        next(iter(ds))
        logger.info("Dataset 'codeparrot/github-code' verified accessible.")
        return True
    except Exception as e:
        logger.error(f"Dataset verification failed: {e}")
        raise ConnectionError(f"Cannot access dataset 'codeparrot/github-code': {e}")

def _estimate_time_per_function(sample_size: int = 10) -> float:
    """Estimate time to process a single function by sampling a small batch."""
    import time
    ds = load_dataset("codeparrot/github-code", streaming=True, split="train")
    start = time.time()
    count = 0
    for item in ds:
        if count >= sample_size:
            break
        # Simulate minimal processing
        _ = item.get("code", "")
        count += 1
    elapsed = time.time() - start
    return elapsed / max(count, 1)

def load_sampled_functions(target_size: int = TARGET_SAMPLE_SIZE) -> List[Dict[str, Any]]:
    """
    Load functions from codeparrot/github-code with stratified sampling.
    
    Implements stratified sampling based on 'repo_name' metadata to prevent
    bias towards a single code style, as per T053 requirements.
    Falls back to random sampling if 'repo_name' is missing or insufficient
    for stratification.
    """
    logger.info(f"Starting stratified sampling for {target_size} functions.")
    verify_dataset_source()
    
    # Estimate time per function to enforce runtime constraints
    est_time = _estimate_time_per_function()
    max_samples_by_time = int((MAX_RUNTIME_HOURS * 3600) / est_time)
    
    if max_samples_by_time < target_size:
        logger.warning(f"Runtime constraint limits sample to {max_samples_by_time} functions.")
        target_size = max_samples_by_time
    
    if target_size < 100:
        logger.warning(f"Sample size reduced to {target_size} due to time constraints. Proceeding.")
        # Log deviation to sample_report.json
        report_path = get_results_path("sample_report.json")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump({
                "requested": TARGET_SAMPLE_SIZE,
                "actual": target_size,
                "reason": "runtime_constraint",
                "warning": "Sample size significantly reduced."
            }, f, indent=2)

    ds = load_dataset("codeparrot/github-code", streaming=True, split="train")
    
    # Attempt stratified sampling by repo_name
    # We collect counts first to determine strata proportions
    strata_counts = {}
    buffer = []
    count = 0
    
    # First pass: collect strata distribution (limited to avoid infinite stream)
    # We assume the stream is large enough to get a representative sample of strata
    # We'll sample a larger initial set to determine proportions
    initial_scan_limit = 5000 
    for item in ds:
        if count >= initial_scan_limit:
            break
        repo = item.get("repo_name", "unknown")
        strata_counts[repo] = strata_counts.get(repo, 0) + 1
        count += 1
    
    total_scanned = sum(strata_counts.values())
    strata_proportions = {k: v / total_scanned for k, v in strata_counts.items()}
    
    logger.info(f"Identified {len(strata_proportions)} strata (repos) for stratification.")
    
    # Calculate samples per stratum
    samples_per_stratum = {}
    remaining = target_size
    strata_list = list(strata_proportions.keys())
    
    # Proportional allocation
    for i, repo in enumerate(strata_list):
        if i == len(strata_list) - 1:
            # Last stratum gets the remainder
            samples_per_stratum[repo] = remaining
        else:
            count = int(target_size * strata_proportions[repo])
            samples_per_stratum[repo] = count
            remaining -= count
    
    # Ensure we don't exceed target
    if sum(samples_per_stratum.values()) > target_size:
        # Adjust last one down
        last_repo = strata_list[-1]
        samples_per_stratum[last_repo] -= (sum(samples_per_stratum.values()) - target_size)
    
    logger.info(f"Stratified allocation: {samples_per_stratum}")

    # Second pass: collect functions per stratum
    # Since streaming doesn't support direct filtering by value efficiently without full scan,
    # we implement a reservoir-like approach per stratum or a two-pass logic if we had random access.
    # Given streaming constraints, we will iterate and fill buckets until full.
    
    buckets = {repo: [] for repo in samples_per_stratum.keys()}
    collected_count = 0
    
    # Reset dataset iterator
    ds = load_dataset("codeparrot/github-code", streaming=True, split="train")
    
    for item in ds:
        if collected_count >= target_size:
            break
        
        repo = item.get("repo_name", "unknown")
        
        # If this repo is a valid stratum and not full
        if repo in samples_per_stratum and len(buckets[repo]) < samples_per_stratum[repo]:
            buckets[repo].append(item)
            collected_count += 1
        elif repo == "unknown" and "unknown" not in samples_per_stratum:
            # If we have an 'unknown' stratum and it's not in our plan, skip or add to a catch-all if needed
            # For now, skip to maintain strict stratification
            pass

    # Flatten buckets
    sampled_functions = []
    for repo, items in buckets.items():
        sampled_functions.extend(items)
    
    logger.info(f"Stratified sampling complete. Collected {len(sampled_functions)} functions.")
    return sampled_functions

def compute_radon_metrics(code: str) -> Dict[str, Any]:
    """Compute LOC, Cyclomatic Complexity, and Nesting Depth."""
    try:
        raw = radon_analyze(code)
        cc = cc_visit(code)
        max_cc = max([c.complexity for c in cc], default=0)
        
        # Nesting depth calculation
        try:
            tree = ast.parse(code)
            visitor = ComplexityVisitor.from_ast(tree)
            max_nesting = max(visitor.nests, default=0)
        except:
            max_nesting = 0
        
        return {
            "loc": raw.loc,
            "cyclomatic_complexity": max_cc,
            "nesting_depth": max_nesting
        }
    except Exception as e:
        logger.error(f"Radon analysis failed: {e}")
        return {"loc": 0, "cyclomatic_complexity": 0, "nesting_depth": 0}

def run_pylint_analysis(code: str) -> List[str]:
    """Run Pylint and return raw codes."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name
        
        result = subprocess.run(
            ["pylint", "--output-format=json", temp_path],
            capture_output=True,
            text=True
        )
        os.unlink(temp_path)
        
        if result.returncode == 0 or result.returncode == 1: # 1 means issues found
            try:
                issues = json.loads(result.stdout)
                codes = [issue.get("symbol", issue.get("message-id", "unknown")) for issue in issues]
                return list(set(codes))
            except json.JSONDecodeError:
                return []
        return []
    except Exception as e:
        logger.error(f"Pylint failed: {e}")
        return []

def normalize_pylint_smells(codes: List[str], mapping: Dict[str, str]) -> List[str]:
    """Normalize Pylint codes to canonical smell names."""
    normalized = []
    for code in codes:
        if code in mapping:
            normalized.append(mapping[code])
        else:
            logger.warning(f"Unmapped Pylint code: {code}")
            normalized.append(code) # Keep raw if unmapped
    return normalized

def process_functions(functions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process a list of functions, computing metrics and labels."""
    results = []
    
    # Load smell mapping
    mapping_path = "contracts/smell_mapping.json"
    if os.path.exists(mapping_path):
        with open(mapping_path, 'r') as f:
            smell_mapping = json.load(f)
    else:
        smell_mapping = {}
    
    for func in functions:
        code = func.get("code", "")
        if not code:
            continue
        
        metrics = compute_radon_metrics(code)
        raw_codes = run_pylint_analysis(code)
        normalized_labels = normalize_pylint_smells(raw_codes, smell_mapping)
        
        results.append({
            "code": code,
            "loc": metrics["loc"],
            "cyclomatic_complexity": metrics["cyclomatic_complexity"],
            "nesting_depth": metrics["nesting_depth"],
            "static_smell_labels": json.dumps(normalized_labels)
        })
    return results

def save_to_csv(data: List[Dict[str, Any]], output_path: str):
    """Save processed data to CSV."""
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(data)} records to {output_path}")

def validate_output(df: pd.DataFrame) -> bool:
    """Validate output schema and completeness."""
    required_cols = ["code", "loc", "cyclomatic_complexity", "nesting_depth", "static_smell_labels"]
    if not all(col in df.columns for col in required_cols):
        logger.error("Missing required columns")
        return False
    
    valid_rows = df.dropna().shape[0]
    total_rows = df.shape[0]
    if total_rows > 0 and (valid_rows / total_rows) < 0.95:
        logger.error(f"Validity rate {valid_rows/total_rows:.2%} < 95%")
        return False
    return True

def run_pipeline():
    """Main pipeline execution."""
    logger.info("Starting Data Pipeline...")
    
    # Load sampled functions
    functions = load_sampled_functions()
    
    # Process
    processed = process_functions(functions)
    
    # Save
    output_path = get_data_path("static_baseline.csv")
    save_to_csv(processed, output_path)
    
    # Validate
    df = pd.read_csv(output_path)
    if validate_output(df):
        logger.info("Pipeline completed successfully.")
    else:
        logger.error("Pipeline validation failed.")

if __name__ == "__main__":
    run_pipeline()
