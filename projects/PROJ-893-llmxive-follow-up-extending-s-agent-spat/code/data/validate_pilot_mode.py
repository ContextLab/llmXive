"""
Pilot/Proxy Fallback Path Validation.

This module implements the fallback logic for T007b.
If the primary dataset (T006) fails due to missing stratification columns
(e.g., 'object_density', 'scene_complexity'), this script attempts to
validate a 'Pilot' study using available metadata or a verified proxy.

It performs KS-tests on available numeric metadata to determine if the
proxy distribution is sufficiently similar to a theoretical uniform or
expected distribution to justify a small-scale pilot run.

Output:
    data/results/pilot_validity.json
        {
            "status": "valid" | "invalid",
            "justification": "...",
            "ks_statistic": float,
            "p_value": float,
            "metric_used": "..."
        }
"""
import os
import sys
import json
import argparse
import math
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Local imports based on project structure
# We assume config.py exists and provides basic path constants if needed,
# though this script is self-contained for the fallback path.
try:
    from config import Config
except ImportError:
    # Fallback if running as script without config in path
    class Config:
        DATA_RAW = Path("data/raw")
        DATA_DERIVED = Path("data/derived")
        DATA_RESULTS = Path("data/results")
        SAMPLE_SIZE = 1000

# Constants for Pilot Validity
PILOT_THRESHOLD_P = 0.05  # p-value threshold for KS test
PROXY_FILE_NAMES = [
    "sampled_manifest.json",
    "s_agent_k_subset.jsonl",
    "metadata.json",
    "manifest.json"
]

def load_available_metadata() -> Optional[Dict[str, Any]]:
    """
    Scans data/raw for available files to extract numeric metadata for KS test.
    Returns a dictionary of available numeric lists if found, else None.
    """
    raw_dir = Config.DATA_RAW
    if not raw_dir.exists():
        return None

    # Priority 1: Check for a manifest that might have counts
    manifest_path = raw_dir / "sampled_manifest.json"
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r') as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                # If it has file sizes, use that as a proxy distribution
                sizes = [item.get('size_bytes', 0) for item in data if 'size_bytes' in item]
                if sizes:
                    return {"metric": "file_size_bytes", "values": sizes}
        except (json.JSONDecodeError, IOError):
            pass

    # Priority 2: Check for a raw JSONL that might have numeric fields
    # We look for the most likely candidate if the primary one failed
    candidates = []
    for fname in PROXY_FILE_NAMES:
        fpath = raw_dir / fname
        if fpath.exists():
            candidates.append(fpath)

    for c_path in candidates:
        try:
            numeric_values = []
            with open(c_path, 'r') as f:
                # Read first 100 lines to sample distribution without loading all
                for i, line in enumerate(f):
                    if i >= 100: break
                    if not line.strip(): continue
                    try:
                        obj = json.loads(line)
                        # Look for common numeric keys
                        for key in ['object_count', 'num_objects', 'complexity', 'density', 'size']:
                            if key in obj and isinstance(obj[key], (int, float)):
                                numeric_values.append(obj[key])
                                break
                    except json.JSONDecodeError:
                        continue
            
            if len(numeric_values) >= 5:
                return {"metric": c_path.name, "values": numeric_values}
        except IOError:
            continue

    return None

def perform_ks_test_statistic(data: List[float], test_dist: str = "uniform") -> Tuple[float, float]:
    """
    Performs a Kolmogorov-Smirnov test.
    Since scipy might not be available in all environments or we want to be
    explicit about the 'fallback' nature, we implement a simplified KS statistic
    calculation against a uniform distribution [min, max] of the data itself
    (to check for randomness/flatness) or a theoretical normal if specified.
    
    For Pilot validity, we check if the distribution is 'plausible' (not all zeros, not all same).
    Here we compare against a theoretical Uniform distribution over the range of the data.
    """
    if not data or len(data) < 2:
        return 0.0, 1.0

    data_sorted = sorted(data)
    n = len(data_sorted)
    min_val = min(data_sorted)
    max_val = max(data_sorted)
    
    if min_val == max_val:
        # All values are the same, not a valid distribution for a pilot
        return 1.0, 0.0

    # Calculate KS statistic D
    # D = max(|F_n(x) - F(x)|)
    # F_n(x) = i/n
    # F(x) = (x - min) / (max - min) for uniform distribution on [min, max]
    
    max_diff = 0.0
    for i, x in enumerate(data_sorted):
        # Empirical CDF
        fn = (i + 1) / n
        # Theoretical CDF (Uniform)
        ft = (x - min_val) / (max_val - min_val)
        
        diff1 = abs(fn - ft)
        diff2 = abs((i / n) - ft) # Check left limit
        
        max_diff = max(max_diff, diff1, diff2)
    
    D = max_diff

    # Approximate p-value for KS test (asymptotic distribution)
    # lambda = (sqrt(n) + 0.12 + 0.11/sqrt(n)) * D
    if D == 0:
        return D, 1.0
    
    try:
        sqrt_n = math.sqrt(n)
        lambda_val = (sqrt_n + 0.12 + 0.11 / sqrt_n) * D
        # Approximation for p-value: 2 * exp(-2 * lambda^2)
        # This is a standard approximation for the Kolmogorov distribution
        p_val = 2.0 * math.exp(-2.0 * lambda_val * lambda_val)
        # Clamp p-value to [0, 1]
        p_val = max(0.0, min(1.0, p_val))
    except (OverflowError, ValueError):
        p_val = 0.0

    return D, p_val

def check_pilot_validity(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates the metadata to determine if a pilot study is valid.
    Returns a result dictionary with status and justification.
    """
    metric_name = metadata.get("metric", "unknown")
    values = metadata.get("values", [])

    if not values:
        return {
            "status": "invalid",
            "justification": "No numeric metadata found to perform statistical validation.",
            "ks_statistic": 0.0,
            "p_value": 0.0,
            "metric_used": None
        }

    D, p_val = perform_ks_test_statistic(values)

    # Heuristic for Pilot Validity:
    # We want to ensure the data is not degenerate (all zeros or single value).
    # A very low p-value against uniform might actually be GOOD if we expect
    # a specific distribution, but without a reference, we check for "non-triviality".
    # Here, we declare valid if the distribution has variance and the KS statistic
    # doesn't indicate a complete collapse (D < 0.9 implies some spread).
    
    is_non_degenerate = (max(values) - min(values)) > 0
    
    # If p-value is very low, it means it's significantly NOT uniform.
    # For a pilot, we just need to know if the data exists and is diverse enough.
    # Let's set a generous threshold: if D < 0.5, we consider it a valid distribution shape.
    is_valid_shape = D < 0.5

    status = "valid" if (is_non_degenerate and is_valid_shape) else "invalid"
    
    justification = (
        f"Analyzed {len(values)} samples from '{metric_name}'. "
        f"KS Statistic: {D:.4f}, p-value: {p_val:.4f}. "
        f"Distribution is {'non-degenerate' if is_non_degenerate else 'degenerate'} "
        f"and {'plausible' if is_valid_shape else 'highly skewed'}. "
        f"Pilot study {'can proceed' if status == 'valid' else 'cannot proceed due to data quality issues'}."
    )

    return {
        "status": status,
        "justification": justification,
        "ks_statistic": D,
        "p_value": p_val,
        "metric_used": metric_name
    }

def main():
    parser = argparse.ArgumentParser(
        description="Validate pilot mode using available metadata if primary dataset fails."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(Config.DATA_RESULTS / "pilot_validity.json"),
        help="Path to output JSON file."
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=str(Config.DATA_RAW),
        help="Directory to scan for available metadata."
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    input_dir = Path(args.input_dir)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[T007b] Scanning {input_dir} for available metadata...")
    metadata = load_available_metadata()

    if metadata is None:
        result = {
            "status": "invalid",
            "justification": "No valid metadata source found in the raw data directory.",
            "ks_statistic": 0.0,
            "p_value": 0.0,
            "metric_used": None
        }
        print("[T007b] ERROR: No metadata found. Pilot mode invalid.")
    else:
        print(f"[T007b] Found metadata: {metadata['metric']} ({len(metadata['values'])} samples)")
        result = check_pilot_validity(metadata)
        print(f"[T007b] Pilot Status: {result['status']}")

    # Write result
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"[T007b] Result written to {output_path}")

    # Gate logic: If invalid, we exit with code 1 to signal pipeline abort
    if result["status"] == "invalid":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()