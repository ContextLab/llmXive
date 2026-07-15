"""
Test script to validate architecture matching between baseline and dendritic transformers.
This script is invoked by the run-book to verify FR-002 (computational parity).

It instantiates both models, calculates FLOPs and parameters, verifies the match
within tolerance, and writes a JSON report to artifacts/results/architecture_match_report.json.
"""
import os
import sys
import argparse
import logging
import json

# Ensure the project root (parent of code/) is in the path for imports
# The script is at code/tests/test_architecture_match.py
# Project root is the parent of 'code'
script_dir = os.path.dirname(os.path.abspath(__file__))
code_dir = os.path.dirname(script_dir)
project_root = os.path.dirname(code_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import models and utils
# These are defined in T007 (transformer_base), T011 (transformer_dendritic), T005 (utils)
from models.transformer_base import TransformerBaseline
from models.transformer_dendritic import TransformerDendritic
from models.utils import calc_flops

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Runs the architecture match validation.
    1. Instantiates both models with default config.
    2. Calculates FLOPs and Parameters.
    3. Verifies diff < 0.1% for params and < 1% for FLOPs.
    4. Writes results to artifacts/results/architecture_match_report.json.
    """
    logger.info("Starting architecture match validation...")

    # Configuration for testing (matching T004 defaults where applicable)
    # Hidden dim adjusted by T014 logic to match FLOPs
    base_cfg = {
        'd_model': 256,
        'n_heads': 4,
        'n_layers': 2,
        'd_ff': 512,
        'max_seq_len': 128,
        'vocab_size': 1000,
        'dendritic_thresholds': [0.1, 0.5, 0.9]
    }

    try:
        # Instantiate models
        logger.info("Instantiating TransformerBaseline...")
        model_baseline = TransformerBaseline(**base_cfg)
        
        logger.info("Instantiating TransformerDendritic...")
        # The dendritic model constructor handles internal adjustments (T014)
        model_dendritic = TransformerDendritic(**base_cfg)

        # Calculate metrics
        # Input shape: (batch_size, seq_len, d_model)
        input_shape = (2, 128, 256) 
        
        flops_baseline = calc_flops(model_baseline, input_shape)
        params_baseline = sum(p.numel() for p in model_baseline.parameters())
        
        flops_dendritic = calc_flops(model_dendritic, input_shape)
        params_dendritic = sum(p.numel() for p in model_dendritic.parameters())

        # Calculate differences
        param_diff = abs(params_baseline - params_dendritic)
        param_diff_pct = (param_diff / params_baseline) * 100 if params_baseline > 0 else 0.0
        
        flop_diff = abs(flops_baseline - flops_dendritic)
        flop_diff_pct = (flop_diff / flops_baseline) * 100 if flops_baseline > 0 else 0.0

        # Validation thresholds (FR-002)
        PARAM_TOL = 0.1  # 0.1%
        FLOP_TOL = 1.0   # 1.0%

        logger.info(f"Baseline - Params: {params_baseline:,}, FLOPs: {flops_baseline:,}")
        logger.info(f"Dendritic - Params: {params_dendritic:,}, FLOPs: {flops_dendritic:,}")
        logger.info(f"Param Diff: {param_diff_pct:.4f}% (Threshold: {PARAM_TOL}%)")
        logger.info(f"FLOP Diff: {flop_diff_pct:.4f}% (Threshold: {FLOP_TOL}%)")

        # Structural check: Ensure DendriticBranch class exists and is used
        # T011 requires explicit implementation of "branch" sub-units
        has_dendritic_branch = False
        try:
            from models.transformer_dendritic import DendriticBranch
            has_dendritic_branch = any(isinstance(m, DendriticBranch) for m in model_dendritic.modules())
        except ImportError:
            logger.warning("DendriticBranch class not found in models.transformer_dendritic")
            has_dendritic_branch = False

        success = (
            param_diff_pct < PARAM_TOL and
            flop_diff_pct < FLOP_TOL and
            has_dendritic_branch
        )

        # Generate Report
        report = {
            "status": "PASS" if success else "FAIL",
            "baseline": {
                "params": params_baseline,
                "flops": flops_baseline
            },
            "dendritic": {
                "params": params_dendritic,
                "flops": flops_dendritic
            },
            "differences": {
                "param_diff_pct": param_diff_pct,
                "flop_diff_pct": flop_diff_pct
            },
            "thresholds": {
                "param_tol": PARAM_TOL,
                "flop_tol": FLOP_TOL
            },
            "structural_validation": {
                "has_dendritic_branch": has_dendritic_branch
            }
        }

        # Ensure output directory exists
        output_dir = os.path.join(project_root, "artifacts", "results")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "architecture_match_report.json")

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Report written to {output_path}")

        if not success:
            logger.error("Architecture match validation FAILED.")
            sys.exit(1)
        else:
            logger.info("Architecture match validation PASSED.")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()