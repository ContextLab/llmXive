"""
Module to process retrieval results and save them to CSV.
Implements T020: Output generation for retrieval results.
"""
import os
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from config import get_config
from data_models import RetrievalResult, CensorshipStatus
from retrieval_output_schema import map_retrieval_result_to_schema
from utils import handle_non_convergent_retrieval, setup_logging

logger = logging.getLogger(__name__)


def process_retrieval_results(retrieval_results: List[RetrievalResult], output_path: Path) -> None:
    """
    Process a list of RetrievalResult objects and save them to a CSV file.

    Args:
        retrieval_results: List of RetrievalResult objects containing water abundance data.
        output_path: Path to the output CSV file.
    """
    config = get_config()
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Preparing to save {len(retrieval_results)} retrieval results to {output_path}")

    if not retrieval_results:
        logger.warning("No retrieval results to save. Creating empty CSV with headers.")
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'planet_name',
                'water_mixing_ratio',
                'uncertainty',
                'is_upper_limit',
                'detection_limit',
                'min_detectable_concentration'
            ])
        return

    # Define CSV headers based on T020 requirements
    fieldnames = [
        'planet_name',
        'water_mixing_ratio',
        'uncertainty',
        'is_upper_limit',
        'detection_limit',
        'min_detectable_concentration'
    ]

    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in retrieval_results:
                # Map the internal RetrievalResult to the output schema format
                # This handles the conversion of CensorshipStatus enum to boolean and ensures
                # all numeric values are properly formatted
                row_data = map_retrieval_result_to_schema(result)

                # Ensure numeric columns are formatted correctly (float or None)
                row_data['water_mixing_ratio'] = float(row_data['water_mixing_ratio']) if row_data['water_mixing_ratio'] is not None else ''
                row_data['uncertainty'] = float(row_data['uncertainty']) if row_data['uncertainty'] is not None else ''
                row_data['detection_limit'] = float(row_data['detection_limit']) if row_data['detection_limit'] is not None else ''
                row_data['min_detectable_concentration'] = float(row_data['min_detectable_concentration']) if row_data['min_detectable_concentration'] is not None else ''

                # is_upper_limit is already boolean from mapping
                writer.writerow(row_data)

        logger.info(f"Successfully saved {len(retrieval_results)} retrieval results to {output_path}")

    except IOError as e:
        logger.error(f"Failed to write retrieval results to {output_path}: {e}")
        raise


def main() -> None:
    """
    Main entry point for the retrieval output generation script.
    This function is designed to be called after retrieval results have been
    generated and stored, typically by the retrieval pipeline.
    """
    setup_logging()
    config = get_config()

    # Define paths based on project structure
    output_path = Path(config['output_dir']) / 'retrieval_results.csv'
    
    # In a real pipeline, retrieval_results would be loaded from a previous stage
    # For this implementation, we assume results are passed via config or loaded from a temporary store
    # In the actual pipeline flow, this would be called after T019 completes

    logger.info("Starting retrieval output generation (T020)")
    
    # This is a placeholder for the actual retrieval results that would be
    # loaded from the previous stage (T019). In the full pipeline, this data
    # would come from the retrieval engine.
    # For demonstration purposes, we'll simulate loading from a temporary JSON
    # that would be created by the retrieval stage.
    
    # In the actual implementation, the retrieval stage would write results
    # to a temporary file or database, and this stage would read from there.
    # For now, we'll assume the results are available via the config or a standard location.
    
    # Since we cannot run the full retrieval pipeline here (it requires real data),
    # we'll create a function that can be called with actual results.
    # The main() function serves as the entry point for the script when run standalone.
    
    # Load results from a temporary file if it exists (created by previous stage)
    temp_results_path = Path(config['output_dir']) / 'temp_retrieval_results.json'
    
    if temp_results_path.exists():
        import json
        with open(temp_results_path, 'r') as f:
            raw_results = json.load(f)
        
        # Convert raw JSON to RetrievalResult objects
        retrieval_results = []
        for item in raw_results:
            result = RetrievalResult(
                planet_name=item['planet_name'],
                water_mixing_ratio=item['water_mixing_ratio'],
                uncertainty=item['uncertainty'],
                censorship_status=CensorshipStatus(item['censorship_status']),
                detection_limit=item['detection_limit'],
                min_detectable_concentration=item['min_detectable_concentration']
            )
            retrieval_results.append(result)
        
        process_retrieval_results(retrieval_results, output_path)
    else:
        logger.warning("No temporary retrieval results found. Creating empty output file.")
        # Create empty CSV with headers to indicate the pipeline stage completed
        process_retrieval_results([], output_path)


if __name__ == "__main__":
    main()
