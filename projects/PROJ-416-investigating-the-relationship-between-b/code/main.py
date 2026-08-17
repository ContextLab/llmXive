import argparse
import logging
import sys
from pathlib import Path

from code.config import Config
from code.utils.logging import setup_logging
from code.data.download import run_download
from code.data.validate import run_validation
from code.data.preprocess import run_preprocessing
from code.data.save_metadata import run_save_metadata
from code.analysis.network import run_analysis as run_network_analysis
from code.analysis.stats import run_analysis as run_stats_analysis
from code.analysis.report import run_analysis as run_report_generation
from code.analysis.verify_power_analysis import run_verification

def parse_args():
    parser = argparse.ArgumentParser(description='Brain Network Dynamics Pipeline')
    parser.add_argument('--mode', choices=['download', 'validate', 'preprocess', 'analysis', 'full', 'verify'],
                        default='full', help='Pipeline mode')
    parser.add_argument('--max-subjects', type=int, default=20, help='Maximum number of subjects')
    parser.add_argument('--atlas', type=str, default='Schaefer-100', help='Atlas to use')
    parser.add_argument('--correction', type=str, default='fdr', help='Multiple comparison correction method')
    parser.add_argument('--sweep-motion', type=str, default='2.0,3.0', help='Motion thresholds to sweep')
    parser.add_argument('--sweep-pval', type=str, default='0.01,0.05,0.1', help='P-values to sweep')
    parser.add_argument('--sweep-outcome', type=str, default='change,residual,raw', help='Outcome definitions to sweep')
    parser.add_argument('--effect-size', type=float, default=0.15, help='Effect size for power analysis')
    parser.add_argument('--alpha', type=float, default=0.05, help='Alpha for power analysis')
    parser.add_argument('--power', type=float, default=0.8, help='Target power for power analysis')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode')
    parser.add_argument('--verify-gate', action='store_true', help='Verify the gate logic')
    
    return parser.parse_args()

def run_stage(mode: str, args):
    config = Config()
    
    if mode == 'download':
        logging.info("Running download stage...")
        run_download()
    elif mode == 'validate':
        logging.info("Running validation stage...")
        run_validation()
    elif mode == 'preprocess':
        logging.info("Running preprocessing stage...")
        run_preprocessing(max_subjects=args.max_subjects)
    elif mode == 'analysis':
        logging.info("Running analysis stage...")
        run_network_analysis()
        run_stats_analysis(
            correction=args.correction,
            sweep_motion=[float(x) for x in args.sweep_motion.split(',')],
            sweep_pval=[float(x) for x in args.sweep_pval.split(',')],
            sweep_outcome=args.sweep_outcome.split(',')
        )
    elif mode == 'full':
        logging.info("Running full pipeline...")
        run_download()
        run_validation()
        run_preprocessing(max_subjects=args.max_subjects)
        run_network_analysis()
        run_stats_analysis(
            correction=args.correction,
            sweep_motion=[float(x) for x in args.sweep_motion.split(',')],
            sweep_pval=[float(x) for x in args.sweep_pval.split(',')],
            sweep_outcome=args.sweep_outcome.split(',')
        )
        run_report_generation()
    elif mode == 'verify':
        logging.info("Running verification stage...")
        run_verification()
    else:
        raise ValueError(f"Unknown mode: {mode}")

def main():
    args = parse_args()
    
    # Setup logging
    setup_logging()
    
    try:
        run_stage(args.mode, args)
        logging.info("Pipeline completed successfully.")
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()