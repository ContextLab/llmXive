"""
CLI entry point for the llmXive automated science pipeline.

Orchestrates data loading, processing, narrative generation, and evaluation
based on command-line arguments.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Import from project modules
from config import get_config, set_config_override
from data.loader import load_all_datasets, RAMExceededError, LowPowerError, LowNumericColumnsError
from data.processor import process_dataset, generate_cleaning_report, generate_statistical_summaries
from narrative.flag_propagator import propagate_low_power_flag, write_propagated_report
from data.dataset_registry import verify_checksum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('output/pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='llmXive Automated Science Pipeline CLI',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--dataset', '-d',
        type=str,
        default=None,
        help='Specific dataset name from registry to process. If None, processes all valid datasets.'
    )
    
    parser.add_argument(
        '--stage', '-s',
        type=str,
        choices=['load', 'process', 'narrative', 'full'],
        default='full',
        help='Pipeline stage to execute'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='output',
        help='Directory for output files'
    )
    
    parser.add_argument(
        '--config-override',
        type=str,
        nargs='*',
        help='Key-value pairs to override execution config (e.g., --config-override ram_limit 4096)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()

def apply_config_overrides(overrides: Optional[List[str]]) -> None:
    """Apply configuration overrides from command line."""
    if not overrides:
        return
    
    if len(overrides) % 2 != 0:
        raise ValueError("Config overrides must be provided as key-value pairs")
    
    for i in range(0, len(overrides), 2):
        key = overrides[i]
        value = overrides[i + 1]
        set_config_override(key, value)
        logger.info(f"Config override: {key} = {value}")

def run_load_stage(dataset_name: Optional[str], output_dir: Path) -> List[dict]:
    """Execute the data loading stage."""
    logger.info(f"Starting data loading stage for dataset: {dataset_name or 'all'}")
    
    try:
        datasets = load_all_datasets(dataset_name=dataset_name)
        
        # Save loaded datasets metadata
        metadata_path = output_dir / "loaded_datasets.json"
        with open(metadata_path, 'w') as f:
            json.dump([
                {
                    'name': ds['name'],
                    'path': str(ds['path']),
                    'n_rows': len(ds['data']),
                    'n_columns': len(ds['data'].columns),
                    'numeric_columns': ds['numeric_columns']
                }
                for ds in datasets
            ], f, indent=2)
        
        logger.info(f"Loaded {len(datasets)} datasets. Metadata saved to {metadata_path}")
        return datasets
        
    except (RAMExceededError, LowPowerError, LowNumericColumnsError) as e:
        logger.error(f"Data loading failed: {str(e)}")
        raise

def run_process_stage(datasets: List[dict], output_dir: Path) -> List[dict]:
    """Execute the data processing stage."""
    logger.info(f"Starting data processing stage for {len(datasets)} datasets")
    
    processed_datasets = []
    
    for ds in datasets:
        logger.info(f"Processing dataset: {ds['name']}")
        
        try:
            # Detect and handle missing values
            missing_report = generate_cleaning_report(ds['data'])
            
            # Handle missing values and generate cleaned data
            cleaned_data, imputation_report = process_dataset(ds['data'])
            
            # Generate statistical summaries
            stats_summary = generate_statistical_summaries(cleaned_data)
            
            # Save processed data
            processed_path = output_dir / f"{ds['name']}_processed.csv"
            cleaned_data.to_csv(processed_path, index=False)
            
            # Save reports
            report_path = output_dir / f"{ds['name']}_reports.json"
            with open(report_path, 'w') as f:
                json.dump({
                    'missing_values': missing_report,
                    'imputation': imputation_report,
                    'statistics': stats_summary
                }, f, indent=2, default=str)
            
            processed_datasets.append({
                'name': ds['name'],
                'path': str(processed_path),
                'data': cleaned_data,
                'reports': report_path
            })
            
            logger.info(f"Successfully processed {ds['name']}")
            
        except Exception as e:
            logger.error(f"Failed to process {ds['name']}: {str(e)}")
            # Continue with other datasets
            continue
    
    logger.info(f"Completed processing {len(processed_datasets)} datasets")
    return processed_datasets

def run_narrative_stage(processed_datasets: List[dict], output_dir: Path) -> None:
    """Execute the narrative generation stage."""
    logger.info(f"Starting narrative generation stage for {len(processed_datasets)} datasets")
    
    narrative_results = []
    
    for ds in processed_datasets:
        logger.info(f"Generating narrative for dataset: {ds['name']}")
        
        try:
            # Propagate low power flags if applicable
            propagated_report = propagate_low_power_flag(ds['data'], ds['name'])
            
            # Save propagated report
            flag_path = output_dir / f"{ds['name']}_flags.json"
            write_propagated_report(propagated_report, flag_path)
            
            narrative_results.append({
                'dataset': ds['name'],
                'flag_report': str(flag_path),
                'status': 'success'
            })
            
            logger.info(f"Successfully generated narrative components for {ds['name']}")
            
        except Exception as e:
            logger.error(f"Failed to generate narrative for {ds['name']}: {str(e)}")
            narrative_results.append({
                'dataset': ds['name'],
                'status': 'failed',
                'error': str(e)
            })
            continue
    
    # Save summary
    summary_path = output_dir / "narrative_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(narrative_results, f, indent=2)
    
    logger.info(f"Narrative stage completed. Summary saved to {summary_path}")

def main():
    """Main entry point for the pipeline."""
    args = parse_arguments()
    
    # Apply config overrides if provided
    apply_config_overrides(args.config_override)
    
    # Set log level if verbose
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting llmXive pipeline with stage: {args.stage}")
    logger.info(f"Output directory: {output_dir}")
    
    try:
        # Execute pipeline stages
        if args.stage in ['load', 'full']:
            datasets = run_load_stage(args.dataset, output_dir)
        else:
            datasets = []
            logger.warning("Skipping load stage - no datasets available")
        
        if args.stage in ['process', 'full'] and datasets:
            processed_datasets = run_process_stage(datasets, output_dir)
        else:
            processed_datasets = []
            logger.warning("Skipping process stage - no datasets available")
        
        if args.stage in ['narrative', 'full'] and processed_datasets:
            run_narrative_stage(processed_datasets, output_dir)
        else:
            logger.warning("Skipping narrative stage - no processed datasets available")
        
        logger.info("Pipeline execution completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()