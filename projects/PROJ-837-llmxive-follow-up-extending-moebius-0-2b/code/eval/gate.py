import os
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from config import is_ci_mode, is_research_mode, get_mode, get_path
from utils.logger import get_logger, get_timestamp
from eval.stats import load_json, save_json, run_proxy_correlation_analysis

logger = get_logger(__name__)

def load_validation_result(path: str) -> Optional[Dict[str, Any]]:
    """Load a validation result JSON file if it exists."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load validation result from {path}: {e}")
        return None

def save_validation_result(data: Dict[str, Any], path: str) -> None:
    """Save validation results to a JSON file, ensuring directory exists."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved validation results to {path}")

def run_proxy_correlation_gate() -> Dict[str, Any]:
    """
    Execute the proxy correlation analysis and enforce the gate.
    
    This function:
    1. Runs the correlation analysis (Pearson r) between synthetic metrics 
       (gradient_variance, texture_entropy) and ground truth scores.
    2. Checks the correlation coefficient against the threshold (r >= 0.7).
    3. Enforces the gate:
       - RESEARCH Mode: If r < 0.7, raises SystemExit(1) to block downstream training.
       - CI Mode: Logs expected low correlation and continues.
    4. Persists results to data/results/proxy_validation.json.
    
    Returns:
        Dict containing the correlation result and gate status.
    """
    logger.info("Starting proxy correlation gate enforcement...")
    
    # Ensure the input files exist before proceeding
    mask_metrics_path = get_path('processed/mask_metrics.json')
    scores_path = get_path('annotations/decoupled_scores.csv') if is_ci_mode() else get_path('annotations/human_scores.csv')
    
    if not os.path.exists(mask_metrics_path):
        logger.error(f"Mask metrics file not found: {mask_metrics_path}")
        raise FileNotFoundError(f"Required file missing: {mask_metrics_path}")
    
    if not os.path.exists(scores_path):
        logger.error(f"Scores file not found: {scores_path}")
        raise FileNotFoundError(f"Required file missing: {scores_path}")
    
    # Run the correlation analysis
    result = run_proxy_correlation_analysis(mask_metrics_path, scores_path)
    
    r_value = result.get('pearson_r')
    gate_status = result.get('gate_status')
    mode = get_mode()
    
    output_path = get_path('results/proxy_validation.json')
    
    # Gate Logic Enforcement
    if mode == 'RESEARCH':
        if r_value < 0.7:
            logger.error(f"RESEARCH MODE: Proxy correlation r={r_value:.4f} < 0.7. GATE BLOCKED.")
            save_validation_result({
                'pearson_r': r_value,
                'gate_status': 'BLOCKED',
                'mode': mode,
                'timestamp': get_timestamp(),
                'reason': 'Correlation below threshold (r < 0.7) in Research Mode.'
            }, output_path)
            # CRITICAL: Unconditionally raise SystemExit to prevent downstream execution
            sys.exit(1)
        else:
            logger.info(f"RESEARCH MODE: Proxy correlation r={r_value:.4f} >= 0.7. GATE PASSED.")
    elif mode == 'CI':
        logger.info(f"CI MODE: Correlation r={r_value:.4f}. Expected behavior (simulation). Gate status: EXPECTED_LOW_CORRELATION")
        # In CI mode, we do not block, but we record the status as expected
        if gate_status != 'EXPECTED_LOW_CORRELATION':
            result['gate_status'] = 'EXPECTED_LOW_CORRELATION'
    else:
        logger.warning(f"Unknown mode: {mode}. Proceeding with caution.")

    # Persist the final result
    save_validation_result(result, output_path)
    
    logger.info(f"Proxy validation gate complete. Status: {result['gate_status']}, r={r_value:.4f}")
    return result

def main():
    """Entry point for the gate script."""
    parser = argparse.ArgumentParser(description="Run proxy correlation gate enforcement.")
    parser.parse_args()
    
    try:
        result = run_proxy_correlation_gate()
        print(json.dumps(result, indent=2))
    except FileNotFoundError as e:
        logger.error(f"Data missing for gate: {e}")
        sys.exit(2)
    except SystemExit as e:
        # Re-raise SystemExit if it was raised by the gate logic
        raise
    except Exception as e:
        logger.error(f"Gate execution failed: {e}")
        sys.exit(3)

if __name__ == '__main__':
    main()
