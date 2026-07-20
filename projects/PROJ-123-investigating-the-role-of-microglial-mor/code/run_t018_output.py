import os
import sys
import logging
from pathlib import Path

from code.config import get_path, ensure_dirs, set_seed, load_config
from code.synthetic_data import run_synthetic_pipeline
from code.output_metrics import run_output_pipeline
from code.morphometry import process_microglia_image
from code.data_ingestion import run_ingestion_pipeline_with_exclusion

logger = logging.getLogger(__name__)

def main():
    """
    Execute the T018 output pipeline.
    
    This script:
    1. Loads data (preferring real data, falling back to synthetic for validation only if configured).
    2. Processes images to extract morphological metrics.
    3. Writes the final CSV to data/processed/morphological_metrics.csv.
    """
    config = load_config()
    set_seed(config.get('SEED', 42))
    
    # Setup logging
    log_path = get_path('logs', 't018_output.log')
    ensure_dirs(log_path)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger.info("Starting T018 Output Pipeline")
    
    # Check if real data path is configured
    use_real_data = config.get('USE_REAL_DATA', False)
    
    processed_records = []
    
    if use_real_data:
        logger.info("Attempting real data ingestion path (T012a)...")
        # This will fail loudly if real data is not available
        image_paths, metadata_list = run_ingestion_pipeline_with_exclusion()
        
        for img_path, meta in zip(image_paths, metadata_list):
            # Process image using the pipeline functions from T013-T017
            try:
                metrics = process_microglia_image(img_path)
                if metrics:
                    record = {
                        'file_path': img_path,
                        'brain_region': meta.get('brain_region'),
                        'pathology_status': meta.get('pathology_status'),
                        'branch_points': metrics['branch_points'],
                        'total_length': metrics['total_length'],
                        'soma_area': metrics['soma_area'],
                        'sholl_intersections': metrics['sholl_intersections']
                    }
                    processed_records.append(record)
            except Exception as e:
                logger.error(f"Failed to process {img_path}: {e}")
    else:
        logger.info("Using synthetic data path for validation (T012b)...")
        # Generate synthetic data for validation
        synthetic_data = run_synthetic_pipeline()
        
        for item in synthetic_data:
            processed_records.append({
                'file_path': item.get('file_path', 'synthetic'),
                'brain_region': item.get('brain_region'),
                'pathology_status': item.get('pathology_status'),
                'branch_points': item.get('branch_points'),
                'total_length': item.get('total_length'),
                'soma_area': item.get('soma_area'),
                'sholl_intersections': item.get('sholl_intersections')
            })

    if not processed_records:
        logger.error("No records processed. T018 cannot complete.")
        sys.exit(1)

    # Write output CSV
    output_path = run_output_pipeline(processed_records)
    
    if output_path:
        logger.info(f"T018 Complete. Output written to: {output_path}")
    else:
        logger.error("Failed to write output CSV.")
        sys.exit(1)

if __name__ == "__main__":
    main()
