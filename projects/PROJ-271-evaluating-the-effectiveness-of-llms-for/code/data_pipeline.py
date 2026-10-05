import os
import json
import logging
import subprocess
import tempfile
import time
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

import pandas as pd
from datasets import load_dataset
from radon.raw import analyze as radon_analyze
from radon.complexity import cc_visit
import pylint.lint
from io import StringIO
import sys

from config import get_data_path, get_results_path, setup_logging
from monitoring import get_ram_usage_mb, get_cpu_utilization, record_batch_metrics, save_metrics_to_file

# Configure logging
logger = setup_logging(__name__)

# Constants
RANDOM_SEED = 42
TARGET_SAMPLE_SIZE = 800
MAX_RUNTIME_HOURS = 5.5
BATCH_SIZE = 10

def verify_dataset_source(dataset_id: str, split: str) -> bool:
    """Verify the dataset is accessible before attempting to stream."""
    try:
        ds = load_dataset(dataset_id, split=split, streaming=True)
        # Attempt to fetch one item to verify connectivity
        next(iter(ds))
        logger.info(f"Dataset {dataset_id} split {split} verified successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to verify dataset source {dataset_id}: {e}")
        raise ConnectionError(f"Dataset {dataset_id} is unreachable: {e}")

def load_sampled_functions(dataset_id: str = "codeparrot/github-code", split: str = "train", target_size: int = TARGET_SAMPLE_SIZE) -> List[Dict[str, Any]]:
    """
    Load functions from the dataset with stratified sampling based on file extension.
    Ensures proportional distribution across file types to prevent bias.
    """
    logger.info(f"Loading and stratifying sample from {dataset_id}...")
    
    # Load dataset with streaming
    ds = load_dataset(dataset_id, split=split, streaming=True)
    
    # First pass: Collect statistics on file extensions (stratification key)
    # We need to estimate the distribution to sample proportionally
    # Since we can't load everything, we sample a large chunk to estimate distribution
    # or use the dataset's metadata if available.
    
    # Strategy: 
    # 1. Stream a representative subset (e.g., 10k items) to estimate distribution
    # 2. Calculate target counts per stratum
    # 3. Stream the full dataset again and collect items until quotas are met
    
    estimate_sample_size = 10000
    logger.info(f"Estimating distribution from {estimate_sample_size} items...")
    
    distribution_counter = Counter()
    total_estimated = 0
    
    try:
        for i, item in enumerate(ds):
            if i >= estimate_sample_size:
                break
            path = item.get("path", "")
            if path:
                ext = os.path.splitext(path)[1] or "no_ext"
                distribution_counter[ext] += 1
                total_estimated += 1
    except Exception as e:
        logger.warning(f"Error during distribution estimation: {e}. Falling back to random sampling.")
        # Fallback: simple random sample if stratification fails
        ds_sample = ds.shuffle(seed=RANDOM_SEED).take(target_size)
        return [item for item in ds_sample]
    
    if total_estimated == 0:
        logger.warning("No files found in estimate sample. Falling back to random sampling.")
        ds_sample = ds.shuffle(seed=RANDOM_SEED).take(target_size)
        return [item for item in ds_sample]

    # Calculate proportions
    proportions = {k: v / total_estimated for k, v in distribution_counter.items()}
    logger.info(f"Estimated distribution: {proportions}")
    
    # Calculate target counts per stratum
    strata_targets = {k: int(v * target_size) for k, v in proportions.items()}
    
    # Ensure we meet the target size (adjust last bucket if needed)
    current_sum = sum(strata_targets.values())
    if current_sum < target_size:
        # Add the remainder to the largest stratum
        max_stratum = max(strata_targets, key=strata_targets.get)
        strata_targets[max_stratum] += (target_size - current_sum)
    
    logger.info(f"Stratification targets: {strata_targets}")
    
    # Second pass: Collect items meeting quotas
    collected = {}
    quotas = dict(strata_targets)
    total_collected = 0
    
    for item in ds:
        path = item.get("path", "")
        if not path:
            continue
        ext = os.path.splitext(path)[1] or "no_ext"
        
        if ext in quotas and quotas[ext] > 0:
            if ext not in collected:
                collected[ext] = []
            collected[ext].append(item)
            quotas[ext] -= 1
            total_collected += 1
            
            if total_collected >= target_size:
                break
    
    # Flatten the collected items
    final_sample = []
    for ext, items in collected.items():
        final_sample.extend(items)
    
    logger.info(f"Stratified sampling complete. Collected {len(final_sample)} functions.")
    
    # Log sample report
    report = {
        "total_collected": len(final_sample),
        "target": target_size,
        "distribution": {k: len(v) for k, v in collected.items()},
        "proportions": {k: len(v)/len(final_sample) for k, v in collected.items()}
    }
    
    results_path = get_results_path()
    os.makedirs(results_path, exist_ok=True)
    report_path = os.path.join(results_path, "sample_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Sample report written to {report_path}")
    
    return final_sample

def compute_radon_metrics(code: str) -> Dict[str, Any]:
    """Compute LOC, Cyclomatic Complexity, and Nesting Depth."""
    try:
        raw = radon_analyze(code)
        loc = raw.loc
        cc = cc_visit(code)
        max_cc = max([c.complexity for c in cc]) if cc else 0
        
        # Estimate nesting depth from raw stats or AST
        # Radon raw doesn't give nesting depth directly, but we can estimate from max_nesting
        # Using a heuristic or simpler metric if direct nesting is hard
        # For this implementation, we'll use a simplified nesting depth calculation
        # based on indentation levels or a heuristic
        lines = code.split('\n')
        max_indent = 0
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)
        
        # Normalize indentation to depth (assuming 4 spaces per level)
        nesting_depth = max_indent // 4
        
        return {
            "loc": loc,
            "cyclomatic_complexity": max_cc,
            "nesting_depth": nesting_depth
        }
    except Exception as e:
        logger.error(f"Radon analysis failed: {e}")
        return {"loc": 0, "cyclomatic_complexity": 0, "nesting_depth": 0}

def run_pylint_analysis(code: str) -> List[str]:
    """Run Pylint and return list of message codes."""
    try:
        # Create a temporary file for Pylint
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name

        # Run Pylint
        output = StringIO()
        sys.stdout = output
        try:
            pylint.lint.Run([temp_path, "--output-format=text", "--score=no"], do_exit=False)
        except SystemExit:
            pass
        finally:
            sys.stdout = sys.__stdout__
        
        # Cleanup
        os.unlink(temp_path)
        
        # Parse output for codes
        # Format: "filename:line: [code(message), ...]"
        codes = []
        for line in output.getvalue().split('\n'):
            if '[' in line and ']' in line:
                # Extract code (e.g., C0111)
                import re
                matches = re.findall(r'\[([A-Z]\d{4})', line)
                codes.extend(matches)
        
        return list(set(codes))
    except Exception as e:
        logger.error(f"Pylint analysis failed: {e}")
        return []

def normalize_pylint_smells(codes: List[str], mapping: Dict[str, str]) -> List[str]:
    """Normalize Pylint codes to canonical smell names."""
    normalized = []
    for code in codes:
        if code in mapping:
            normalized.append(mapping[code])
        else:
            logger.warning(f"Unmapped Pylint code: {code}")
            normalized.append(code) # Keep raw code if unmapped
    return normalized

def save_to_csv(data: List[Dict[str, Any]], filepath: str):
    """Save processed data to CSV."""
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
    logger.info(f"Saved {len(data)} rows to {filepath}")

def validate_output(filepath: str, required_columns: List[str]) -> bool:
    """Validate CSV schema."""
    if not os.path.exists(filepath):
        return False
    df = pd.read_csv(filepath)
    return all(col in df.columns for col in required_columns)

def run_pipeline():
    """Main pipeline execution."""
    # 1. Verify source
    verify_dataset_source("codeparrot/github-code", "train")
    
    # 2. Load stratified sample
    sample = load_sampled_functions()
    
    # 3. Load smell mapping
    mapping_path = os.path.join("contracts", "smell_mapping.json")
    if not os.path.exists(mapping_path):
        logger.error("Smell mapping not found. Run T009a first.")
        return
    with open(mapping_path, 'r') as f:
        smell_mapping = json.load(f)
    
    results = []
    batch_metrics = []
    
    for i in range(0, len(sample), BATCH_SIZE):
        batch = sample[i:i+BATCH_SIZE]
        batch_start = time.time()
        batch_ram = []
        batch_cpu = []
        
        for item in batch:
            code = item.get("code", "")
            if not code:
                continue
            
            # Metrics
            radon_metrics = compute_radon_metrics(code)
            
            # Pylint
            raw_codes = run_pylint_analysis(code)
            normalized_smells = normalize_pylint_smells(raw_codes, smell_mapping)
            
            results.append({
                "code": code,
                "loc": radon_metrics["loc"],
                "cyclomatic_complexity": radon_metrics["cyclomatic_complexity"],
                "nesting_depth": radon_metrics["nesting_depth"],
                "static_smell_labels": ",".join(normalized_smells)
            })
            
            # Monitoring
            batch_ram.append(get_ram_usage_mb())
            batch_cpu.append(get_cpu_utilization())
        
        batch_time = time.time() - batch_start
        batch_metrics.append({
            "batch_id": i // BATCH_SIZE,
            "ram_mb": sum(batch_ram) / len(batch_ram) if batch_ram else 0,
            "cpu_util": sum(batch_cpu) / len(batch_cpu) if batch_cpu else 0,
            "time_sec": batch_time
        })
        
        # Record batch metrics
        record_batch_metrics(batch_metrics[-1])
    
    # Save metrics
    save_metrics_to_file()
    
    # 4. Save results
    output_path = os.path.join(get_data_path(), "static_baseline.csv")
    save_to_csv(results, output_path)
    
    # 5. Validate
    if not validate_output(output_path, ["code", "loc", "cyclomatic_complexity", "nesting_depth", "static_smell_labels"]):
        logger.error("Output validation failed.")
        return False
    
    logger.info("Pipeline completed successfully.")
    return True

if __name__ == "__main__":
    run_pipeline()
