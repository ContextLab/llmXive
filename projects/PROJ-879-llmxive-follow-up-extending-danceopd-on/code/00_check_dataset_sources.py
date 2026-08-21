import argparse
import sys
import json
from pathlib import Path
import pandas as pd
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def validate_dataset_sources(
    parquet_path: Path,
    min_samples: int = 1000,
    required_sources: list = None
) -> dict:
    """
    Validate that the dataset contains samples from both ImageNet-1K and LAION-400M.
    
    Args:
        parquet_path: Path to the teacher_routing_dataset.parquet file.
        min_samples: Minimum required number of samples.
        required_sources: List of source identifiers to check for.
    
    Returns:
        dict: Validation result with status, counts, and error messages.
    """
    if required_sources is None:
        required_sources = ['imagenet', 'laion']
    
    result = {
        'status': 'failed',
        'file_path': str(parquet_path),
        'total_samples': 0,
        'source_counts': {},
        'missing_sources': [],
        'errors': [],
        'warnings': []
    }
    
    # Check if file exists
    if not parquet_path.exists():
        result['errors'].append(f"File not found: {parquet_path}")
        return result
    
    try:
        # Load the dataset
        logger.info(f"Loading dataset from {parquet_path}...")
        df = pd.read_parquet(parquet_path)
        
        result['total_samples'] = len(df)
        
        # Check minimum sample size
        if len(df) < min_samples:
            result['errors'].append(
                f"Dataset size ({len(df)}) is below minimum required ({min_samples})."
            )
            # Save partial status report
            partial_status = {
                'status': 'insufficient_data',
                'total_samples': len(df),
                'min_required': min_samples,
                'source_counts': {},
                'timestamp': pd.Timestamp.now().isoformat()
            }
            partial_path = parquet_path.parent / 'source_validation_partial.json'
            with open(partial_path, 'w') as f:
                json.dump(partial_status, f, indent=2)
            logger.warning(f"Saved partial status to {partial_path}")
            return result
        
        # Identify source column
        source_column = None
        possible_columns = ['source', 'dataset_source', 'data_source', 'source_type']
        for col in possible_columns:
            if col in df.columns:
                source_column = col
                break
        
        if source_column is None:
            # Try to infer from existing columns
            available_cols = list(df.columns)
            result['errors'].append(
                f"Could not find source column. Available columns: {available_cols}"
            )
            return result
        
        # Count samples by source
        source_counts = df[source_column].value_counts().to_dict()
        result['source_counts'] = {str(k): int(v) for k, v in source_counts.items()}
        
        # Check for required sources
        missing = []
        for source in required_sources:
            found = False
            for key in source_counts.keys():
                if source.lower() in str(key).lower():
                    found = True
                    break
            if not found:
                missing.append(source)
        
        if missing:
            result['missing_sources'] = missing
            result['errors'].append(
                f"Missing required sources: {missing}. Found: {list(source_counts.keys())}"
            )
        else:
            result['status'] = 'verified'
            logger.info(f"Validation passed. Found sources: {list(source_counts.keys())}")
            logger.info(f"Total samples: {len(df)}")
            
            # Save success report
            success_report = {
                'status': 'verified',
                'total_samples': len(df),
                'source_counts': result['source_counts'],
                'min_required': min_samples,
                'timestamp': pd.Timestamp.now().isoformat()
            }
            report_path = parquet_path.parent / 'source_validation_report.json'
            with open(report_path, 'w') as f:
                json.dump(success_report, f, indent=2)
            logger.info(f"Saved validation report to {report_path}")
        
    except Exception as e:
        result['errors'].append(f"Error processing dataset: {str(e)}")
        logger.error(f"Error processing dataset: {str(e)}", exc_info=True)
    
    return result

def main():
    """Main entry point for dataset source validation."""
    parser = argparse.ArgumentParser(
        description='Validate dataset sources in teacher_routing_dataset.parquet'
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='Path to the parquet file. Defaults to data/processed/teacher_routing_dataset.parquet'
    )
    parser.add_argument(
        '--min-samples',
        type=int,
        default=1000,
        help='Minimum required number of samples (default: 1000)'
    )
    parser.add_argument(
        '--sources',
        type=str,
        nargs='+',
        default=None,
        help='Space-separated list of required sources (default: imagenet laion)'
    )
    
    args = parser.parse_args()
    
    project_root = get_project_root()
    
    if args.input:
        parquet_path = Path(args.input)
    else:
        parquet_path = project_root / 'data' / 'processed' / 'teacher_routing_dataset.parquet'
    
    required_sources = args.sources if args.sources else ['imagenet', 'laion']
    
    logger.info(f"Validating dataset sources for: {parquet_path}")
    logger.info(f"Required sources: {required_sources}")
    logger.info(f"Minimum samples: {args.min_samples}")
    
    result = validate_dataset_sources(
        parquet_path=parquet_path,
        min_samples=args.min_samples,
        required_sources=required_sources
    )
    
    # Output result
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    if result['status'] == 'verified':
        logger.info("Validation PASSED")
        sys.exit(0)
    else:
        logger.error("Validation FAILED")
        if result.get('errors'):
            for err in result['errors']:
                logger.error(f"  - {err}")
        sys.exit(1)

if __name__ == '__main__':
    main()