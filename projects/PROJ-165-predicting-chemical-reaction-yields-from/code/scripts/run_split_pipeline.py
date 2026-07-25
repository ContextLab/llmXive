"""
Script to execute the reaction template splitting pipeline (T017a).

This script:
1. Loads the raw data from data/raw/
2. Extracts reaction templates
3. Performs strict template-based splitting
4. Verifies zero overlap
5. Generates output artifacts:
   - data/processed/split_indices.parquet
   - data/artifacts/split_manifest.json

Usage:
    python scripts/run_split_pipeline.py --data-path data/raw/molspectra.csv --output-dir data/

Note: This script expects the raw data to be available. If not, it will fail loudly.
"""

import argparse
import logging
import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.preprocessing import load_and_preprocess, verify_reaction_template_split

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Run reaction template splitting pipeline')
    parser.add_argument('--data-path', type=str, required=True,
                      help='Path to raw data file (CSV or Parquet)')
    parser.add_argument('--output-dir', type=str, default='data/',
                      help='Output directory for artifacts')
    parser.add_argument('--template-col', type=str, default='reaction_template',
                      help='Column name for reaction templates')
    parser.add_argument('--condition-cols', type=str, nargs='+', default=None,
                      help='Condition columns to use in splitting')
    parser.add_argument('--smiles-col', type=str, default='reactant_smiles',
                      help='Column name for SMILES strings')
    parser.add_argument('--energy-col', type=str, default='dft_total_energy',
                      help='Column name for target energy')
    parser.add_argument('--train-ratio', type=float, default=0.8,
                      help='Training set ratio')
    parser.add_argument('--val-ratio', type=float, default=0.1,
                      help='Validation set ratio')
    parser.add_argument('--test-ratio', type=float, default=0.1,
                      help='Test set ratio')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    logger.info(f"Starting splitting pipeline with data from: {args.data_path}")
    logger.info(f"Output directory: {args.output_dir}")
    
    # Validate input
    data_path = Path(args.data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run preprocessing pipeline
    result = load_and_preprocess(
        data_path=data_path,
        template_col=args.template_col,
        condition_cols=args.condition_cols,
        smiles_col=args.smiles_col,
        energy_col=args.energy_col,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
        output_dir=output_dir / 'processed'
    )
    
    # Log results
    manifest = result['manifest']
    logger.info(f"Split completed successfully!")
    logger.info(f"Train: {manifest['train_count']} samples")
    logger.info(f"Val: {manifest['val_count']} samples")
    logger.info(f"Test: {manifest['test_count']} samples")
    logger.info(f"Overlap check passed: {manifest['overlap_check']}")
    logger.info(f"Conditions used: {manifest['conditions_used']}")
    
    # Write summary to artifacts
    summary_path = output_dir / 'artifacts' / 'split_summary.json'
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, 'w') as f:
        json.dump({
            'status': 'success',
            'manifest': manifest,
            'config': {
                'data_path': str(data_path),
                'seed': args.seed,
                'ratios': {
                    'train': args.train_ratio,
                    'val': args.val_ratio,
                    'test': args.test_ratio
                }
            }
        }, f, indent=2)
    
    logger.info(f"Summary written to: {summary_path}")
    logger.info("Pipeline execution complete.")

if __name__ == '__main__':
    main()
