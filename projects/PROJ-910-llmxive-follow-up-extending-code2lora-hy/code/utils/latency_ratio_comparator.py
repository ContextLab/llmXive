"""
T049b: Compute latency reduction ratio between AST-based generation and baseline.

This module reads the AST generation latency (from T040) and the baseline
generation latency (from T049a), computes the reduction ratio, and verifies
if it meets the SC-001 requirement of >= 10x reduction.

Output: data/results/generation_latency_comparison.json
"""
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RESULTS_DIR = Path("data/results")
AST_LATENCY_FILE = RESULTS_DIR / "generation_latency.json"
BASELINE_LATENCY_FILE = RESULTS_DIR / "baseline_generation_latency.json"
OUTPUT_FILE = RESULTS_DIR / "generation_latency_comparison.json"

def ensure_results_dir() -> Path:
    """Ensure the results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return RESULTS_DIR

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def compute_latency_ratio(
    ast_latency_ms: float, 
    baseline_latency_ms: float
) -> Tuple[float, str]:
    """
    Compute the reduction ratio and status.
    
    Ratio = Baseline / AST (how many times faster AST is)
    """
    if ast_latency_ms <= 0:
        raise ValueError(f"AST latency must be positive, got {ast_latency_ms}")
    if baseline_latency_ms <= 0:
        raise ValueError(f"Baseline latency must be positive, got {baseline_latency_ms}")
    
    ratio = baseline_latency_ms / ast_latency_ms
    meets_requirement = ratio >= 10.0
    status = "PASS" if meets_requirement else "FAIL"
    
    return ratio, status

def generate_comparison_report(
    ast_latency_ms: float,
    baseline_latency_ms: float,
    ratio: float,
    status: str
) -> Dict[str, Any]:
    """Generate the comparison report dictionary."""
    reduction_percentage = ((baseline_latency_ms - ast_latency_ms) / baseline_latency_ms) * 100
    
    return {
        "ast_generation_latency_ms": ast_latency_ms,
        "baseline_generation_latency_ms": baseline_latency_ms,
        "latency_reduction_ratio": round(ratio, 4),
        "reduction_percentage": round(reduction_percentage, 2),
        "sc_001_requirement": ">= 10x reduction",
        "meets_requirement": status == "PASS",
        "status": status,
        "message": (
            f"AST generation is {ratio:.2f}x faster than baseline. "
            f"{'Requirement met.' if status == 'PASS' else 'Requirement NOT met.'}"
        )
    }

def save_comparison_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the comparison report to JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Comparison report saved to: {output_path}")

def run_latency_comparison() -> Dict[str, Any]:
    """
    Main entry point to run the latency comparison.
    
    Reads AST and baseline latencies, computes ratio, and saves report.
    """
    ensure_results_dir()
    
    logger.info("Loading AST generation latency...")
    try:
        ast_data = load_json_file(AST_LATENCY_FILE)
        # Handle potential variations in key names
        ast_latency_ms = ast_data.get("generation_latency_ms") or ast_data.get("latency_ms")
        if ast_latency_ms is None:
            raise ValueError(f"Could not find latency value in {AST_LATENCY_FILE}")
    except FileNotFoundError as e:
        logger.error(f"AST latency file missing. Did you run T040? Error: {e}")
        raise
    
    logger.info("Loading baseline generation latency...")
    try:
        baseline_data = load_json_file(BASELINE_LATENCY_FILE)
        baseline_latency_ms = baseline_data.get("generation_latency_ms") or baseline_data.get("latency_ms")
        if baseline_latency_ms is None:
            raise ValueError(f"Could not find latency value in {BASELINE_LATENCY_FILE}")
    except FileNotFoundError as e:
        logger.error(f"Baseline latency file missing. Did you run T049a? Error: {e}")
        raise
    
    logger.info(f"AST Latency: {ast_latency_ms:.2f} ms")
    logger.info(f"Baseline Latency: {baseline_latency_ms:.2f} ms")
    
    ratio, status = compute_latency_ratio(ast_latency_ms, baseline_latency_ms)
    
    logger.info(f"Latency Reduction Ratio: {ratio:.4f}x")
    logger.info(f"SC-001 Requirement (>= 10x): {status}")
    
    report = generate_comparison_report(ast_latency_ms, baseline_latency_ms, ratio, status)
    save_comparison_report(report, OUTPUT_FILE)
    
    return report

def main() -> int:
    """CLI entry point."""
    try:
        report = run_latency_comparison()
        print(json.dumps(report, indent=2))
        return 0 if report["meets_requirement"] else 1
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        return 2
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        return 3
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 4

if __name__ == "__main__":
    import sys
    sys.exit(main())
