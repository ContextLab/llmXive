import argparse
import logging
import sys
from pathlib import Path
from src.pipelines.ingest import ingest_and_report
from src.pipelines.analysis import run_stratification_pipeline, load_cleaned_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Fungal Community Analysis Pipeline')
    parser.add_argument('--mode', choices=['validation', 'research'], default='research',
                      help='Mode of operation: validation or research')
    parser.add_argument('--stratify-by', type=str, default=None,
                      help='Column name to stratify analysis by (e.g., biome)')
    parser.add_argument('--output-dir', type=str, default='results',
                      help='Output directory for results')
    parser.add_argument('--data-dir', type=str, default='data',
                      help='Input data directory')
    parser.add_argument('--sweep-thresholds', action='store_true',
                      help='Run threshold sweep for sensitivity analysis')
    return parser.parse_args()

def validate_args(args):
    """Validate parsed arguments."""
    if args.mode not in ['validation', 'research']:
        raise ValueError(f"Invalid mode: {args.mode}. Must be 'validation' or 'research'.")
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    return True

def main():
    """Main entry point for the pipeline."""
    args = parse_args()
    validate_args(args)
    
    logger.info(f"Starting pipeline in {args.mode} mode")
    logger.info(f"Output directory: {args.output_dir}")
    
    # Example: Ingest data
    # In a real scenario, we would load dataset IDs and URLs from a config or file
    dataset_ids = ['dataset1', 'dataset2']
    urls = {
        'dataset1': 'https://example.com/dataset1.fastq.gz',
        'dataset2': 'https://example.com/dataset2.fastq.gz'
    }
    metadata_paths = [
        str(Path(args.data_dir) / 'metadata1.csv'),
        str(Path(args.data_dir) / 'metadata2.csv')
    ]
    
    try:
        metadata_df = ingest_and_report(dataset_ids, urls, metadata_paths, args.data_dir)
        
        if args.stratify_by:
            logger.info(f"Running stratified analysis by {args.stratify_by}")
            run_stratification_pipeline(metadata_df, args.stratify_by, args.output_dir)
        
        if args.sweep_thresholds:
            logger.info("Running threshold sweep for sensitivity analysis")
            from src.pipelines.report import run_report_pipeline_with_null_handling
            permanova_path = Path(args.output_dir) / 'permanova_summary.csv'
            sensitivity_path = Path(args.output_dir) / 'sensitivity_analysis.csv'
            robustness_path = Path(args.output_dir) / 'robustness_summary.md'
            
            if permanova_path.exists():
                run_report_pipeline_with_null_handling(
                    str(permanova_path),
                    str(sensitivity_path),
                    str(robustness_path)
                )
            else:
                logger.warning(f"PERMANOVA results not found at {permanova_path}. Skipping threshold sweep.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
    
    logger.info("Pipeline completed successfully")

if __name__ == '__main__':
    main()