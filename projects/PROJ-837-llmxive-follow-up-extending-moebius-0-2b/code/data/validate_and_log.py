"""
Script to execute T016 validation logic and produce validation_log.txt.

This script:
1. Loads scores from data/annotations/decoupled_scores.csv (CI) or human_scores.csv (Research)
2. Validates sample size >= 50
3. Validates label independence (if metrics available)
4. Logs results to data/results/validation_log.txt
5. Raises errors on failure (no silent fallback)
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import is_ci_mode, is_research_mode, get_mode
from data.annotator import (
    load_research_annotations,
    validate_sample_size,
    validate_label_independence,
    log_validation
)
from eval.stats import load_mask_metrics_csv
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    """Execute T016 validation pipeline."""
    parser = argparse.ArgumentParser(description='T016: Validate sample size and label independence')
    parser.add_argument('--mode', choices=['auto', 'ci', 'research'], default='auto',
                      help='Mode selection (default: auto detect from config)')
    parser.add_argument('--scores', type=str, default=None,
                      help='Path to scores CSV (auto-detected if not provided)')
    parser.add_argument('--metrics', type=str, default=None,
                      help='Path to mask metrics CSV')
    parser.add_argument('--log', type=str, default='data/results/validation_log.txt',
                      help='Output validation log file')
    
    args = parser.parse_args()
    
    # Determine mode
    if args.mode == 'auto':
        mode = get_mode()
    else:
        mode = args.mode
    
    logger.info(f"Starting T016 validation in {mode.upper()} mode")
    
    # Set paths
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    if mode == 'ci':
        scores_path = Path(args.scores) if args.scores else Path('data/annotations/decoupled_scores.csv')
        metrics_path = None
    else:
        scores_path = Path(args.scores) if args.scores else Path('data/annotations/human_scores.csv')
        metrics_path = Path(args.metrics) if args.metrics else Path('data/processed/mask_metrics.csv')
    
    # Log start
    log_validation(f"[{mode.upper()}] Starting validation: sample size >= 50, independence check", log_path)
    
    try:
        # Load scores
        if mode == 'ci':
            # CI mode: load decoupled scores
            import csv
            scores = []
            if not scores_path.exists():
                raise FileNotFoundError(f"CI mode requires {scores_path} but file not found")
            
            with open(scores_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    scores.append({
                        'image_id': row['image_id'],
                        'score': float(row['score']),
                        'mode': row.get('mode', 'CI_MODE')
                    })
        else:
            # Research mode: load human annotations
            scores = load_research_annotations(scores_path)
        
        if len(scores) == 0:
            raise ValueError("No scores loaded from file")
        
        logger.info(f"Loaded {len(scores)} scores from {scores_path}")
        log_validation(f"Loaded {len(scores)} scores from {scores_path}", log_path)
        
        # Validate sample size
        try:
            validate_sample_size(scores)
            log_validation(f"[PASS] Sample size validation: {len(set(s['image_id'] for s in scores))} >= 50", log_path)
        except ValueError as e:
            log_validation(f"[FAIL] Sample size validation: {str(e)}", log_path)
            raise
        
        # Validate label independence if metrics available
        if metrics_path and metrics_path.exists():
            try:
                metrics = load_mask_metrics_csv(metrics_path)
                validate_label_independence(scores, metrics)
                log_validation(f"[PASS] Label independence validation passed", log_path)
            except FileNotFoundError:
                log_validation(f"[SKIP] Metrics file not found at {metrics_path}, skipping independence check", log_path)
            except ValueError as e:
                log_validation(f"[FAIL] Label independence validation: {str(e)}", log_path)
                raise
        else:
            log_validation(f"[SKIP] No metrics file, skipping independence check", log_path)
        
        log_validation(f"[COMPLETE] T016 validation successful", log_path)
        logger.info("T016 validation completed successfully")
        
    except Exception as e:
        log_validation(f"[ERROR] T016 validation failed: {str(e)}", log_path)
        logger.error(f"T016 validation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()